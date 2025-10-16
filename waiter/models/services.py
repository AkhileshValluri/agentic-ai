from google.adk.tools import ToolContext
from google.adk.agents.callback_context import CallbackContext
from google.adk.sessions.state import State

from waiter.models.schema import *
from waiter.shared_libraries import constants

class DishStore:
    """
    Class to access the state of available dishes at all times
    Singleton for consistency across all instantiations
    """
    _instance = None
    _dishes: List[Dish] = []

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._dishes = Dish.all()
        return cls._instance
    
    def _get_dish(self, dish_name: str) -> Optional[Dish]: 
        dish_names: list[str] = [dish.name.lower() for dish in self._dishes]
        try: 
            return self._dishes[dish_names.index(dish_name)]
        except ValueError:
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
        if DishStore()._get_dish(dish_name) is None:
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


class GuestStore: 
    """
    Class to access the state of all Guests
    Singleton so class holds consistent state
    """
    _instance = None
    _guests: List[Guest] = []

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._guests = Guest.all()
        return cls._instance
    
    @staticmethod
    def get_curr_guest(state: State) -> Guest: 
        curr_guest_id = state[constants.GUEST_KEY]
        all_guest_ids: list[str] = [guest.id for guest in GuestStore()._guests]
        return GuestStore()._guests[all_guest_ids.index(curr_guest_id)]

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
        guest_store: "GuestStore" = tool_context.state[constants.GUEST_KEY]
        guest_store._guests.append(guest)
        tool_context.state[constants.GUEST_KEY] = guest.id
        return guest
    
    @staticmethod
    def set_preferences(tool_context: ToolContext, preferences: List[str]):
        """
        Update the guest's preferences list.

        Args:
            preferences (List[str]): New list of preferred dish IDs or categories.
        """
        g = GuestStore.get_curr_guest(tool_context.state)
        g.preferences += preferences
        g.save()

    @staticmethod
    def set_allergies(tool_context: ToolContext, allergies: List[str]):
        """
        Update the guest's allergy list.

        Args:
            allergies (List[str]): New list of ingredients the guest is allergic to.
        """
        g = GuestStore.get_curr_guest(tool_context.state)
        g.allergies += allergies
        g.save()

    @staticmethod
    def _add_to_history(tool_context: ToolContext, dish: Dish):
        """
        Append a dish to the guest's order history.

        Args:
            dish_id (str): The ID of the dish to add to the guest's history.

        Returns:
            Optional[dict]: The updated guest dict if found, else None.
        """
        g = GuestStore.get_curr_guest(tool_context.state)
        historic_dish_ids = [d.id for d in g.history]
        if dish not in historic_dish_ids:
            g.history.append(dish)
        g.save()

class RecommendationService: 
    """
    Class to get, modify, and store recommendations for a guest for a dish
    """
    _recommendation: Recommendation
    _recommendations: list[Recommendation] = []
    _guest: Optional[Guest] = None

    def _init__(self, callback_context: CallbackContext):
        self._recommendations = Recommendation.all()
        current_guest: Guest = GuestStore().get_curr_guest(callback_context.state)
        self._guest = current_guest
        self._recommendations = Recommendation.all()
        # get recommendation for guest only
        self._recommendation = next((rec for rec in self._recommendations if rec.guest_id == self._guest.id), None)
        if self._recommendation is None: 
            self._recommendation = Recommendation(
                guest_id=self._guest.id,
                recommended_dishes=[]
            )
        
    def get_modifications_for_dish(self, dish: Dish) -> dict[str, str]: 
        # doesn't handle case when guest asks for multiple modifications of same dish
        recommended_dish_ids: list[str] = [dish[0].id for dish in self._recommendation.recommended_dishes]
        if dish.id not in recommended_dish_ids:
            return {}
        ind = recommended_dish_ids.index(dish.id)
        return self._recommendation.recommended_dishes[ind][1] 

    def store_modifications_for_dish(self, dish: Dish, modifications: dict[str, str]): 
        recommended_dish_ids: list[str] = [dish[0].id for dish in self._recommendation.recommended_dishes]
        if len(modifications.keys()) == 0:
            return
        if dish.id not in recommended_dish_ids:
            self._recommendation.recommended_dishes.append((dish, modifications))
            return

        ind = recommended_dish_ids.index(dish.id)
        # merge modifications to keep old info
        self._recommendation.recommended_dishes[ind][1] |= modifications

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
        recommended_dish: Optional[Dish] = DishStore()._get_dish(dish_name)
        if recommended_dish is None:
            return [False, "We don't make that dish or isn't in stock"]            
        recommendation_service: RecommendationService = tool_context.state[constants.RECOMMENDATION_KEY]
        recommendation_service.store_modifications_for_dish(recommended_dish, modifications)
        return (True, "")

