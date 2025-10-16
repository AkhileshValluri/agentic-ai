import json
from random import randint
import uuid
from dataclasses import dataclass, asdict, field
from typing import Any, List, Optional
from datetime import datetime
from pathlib import Path

from waiter.shared_libraries import constants

@dataclass
class DB:
    id: str | None
    filename: str

    def __post_init__(self): 
        if not Path(self.filename).exists(): # check that it exists 
            raise Exception(f"DB connection wasn't possible for: '{self.filename}'")
        if not self.id: 
            self.id = str(randint(1, 100))

    def _save_json(self, data: list[dict]):
        print("Saving to DB: ", Path(self.filename).absolute())
        with open(self.filename, "w") as f:
            json.dump(data, f, indent=2)

    @staticmethod
    def _load_json(filename: str) -> list[dict]:
        path = Path(filename)
        with open(path) as f:
            return json.load(f)

    @staticmethod
    def all() -> List["DB"]:
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
    filename:str = field(default="dish.json", init=False) 

    @staticmethod
    def all() -> List["Dish"]:
        return [Dish(**d) for d in Dish._load_json(Dish.filename)]

    def save(self):
        """
        save the current guest instance to storage. overwrites existing guest with the same id.
        """
        dishes = self._load_json(Dish.filename)
        dishes = [d for d in dishes if d.get("id") != self.id]
        dishes.append(asdict(self))
        self._save_json(dishes)


@dataclass
class Guest(DB):
    name: str = field(default_factory=str)
    preferences: List[str] = field(default_factory=list)
    allergies: List[str] = field(default_factory=list)
    history: List[Dish] = field(default_factory=list)
    filename: str = field(default="guest.json", init=False)

    def all() -> List["Guest"]:
        return [Guest(**g) for g in Guest._load_json(Guest.filename)]

    def save(self):
        """
        save the current guest instance to storage. overwrites existing guest with the same id.
        """
        guests = self._load_json(Guest.filename)
        guests = [g for g in guests if g.get("id") != self.id]
        guests.append(asdict(self))
        self._save_json(guests)


@dataclass
class Recommendation(DB): 
    guest_id: str
    recommended_dishes: List[tuple[str, dict[str, str]]] # (dish_id, modifications)
    filename: str = field(default="recommendation.json", init=False)

    def __post_init__(self): 
        # load history dynamically if guest already visited restaurant
        recs = self._load_json(Recommendation.filename)
        existing_guest = next([rec for rec in recs if rec["guest_id"] == self.guest_id], None)
        if existing_guest: 
            self.recommended_dishes = existing_guest["recommended_dishes"]

    @staticmethod
    def all() -> List["Recommendation"]:
        return [Recommendation(**r) for r in Recommendation._load_json(Recommendation.filename)]

    def save(self):
        recs = self._load_json(Recommendation.filename)
        recs = [r for r in recs if r["id"] != self.id]
        recs.append(asdict(self))
        self._save_json(recs)

        

@dataclass
class Order(DB):
    guest_id: str
    dishes: List[tuple[Dish, dict[str, str]]] # dishes with modifications according to preference
    filename: str = field(default="order.json", init=False)

    @staticmethod
    def all() -> List["Order"]:
        return [Order(**o) for o in Order._load_json(Order.filename)]

    def save(self):
        orders = self._load_json(Order.filename)
        orders = [o for o in orders if o["id"] != self.id]
        orders.append(asdict(self))
        self._save_json(orders)


@dataclass
class Table(DB):
    capacity: int
    environment:List[str]
    occupied: bool
    guest_id: Optional[str]

    filename: str = field(default="table.json", init = False)

    def all() -> List["Table"]:
        return [Table(**t) for t in Table._load_json(Table.filename)]

    def save(self):
        tables = self._load_json(Table.filename)

        tables = [t for t in tables if str(t["tableNumber"]) != str(self.id)]
        tables.append(asdict(self))

        self._save_json(tables)

    def allot_table(self, guest_id: str):
        """
        Allots the table with the matching table number to the guest

        Args:
            tableNumber: The number of the table to allot. 
        
        Returns: 
            str: Error or Sucess and reason
        """
        self.guest_id = guest_id
        self.occupied = True
        self.save()
                