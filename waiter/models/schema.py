import json
from random import randint
import uuid
from dataclasses import dataclass, asdict, field
from typing import List, Optional
from datetime import datetime
from pathlib import Path

from google.adk.tools import ToolContext
from google.adk.sessions.state import State

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
    ingredients: List[str]
    category: str
    description: Optional[str] = None
    filename: str = "dish.json"

    def all(self) -> List["Dish"]:
        return [Dish(**d) for d in self._load_json()]

    def save(self):
        dishes = self._load_json()
        dishes = [d for d in dishes if d["id"] != self.id]
        dishes.append(asdict(self))
        self._save_json(dishes)

@dataclass
class Guest(DB):
    name: str = field(default_factory=str)
    preferences: List[str] = field(default_factory=list)
    allergies: List[str] = field(default_factory=list)
    history: List[str] = field(default_factory=list)
    filename: str = "guest.json"

    @staticmethod
    def new_guest(
        tool_context: ToolContext,
        name: str,
        preferences: List[str],
        allergies: List[str],
        history: List[str]
    ) -> "Guest":
        """
        Create a new guest and persist to storage.

        Args:
            name (str): Full name of the guest.
            preferences (List[str], optional): List of preferred dish IDs or categories. Defaults to [].
            allergies (List[str], optional): List of ingredients the guest is allergic to. Defaults to [].
            history (List[str], optional): List of previously ordered dish IDs. Defaults to [].

        Returns:
            Guest: The created Guest instance.
        """
        guest = Guest(name=name, preferences=preferences, allergies=allergies, history=history)
        guest.save()
        tool_context.state['guest'] = guest
        return guest
    
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
    suggested_dishes: List[str]
    reason: str
    created_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    filename: str = "recommendation.json"

    def all(self) -> List["Recommendation"]:
        return [Recommendation(**r) for r in self._load_json()]

    def save(self):
        recs = self._load_json()
        recs = [r for r in recs if r["id"] != self.id]
        recs.append(asdict(self))
        self._save_json(recs)

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