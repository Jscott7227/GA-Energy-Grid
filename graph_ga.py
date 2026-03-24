import numpy as np
import networkx as nx
import math
import matplotlib.pyplot as plt

EDGE_TYPES = {
        "normal": {
            "cost_per_distance": 1.5,
            "max_distance": 75.0
        },
        "high_voltage": {
            "cost_per_distance": 4,
            "max_distance": 250.0
        }
    }

class GraphCandidate:
    def __init__(self, base_graph, rng=None):
        self.base_graph = base_graph
        self.G = nx.Graph()
        self.G.add_nodes_from(base_graph.nodes(data=True))
        self.rng = rng or np.random.default_rng()
        self.edge_set = set()
        self.fitness = None
        
     
    # Currently Random
    def generate_edges(self, edge_prob=0.1):
        nodes = list(self.base_graph.nodes)
        N = len(nodes)
        self.edge_set.clear()
        
        edge_types = EDGE_TYPES
        
        for i in range(N):
            for j in range(i + 1, N):
                if self.rng.random() < edge_prob:
                    
                    type_i = self.G.nodes[i]["type"]
                    type_j = self.G.nodes[j]["type"]
                    if (
                        ("generator" in (type_i, type_j)) and
                        ("substation" not in (type_i, type_j))
                    ):
                        continue
                    
                    x1, y1 = self._get_position(i)
                    x2, y2 = self._get_position(j)
                    dist = math.hypot(x2 - x1, y2 - y1)

                    edge_type = self._choose_edge_type(dist)
                    
                    if edge_type == "high_voltage":
                        if not (
                            (type_i == "generator" and type_j == "substation") or
                            (type_j == "generator" and type_i == "substation") or
                            (type_i == "substation" and type_j == "substation")
                        ):
                            continue

                    params = edge_types[edge_type]

                    if dist <= params["max_distance"]:
                        cost = dist * params["cost_per_distance"]

                        self.edge_set.add((
                        i,
                        j,
                        edge_type,
                        dist,
                        cost,
                        params["cost_per_distance"],
                        params["max_distance"]
                    ))

        self._apply_edges()

    def _choose_edge_type(self, dist):
        if dist < 100:
            p_high_voltage = 0.0
        else:
            p_high_voltage = 0.95

        return "high_voltage" if self.rng.random() < p_high_voltage else "normal"
    
    def _apply_edges(self):
        self.G.clear_edges()
        for i, j, edge_type, dist, cost, cpd, max_dist in self.edge_set:
            self.G.add_edge(
                i,
                j,
                type=edge_type,
                distance=dist,
                cost=cost,
                cost_per_distance=cpd,
                max_distance=max_dist
            )

    def _get_position(self, node_id):
        return self.base_graph.nodes[node_id]["pos"]
    
    def evaluate_fitness(self, fitness_env):
        self.fitness = fitness_env.evaluate(self.G)
        return self.fitness
    
