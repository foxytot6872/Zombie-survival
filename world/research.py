"""
Research system for unlocking buildings and upgrades.
"""
import json
import os
from typing import Set, Dict

class ResearchManager:
    """Manages research unlocks and research definitions."""
    
    def __init__(self, world):
        """
        Initialize research manager.
        Args:
            world: World object with resources
        """
        self.world = world
        self.unlocked: Set[str] = set()  # Unlocked items (e.g., "sawmill", "railgun_turret")
        self.purchased: Set[str] = set()  # Purchased research keys (e.g., "sawmill_unlock")
        self.research_defs: Dict = {}
        
        # Load research definitions
        path = "data/config/research.json"
        try:
            if os.path.exists(path):
                with open(path, "r") as f:
                    self.research_defs = json.load(f)
            else:
                print(f"Warning: Research config not found at {path}, using empty definitions")
        except Exception as e:
            print(f"Error loading research config: {e}")
            self.research_defs = {}
    
    def is_unlocked(self, key: str) -> bool:
        """
        Check if a research item is unlocked.
        Args:
            key: Research key (e.g., "sawmill", "turret_lv2")
        Returns:
            True if unlocked, False otherwise
        """
        return key in self.unlocked
    
    def can_research(self, research_key: str) -> bool:
        """
        Check if a research can be purchased.
        Args:
            research_key: Key from research.json
        Returns:
            True if can afford and not already purchased
        """
        if research_key not in self.research_defs:
            return False
        if research_key in self.purchased:
            return False  # Already purchased
        cost = self.research_defs[research_key].get("cost_coins", 0)
        return self.world.resources.coins >= cost
    
    def is_research_purchased(self, research_key: str) -> bool:
        """
        Check if a research has been purchased.
        Args:
            research_key: Key from research.json
        Returns:
            True if purchased, False otherwise
        """
        return research_key in self.purchased
    
    def unlock(self, research_key: str) -> bool:
        """
        Unlock a research item.
        Args:
            research_key: Key from research.json
        Returns:
            True if successful, False otherwise
        """
        if research_key not in self.research_defs:
            return False
        
        # Check if already purchased
        if research_key in self.purchased:
            return False
        
        # Check cost
        cost = self.research_defs[research_key].get("cost_coins", 0)
        if not self.world.resources.spend_coins(cost):
            return False
        
        # Mark as purchased
        self.purchased.add(research_key)
        
        # Grant unlocks
        unlocks = self.research_defs[research_key].get("unlocks", [])
        for item in unlocks:
            self.unlocked.add(item)
        
        return True
    
    def get_research_list(self) -> Dict:
        """Get all research definitions."""
        return self.research_defs.copy()

