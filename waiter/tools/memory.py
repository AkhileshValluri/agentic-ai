"""The 'memorize' tool for several agents to affect session states."""
from google.adk.agents.callback_context import CallbackContext

from waiter.models.schema import *
from waiter.models.services import * 
from waiter.shared_libraries import constants

def parse_user_query(callback_context: CallbackContext) -> str:
    user_query = "".join([part.text for part in callback_context.user_content.parts])
    return user_query 

def get_next_phase(callback_context: CallbackContext) -> str: 
    next_phase: dict[str, str] = {
        "introduction": "selection",
        "selection": "order placement",
        "order placement": "introduction"
    }
    curr_phase = callback_context.state[constants.PHASE_KEY]
    return next_phase[curr_phase]

def guest_model_init(callback_context: CallbackContext):
    """
    Initializes the state for a new guest

    Args:
        callback_context: The callback context.
    """
    if constants.GUEST_KEY not in callback_context.state: 
        callback_context.state[constants.GUEST_KEY] = GuestStore()
    callback_context.state[constants.PHASE_KEY] = "introduction"
    callback_context.state[constants.ERROR_KEY] = None
    callback_context.state[constants.SPECIALS_KEY] = DishStore().specials()

def recommendation_model_init(callback_context: CallbackContext):
    """
    Initializes the state of recommendation for new guest

    Args:
        callbcak_context: The callback context
    """
    # add all conditions to be able to initialize recommendations object
    if constants.GUEST_KEY not in callback_context.state:
        callback_context.state[constants.ERROR_KEY] = (
            "All information about guest not gathered yet"
        )
        return

    callback_context.state[constants.PHASE_KEY] = "selection"
    if constants.RECOMMENDATION_KEY not in callback_context.state: 
        callback_context.state[constants.RECOMMENDATION_KEY] = RecommendationService(callback_context)
        callback_context.state[constants.INITIAL_RECOMMENDATION_KEY] = ""
        callback_context.state[constants.INITIAL_CRITIQUE_KEY] = ""

    callback_context.state[constants.ERROR_KEY] = None
    callback_context.state[constants.USER_QUERY_KEY] = parse_user_query(callback_context)

def order_model_init(callback_context: CallbackContext):
    """
    Initializes the state of the orders for the guest
    """
    if constants.GUEST_INITIALIZED not in callback_context.state: 
        callback_context.state[constants.ERROR_KEY] = (
            "All information about guest not gathered yet"
        )
        return

    callback_context.state[constants.PHASE_KEY] = "order placement"
    if constants.ORDER_KEY not in callback_context.state:
        callback_context.state[constants.ORDER_KEY] = OrderService(callback_context)
    callback_context.state[constants.ERROR_KEY] = None
    callback_context.state[constants.USER_QUERY_KEY] = parse_user_query(callback_context)
    if constants.INITIAL_USER_QUERY_KEY not in callback_context.state: 
        callback_context.state[constants.INITIAL_USER_QUERY_KEY] = parse_user_query(callback_context)

def seating_state_init(callback_context: CallbackContext):
    """
    Initializes the state of seating for new guest

    Args:
        callback_context: The callback context
    """
    if constants.GUEST_KEY not in callback_context.state: 
        callback_context.state[constants.ERROR_KEY] = (
            "Gather information about guest first"
        )
        return

    if constants.TABLE_KEY in callback_context.state:
        return 

    callback_context.state[constants.PHASE_KEY] = "seating"
    callback_context.state[constants.ERROR_KEY] = None
    callback_context.state[constants.TABLE_KEY] = TableStore()