class OrderService: 
    """
    Class to access state of order for guest
    """
    _orders: list[Order] = []
    _order: Order
    _guest: Guest
    
    def __init__(self, callback_context: ToolContext): 
        self._guest = GuestStore().get_curr_guest(callback_context.state)
        self._orders = Order.all()
        self._order = next((order for order in self._orders if order.guest_id == self._guest.id), None)
        if self._order is None: 
            self._order = Order(
                guest_id=self._guest.id,
                dishes=[],
            )

    def _get_dish_index(self, dish: Dish) -> int:
        dish_ids: list[str] = [dish[0].id for dish in self._order.dishes]
        return dish_ids.index(dish.id)

    def _add_dish(self, dish: Dish, modifications: Optional[dict[str, str]] = {}): 
        try: 
            ind = self._get_dish_index(dish)
            self._order.dishes[ind][1] = modifications
        except: 
            self._order.dishes.append((dish, modifications))
        self._order.save()

    @staticmethod
    def get_dishes(tool_context: ToolContext): 
        """
        Get the current dishes and their modifications
        
        Returns: 
            List[tuple[Dish, dict[str, str]]] : list of dishes with their modifications as a tuple
        """
        order_service: "OrderService" = tool_context[constants.ORDER_KEY]
        return order_service._order.dishes

    @staticmethod
    def update_dishes(tool_context: ToolContext, dish_names: list[str]):
        """
        Updates the current state of the dishes to be ordered

        Args: 
            dishes(list[str]): name of the dishes as a list
        """
        recommendation_state: RecommendationService = tool_context.state[constants.RECOMMENDATION_KEY]
        order_service: OrderService = tool_context.state[constants.ORDER_KEY]

        for dish_name in dish_names: 
            dish: Dish = DishStore()._get_dish(dish_name)
            modifications: dict[str, str] = recommendation_state.get_modifications_for_dish(dish)
            order_service._add_dish((dish, modifications))
    
    @staticmethod
    def add_dish(tool_context: ToolContext, dish_name: str):
        """
        Adds a dish to the order list
        Args: 
            dish(str): name of the dish
        """
        order_service: "OrderService" = tool_context.state[constants.ORDER_KEY]
        recommendation_state: RecommendationService = tool_context.state[constants.RECOMMENDATION_KEY]

        dish: Dish = DishStore()._get_dish(dish_name)
        modifications: dict[str, str] = recommendation_state.get_modifications_for_dish(dish)

        order_service._add_dish(dish, modifications)
  
    @staticmethod
    def place_order(tool_context: ToolContext):
        """
        Places the order of the dishes
        """
        order_service: "OrderService" = tool_context[constants.ORDER_KEY]
        order_service._order.save()
        print(f"Order has been placed for: {json.dumps(order_service._order, indent=2)}")

class TableStore:
    """
    Class to access the state of available tables
    """
    _instance = None
    _tables: List[Table] = []

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._tables = Table.all()
        return cls._instance
    
    def _get_table(self, table_id: str) -> Optional[Table]: 
        # can add deterministic logic / another agent to filter tables by weather condns
        for table in self._tables: 
            if table.id == table_id: 
                return table
        return None

    @staticmethod
    def allot_to_guest(tool_context: ToolContext, table_id: str): 
        """
        Allots a table to the guest currently being serviced
        Args:
            table_id(str): id of table you want to allot to guest
        """
        table_store: "TableStore" = tool_context.state[constants.TABLE_KEY]
        table: Table = table_store._get_table(table_id)
        if table.occupied: 
            raise Exception(f"ERROR: Table {table.id} is already occupied")
        table.allot_table(GuestStore().get_curr_guest(tool_context.state).id)

    @staticmethod
    def get_tables(tool_context: ToolContext) -> list[Table]:
        """
        Gets a list of available tables according to user preference

        Args:

        Returns:
            List[Table]: List of available tables according to user preference
        """
        table_state: "TableStore" = tool_context.state[constants.TABLE_KEY]
        return table_state._tables
    