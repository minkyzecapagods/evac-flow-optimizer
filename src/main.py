"""
main.py
=======
Interface de linha de comando (CLI) para o Evac-Flow Optimizer.

Uso:
  python src/main.py                    # modo interativo: lista instâncias disponíveis
  python src/main.py <arquivo.net>      # executa diretamente sobre o arquivo informado
  python src/main.py --tmax 300         # define horizonte máximo de busca

Saída:
  - Relatório impresso na tela
  - Relatório salvo em outputs/<nome_instancia>_relatorio.txt
"""

import sys
import os
import time
import datetime

# Garante que importações relativas funcionem independente de onde main.py é chamado
_SRC_DIR  = os.path.dirname(os.path.abspath(__file__))
_PROJ_DIR = os.path.dirname(_SRC_DIR)
sys.path.insert(0, _SRC_DIR)

from parser    import parse
from optimizer import find_min_T

# ── Constantes ───────────────────────────────────────────────────────────────
INSTANCES_DIR = os.path.join(_PROJ_DIR, 'instances')
OUTPUTS_DIR   = os.path.join(_PROJ_DIR, 'outputs')
DEFAULT_TMAX  = 200
SEPARATOR     = "=" * 65


def list_instances() -> list:
    """Retorna lista de arquivos .net no diretório instances/."""
    if not os.path.isdir(INSTANCES_DIR):
        return []
    return sorted(f for f in os.listdir(INSTANCES_DIR) if f.endswith('.net'))


def choose_instance(files: list) -> str:
    """Apresenta menu interativo e retorna o caminho do arquivo escolhido."""
    print("\n" + SEPARATOR)
    print("  EVAC-FLOW OPTIMIZER — Otimizador de Evacuação de Edifícios")
    print(SEPARATOR)
    print("\n  Instâncias disponíveis:\n")
    for i, f in enumerate(files, start=1):
        print(f"    [{i}] {f}")
    print()

    while True:
        raw = input("  Escolha o número da instância: ").strip()
        if raw.isdigit():
            idx = int(raw) - 1
            if 0 <= idx < len(files):
                return os.path.join(INSTANCES_DIR, files[idx])
        print("  Opção inválida. Tente novamente.")


def ask_tmax() -> int:
    """Pergunta ao usuário o horizonte máximo de tempo."""
    raw = input(f"  Horizonte máximo T_max [{DEFAULT_TMAX}]: ").strip()
    if raw.isdigit() and int(raw) > 0:
        return int(raw)
    return DEFAULT_TMAX


def build_report(filepath: str, static_graph: dict, result: dict, tmax: int) -> str:
    """Constrói o texto do relatório do experimento."""
    now      = datetime.datetime.now().strftime("%d/%m/%Y %H:%M:%S")
    basename = os.path.basename(filepath)

    lines = []
    lines.append(SEPARATOR)
    lines.append("  RELATÓRIO DO EXPERIMENTO — EVAC-FLOW OPTIMIZER")
    lines.append(SEPARATOR)
    lines.append(f"  Data/Hora       : {now}")
    lines.append(f"  Instância       : {basename}")
    lines.append(f"  Arquivo         : {filepath}")
    lines.append("")
    lines.append("  ── Estatísticas da Instância ──────────────────────────")
    lines.append(f"  Nós (grafo base): {static_graph['num_nodes']}")
    lines.append(f"  Arestas         : {static_graph['num_edges']}")
    lines.append(f"  Fontes (salas)  : {static_graph['sources']}")
    lines.append(f"  Sumidouros(saídas): {static_graph['sinks']}")
    lines.append(f"  População total : {static_graph['total_people']} pessoas")
    lines.append(f"  Horizonte T_max : {tmax}")
    lines.append("")
    lines.append("  ── Algoritmo ──────────────────────────────────────────")
    lines.append("  Método          : Grafo Expandido no Tempo + Edmonds-Karp")
    lines.append("  Busca de T*     : Busca Binária + Refinamento Local")
    lines.append("")
    lines.append("  ── Histórico de Iterações ─────────────────────────────")
    lines.append(f"  {'T':>5}  {'Fluxo':>8}  {'Pop.':>6}  {'Viável':>7}  {'Tempo(ms)':>10}")
    lines.append("  " + "-" * 44)
    for (T_it, flow_it, viavel_it, ms_it) in result['history']:
        v_str = "Sim" if viavel_it else "Não"
        lines.append(
            f"  {T_it:>5}  {flow_it:>8}  {result['total_people']:>6}  {v_str:>7}  {ms_it:>10.2f}"
        )
    lines.append("")
    lines.append("  ── Resultado ──────────────────────────────────────────")

    if result['feasible']:
        lines.append(f"  ✓ Evacuação VIÁVEL dentro de T_max = {tmax}")
        lines.append(f"  T* mínimo       : {result['T_min']} unidades de tempo")
        lines.append(f"  Fluxo máximo    : {result['flow']} pessoas")
        lines.append(f"  Total a evacuar : {result['total_people']} pessoas")
        lines.append(f"  Taxa de evacuação: {result['flow']/result['total_people']*100:.1f}%")
    else:
        lines.append(f"  ✗ Evacuação IMPOSSÍVEL dentro de T_max = {tmax}")
        lines.append(f"    Fluxo máximo alcançado: {result['flow']}/{result['total_people']}")
        lines.append(f"    Considere aumentar T_max ou revisar as capacidades da instância.")

    lines.append("")
    lines.append(f"  Tempo total de execução: {result['total_time_ms']:.2f} ms")
    lines.append(f"  Nº de iterações (chamadas ao fluxo máximo): {len(result['history'])}")
    lines.append(SEPARATOR)
    return "\n".join(lines)


