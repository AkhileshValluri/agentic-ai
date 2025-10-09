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
    id: Optional[str]

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
            raw_dishes = cls._instance._load_json()
            cls._dishes = [Dish(**d) for d in raw_dishes]  
        return cls._instance

    def all(self) -> List[Dish]:
        return [Dish(**d) for d in self._dishes]

    def save(self):
        for i, d in enumerate(self._dishes):
            if d.id == self.id:
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
        Request if the dish can be modified

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
        
        print(f"REQUESTED MODIFICATION::DISH:{dish_name}|MODIFICIATIONS:{modification}")
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
    recommended_dishes: List[tuple[Dish, dict[str, str]]] # (dish, modifications)
    filename: str = "recommendation.json"

    def __post_init__(self): 
        recs = self._load_json()
        existing_guest = next([rec for rec in recs if rec["guest_id"] == self.guest_id], None)
        if existing_guest: 
            self.recommended_dishes = existing_guest["recommended_dishes"]

    def all(self) -> List["Recommendation"]:
        return [Recommendation(**r) for r in self._load_json()]

    def save(self):
        recs = self._load_json()
        recs = [r for r in recs if r["id"] != self.id]
        recs.append(asdict(self))
        self._save_json(recs)

    def get_modifications_for_dish(self, dish: Dish) -> dict[str, str]: 
        recommended_dish_ids: list[str] = [dish[0].id for dish in self.recommended_dishes]
        if dish.id in recommended_dish_ids:
            ind = recommended_dish_ids.index(dish.id)
            return self.recommended_dishes[ind][1] 
        return {}

    def store_modifications_for_dish(self, dish: Dish, modifications: dict[str, str]): 
        recommended_dish_ids: list[str] = [dish[0].id for dish in self.recommended_dishes]
        ind = recommended_dish_ids.index(dish.id)

        if dish.id not in recommended_dish_ids:
            self.recommended_dishes.append((dish, modifications))
            return
        else: 
            if len(modifications.keys()) == 0:
                return
            # merge modifications
            self.recommended_dishes[ind][1] = modifications

    @staticmethod
    def save_recommendation(tool_context: ToolContext, dish_name: str, modifications: dict[str, str]): 
        """
        Stores recommendation with modifications for dish in memory to persist changes to comply with allergy information
        To be called if dish is already checked to be modifiable 

        Args: 
            dish_name (str): name of dish to be added exactly as is
            modification (dict(str, str)): Description of ingredients and their modifications

        Returns: 
            Tuple:
                bool: whether the modification is possible
                str: reason modification isn't possible
        
        Example: 
            save_recommendation("Margherita Pizza", {"Wheat flour": "Change to whole wheat", "basil": "remove"})
            save_recommendation("Penne Alfredo", {"cream": "less", "garlic": "extra"})
        """
        print("SAVING RECOMMENDATION for dish: ", dish_name)
        recommended_dish: Optional[Dish] = DishStore().get_dish(dish_name)
        if recommended_dish is None:
            return [False, "We don't make that dish or isn't in stock"]            
        recommendation_state: Recommendation = tool_context.state[constants.RECOMMENDATION_KEY]
        recommendation_state.store_modifications_for_dish(recommended_dish, modifications)
        recommendation_state.save()
        return (True, "")
        

@dataclass
class Order(DB):
    guest_id: str
    dishes: List[tuple[Dish, dict[str, str]]] # dishes with modifications according to preference
    filename: str = "order.json"

    def all(self) -> List["Order"]:
        return [Order(**o) for o in self._load_json()]

    def save(self):
        orders = self._load_json()
        orders = [o for o in orders if o["id"] != self.id]
        orders.append(asdict(self))
        self._save_json(orders)

    def get_dish_index(self, dish: Dish) -> int:
        dish_ids: list[str] = [dish[0].id for dish in self.dishes]
        return dish_ids.index(dish.id)

    @staticmethod
    def get_dishes(tool_context: ToolContext): 
        """
        Get the current dishes and their modifications
        
        Returns: 
            List[tuple[Dish, dict[str, str]]] : list of dishes with their modifications as a tuple
        """
        return tool_context.state[constants.ORDER_KEY]["dishes"]

    @staticmethod
    def update_dishes(tool_context: ToolContext, dishes: list[str]):
        """
        Updates the current state of the dishes to be ordered

        Args: 
            dishes(list[str]): name of the dishes as a list
        """
        recommendation_state: Recommendation = tool_context.state[constants.RECOMMENDATION_KEY]
        order_state: "Order" = tool_context.state[constants.ORDER_KEY]

        for dish_name in dishes: 
            dish: Dish = DishStore().get_dish(dish_name)
            modifications: dict[str, str] = recommendation_state.get_modifications_for_dish(dish)
            try: 
                ind = order_state.get_dish_index(dish)
                # new modifications
                order_state.dishes[ind][1] = modifications
            except:
                # dish isn't added to order list yet  
                order_state.dishes.append((dish, modifications))

        order_state.save()
    
    @staticmethod
    def place_order(tool_context: ToolContext):
        """
        Places the order of the dishes
        """
        order: "Order" = tool_context[constants.ORDER_KEY]
        order.save()
            