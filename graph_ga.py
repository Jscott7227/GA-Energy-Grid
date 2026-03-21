import numpy as np
import networkx as nx
import math

EDGE_TYPES = {
        "normal": {
            "cost_per_distance": 1.0,
            "max_distance": 50.0
        },
        "high_voltage": {
            "cost_per_distance": 2.0,
            "max_distance": 120.0
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
        
     
    # TODO build edge generation logic with line data in mind
    # Currently Random
    def generate_edges(self, edge_prob=0.1):
        nodes = list(self.base_graph.nodes)
        N = len(nodes)
        self.edge_set.clear()
        
        #TODO Send to a config file and get realistic numbers
        edge_types = EDGE_TYPES
        
        for i in range(N):
            for j in range(i + 1, N):
                if self.rng.random() < edge_prob:
                    x1, y1 = self.positions[i]
                    x2, y2 = self.positions[j]
                    dist = math.hypot(x2 - x1, y2 - y1)

                    edge_type = self._choose_edge_type(dist)

                    params = edge_types[edge_type]

                    if dist <= params["max_distance"]:
                        cost = dist * params["cost_per_distance"]

                        self.edge_set.add((
                            i,
                            j,
                            {
                                "type": edge_type,
                                "distance": dist,
                                "cost": cost,
                                "cost_per_distance": params["cost_per_distance"],
                                "max_distance": params["max_distance"]
                            }
                        ))

        self._apply_edges()

    def _choose_edge_type(self, dist):
        if dist < 30:
            p_high_voltage = 0.1
        elif dist < 80:
            p_high_voltage = 0.4
        else:
            p_high_voltage = 0.8

        return "high_voltage" if self.rng.random() < p_high_voltage else "normal"
    
    def _apply_edges(self):
        self.G.clear_edges()
        self.G.add_edges_from(self.edge_set)
        
    def evaluate_fitness(self, fitness_fn):
        self.fitness = fitness_fn(self.G)
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
        
        for (i, j, attr) in child_edges_list:
            pair = (i, j)
            if pair not in seen_pairs:
                seen_pairs.add(pair)
                child_edges.add((i, j, attr))
        
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
        
        for i in range(N):
            for j in range(i + 1, N):
                if self.rng.random() < mutation_rate:
                    existing_edge = None
                    for e in new_edges:
                        if e[0] == i and e[1] == j:
                            existing_edge = e
                            break
                    if existing_edge:
                        new_edges.remove(existing_edge)
                        
                    else:
                        x1, y1 = candidate.positions[i]
                        x2, y2 = candidate.positions[j]
                        dist = math.hypot(x2 - x1, y2 - y1)
                        edge_type = candidate._choose_edge_type(dist)
                        params = edge_types[edge_type]
                        if dist <= params["max_distance"]:
                            cost = dist * params["cost_per_distance"]
                            new_edges.add((
                                i,
                                j,
                                {
                                    "type": edge_type,
                                    "distance": dist,
                                    "cost": cost,
                                    "cost_per_distance": params["cost_per_distance"],
                                    "max_distance": params["max_distance"]
                                }
                            ))
                        
                    if existing_edge and self.rng.random() < 0.3:
                        i0, j0, attr = existing_edge

                        new_type = (
                            "high_voltage"
                            if attr["type"] == "normal"
                            else "normal"
                        )

                        x1, y1 = candidate.positions[i0]
                        x2, y2 = candidate.positions[j0]
                        dist = math.hypot(x2 - x1, y2 - y1)

                        params = edge_types[new_type]

                        if dist <= params["max_distance"]:
                            cost = dist * params["cost_per_distance"]
                            new_edges.add((
                                i0,
                                j0,
                                {
                                    "type": new_type,
                                    "distance": dist,
                                    "cost": cost,
                                    "cost_per_distance": params["cost_per_distance"],
                                    "max_distance": params["max_distance"]
                                }
                            ))
        candidate.edge_set = new_edges
        candidate._apply_edges()
            
    def run(self, fitness_fn, generations=50, edge_prob=0.1,
            mutation_rate=0.05, top_k=3, verbose=True):
        
        self.initialize_population(edge_prob=edge_prob)
        for c in self.population:
            c.evaluate_fitness(fitness_fn)

        for gen in range(generations):
            new_population = []
            
            elites, parents = self.select_parents(top_k=top_k)
            new_population.extend(elites)
            for p1, p2 in parents:
                child = self.crossover(p1, p2)
                self.mutate(child, mutation_rate=mutation_rate)
                new_population.append(child)
                
            self.population = new_population

            if verbose:
                best = max(self.population, key=lambda c: c.fitness)
                print(f"Gen {gen+1}: Best fitness = {best.fitness:.4f}")

        return max(self.population, key=lambda c: c.fitness)