import networkx as nx
import random
import math
from node_generation import NodeFactory
from distribution_setup import sample_distance


class GridEnvironment:

    def __init__(self, config):
        self.config = config
        self.width, self.height = config["grid_size"]
        self.node_count = config["node_count"]
        self.graph = nx.Graph()
        self.node_factory = NodeFactory(config)
        
    def generate(self):
        self.graph.clear()

        for node_id in range(self.node_count):
            node_type = self.node_factory.generate_node_type()
            power_required, power_generated = self.node_factory.generate_power_attributes(node_type)

            position = self._generate_position(node_type)

            self.graph.add_node(
                node_id,
                type=node_type,
                pos=position,
                power_required=power_required,
                power_generated=power_generated
            )

        return self.graph
    
    
    def _generate_position(self, node_type):
        """
        Assign each node a position using placememt distrobutions
        """

        bias = self.config["spatial_bias"][node_type]

        if len(self.graph.nodes) == 0:
            return (
                random.uniform(0, self.width),
                random.uniform(0, self.height)
            )

        while True:

            if random.random() < bias["attract_prob"]:
                if node_type == "commercial":
                    target_types = ["residential", "commercial"]
                elif node_type == "essential":
                    target_types = ["commercial", "residential"]
                else:
                    target_types = [node_type]

                candidates = [
                    data for _, data in self.graph.nodes(data=True)
                    if data["type"] in target_types
                ]

                if candidates:
                    base = random.choice(candidates)
                    bx, by = base["pos"]

                    angle = random.uniform(0, 2 * math.pi)
                    radius = random.uniform(0, bias["radius"])

                    x = bx + radius * math.cos(angle)
                    y = by + radius * math.sin(angle)
                else:
                    x = random.uniform(0, self.width)
                    y = random.uniform(0, self.height)

            else:
                x = random.uniform(0, self.width)
                y = random.uniform(0, self.height)

            if not (0 <= x <= self.width and 0 <= y <= self.height):
                continue
            valid = True
            for _, data in self.graph.nodes(data=True):
                px, py = data["pos"]
                if math.hypot(px - x, py - y) < bias["min_dist"]:
                    valid = False
                    break

            if valid:
                return (x, y)
            
            
    