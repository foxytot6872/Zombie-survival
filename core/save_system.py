"""
Save/Load system for game state.
"""
import json
import os
from typing import Dict, Optional
from pathlib import Path

class SaveSystem:
    """Handles saving and loading game state"""
    
    def __init__(self, save_dir: str = "data/saves"):
        """
        Initialize save system.
        Args:
            save_dir: Directory for save files
        """
        self.save_dir = Path(save_dir)
        self.save_dir.mkdir(parents=True, exist_ok=True)
        self.save_file = self.save_dir / "last_run.json"
        
    def save_world(self, world, wave_manager, game_state_manager, resources) -> bool:
        """
        Save world state to JSON file.
        Args:
            world: World object containing game state
            wave_manager: Wave manager object
            game_state_manager: Game state manager
            resources: Resources object
        Returns:
            True if save successful, False otherwise
        """
        try:
            save_data = {
                "version": "1.0",
                "wave_manager": {
                    "night": wave_manager.night,
                    "day": wave_manager.day,
                    "state": wave_manager.state,
                    "difficulty": wave_manager.difficulty,
                    "enemies_killed": wave_manager.enemies_killed,
                    "enemies_spawned": wave_manager.enemies_spawned,
                    "timer": wave_manager.timer
                },
                "resources": {
                    "wood": resources.wood,
                    "iron": resources.iron,
                    "food": resources.food
                },
                "buildings": [],
                "game_state": game_state_manager.state.value
            }
            
            # Save buildings
            if world and hasattr(world, 'building_group'):
                for building in world.building_group:
                    building_data = building.to_dict()
                    # Add turret-specific data if needed
                    if hasattr(building, 'turret_image'):
                        # Store turret type and tier
                        building_data["turret_type"] = building.TYPE_ID
                    save_data["buildings"].append(building_data)
            
            # Write to file
            with open(self.save_file, 'w') as f:
                json.dump(save_data, f, indent=2)
            
            return True
            
        except Exception as e:
            print(f"Error saving game: {e}")
            return False
    
    def load_world(self) -> Optional[Dict]:
        """
        Load world state from JSON file.
        Returns:
            Dictionary containing game state, or None if load failed
        """
        try:
            if not self.save_file.exists():
                return None
            
            with open(self.save_file, 'r') as f:
                save_data = json.load(f)
            
            return save_data
            
        except Exception as e:
            print(f"Error loading game: {e}")
            return None
    
    def has_save(self) -> bool:
        """Check if a save file exists"""
        return self.save_file.exists()
    
    def delete_save(self) -> bool:
        """Delete the save file"""
        try:
            if self.save_file.exists():
                self.save_file.unlink()
                return True
            return False
        except Exception as e:
            print(f"Error deleting save: {e}")
            return False

