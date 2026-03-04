from distribution_setup import CONFIG
from grid_environment import GridEnvironment
import matplotlib.pyplot as plt
import io
from PIL import Image
import networkx as nx

env = GridEnvironment(CONFIG)
graph = env.generate()

print("Generated nodes:", graph.number_of_nodes())

plt.figure()

pos = nx.get_node_attributes(graph, "pos")


color_map = {
    "residential": "blue",
    "commercial": "orange",
    "essential": "red",
    "generator": "green"
}


node_colors = [
    color_map[graph.nodes[n]["type"]]
    for n in graph.nodes
]

nx.draw(
    graph,
    pos,
    node_color=node_colors,
    with_labels=True
)

plt.title("Generated Grid Node Distribution (Colored by Type)")
plt.show()


#for n, data in graph.nodes(data=True):
    #print(n, data)