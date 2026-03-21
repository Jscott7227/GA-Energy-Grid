import networkx as nx
import random
import json

class GridFitnessEnv:
    def __init__(self, weather_config_path, cyber_model, years=5, weeks_per_year=52, rng=None):
        # Load weather configuration from JSON
        with open(weather_config_path, "r") as f:
            self.weather_config = json.load(f)
            
        self.cyber = cyber_model
        self.years = years
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
        for year in range(self.years):
            for week in range(self.weeks_per_year):
                season = self._get_season(week)
                event = self._sample_event(season)
                severity = None
                if event is not None:
                    severity = self._sample_severity(season, event)
                
                scenarios.append({
                    "year": year,
                    "week": week,
                    "season": season,
                    "event": event,
                    "severity": severity
                })
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
        r = self.rng.random()
        cumulative = 0.0
        for event, prob in events.items():
            cumulative += prob
            if r < cumulative:
                return event
        return None
        
    def _sample_severity(self, season, event):
        dist = (
            self.weather_config
            .get("seasonal_severity_distribution", {})
            .get(season, {})
            .get(event)
        )

        if not dist:
            return None

        severity = self.rng.gauss(dist["mean"], dist["std"])

        #[1.0, 10.0]
        return max(1.0, min(10.0, severity))
    
    def _edge_failure_prob(self, event):
        return self.weather_config["edge_failure_probability"].get(event, 0)
    
    #TODO currently requires one generator per sub-graph
    #TODO Set lenght of blackout / node trims / node disconnections
    def _weather_propigation(self, G, severity, alpha=0.01, super_failure = 10):
        generation_scale = (1 - alpha * severity)
        #TODO grab from config
        line_fail_prob = min(1.0, 0.02 * severity)
        
        supply = 0.0
        demand = 0.0
        visited = set()
        
        for node, data in G.nodes(data=True):
            if data.get("type") != "generator":
                continue
            if node in visited:
                continue
            
            component_nodes = nx.node_connected_component(G, node)
            visited.update(component_nodes)
            
            sub_nodes = list(component_nodes)
            
            supply = data.get("power_generated", 0.0) * generation_scale
            
            demand = 0.0
            #TODO Determine how to add substations either GA placed or env generated
            
            substations = []
            demand_nodes = {
                "essential": [],
                "commercial": [],
                "residential": []
            }
            
            for n in sub_nodes:
                n_data = G.nodes[n]
                n_type = n_data.get("type")

                if n_type != "generator":
                    demand += n_data.get("power_required", 0.0)

                    if n_type in demand_nodes:
                        demand_nodes[n_type].append(n)

                if n_type == "substation":
                    substations.append(n)
            
            if supply < demand:
                deficit = abs(supply - demand)
                
                # Rolling blackout (local)
                if deficit < super_failure:
                    trim_order = ["residential", "commercial", "essential"]
                    
                    #TODO ADD smart trim logic
                    for t in trim_order:
                        for n in demand_nodes[t]:
                            for neigh in list(G.neighbors(n)):
                                if neigh in substations:
                                    if random.random() < severity * 0.05:
                                        G.remove_edge(n, neigh)
                                        
                    connected = nx.node_connected_component(G, node)
                    demand = sum(
                        G.nodes[x].get("power_required", 0.0)
                        for x in connected
                        if G.nodes[x].get("type") != "generator"
                    )

                    if supply >= demand:
                        break
                
                # Full Blackout of generator
                else: 
                    G.nodes[node]["power_generated"] = 0.0

                    for n in sub_nodes:
                        if G.nodes[n].get("type") != "generator":
                            G.nodes[n]["served"] = False
                    
            # Weather related line failures
            else:
                edges_to_remove = []
                
                for u, v in G.edges(sub_nodes):
                    if random.random() < line_fail_prob:
                        edges_to_remove.append((u, v))

                G.remove_edges_from(edges_to_remove)
        
        # Mark disconnected nodes as unserved
        for component in nx.connected_components(G):
            has_generator = any(
                G.nodes[n].get("type") == "generator" and 
                G.nodes[n].get("power_generated", 0) > 0
                for n in component
            )

            for n in component:
                if G.nodes[n].get("type") != "generator":
                    G.nodes[n]["served"] = has_generator
        
    def run_scenario(self, G, scenario):
        G_sim = G.copy()
        total_score = 0

        event = scenario["event"]
        severity = scenario['severity']
        #Percentage of power generation lost per storm severity
        alpha = 0.01
        
        # Apply weather failures
        if severity is not None:
            self._weather_propigation(G_sim, severity, alpha)



        #TODO Propigation to nodes in a realistic manner
        # Apply cyber attack failures
        if self.cyber.attack_occurs():
            for edge in list(G_sim.edges):
                if self.rng.random() < self.cyber.edge_failure_probability:
                    G_sim.remove_edge(*edge)

        # Evaluate power availability
        total_score = self._evaluate_power(G_sim)

        return total_score
    
    #TODO Currently treats each week independently adjust if wanting a time based scenario
    def run_simulation(self, G):
        scores = [self.run_scenario(G, scenario) for scenario in self.weather_scenarios]
        return sum(scores) / len(scores)
    
    def _evaluate_power(self, G):
        
        node_type_weights = {
            "essential": 0.5,
            "residential": 0.2,
            "commercial": 0.30
        }
        
        type_totals = {k: 0 for k in node_type_weights}
        type_served = {k: 0 for k in node_type_weights}
        
        for node, data in G.nodes(data=True):
            node_type = data.get("type")
            if node_type in type_totals:
                type_totals[node_type] += 1
                if data.get("served", False):
                    type_served[node_type] += 1
        
        score = 0.0      
        for node_type, weight in node_type_weights.items():
            total = type_totals[node_type]
            if total > 0:
                served_fraction = type_served[node_type] / total
            else:
                served_fraction = 0.0
            score += weight * served_fraction
        
        # Percentage of total system functionality satisfied, weighted by importance
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
    