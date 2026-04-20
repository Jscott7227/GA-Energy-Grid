import random

class CyberAttackModel:

    def __init__(self, attack_prob = 0.2, rng=None):
        self.rng = rng or random.Random()

        self.attack_probability_per_week = attack_prob

        # attack parameters
        self.beta = 1.5   # load increase factor
        self.gamma = 0.5  # generation reduction
        self.k = 2        # edges cut in breaker attack
        self.delta_t = 2  # relay delay steps

        self.active_attack = None

    # ------------------------
    # Attack Trigger
    # ------------------------
    def attack_occurs(self):
        return self.rng.random() < self.attack_probability_per_week

    def choose_attack(self):
        return self.rng.choice([
            "false_load",
            "breaker",
            "generator",
            "relay",
            "control"
        ])

    # ------------------------
    # False Load Injection
    # ------------------------
    def false_load_injection(self, G):
        load_nodes = [
            n for n, d in G.nodes(data=True)
            if d.get("type") in ["residential", "commercial", "essential"]
        ]

        targets = self.rng.sample(load_nodes, max(1, len(load_nodes)//10))

        for n in targets:
            G.nodes[n]["power_required"] *= self.beta

    # ------------------------
    # Breaker Manipulation
    # ------------------------
    def breaker_attack(self, G):
        substations = [
            n for n, d in G.nodes(data=True)
            if d.get("type") == "substation"
        ]

        if not substations:
            return

        target = self.rng.choice(substations)

        connected_edges = list(G.edges(target))

        for u, v in self.rng.sample(connected_edges, min(self.k, len(connected_edges))):
            if G.has_edge(u, v):
                G.remove_edge(u, v)

    # ------------------------
    # Generator Attack
    # ------------------------
    def generator_attack(self, G):
        generators = [
            n for n, d in G.nodes(data=True)
            if d.get("type") == "generator"
        ]

        if not generators:
            return

        target = self.rng.choice(generators)
        G.nodes[target]["power_generated"] *= self.gamma

    # ------------------------
    # Relay Attack (delayed failure)
    # ------------------------
    def relay_attack(self, G):
        edges = list(G.edges())
        if not edges:
            return

        u, v = self.rng.choice(edges)
        G[u][v]["compromised"] = True
        G[u][v]["delay_counter"] = self.delta_t

    def cascade_relay(self, G):
        for u, v, data in G.edges(data=True):
            if data.get("compromised", False):
                if data.get("delay_counter", 0) > 0:
                    data["delay_counter"] -= 1
                else:
                    if G.has_edge(u, v):
                        G.remove_edge(u, v)

    # ------------------------
    # Control Center Attack
    # ------------------------
    def control_attack(self, G):
        substations = [
            n for n, d in G.nodes(data=True)
            if d.get("type") == "substation"
        ]

        targets = self.rng.sample(substations, max(1, len(substations)//5))

        for n in targets:
            G.nodes[n]["monitored"] = False

    # ------------------------
    # Main Simulation Step
    # ------------------------
    def step(self, G):

        # Trigger new attack
        if self.active_attack is None and self.attack_occurs():
            self.active_attack = self.choose_attack()

            if self.active_attack == "false_load":
                self.false_load_injection(G)

            elif self.active_attack == "breaker":
                self.breaker_attack(G)

            elif self.active_attack == "generator":
                self.generator_attack(G)

            elif self.active_attack == "relay":
                self.relay_attack(G)

            elif self.active_attack == "control":
                self.control_attack(G)

        # Cascading behavior
        if self.active_attack == "relay":
            self.cascade_relay(G)