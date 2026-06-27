"""
parser.py
=========
Leitor de arquivos no formato DIMACS / pynetgen (.net).

Formato suportado:
  c  comentário
  p  min  <#nós>  <#arestas>     (linha de problema; aceitamos "max" também)
  n  <id>  <suprimento>           (nó com suprimento positivo = fonte, negativo = sumidouro)
  a  <orig>  <dest>  <cap>  [tau] (aresta com capacidade e tempo de travessia opcional)

Extensões proprietárias do projeto:
  s  <id>  <pessoas>              (vértice com suprimento de pessoas — alias de 'n' positivo)
  t  <id>                         (vértice de saída/sumidouro — alias de 'n' negativo)
  a  <orig>  <dest>  <cap>  <tau> (quarto campo = tempo de travessia τ em unidades discretas)

Retorno:
  {
    'num_nodes'   : int,
    'num_edges'   : int,
    'supply'      : {node_id: int},   # positivo = pessoas iniciais, negativo = capacidade sumidouro
    'edges'       : [(u, v, cap, tau)],
    'sources'     : [node_id],        # nós com supply > 0
    'sinks'       : [node_id],        # nós com supply < 0 (ou marcados como saída)
  }
"""

import re


def parse(filepath: str) -> dict:
    """Lê um arquivo .net e devolve a representação interna do grafo."""
    supply   = {}   # node_id -> suprimento
    edges    = []   # (u, v, cap, tau)
    sinks_explicit = []

    num_nodes = 0
    num_edges = 0

    with open(filepath, 'r', encoding='utf-8') as fh:
        for raw in fh:
            line = raw.strip()
            if not line or line.startswith('c'):
                continue

            tokens = line.split()
            kind   = tokens[0].lower()

            if kind == 'p':
                # p min|max <#nós> <#arestas>
                num_nodes = int(tokens[2])
                num_edges = int(tokens[3])

            elif kind == 'n':
                # n <id> <suprimento>
                node_id   = int(tokens[1])
                sup_val   = int(tokens[2])
                supply[node_id] = supply.get(node_id, 0) + sup_val

            elif kind == 's':
                # s <id> <pessoas>  — extensão: vértice fonte com pessoas
                node_id = int(tokens[1])
                pessoas = int(tokens[2])
                supply[node_id] = supply.get(node_id, 0) + pessoas

            elif kind == 't':
                # t <id>  — extensão: vértice de saída explícito
                node_id = int(tokens[1])
                sinks_explicit.append(node_id)

            elif kind == 'a':
                # a <u> <v> <cap> [tau]
                u   = int(tokens[1])
                v   = int(tokens[2])
                cap = int(tokens[3])
                tau = int(tokens[4]) if len(tokens) > 4 else 1
                edges.append((u, v, cap, tau))

    # Inferir fontes e sumidouros a partir de supply
    sources = [n for n, s in supply.items() if s > 0]
    sinks   = [n for n, s in supply.items() if s < 0]

    # Sumidouros explícitos via linha 't' sobrescrevem supply zero
    for node_id in sinks_explicit:
        if node_id not in sinks:
            sinks.append(node_id)
        if node_id not in supply:
            supply[node_id] = -1  # marcador simbólico

    # Calcular população total (soma dos suprimentos positivos)
    total_people = sum(s for s in supply.values() if s > 0)

    # Coletar todos os nós mencionados
    all_nodes = set(supply.keys())
    for u, v, _, _ in edges:
        all_nodes.add(u)
        all_nodes.add(v)

    return {
        'num_nodes'    : max(num_nodes, len(all_nodes)),
        'num_edges'    : max(num_edges, len(edges)),
        'supply'       : supply,
        'edges'        : edges,
        'sources'      : sorted(sources),
        'sinks'        : sorted(sinks),
        'total_people' : total_people,
        'all_nodes'    : sorted(all_nodes),
    }
