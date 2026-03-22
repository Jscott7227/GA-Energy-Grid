from distribution_setup import CONFIG
from grid_environment import GridEnvironment
import matplotlib.pyplot as plt
import io
from PIL import Image
import networkx as nx
from graph_ga import GraphGA
from fitness_env import GridFitnessEnv
from cyber_model import CyberAttackModel
import numpy as np
import random

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

cyber_model = CyberAttackModel()
env = GridFitnessEnv("weather_configs/new_england.json", cyber_model, rng=random.Random(42))
ga = GraphGA(graph, population_size=100, rng=np.random.default_rng(42))

best_candidate = ga.run(
    env,
    generations=100,
    edge_prob=0.2,
    mutation_rate=0.05,
    top_k=3
)

print("Best candidate fitness:", best_candidate.fitness)
#for n, data in graph.nodes(data=True):
    #print(n, data)