from __future__ import annotations
from dataclasses import dataclass, field, asdict
from typing import List, Optional
from random import randint
from pathlib import Path
import json


# ========== BASE CLASS ==========

@dataclass(kw_only=True)
class DB:
    id: Optional[str] = field(default=None)
    _filename: str = field(default="db.json", repr=False)

    def __post_init__(self):
        if not Path(self._filename).exists():
            raise FileNotFoundError(f"DB connection wasn't possible for: '{self._filename}'")
        if not self.id:
            self.id = str(randint(1, 100))

    def _save_json(self, data: list[dict]):
        print("Saving to DB:", Path(self._filename).absolute())
        with open(self._filename, "w") as f:
            json.dump(data, f, indent=2)

    @staticmethod
    def _load_json(filename: str) -> list[dict]:
        path = Path(filename)
        if not path.exists():
            return []
        with open(path) as f:
            return json.load(f)

    @staticmethod
    def all() -> List["DB"]:
        raise NotImplementedError

    def save(self):
        raise NotImplementedError

    def to_dict(self):
        d = asdict(self)
        d.pop("_filename", None)
        return d


# ========== CHILD CLASSES ==========

@dataclass
class Dish(DB):
    name: Optional[str] = None
    price: Optional[float] = None
    ingredients: List[str] = field(default_factory=list)
    category: Optional[str] = None
    description: Optional[str] = None
    _filename: str = field(default="dish.json", init=False, repr=False)

    @staticmethod
    def all() -> List["Dish"]:
        return [Dish(**d) for d in Dish._load_json(Dish._filename)]

    def save(self):
        dishes = self._load_json(Dish._filename)
        dishes = [d for d in dishes if d.get("id") != self.id]
        dishes.append(self.to_dict())
        self._save_json(dishes)


@dataclass
class Guest(DB):
    name: Optional[str] = None
    preferences: List[str] = field(default_factory=list)
    allergies: List[str] = field(default_factory=list)
    history: List[Dish] = field(default_factory=list)
    _filename: str = field(default="guest.json", init=False, repr=False)

    @staticmethod
    def all() -> List["Guest"]:
        return [Guest(**g) for g in Guest._load_json(Guest._filename)]

    def save(self):
        guests = self._load_json(Guest._filename)
        guests = [g for g in guests if g.get("id") != self.id]
        guests.append(self.to_dict())
        self._save_json(guests)


@dataclass
class Recommendation(DB):
    guest_id: Optional[str] = None
    # dish name, {ingredient: modifications}
    recommended_dishes: List[tuple[str, dict[str, str]]] = field(default_factory=list)
    reason: str = field(default_factory=str)
    _filename: str = field(default="recommendation.json", init=False, repr=False)

    def __post_init__(self):
        super().__post_init__()
        recs = self._load_json(Recommendation._filename)
        existing_guest = next((rec for rec in recs if rec["guest_id"] == self.guest_id), None)
        if existing_guest:
            self.recommended_dishes = existing_guest["recommended_dishes"]

    @staticmethod
    def all() -> List["Recommendation"]:
        return [Recommendation(**r) for r in Recommendation._load_json(Recommendation._filename)]

    def save(self):
        recs = self._load_json(Recommendation._filename)
        recs = [r for r in recs if r["id"] != self.id]
        recs.append(self.to_dict())
        self._save_json(recs)


@dataclass
class Order(DB):
    guest_id: Optional[str] = None
    dishes: List[tuple[Dish, dict[str, str]]] = field(default_factory=list)
    _filename: str = field(default="order.json", init=False, repr=False)

    @staticmethod
    def all() -> List["Order"]:
        return [Order(**o) for o in Order._load_json(Order._filename)]

    def save(self):
        orders = self._load_json(Order._filename)
        orders = [o for o in orders if o["id"] != self.id]
        orders.append(self.to_dict())
        self._save_json(orders)


@dataclass
class Table(DB):
    capacity: Optional[int] = None
    environment: List[str] = field(default_factory=list)
    occupied: bool = False
    guest_id: Optional[str] = None
    _filename: str = field(default="table.json", init=False, repr=False)

    @staticmethod
    def all() -> List["Table"]:
        return [Table(**t) for t in Table._load_json(Table._filename)]

    def save(self):
        tables = self._load_json(Table._filename)
        tables = [t for t in tables if str(t["id"]) != str(self.id)]
        tables.append(self.to_dict())
        self._save_json(tables)

    def allot_table(self, guest_id: str):
        self.guest_id = guest_id
        self.occupied = True
        self.save()
