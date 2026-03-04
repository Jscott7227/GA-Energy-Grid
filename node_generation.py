import random
from distribution_setup import sample_power

class NodeFactory:

    def __init__(self, config):
        self.config = config

    def generate_node_type(self):
        types = list(self.config["node_type_percentages"].keys())
        probs = list(self.config["node_type_percentages"].values())
        return random.choices(types, probs)[0]

    def generate_power_attributes(self, node_type):
        power_req_config = self.config["power_requirement_distribution"][node_type]
        power_required = sample_power(power_req_config)

        power_generated = 0
        if node_type == "generator":
            gen_config = self.config["power_generation_distribution"]
            power_generated = sample_power(gen_config)

        return power_required, power_generated