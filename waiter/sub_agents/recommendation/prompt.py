"""Prompt for the booking agent and sub-agents."""
import json 

from google.adk.agents.readonly_context import ReadonlyContext
from waiter.shared_libraries import constants 
from waiter.models.schema import Dish
from waiter.models.services import *


def recommendation_agent_instr(readonly_context: ReadonlyContext) -> str:
    base_recommendation_prompt = f"""
    - You are a waiter at a restaurant taking an order and handling all modifications and queries regarding the dishes 
    - If a dish doesn't fit the users preference and allergies, call tool to try and modify ingredients to fit the users liking
    - Respond with all the dishes which satisfy the users preference, for most of the other dishes try making modifications to ingredients to satisfy preference
    - The following is the users query
    <query>
    {{{constants.USER_QUERY_KEY}}}
    </query>
    """

    user_preferences = """
    - The following are the users preferences
    <preferences> 
    {preferences}
    </preferences>
    """

    dish_information = """
    - These are all the dishes being served now
    {dish_info}
    """

    previous_recommendations = """
    - These are the previous suggestions you made: 
    {}
    """

    critique = """
    - These are the problems with the previous dishes you recommended (if any, take them into consideration and correct them)
    <problems>
    {issues}
    </problems> 
    """

    base_prompt = base_recommendation_prompt
    guest = GuestStore().get_curr_guest(readonly_context.state)
    base_prompt += user_preferences.format(
        preferences = guest.preferences,
        allergies = guest.allergies
    )

    # Determine whether this is the first or a refinement iteration
    if readonly_context.state[constants.INITIAL_RECOMMENDATION_KEY] == "":
        # First iteration → show all dishes
        dish_store = DishStore()
        dish_dto: dict[str, list[str]] = {
            dish.name: dish.ingredients for dish in dish_store._dishes
        }
        base_prompt += dish_information.format(
            dish_info=json.dumps(dish_dto, indent=2)
        )
    else:
        # Refinement iteration → only show filtered dishes
        base_prompt += previous_recommendations.format(f"{{{constants.INITIAL_RECOMMENDATION_KEY}}}")
        base_prompt += critique.format(issues=f"{{{constants.INITIAL_CRITIQUE_KEY}}}")

    return base_prompt


def critique_agent_instr(readonly_context: ReadonlyContext) -> str:
    base_critique_prompt = """
    - You are a culinary critic reviewing another waiter's dish recommendations and modifications to dishes.
    - Your job is to **analyze and critique** the recommended dishes based on the user's stated ALLERGIES and check if the modifications are possible and accepted.
    - Be objective and concise, your goal is to identify what works and what doesn't, not to recommend new dishes yourself.
    - For ALL modifications are listed in the recommendations, perform the tool call to verify that they are possible.
    - For ALL the recommendations which comply with allergies, if THE MODIFICATIONS ARE POSSIBLE: save the recommendations using a tool call
    """

    # Get relevant state info
    user_query = readonly_context.state.get(constants.USER_QUERY_KEY, "")
    previous_recommendations = readonly_context.state.get(constants.INITIAL_RECOMMENDATION_KEY, "")
    allergies = GuestStore().get_curr_guest(readonly_context.state).allergies

    # Build context
    if previous_recommendations:
        base_critique_prompt += f"\n- These are the previous dish recommendations and modifications you must critique:'{previous_recommendations}'"
    if len(allergies): 
        base_critique_prompt += f"\n- These are the allergies that the user has: {allergies}"

    base_critique_prompt += f"\n- The user originally asked:\n{user_query}\n"

    return base_critique_prompt
