"""
time_expansion.py
=================
Constrói o grafo expandido no tempo G_T a partir de um grafo estático G(V,E).

Definição formal (conforme Ford & Fulkerson, 1962; Hamacher & Tjandra, 2001):
  - Para cada vértice v ∈ V e cada instante t = 0, 1, ..., T, cria-se o nó (v, t).
  - Para cada aresta (u, v, cap, τ) ∈ E e cada t tal que t + τ ≤ T,
    cria-se a aresta temporal ((u,t), (v, t+τ)) com capacidade cap.
  - Para cada vértice v ∈ V e cada t = 0, ..., T-1,
    cria-se uma aresta de ESPERA ((v,t), (v, t+1)) com capacidade = soma das caps de saída de v
    (ou infinito — aqui usamos INF = 10**9).
  - Super-source ss: conectado a (src, 0) com capacidade = supply[src], para cada fonte src.
  - Super-sink   st: conectado de (snk, t) com capacidade INF, para cada sumidouro snk e t=0..T.

IDs internos:
  Usamos inteiros contíguos.
    node_id(v, t) = v_index * (T+1) + t      (v_index = posição de v na lista ordenada)
    ss             = |V| * (T+1)
    st             = |V| * (T+1) + 1

Retorno de `build`:
  (graph, ss, st, n_total)
  onde `graph` é uma lista de adjacência no formato requerido por edmonds_karp:
    graph[u] = [(v, cap_forward, rev_idx), ...]
  A lista usa representação de grafo residual com arestas reversas.
"""

INF = 10 ** 9


def build(static_graph: dict, T: int):
    """
    Parâmetros
    ----------
    static_graph : dict  — saída de parser.parse()
    T            : int   — horizonte de tempo

    Retorna
    -------
    graph  : lista de adjacência residual  (lista de listas de [v, cap, rev_ptr])
    ss     : int  — índice do super-source
    st     : int  — índice do super-sink
    n_total: int  — número total de nós no grafo expandido (incluindo ss e st)
    """
    all_nodes = static_graph['all_nodes']
    supply    = static_graph['supply']
    edges     = static_graph['edges']      # (u, v, cap, tau)
    sources   = static_graph['sources']
    sinks     = static_graph['sinks']

    V = len(all_nodes)
    node_index = {v: i for i, v in enumerate(all_nodes)}   # v → índice 0..V-1

    # Número total de nós: V*(T+1) + 2 (ss e st)
    n_total = V * (T + 1) + 2
    ss      = V * (T + 1)
    st      = V * (T + 1) + 1

    # Inicializa lista de adjacência residual
    # Cada entrada: [destino, capacidade_residual, índice_da_aresta_reversa]
    graph = [[] for _ in range(n_total)]

    def add_edge(u: int, v: int, cap: int):
        """Adiciona aresta dirigida u→v (e sua reversa v→u com cap=0)."""
        graph[u].append([v, cap, len(graph[v])])
        graph[v].append([u, 0,   len(graph[u]) - 1])

    def node_id(v_orig: int, t: int) -> int:
        return node_index[v_orig] * (T + 1) + t

    # ── 1. Arestas de TRÂNSITO temporal ────────────────────────────────────
    for (u, v, cap, tau) in edges:
        for t in range(T + 1):
            if t + tau <= T:
                add_edge(node_id(u, t), node_id(v, t + tau), cap)

    # ── 2. Arestas de ESPERA ────────────────────────────────────────────────
    # Capacidade de espera = INF (pessoas podem aguardar em qualquer ponto)
    for v_orig in all_nodes:
        for t in range(T):
            add_edge(node_id(v_orig, t), node_id(v_orig, t + 1), INF)

    # ── 3. Super-source → fontes no instante 0 ──────────────────────────────
    for src in sources:
        pessoas = supply.get(src, 0)
        if pessoas > 0:
            add_edge(ss, node_id(src, 0), pessoas)

    # ── 4. Sumidouros em todos os instantes → super-sink ────────────────────
    for snk in sinks:
        for t in range(T + 1):
            add_edge(node_id(snk, t), st, INF)

    return graph, ss, st, n_total
