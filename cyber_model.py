import random

#TODO update with proper cyber attacks
class CyberAttackModel:

    def __init__(self, rng=None):

        self.rng = rng or random.Random()

        self.attack_probability_per_week = 0.02
        self.edge_failure_probability = 0.07


    def attack_occurs(self):
        return self.rng.random() < self.attack_probability_per_week