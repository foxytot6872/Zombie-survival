"""
Resource management system for the game.
"""
from dataclasses import dataclass

@dataclass
class Resources:
    """Game resources (wood, iron, food, coins)."""
    wood: int = 0
    iron: int = 0
    food: int = 0
    coins: int = 0
    
    def add(self, wood: int = 0, iron: int = 0, food: int = 0):
        """Add resources."""
        self.wood += wood
        self.iron += iron
        self.food += food
    
    def subtract(self, wood: int = 0, iron: int = 0, food: int = 0):
        """Subtract resources (no negative checks)."""
        self.wood -= wood
        self.iron -= iron
        self.food -= food
    
    def has_enough(self, wood: int = 0, iron: int = 0, food: int = 0) -> bool:
        """Check if we have enough resources."""
        return self.wood >= wood and self.iron >= iron and self.food >= food
    
    def add_coins(self, amount: int):
        """Add coins."""
        self.coins += amount
    
    def spend_coins(self, amount: int) -> bool:
        """Spend coins if we have enough."""
        if self.coins >= amount:
            self.coins -= amount
            return True
        return False

