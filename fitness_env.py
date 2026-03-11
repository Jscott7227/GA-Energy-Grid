import networkx as nx
import random
import json

class GridFitnessEnv:
    def __init__(self, weather_config_path, cyber_model, years=5, n_scenarios=100, weeks_per_year=52, rng=None):
        # Load weather configuration from JSON
        with open(weather_config_path, "r") as f:
            self.weather_config = json.load(f)
            
        self.cyber = cyber_model
        self.years = years
        self.n_scenarios = n_scenarios
        self.weeks_per_year = weeks_per_year
        self.rng = rng or random.Random()

        # Node importance weights
        self.node_weights = {
            "essential": 5.0,
            "commercial": 2.0,
            "residential": 1.0
        }

        # Generate all weather scenarios at initialization for consitant eval accross population step
        self.weather_scenarios = self._generate_weather_scenarios()
        
    def _generate_weather_scenarios(self):
        scenarios = []

        for _ in range(self.n_scenarios):
            scenario = []
            for year in range(self.years):
                for week in range(self.weeks_per_year):
                    season = self._get_season(week)
                    event = self._sample_event(season)
                    scenario.append({
                        "year": year,
                        "week": week,
                        "season": season,
                        "event": event
                    })
            scenarios.append(scenario)
        return scenarios
    
    def _get_season(self, week):
        if week < 13:
            return "winter"
        elif week < 26:
            return "spring"
        elif week < 39:
            return "summer"
        else:
            return "fall"
        
    def _sample_event(self, season):
        events = self.weather_config["seasonal_event_probs"].get(season, {})
        for event, prob in events.items():
            if self.rng.random() < prob:
                return event
        return None
        
    def _edge_failure_prob(self, event):
        return self.weather_config["edge_failure_probability"].get(event, 0)
    
    def run_scenario(self, G, scenario):
        G_sim = G.copy()
        total_score = 0

        for step in scenario:
            event = step["event"]
            
            #TODO Propigation to nodes in a realistic manner
            # Apply weather failures
            if event is not None:
                fail_prob = self._edge_failure_prob(event)
                for edge in list(G_sim.edges):
                    if self.rng.random() < fail_prob:
                        G_sim.remove_edge(*edge)

            #TODO Propigation to nodes in a realistic manner
            # Apply cyber attack failures
            if self.cyber.attack_occurs():
                for edge in list(G_sim.edges):
                    if self.rng.random() < self.cyber.edge_failure_probability:
                        G_sim.remove_edge(*edge)

            #TODO Per week or per year or per season
            # Evaluate power availability
            total_score += self._evaluate_power(G_sim)

        return total_score / len(scenario)
    
    def run_simulation(self, G):
        scores = [self.run_scenario(G, scenario) for scenario in self.weather_scenarios]
        return sum(scores) / len(scores)
    
    #TODO add power Reqs from and for each node
    def _evaluate_power(self, G):
        generators = [n for n, d in G.nodes(data=True) if d["type"] == "generator"]
        powered_nodes = set()

        for g in generators:
            powered_nodes.update(nx.node_connected_component(G, g))

        score = 0
        for node, data in G.nodes(data=True):
            if data["type"] in self.node_weights and node in powered_nodes:
                score += self.node_weights[data["type"]]
        return score
    
    #TODO Calc cost of lines
    def infrastructure_cost(self, G):
        # Simple cost: 1 per edge
        edge_cost = len(G.edges)
        return edge_cost
    
    def evaluate(self, G):
        reliability_score = self.run_simulation(G)
        cost_penalty = self.infrastructure_cost(G)
        fitness = reliability_score - cost_penalty
        return fitness
    