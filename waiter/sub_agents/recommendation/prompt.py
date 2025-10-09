"""Prompt for the booking agent and sub-agents."""
import json 

from google.adk.agents.readonly_context import ReadonlyContext
from waiter.shared_libraries import constants 
from waiter.models.schema import Dish, DishStore

base_recommendation_prompt = f"""
- You are a waiter at a restaurant taking an order and handling all modifications and queries regarding the dishes 
- If a dish doesn't fit the users preference and allergies, attempt to modify one or more ingredients so the dish fits the users liking
- Return the filtered dishes with the modifications to them (if any)
- The following is the users query
<query>
{{{constants.USER_QUERY_KEY}}}
</query>
"""

user_preferences = """
- The following are the users preferneces
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

def recommendation_agent_instr(readonly_context: ReadonlyContext) -> str:
    base_prompt = base_recommendation_prompt
    base_prompt += user_preferences.format(
        preferences = readonly_context.state[constants.GUEST_KEY].preferences
    )

    # Determine whether this is the first or a refinement iteration
    if readonly_context.state.get(constants.INITIAL_RECOMMENDATION_KEY, None) is None:
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
    - Your job is to **analyze and critique** the recommended dishes based on the user's stated preferences and ALLERGIES and taste.
    - You have access to the specials and can suggest minor modifications if the restaurant allows them, use appropriate tools to check
    - Be objective and concise, your goal is to identify what works and what doesn't, not to recommend new dishes yourself.
    - If modifications are listed in the recommendations, perform the tool call to verify that they are possible.
    - If there are no changes to be done, after considering the allergies call the appropriate tool to exit the loop
    """

    # Get relevant state info
    user_query = readonly_context.state.get(constants.USER_QUERY_KEY, "")
    previous_recommendations = readonly_context.state.get(constants.INITIAL_RECOMMENDATION_KEY, "")
    specials = DishStore().specials()

    # Build context
    if previous_recommendations:
        base_critique_prompt += f"\n- These are the previous dish recommendations and modifications you must critique:\n{previous_recommendations}\n"
    if specials:
        base_critique_prompt += f"\n- Current specials on the menu:\n{specials}\n"

    base_critique_prompt += f"\n- The user originally asked:\n{user_query}\n"

    return base_critique_prompt
