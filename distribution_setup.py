import random
import numpy as np


#TODO update with realisitc probs 
CONFIG = {
    "grid_size": (500, 500),

    "node_count": 100,

    "node_type_percentages": {
        "essential": 0.15,
        "generator": 0.04,
        "residential": 0.41,
        "commercial": 0.25,
        "substation": 0.15
    },

    "spatial_bias": {
        "residential": {"attract_prob": 0.7, "radius": 80, "min_dist": 15},
        "commercial": {"attract_prob": 0.6, "radius": 100, "min_dist": 20},
        "essential": {"attract_prob": 0.5, "radius": 120, "min_dist": 30},
        "generator": {"attract_prob": 0.0, "radius": 150, "min_dist": 50},
        "substation": {"attract_prob": 0.0, "radius": 150, "min_dist": 50}
    },

    "power_generation_distribution": {
        "type": "normal",
        "mean": 1000,
        "std": 20
    },

    "power_requirement_distribution": {
        "essential": {"mean": 100, "std": 10},
        "residential": {"mean": 25, "std": 5},
        "commercial": {"mean": 50, "std": 10},
        "generator": {"mean": 5, "std": 2},
        "substation": {"mean": 5, "std": 2}
    }
}

def sample_distance(config):
    if config["type"] == "uniform":
        return random.uniform(config["min"], config["max"])
    elif config["type"] == "normal":
        return max(0, np.random.normal(config["mean"], config["std"]))


def sample_power(config):
    return max(0, np.random.normal(config["mean"], config["std"]))