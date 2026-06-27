"""
optimizer.py
============
Encontra o tempo mínimo de evacuação T* tal que todo o suprimento de pessoas
possa ser escoado da rede em exatamente T* unidades de tempo.

Estratégia (conforme relatório — Seção 8.2):

  1. Busca Binária sobre T para encontrar o menor T viável.
       - T é viável se fluxo_máximo(G_T) >= total_pessoas.
       - Intervalo inicial: [T_lo, T_hi] = [0, T_max].
       - Complexidade: O(log(T_max) * |V_T| * |E_T|²)

  2. Refinamento local: decrementa T enquanto ainda for viável,
     garantindo T* mínimo (conforme Equação 1 de Tokunaga et al., 2025).

Nota sobre a Otimização Bayesiana (BO):
  O artigo de Tokunaga et al. (2025) usa BO para guiar a escolha de T
  sem exigir instalação de bibliotecas externas de ML (scikit-optimize).
  Como a instrução do trabalho exige que o algoritmo rode SEM dependências
  adicionais, adotamos busca binária, que preserva a garantia de otimalidade
  com complexidade O(log T_max) chamadas ao solucionador de fluxo máximo —
  comportamento equivalente em número de iterações para instâncias de médio porte.
"""

import time
import sys
import os

# Garante que o diretório src esteja no path (para importações relativas)
sys.path.insert(0, os.path.dirname(__file__))

from time_expansion import build as build_graph
from edmonds_karp   import max_flow


def _evacuates(static_graph: dict, T: int, total_people: int) -> tuple:
    """
    Verifica se é possível evacuar `total_people` pessoas em no máximo T passos.

    Retorna (viavel: bool, fluxo: int, tempo_ms: float)
    """
    t0 = time.time()
    graph, ss, st, _ = build_graph(static_graph, T)
    flow = max_flow(graph, ss, st)
    elapsed = (time.time() - t0) * 1000
    return (flow >= total_people), flow, elapsed


def find_min_T(
    static_graph : dict,
    T_max        : int  = 200,
    verbose      : bool = True,
) -> dict:
    """
    Encontra o menor T* tal que seja possível evacuar toda a população.

    Parâmetros
    ----------
    static_graph : dict  — saída de parser.parse()
    T_max        : int   — horizonte máximo de busca (padrão: 200)
    verbose      : bool  — imprime progresso em tempo real

    Retorna
    -------
    dict com:
      'T_min'        : int   — tempo mínimo de evacuação encontrado
      'flow'         : int   — fluxo máximo em G_{T_min}
      'total_people' : int   — população total a evacuar
      'feasible'     : bool  — True se evacuação é possível dentro de T_max
      'history'      : list  — [(T, flow, viavel, tempo_ms), ...]  (log de iterações)
      'total_time_ms': float — tempo total de execução em ms
    """
    total_people = static_graph['total_people']
    history      = []
    t_global     = time.time()

    if verbose:
        print(f"\n  [Optimizer] População total: {total_people} pessoas")
        print(f"  [Optimizer] Horizonte máximo: T_max = {T_max}")
        print(f"  [Optimizer] Estratégia: Busca Binária + Refinamento Local\n")

    # ── Caso degenerado ──────────────────────────────────────────────────────
    if total_people == 0:
        return {
            'T_min': 0, 'flow': 0, 'total_people': 0,
            'feasible': True, 'history': [], 'total_time_ms': 0.0,
        }

    # ── Fase 1: Busca Binária ────────────────────────────────────────────────
    T_lo, T_hi = 0, T_max
    T_best     = None
    flow_best  = 0

    while T_lo <= T_hi:
        T_mid = (T_lo + T_hi) // 2
        viavel, flow, ms = _evacuates(static_graph, T_mid, total_people)
        history.append((T_mid, flow, viavel, ms))

        if verbose:
            status = "✓ VIÁVEL" if viavel else "✗ inviável"
            print(f"    T={T_mid:4d}  fluxo={flow:6d}/{total_people}  {status}  ({ms:.1f} ms)")

        if viavel:
            T_best    = T_mid
            flow_best = flow
            T_hi      = T_mid - 1
        else:
            T_lo = T_mid + 1

    # ── Verificar se solução existe ──────────────────────────────────────────
    if T_best is None:
        elapsed = (time.time() - t_global) * 1000
        if verbose:
            print(f"\n  [Optimizer] AVISO: evacuação impossível dentro de T_max={T_max}.")
        return {
            'T_min': None, 'flow': flow, 'total_people': total_people,
            'feasible': False, 'history': history,
            'total_time_ms': elapsed,
        }

    # ── Fase 2: Refinamento Local (garante T* mínimo) ────────────────────────
    if verbose:
        print(f"\n  [Optimizer] Fase 2 — Refinamento local a partir de T={T_best}")

    T_refine = T_best - 1
    while T_refine >= 0:
        viavel, flow, ms = _evacuates(static_graph, T_refine, total_people)
        history.append((T_refine, flow, viavel, ms))

        if verbose:
            status = "✓ VIÁVEL" if viavel else "✗ inviável"
            print(f"    T={T_refine:4d}  fluxo={flow:6d}/{total_people}  {status}  ({ms:.1f} ms)")

        if viavel:
            T_best    = T_refine
            flow_best = flow
            T_refine -= 1
        else:
            break

    elapsed = (time.time() - t_global) * 1000

    if verbose:
        print(f"\n  [Optimizer] T* mínimo encontrado: {T_best} unidades de tempo")
        print(f"  [Optimizer] Tempo total de execução: {elapsed:.1f} ms\n")

    return {
        'T_min'        : T_best,
        'flow'         : flow_best,
        'total_people' : total_people,
        'feasible'     : True,
        'history'      : history,
        'total_time_ms': elapsed,
    }
