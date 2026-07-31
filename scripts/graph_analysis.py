import networkx as nx
import matplotlib.pyplot as plt
import os

desktop = "C:/Users/Dottorandi-next/Desktop"


# ============================================================
# 1. READ backbone.dat (IDs of the DFNWorks conductive backbone)
# ============================================================
backbone_ids = set()
with open(os.path.join(desktop, "backbone_Z.dat"), "r") as f:
    for line in f:
        parts = line.split()
        if parts:
            backbone_ids.add(int(parts[0]))


# ============================================================
# 2. BUILD THE FULL GRAPH FROM connectivity.dat
# ============================================================
G = nx.Graph()
with open(os.path.join(desktop, "connectivity.dat"), "r") as f:
    for i, line in enumerate(f):
        u = i + 1
        neighbors = [int(v) for v in line.split()]
        for v in neighbors:
            G.add_edge(u, v)


# ============================================================
# 3. ADD s AND t NODES (as DFNWorks does)
# ============================================================
left_ids = set()
right_ids = set()

with open(os.path.join(desktop, "bottom.dat"), "r") as f:
    for line in f:
        parts = line.split()
        if parts:
            left_ids.add(int(parts[0]))

with open(os.path.join(desktop, "top.dat"), "r") as f:
    for line in f:
        parts = line.split()
        if parts:
            right_ids.add(int(parts[0]))

G.add_node("s")
G.add_node("t")

for u in left_ids:
    G.add_edge("s", u)

for u in right_ids:
    G.add_edge("t", u)


# ============================================================
# 4. EXTRACT THE CONDUCTIVE BACKBONE
# ============================================================
H = G.subgraph(backbone_ids | {"s", "t"}).copy()


# ============================================================
# 5. APPLY THE TRUE ITERATIVE 2-CORE
# ============================================================
def two_core_iterative(H):
    H = H.copy()
    changed = True
    while changed:
        changed = False
        to_remove = [n for n in H.nodes() if n not in ("s", "t") and H.degree(n) < 2]
        if to_remove:
            H.remove_nodes_from(to_remove)
            changed = True
    return H

H2 = two_core_iterative(H)

print("H2 == H ?", set(H2.nodes()) == set(H.nodes()))
print("Nodes removed by 2-core:", set(H.nodes()) - set(H2.nodes()))


# ============================================================
# 6. GENERATE connectivity_backbone_clean.dat FROM connectivity.dat
# ============================================================
clean_path = os.path.join(desktop, "connectivity_backbone_clean.dat")

# Build adjacency list for the full graph (numeric nodes only)
full_adj = {}
with open(os.path.join(desktop, "connectivity.dat"), "r") as f:
    for i, line in enumerate(f):
        u = i + 1
        neighbors = [int(v) for v in line.split()]
        full_adj[u] = neighbors

# Filter only nodes in the 2-core
H2_numeric = sorted([n for n in H2.nodes() if isinstance(n, int)])

clean_adj = {}
for u in H2_numeric:
    neigh = [v for v in full_adj[u] if v in H2_numeric]
    clean_adj[u] = neigh

# Write the clean adjacency list
with open(clean_path, "w") as f:
    for u in H2_numeric:
        if clean_adj[u]:
            line = " ".join(str(v) for v in clean_adj[u])
        else:
            line = ""
        f.write(line + "\n")

print(f"Generated clean backbone connectivity file: {clean_path}")


# ============================================================
# 7. AVERAGE DEGREE OF THE 2-CORE (INCLUDING s AND t)
# ============================================================
def grado_medio_da_grafo_incluso_st(H):
    N = len(H.nodes())      # all nodes including s and t
    E = len(H.edges())      # all edges including s/t edges
    z = 2 * E / N if N > 0 else 0

    print("====================================")
    print(" ANALYSIS OF THE 2-CORE BACKBONE (H2) - INCLUDING s/t")
    print("====================================")
    print(f"Total number of nodes (N): {N}")
    print(f"Total number of edges (E): {E}")
    print(f"Average degree z = 2E/N = {z:.3f}")
    print("====================================")

grado_medio_da_grafo_incluso_st(H2)


# ============================================================
# 8. READ connectivity_backbone_clean.dat AND FIND ISOLATED FRACTURES
# ============================================================
isolated_from_file = []

with open(clean_path, "r") as f:
    for line in f:
        parts = line.split()
        if len(parts) == 1:
            isolated_from_file.append(int(parts[0]))

print("Isolated fractures from file:", isolated_from_file)


# ============================================================
# 9. PLOT OF THE 2-CORE BACKBONE (H2) WITH EDGE NUMBERS
# ============================================================
pos = nx.spring_layout(G, seed=0)

plt.figure(figsize=(14, 14))

# full graph
nx.draw_networkx_nodes(G, pos, node_size=10, node_color="lightgray")
nx.draw_networkx_edges(G, pos, alpha=0.15, edge_color="gray")

# 2-core backbone in red
nx.draw_networkx_nodes(H2, pos, node_size=40, node_color="red")
nx.draw_networkx_edges(H2, pos, width=2, edge_color="red")

# isolated fractures in blue
nx.draw_networkx_nodes(
    H2, pos,
    nodelist=isolated_from_file,
    node_size=120,
    node_color="blue"
)

# labels for isolated nodes
labels_nodes = {n: str(n) for n in isolated_from_file}
nx.draw_networkx_labels(
    H2, pos,
    labels=labels_nodes,
    font_size=10,
    font_color="black"
)

# edge numbering
edge_list = list(H2.edges())
edge_labels = {edge_list[i]: str(i+1) for i in range(len(edge_list))}

nx.draw_networkx_edge_labels(
    H2, pos,
    edge_labels=edge_labels,
    font_size=7,
    font_color="darkgreen",
    rotate=False
)

# highlight the last edge
last_edge = edge_list[-1]
last_label = {last_edge: str(len(edge_list))}

nx.draw_networkx_edge_labels(
    H2, pos,
    edge_labels=last_label,
    font_size=22,
    font_color="red",
    rotate=False,
    bbox=dict(facecolor="yellow", edgecolor="black", boxstyle="round,pad=0.3")
)

# s and t nodes
nx.draw_networkx_nodes(G, pos, nodelist=["s"], node_size=200, node_color="cyan")
nx.draw_networkx_nodes(G, pos, nodelist=["t"], node_size=200, node_color="green")

plt.title("2-core Backbone (H2) with Edge Numbering and Highlighted Last Edge")
plt.axis("off")
plt.show()

print(f"Number of edges in the 2-core (H2): {len(edge_list)}")

edges_st = [(u, v) for u, v in H2.edges() if "s" in (u, v) or "t" in (u, v)]
print(len(edges_st), edges_st)