class GraphGA:
    def __init__(self, base_graph, population_size=100, rng=None):
        self.rng = rng or np.random.default_rng()
        self.base_graph = base_graph
        self.population_size = population_size
        self.population = []
    
    def initialize_population(self, edge_prob=0.1):
        self.population = []
        for _ in range(self.population_size):
            candidate = GraphCandidate(self.base_graph, rng=self.rng)
            candidate.generate_edges(edge_prob=edge_prob)
            self.population.append(candidate)
        
    #Top K star mating
    def select_parents(self, top_k=3):
        sorted_pop = sorted(self.population, key=lambda c: c.fitness, reverse=True)
        elites = sorted_pop[:top_k]
        non_elites = sorted_pop[top_k:]
        
        all_pairs = [(elite, cand) for elite in elites for cand in non_elites]
        
        n_offspring = self.population_size - top_k

        indices = self.rng.integers(0, len(all_pairs), size=n_offspring)
        parents = [all_pairs[i] for i in indices]

        return elites, parents
    
    #Simple genetic crossover equal chance to inherrit each edge from parent
    def crossover(self, parent1, parent2):
        edges1 = list(parent1.edge_set)
        edges2 = list(parent2.edge_set)
        cut1 = self.rng.integers(0, len(edges1) + 1)
        cut2 = self.rng.integers(0, len(edges2) + 1)
        child_edges_list = edges1[:cut1] + edges2[cut2:]
        seen_pairs = set()
        child_edges = set()
        
        for edge in child_edges_list:
            i, j, edge_type, dist, cost, cpd, max_dist = edge

            pair = (i, j)

            if pair not in seen_pairs:
                seen_pairs.add(pair)
                child_edges.add((i, j, edge_type, dist, cost, cpd, max_dist))
        
        child = GraphCandidate(parent1.base_graph, rng=self.rng)
        child.edge_set = child_edges
        
        child._apply_edges()
        return child
    
    # Random mutation with chance to add, remove and update nodes
    def mutate(self, candidate, mutation_rate=0.05):
        nodes = list(candidate.base_graph.nodes)
        N = len(nodes)
        edge_types = EDGE_TYPES
        new_edges = set(candidate.edge_set)
        existing_edges = list(new_edges)
        
        for edge in existing_edges:
            if self.rng.random() < mutation_rate:
                i, j, edge_type, dist, cost, cpd, max_dist = edge
                type_i = self.base_graph.nodes[i]["type"]
                type_j = self.base_graph.nodes[j]["type"]
                new_type = (
                    "high_voltage"
                    if edge_type == "normal"
                    else "normal"
                )
                if new_type == "high_voltage":
                        if not (
                            (type_i == "generator" and type_j == "substation") or
                            (type_j == "generator" and type_i == "substation") or
                            (type_i == "substation" and type_j == "substation")
                        ):
                            continue
                x1, y1 = candidate.base_graph.nodes[i]["pos"]
                x2, y2 = candidate.base_graph.nodes[j]["pos"]
                dist = math.hypot(x2 - x1, y2 - y1)

                params = edge_types[new_type]

                if dist <= params["max_distance"]:
                    cost = dist * params["cost_per_distance"]

                    new_edges.discard(edge)
                    new_edges.add((
                        i,
                        j,
                        new_type,
                        dist,
                        cost,
                        params["cost_per_distance"],
                        params["max_distance"]
                    ))
        for edge in list(new_edges):
            if self.rng.random() < mutation_rate:
                new_edges.discard(edge)
                
        num_candidates = int(N * mutation_rate)
        edge_pairs = {(e[0], e[1]) for e in new_edges}
        for _ in range(num_candidates):
            i, j = self.rng.integers(0, N, size=2)
            if i == j:
                continue
            
            type_i = self.base_graph.nodes[i]["type"]
            type_j = self.base_graph.nodes[j]["type"]
            if (
                ("generator" in (type_i, type_j)) and
                ("substation" not in (type_i, type_j))
            ):
                continue
            
            pair = (min(i, j), max(i, j))

            # Skip if edge already exists
            if pair in edge_pairs:
                continue

            x1, y1 = candidate.base_graph.nodes[pair[0]]["pos"]
            x2, y2 = candidate.base_graph.nodes[pair[1]]["pos"]
            dist = math.hypot(x2 - x1, y2 - y1)

            edge_type = candidate._choose_edge_type(dist)
            
            if edge_type == "high_voltage":
                        if not (
                            (type_i == "generator" and type_j == "substation") or
                            (type_j == "generator" and type_i == "substation") or
                            (type_i == "substation" and type_j == "substation")
                        ):
                            continue
            
            params = edge_types[edge_type]
            
            if dist <= params["max_distance"]:
                cost = dist * params["cost_per_distance"]

                new_edges.add((
                    pair[0],
                    pair[1],
                    edge_type,
                    dist,
                    cost,
                    params["cost_per_distance"],
                    params["max_distance"]
                ))
                    
        candidate.edge_set = new_edges
        candidate._apply_edges()
        
    
    def plot_graph(self, graph, title="Graph"):
        pos = nx.get_node_attributes(graph, "pos")

        color_map = {
            "residential": "blue",
            "commercial": "orange",
            "essential": "red",
            "generator": "green",
            "substation": "purple"
        }

        node_colors = [
            color_map[graph.nodes[n]["type"]]
            for n in graph.nodes
        ]
        
        node_sizes = [
            125 if graph.nodes[n].get("served") else 100
            for n in graph.nodes
        ]

        normal_edges = []
        high_voltage_edges = []

        for u, v, data in graph.edges(data=True):
            e_type = data.get("type", "normal")
            if e_type == "high_voltage":
                high_voltage_edges.append((u, v))
            else:
                normal_edges.append((u, v))

        plt.clf()

        nx.draw_networkx_nodes(
            graph,
            pos,
            node_color=node_colors,
            node_size=node_sizes
        )

        nx.draw_networkx_edges(
            graph,
            pos,
            edgelist=normal_edges,
            width=1,
            alpha=0.5
        )

        nx.draw_networkx_edges(
            graph,
            pos,
            edgelist=high_voltage_edges,
            width=3,         
            alpha=0.9,
            style="solid"
        )

        plt.title(title)
        plt.pause(1)
            
    def run(self, fitness_env, generations=50, edge_prob=0.1,
            mutation_rate=0.05, top_k=3, verbose=1):
        
        self.initialize_population(edge_prob=edge_prob)
        fitness_env.generate_weather_scenarios()
        for c in self.population:
            c.evaluate_fitness(fitness_env)

        for gen in range(generations):
            new_population = []
            
            elites, parents = self.select_parents(top_k=top_k)
            new_population.extend(elites)
            for p1, p2 in parents:
                child = self.crossover(p1, p2)
                self.mutate(child, mutation_rate=mutation_rate)
                new_population.append(child)
                
                
            self.population = new_population
            fitness_env.generate_weather_scenarios()
            for c in self.population:
                c.evaluate_fitness(fitness_env)
                
            if verbose:
                best = max(self.population, key=lambda c: c.fitness)
                print(f"Gen {gen+1}: Best fitness = {best.fitness:.4f}")
                
            if verbose >= 2:
                self.plot_graph(best.G, title=f"Generation {gen} Best Graph \n Fitness {best.fitness:.4f}")

        return max(self.population, key=lambda c: c.fitness)