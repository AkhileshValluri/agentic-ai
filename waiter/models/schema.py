import json
from random import randint
import uuid
from dataclasses import dataclass, asdict, field
from typing import Any, List, Optional
from datetime import datetime
from pathlib import Path

from google.adk.tools import ToolContext
from google.adk.sessions.state import State

from waiter.shared_libraries import constants

class DB:
    filename: str = ""
    id: str

    def __init__(self): 
        if not Path(self.filename).exists(): # check that it exists 
            raise Exception(f"DB connection wasn't possible for: '{self.filename}'")
        self.id = str(randint(0, 100))

    def _save_json(self, data: list[dict]):
        print("Saving to DB: ", Path(self.filename).absolute())
        with open(self.filename, "w") as f:
            json.dump(data, f, indent=2)

    def _load_json(self) -> list[dict]:
        path = Path(self.filename)
        with open(path) as f:
            return json.load(f)

    def all(self) -> List["DB"]:
        raise NotImplementedError
    
    def save(self): 
        raise NotImplementedError

@dataclass
class Dish(DB):
    name: str 
    price: float
    ingredients: list[str]
    category: str
    description: str

class DishStore(DB):
    """
    Class to access the state of available dishes at all times
    Singleton for consistency across all instantiations
    """
    _instance = None
    _dishes: List[Dish] = []
    filename: str = "dish.json"

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._dishes = cls._instance._load_json()
        return cls._instance

    def all(self) -> List[Dish]:
        return [Dish(**d) for d in self._dishes]

    def save(self):
        for i, d in enumerate(self._dishes):
            if d["id"] == self.id:
                self._dishes[i] = asdict(self)
                break
        else:
            self._dishes.append(asdict(self))
        self._save_json(self._dishes)
    
    @staticmethod
    def get_dish(dish_name: str) -> Optional[Dish]: 
        """
        Check whether a dish exists
        
        Args: 
            dish_name (str): Name of the dish to check if exists

        Returns: 
            Optional[Dish]: None if dish doesn't exist else the dish object
        """
        for dish in DishStore()._dishes:
            if dish.name.lower() == dish_name.lower(): 
                return dish
        return None

    @staticmethod
    def request_modification(dish_name: str, modification: dict[str, str]) -> tuple[bool, str]:
        """
        Check the number of guests being served, if high, reject modification

        Args: 
            dish_name (str): Name of the dish to be modified
            modification (dict(str, str)): Description of ingredients and their modifications

        Returns: 
            Tuple:
                bool: whether the modification is possible
                str: reason modification isn't possible
        
        Example: 
            request_modification("Margherita Pizza", {"Wheat flour": "Change to whole wheat", "basil": "remove"})
            request_modification("Penne Alfredo", {"cream": "less", "garlic": "extra"})
        """
        # check if dish even exists
        if DishStore.get_dish(dish_name) is None:
            return (False, "Creating a new dish for you isn't possible")

        # Mock: check if modification possible due to high capacity
        current_capacity = randint(0, 100)
        modification_complexity = len(modification.keys())
        difficulty_to_satisfy = current_capacity * modification_complexity
        DIFFICULTY_THRESHHOLD = 100
        if difficulty_to_satisfy > DIFFICULTY_THRESHHOLD:
            return (False, "Too many people currently in the restaurant")
        
        return (True, "")

    @staticmethod
    def specials() -> list[Dish]:
        """
        Todays special dishes

        Returns: 
            list[Dish]

        Example:
            specials() -> 
                "{
                    "id": "D001",
                    "name": "Margherita Pizza",
                    "price": 299.0,
                    "ingredients": ["wheat flour", "tomato sauce", "mozzarella cheese", "basil", "olive oil"],
                    "category": "Main Course",
                    "description": "Classic Italian pizza with tomato, mozzarella, and basil."
                },
                {
                    "id": "D002",
                    "name": "Penne Alfredo",
                    "price": 349.0,
                    "ingredients": ["penne pasta", "cream", "parmesan", "garlic", "butter"],
                    "category": "Main Course",
                    "description": "Rich creamy pasta in Alfredo sauce."
                }
                "
        """

