import numpy as np
import networkx as nx

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

        for i in range(N):
            for j in range(i + 1, N):
                if self.rng.random() < edge_prob:
                    self.edge_set.add((i, j))

        self._apply_edges()
        
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
        
    #TODO define proper parent selection
    def select_parents(self):
        return
    
    #TODO add line logic to crossover
    def crossover(self, parent1, parent2):
        edges1 = list(parent1.edge_set)
        edges2 = list(parent2.edge_set)
        cut = self.rng.integers(0, min(len(edges1), len(edges2)) + 1)
        child_edges = set(edges1[:cut] + edges2[cut:])
        child = GraphCandidate(parent1.base_graph, rng=self.rng)
        child.edge_set = child_edges
        child._apply_edges()
        return child
    
    #TODO add line logic to mutation
    def mutate(self, candidate, mutation_rate=0.05):
        nodes = list(candidate.base_graph.nodes)
        N = len(nodes)
        new_edges = set(candidate.edge_set)
        for i in range(N):
            for j in range(i + 1, N):
                if self.rng.random() < mutation_rate:
                    if (i, j) in new_edges:
                        new_edges.remove((i, j))
                    else:
                        new_edges.add((i, j))
        candidate.edge_set = new_edges
        candidate._apply_edges()
        
    def run(self, fitness_fn, generations=50, edge_prob=0.1,
            mutation_rate=0.05, verbose=True):
        
        self.initialize_population(edge_prob=edge_prob)
        for c in self.population:
            c.evaluate_fitness(fitness_fn)

        for gen in range(generations):
            new_population = []
            
            #TODO update with proper parent selection
            while len(new_population) < self.population_size:
                p1, p2 = self.select_parents()
                child = self.crossover(p1, p2)
                self.mutate(child, mutation_rate=mutation_rate)
                child.evaluate_fitness(fitness_fn)
                new_population.append(child)
            self.population = new_population

            if verbose:
                best = max(self.population, key=lambda c: c.fitness)
                print(f"Gen {gen+1}: Best fitness = {best.fitness:.4f}")

        return max(self.population, key=lambda c: c.fitness)