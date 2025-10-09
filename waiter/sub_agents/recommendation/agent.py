from google.adk.agents import Agent
from google.adk.tools.agent_tool import AgentTool
from google.adk.agents import LoopAgent
from google.genai.types import GenerateContentConfig
from google.adk.agents.callback_context import CallbackContext

from waiter.sub_agents.recommendation import prompt
from waiter.tools.memory import recommendation_model_init
from waiter.models.schema import *

def store_user_query(callback_context: CallbackContext):
    callback_context.state[constants.INITIAL_USER_QUERY_KEY] = "".join([part.text for part in callback_context.user_content.parts])

recommendation_agent = Agent(
    model="gemini-2.0-flash",
    name="recommendation_agent ",
    description="Handles the recommendation, possible modifications, checking of dishes as per user query.",
    instruction=prompt.recommendation_agent_instr,
    tools=[
        DishStore.specials,
        DishStore.get_dish,
        Recommendation.add_suggestion,
    ],
    output_key=constants.INITIAL_RECOMMENDATION_KEY,
    before_agent_callback=store_user_query
)

critique_agent = Agent(
    model="gemini-2.0-flash",
    name="critique_agent",
    description="Critiques the recommendation based off of the ingredients and the allergies and the preferences that the user has",
    instruction=prompt.recommendation_agent_instr,
    tools=[
        DishStore.request_modification,
    ],
    output_key=constants.INITIAL_CRITIQUE_KEY
)

recommendations_refinement_loop_agent = LoopAgent(
    name="recommendations_refinement_loop_agent",
    before_agent_callback=recommendation_model_init, # init recom object for guest
    sub_agents=[recommendation_agent, critique_agent],
    max_iterations=5
)