@dataclass
class Guest(DB):
    name: str = field(default_factory=str)
    preferences: List[str] = field(default_factory=list)
    allergies: List[str] = field(default_factory=list)
    history: List[str] = field(default_factory=list)
    filename: str = "guest.json"

    def all(self) -> List["Guest"]:
        """
        Load all guests from storage.

        Returns:
            List[Guest]: List of all Guest instances.
        """
        return [Guest(**g) for g in self._load_json()]

    def save(self):
        """
        Save the current Guest instance to storage. Overwrites existing guest with the same ID.
        """
        guests = self._load_json()
        guests = [g for g in guests if g.get("id") != getattr(self, "id", None)]
        guests.append(asdict(self))
        self._save_json(guests)

    @staticmethod
    def get_curr_guest(state: State) -> "Guest": 
        return state['guest']

    @staticmethod
    def new_guest(
        tool_context: ToolContext,
        name: str,
    ) -> "Guest":
        """
        Create a new guest and persist to storage.

        Args:
            name (str): Full name of the guest.

        Returns:
            Guest: The created Guest instance.
        """
        guest = Guest(name=name)
        guest.save()
        tool_context.state['guest'] = guest
        return guest
    
    @staticmethod
    def set_preferences(tool_context: ToolContext, preferences: List[str]):
        """
        Update the guest's preferences list.

        Args:
            preferences (List[str]): New list of preferred dish IDs or categories.
        """
        g = Guest.get_curr_guest(tool_context.state)
        g.preferences = preferences
        g.save()

    @staticmethod
    def set_allergies(tool_context: ToolContext, allergies: List[str]):
        """
        Update the guest's allergy list.

        Args:
            allergies (List[str]): New list of ingredients the guest is allergic to.
        """
        g = Guest.get_curr_guest(tool_context.state)
        g.allergies = allergies
        g.save()


    @staticmethod
    def add_to_history(tool_context: ToolContext, dish_id: str):
        """
        Append a dish to the guest's order history.

        Args:
            dish_id (str): The ID of the dish to add to the guest's history.

        Returns:
            Optional[dict]: The updated guest dict if found, else None.
        """
        g = Guest.get_curr_guest(tool_context.state)
        if dish_id not in g.history:
            g.history.append(dish_id)
        g.save()

@dataclass
class Recommendation(DB): 
    guest_id: str
    recommended_dishes: List[Dish]
    reason: str
    filename: str = "recommendation.json"

    def __post_init__(self): 
        recs = self._load_json()
        existing_guest = next([rec for rec in recs if rec["guest_id"] == self.guest_id], None)
        if existing_guest: 
            self.recommended_dishes = existing_guest["recommended_dishes"]
            self.reason = existing_guest["reason"]

    def all(self) -> List["Recommendation"]:
        return [Recommendation(**r) for r in self._load_json()]

    def save(self):
        recs = self._load_json()
        recs = [r for r in recs if r["id"] != self.id]
        recs.append(asdict(self))
        self._save_json(recs)

    @staticmethod
    def add_suggestion(tool_context: ToolContext, dish_name: str, reason: str): 
        """
        Stores suggestion for dish in memory

        Args: 
            dish_name (str): name of dish to be added exactly as is
            reason (str): why dish was recommended 
        
        Returns: 
            Tuple: 
                bool: Whether transaction was successfull or not
                str: Reason for failure
        """
        recommended_dish: Optional[Dish] = DishStore().get_dish(dish_name)
        if recommended_dish is None:
            return [False, "We don't make that dish or isn't in stock"]            
        recommendation_state: Recommendation = tool_context.state[constants.RECOMMENDATION_KEY]
        if recommended_dish.id in [dish.id for dish in recommendation_state.recommended_dishes]:
            return (True, "")
        recommendation_state.recommended_dishes.append(recommended_dish)
        recommendation_state.save()
        return (True, "")
        

@dataclass
class Order(DB):
    guest_id: str
    dish_ids: List[str]
    status: str = "pending"  # pending / preparing / served / completed
    filename: str = "order.json"
    created_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())

    def all(self) -> List["Order"]:
        return [Order(**o) for o in self._load_json()]

    def save(self):
        orders = self._load_json()
        orders = [o for o in orders if o["id"] != self.id]
        orders.append(asdict(self))
        self._save_json(orders)