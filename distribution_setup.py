import random
import numpy as np

CONFIG = {
    "grid_size": (50, 50),

    "node_count": 100,

    "node_type_percentages": {
        "essential": 0.15,
        "generator": 0.10,
        "residential": 0.45,
        "commercial": 0.30
    },

    "spatial_bias": {
        "residential": {"attract_prob": 0.7, "radius": 8, "min_dist": 1.5},
        "commercial": {"attract_prob": 0.6, "radius": 10, "min_dist": 2},
        "essential": {"attract_prob": 0.5, "radius": 12, "min_dist": 3},
        "generator": {"attract_prob": 0.2, "radius": 15, "min_dist": 5},
    },

    "power_generation_distribution": {
        "type": "normal",
        "mean": 100,
        "std": 20
    },

    "power_requirement_distribution": {
        "essential": {"mean": 60, "std": 10},
        "residential": {"mean": 30, "std": 5},
        "commercial": {"mean": 50, "std": 10},
        "generator": {"mean": 5, "std": 2}
    }
}

def sample_distance(config):
    if config["type"] == "uniform":
        return random.uniform(config["min"], config["max"])
    elif config["type"] == "normal":
        return max(0, np.random.normal(config["mean"], config["std"]))


def sample_power(config):
    return max(0, np.random.normal(config["mean"], config["std"]))