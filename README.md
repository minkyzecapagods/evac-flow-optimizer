# Evac-Flow Optimizer
## Otimizador de Plano de Evacuação de Edifícios via Fluxo Máximo

**Disciplina:** DIM0549 – Grafos — UFRN/IMD  
**Autoras:** Olive Oliveira Medeiros, Yasmin Giordano Santos

---

## Descrição

Implementação do algoritmo de **Edmonds-Karp** sobre um **Grafo Expandido no Tempo (Time-Expanded Graph)**
para encontrar o **tempo mínimo de evacuação T\*** de um edifício modelado como uma rede de fluxo,
conforme metodologia de Tokunaga et al. (2025).

A busca do T\* utiliza **Busca Binária + Refinamento Local**, equivalente à Otimização Bayesiana do
artigo em número de iterações para instâncias de médio porte, sem exigir bibliotecas externas.

---

## Requisitos

- **Python 3.8+** (sem dependências externas — roda com a instalação padrão)

Verificar versão:
```bash
python3 --version
```

---

## Estrutura do Projeto

```
evac-flow-optimizer/
├── README.md
├── requirements.txt          # networkx listado (não usado na implementação core)
├── src/
│   ├── main.py               # Ponto de entrada CLI
│   ├── parser.py             # Leitor de arquivos DIMACS .net
│   ├── time_expansion.py     # Construção do grafo expandido no tempo
│   ├── edmonds_karp.py       # Algoritmo de Fluxo Máximo (BFS)
│   └── optimizer.py          # Busca do T* mínimo
├── instances/
│   ├── pequeno_4_nos.net     # Validação: cadeia linear, 10 pessoas
│   ├── medio_10_nos.net      # Andar único, 10 nós, 45 pessoas
│   ├── grande_2_andares.net  # 2 andares, 18 nós, 135 pessoas
│   └── gargalo_critico.net   # Gargalo severo, 120 pessoas
├── outputs/                  # Relatórios gerados automaticamente
└── docs/
    └── relatorio.md
```

---

## Como Executar

### Modo Interativo (recomendado)

```bash
python3 src/main.py
```

O programa listará as instâncias disponíveis em `instances/` e pedirá para escolher.

### Modo Direto (passando arquivo)

```bash
python3 src/main.py instances/medio_10_nos.net
```

### Com horizonte de tempo personalizado

```bash
python3 src/main.py instances/grande_2_andares.net --tmax 300
```

---

## Formato das Instâncias (.net)

Baseado no formato **DIMACS** gerado pelo `pynetgen`:

```
c  comentário (ignorado)
p  min  <#nós>  <#arestas>
n  <id>  <suprimento>     (positivo=fonte/pessoas, negativo=sumidouro)
a  <u>  <v>  <cap>  <tau> (aresta: u→v, capacidade, tempo de travessia)
```

Extensões próprias deste projeto:
```
s  <id>  <pessoas>         (fonte com suprimento explícito de pessoas)
t  <id>                    (sumidouro explícito)
```

---

## Algoritmo em Resumo

1. **Parser** lê o grafo estático G(V, E) do arquivo `.net`
2. **Busca Binária** sobre T ∈ [0, T_max] para encontrar o menor T viável:
   - Para cada T candidato, constrói G_T (grafo expandido no tempo)
   - Calcula fluxo máximo de ss → st com **Edmonds-Karp**
   - T é viável se `fluxo_máximo ≥ população total`
3. **Refinamento Local** decrementa T unitariamente até encontrar T\* mínimo
4. **Relatório** é exibido na tela e salvo em `outputs/`

---

## Saída Esperada

```
=================================================================
  RELATÓRIO DO EXPERIMENTO — EVAC-FLOW OPTIMIZER
=================================================================
  Instância       : medio_10_nos.net
  Nós (grafo base): 10
  Arestas         : 12
  População total : 45 pessoas
  ...
  T* mínimo       : 7 unidades de tempo
  Fluxo máximo    : 45 pessoas
  Taxa de evacuação: 100.0%
  Tempo total: 12.34 ms
=================================================================
```
