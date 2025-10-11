"""The 'memorize' tool for several agents to affect session states."""

from datetime import datetime
import json
import os
from typing import Dict, Any

from google.adk.agents.callback_context import CallbackContext
from google.adk.sessions.state import State
from google.adk.tools import ToolContext

from waiter.models.schema import *
from waiter.shared_libraries import constants

SAMPLE_SCENARIO_PATH = "waiter/profiles/new_table_state.json"


def memorize_list(key: str, value: str, tool_context: ToolContext):
    """
    Memorize pieces of information.

    Args:
        key: the label indexing the memory to store the value.
        value: the information to be stored.
        tool_context: The ADK tool context.

    Returns:
        A status message.
    """
    mem_dict = tool_context.state
    if key not in mem_dict:
        mem_dict[key] = []
    if value not in mem_dict[key]:
        mem_dict[key].append(value)
    return {"status": f'Stored "{key}": "{value}"'}


def memorize(key: str, value: str, tool_context: ToolContext):
    """
    Memorize pieces of information, one key-value pair at a time.

    Args:
        key: the label indexing the memory to store the value.
        value: the information to be stored.
        tool_context: The ADK tool context.

    Returns:
        A status message.
    """
    mem_dict = tool_context.state
    mem_dict[key] = value
    return {"status": f'Stored "{key}": "{value}"'}


def forget(key: str, value: str, tool_context: ToolContext):
    """
    Forget pieces of information.

    Args:
        key: the label indexing the memory to store the value.
        value: the information to be removed.
        tool_context: The ADK tool context.

    Returns:
        A status message.
    """
    if tool_context.state[key] is None:
        tool_context.state[key] = []
    if value in tool_context.state[key]:
        tool_context.state[key].remove(value)
    return {"status": f'Removed "{key}": "{value}"'}

def parse_user_query(callback_context: CallbackContext) -> str:
    user_query = "".join([part.text for part in callback_context.user_content.parts])
    return user_query 

def guest_model_init(callback_context: CallbackContext):
    """
    Initializes the state for a new guest

    Args:
        callback_context: The callback context.
    """
    if constants.GUEST_INITIALIZED in callback_context.state:
        return
    callback_context.state[constants.ERROR_KEY] = None
    callback_context.state[constants.GUEST_KEY] = Guest()
    callback_context.state[constants.SPECIALS_KEY] = DishStore().specials()

def recommendation_model_init(callback_context: CallbackContext):
    """
    Initializes the state of recommendation for new guest

    Args:
        callbcak_context: The callback context
    """
    # add all conditions to be able to initialize recommendations object
    if constants.GUEST_INITIALIZED not in callback_context.state:
        callback_context.state[constants.ERROR_KEY] = (
            "All information about guest not gathered yet"
        )
        return

    if constants.INITIAL_CRITIQUE_KEY not in callback_context.state: 
        callback_context.state[constants.INITIAL_CRITIQUE_KEY] = None

    if constants.INITIAL_RECOMMENDATION_KEY not in callback_context.state: 
        callback_context.state[constants.RECOMMENDATION_KEY] = Recommendation(
            guest_id=callback_context.state[constants.GUEST_KEY].id
        )
    
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
    
    if constants.ORDER_KEY not in callback_context.state:
        callback_context.state[constants.ORDER_KEY] = Order(
            guest_id = callback_context.state[constants.GUEST_KEY].id
        )
        print("Set order key ")

    callback_context.state[constants.USER_QUERY_KEY] = parse_user_query(callback_context)
    if constants.INITIAL_USER_QUERY_KEY not in callback_context.state: 
        callback_context.state[constants.INITIAL_USER_QUERY_KEY] = parse_user_query(callback_context)

def seating_state_init(callback_context: CallbackContext):
    """
    Initializes the state of seating for new guest

    Args:
        callback_context: The callback context
    """
    if constants.SEATING_INITIALIZED in callback_context.state:
        return f'Error: Table already allotted, cannot be done again'

    callback_context.state[constants.ERROR_KEY] = None
    callback_context.state[constants.TABLE_KEY] = ""
    callback_context.state[constants.TABLES] = TableStore().get_tables()
