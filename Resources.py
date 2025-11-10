"""
Resource management system
"""
import json
import os

class Resources:
    def __init__(self, wood=0, metal=0, food=0, research=0):
        self.wood = wood
        self.metal = metal
        self.food = food
        self.research = research
    
    def can_afford(self, costs):
        """Check if we can afford the given costs"""
        if costs.get("Wood", 0) > self.wood:
            return False
        if costs.get("Metal", 0) > self.metal:
            return False
        if costs.get("Food", 0) > self.food:
            return False
        if costs.get("Research", 0) > self.research:
            return False
        return True
    
    def spend(self, costs):
        """Spend resources (assumes can_afford was checked)"""
        self.wood -= costs.get("Wood", 0)
        self.metal -= costs.get("Metal", 0)
        self.food -= costs.get("Food", 0)
        self.research -= costs.get("Research", 0)
    
    def add(self, resources):
        """Add resources"""
        self.wood += resources.get("Wood", 0)
        self.metal += resources.get("Metal", 0)
        self.food += resources.get("Food", 0)
        self.research += resources.get("Research", 0)
    
    def to_dict(self):
        """Convert to dictionary for saving"""
        return {
            "wood": self.wood,
            "metal": self.metal,
            "food": self.food,
            "research": self.research
        }
    
    def from_dict(self, data):
        """Load from dictionary"""
        self.wood = data.get("wood", 0)
        self.metal = data.get("metal", 0)
        self.food = data.get("food", 0)
        self.research = data.get("research", 0)
    
    def save(self, filename="save.json"):
        """Save resources to JSON file"""
        data = {
            "resources": self.to_dict()
        }
        with open(filename, 'w') as f:
            json.dump(data, f, indent=2)
    
    def load(self, filename="save.json"):
        """Load resources from JSON file"""
        if os.path.exists(filename):
            with open(filename, 'r') as f:
                data = json.load(f)
                if "resources" in data:
                    self.from_dict(data["resources"])

