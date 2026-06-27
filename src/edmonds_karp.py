"""
edmonds_karp.py
===============
Implementação do algoritmo de Edmonds-Karp para o cálculo de Fluxo Máximo.

O algoritmo de Edmonds-Karp é uma instância específica do método de Ford-Fulkerson
onde o caminho aumentante é sempre escolhido por Busca em Largura (BFS), garantindo
que o caminho encontrado seja o de menor número de arestas.

Complexidade: O(V · E²)
  - O(V·E) iterações no pior caso (cada iteração satura pelo menos uma aresta)
  - O(E) por BFS

Referências:
  Edmonds, J.; Karp, R. M. (1972). Theoretical improvements in algorithmic efficiency
  for network flow problems. Journal of the ACM, 19(2), 248-264.

Interface do grafo residual:
  graph[u] = [[v, cap_residual, idx_reversa], ...]
  A aresta reversa de graph[u][i] é graph[v][graph[u][i][2]].
"""

from collections import deque


def bfs(graph: list, source: int, sink: int, parent: list) -> bool:
    """
    Busca em Largura (BFS) no grafo residual.

    Encontra um caminho aumentante de `source` até `sink`.
    Preenche `parent[v] = (u, idx_aresta)` para reconstrução do caminho.

    Retorna True se existir caminho, False caso contrário.

    Complexidade: O(V + E)
    """
    visited = [False] * len(graph)
    visited[source] = True
    queue = deque([source])

    while queue:
        u = queue.popleft()
        for idx, (v, cap, _) in enumerate(graph[u]):
            if not visited[v] and cap > 0:
                visited[v] = True
                parent[v]  = (u, idx)
                if v == sink:
                    return True
                queue.append(v)

    return False


def max_flow(graph: list, source: int, sink: int) -> int:
    """
    Calcula o fluxo máximo de `source` a `sink` usando Edmonds-Karp.

    Modifica `graph` in-place (atualiza capacidades residuais).

    Parâmetros
    ----------
    graph  : lista de adjacência residual (ver time_expansion.py)
    source : índice do super-source (ss)
    sink   : índice do super-sink   (st)

    Retorna
    -------
    flow_value : int — valor total do fluxo máximo
    """
    n          = len(graph)
    flow_value = 0
    parent     = [None] * n

    # Enquanto existir caminho aumentante (BFS)
    while bfs(graph, source, sink, parent):

        # ── Encontrar o gargalo ao longo do caminho ──────────────────────
        bottleneck = float('inf')
        v = sink
        while v != source:
            u, idx = parent[v]
            bottleneck = min(bottleneck, graph[u][idx][1])
            v = u

        # ── Atualizar o grafo residual ────────────────────────────────────
        v = sink
        while v != source:
            u, idx     = parent[v]
            rev_idx    = graph[u][idx][2]
            graph[u][idx][1]    -= bottleneck   # diminui cap. direta
            graph[v][rev_idx][1] += bottleneck  # aumenta cap. reversa
            v = u

        flow_value += bottleneck

        # Limpar parent para próxima iteração
        parent = [None] * n

    return flow_value