def save_report(report: str, instance_path: str):
    """Salva o relatório em outputs/<nome>_relatorio.txt."""
    os.makedirs(OUTPUTS_DIR, exist_ok=True)
    base    = os.path.splitext(os.path.basename(instance_path))[0]
    ts      = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    outfile = os.path.join(OUTPUTS_DIR, f"{base}_{ts}_relatorio.txt")
    with open(outfile, 'w', encoding='utf-8') as fh:
        fh.write(report)
    return outfile


def run(filepath: str, tmax: int = DEFAULT_TMAX):
    """Executa o pipeline completo para um arquivo de instância."""
    print(f"\n{SEPARATOR}")
    print(f"  Carregando instância: {os.path.basename(filepath)}")
    print(SEPARATOR)

    # 1. Parser
    try:
        static_graph = parse(filepath)
    except Exception as e:
        print(f"\n  ERRO ao ler o arquivo: {e}")
        sys.exit(1)

    print(f"  Nós          : {static_graph['num_nodes']}")
    print(f"  Arestas      : {static_graph['num_edges']}")
    print(f"  Fontes       : {static_graph['sources']}")
    print(f"  Sumidouros   : {static_graph['sinks']}")
    print(f"  População    : {static_graph['total_people']} pessoas")

    if static_graph['total_people'] == 0:
        print("\n  AVISO: Nenhuma pessoa encontrada na instância (verifique linhas 'n' ou 's').")

    # 2. Optimizer
    result = find_min_T(static_graph, T_max=tmax, verbose=True)

    # 3. Relatório
    report   = build_report(filepath, static_graph, result, tmax)
    outfile  = save_report(report, filepath)

    print(report)
    print(f"\n  Relatório salvo em: {outfile}\n")


def main():
    # Parsing de argumentos simples (sem dependências externas)
    args   = sys.argv[1:]
    tmax   = DEFAULT_TMAX
    fpath  = None

    i = 0
    while i < len(args):
        if args[i] in ('--tmax', '-t') and i + 1 < len(args):
            tmax  = int(args[i + 1])
            i    += 2
        elif not args[i].startswith('-'):
            fpath = args[i]
            i    += 1
        else:
            i += 1

    # Se arquivo fornecido via argumento
    if fpath:
        if not os.path.isfile(fpath):
            # Tenta dentro de instances/
            candidate = os.path.join(INSTANCES_DIR, fpath)
            if os.path.isfile(candidate):
                fpath = candidate
            else:
                print(f"  ERRO: arquivo não encontrado: {fpath}")
                sys.exit(1)
        run(fpath, tmax)
        return

    # Modo interativo
    files = list_instances()
    if not files:
        print(f"\n  ERRO: Nenhuma instância (.net) encontrada em '{INSTANCES_DIR}'.")
        print("  Crie ou copie arquivos .net para a pasta instances/ e tente novamente.\n")
        sys.exit(1)

    fpath = choose_instance(files)
    tmax  = ask_tmax()
    run(fpath, tmax)


if __name__ == '__main__':
    main()
