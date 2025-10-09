from google.adk.agents import Agent
from google.adk.tools.agent_tool import AgentTool
from google.adk.tools import ToolContext
from google.adk.agents import LoopAgent
from google.genai.types import GenerateContentConfig

from waiter.sub_agents.recommendation import prompt
from waiter.tools.memory import recommendation_model_init
from waiter.models.schema import *

def exit_if_perfect(tool_context: ToolContext):
    """
    Exits if the recommendations don't contain any issues with allergies and all modifications have been approved
    """
    tool_context.actions.escalate = True
    tool_context.actions.skip_summarization = True

recommendation_agent = Agent(
    model="gemini-2.0-flash",
    name="recommendation_agent",
    description="Handles the recommendation, possible modifications, checking of dishes as per user query.",
    instruction=prompt.recommendation_agent_instr,
    tools=[
        DishStore.specials,
        DishStore.get_dish,
    ],
    output_key=constants.INITIAL_RECOMMENDATION_KEY
)

critique_agent = Agent(
    model="gemini-2.0-flash",
    name="critique_agent",
    description="Critiques the recommendation based off of the ingredients and the allergies and the preferences that the user has",
    instruction=prompt.critique_agent_instr,
    tools=[
        DishStore.request_modification,
        Recommendation.save_recommendation,
        exit_if_perfect,
    ],
    output_key=constants.INITIAL_CRITIQUE_KEY
)

recommendations_refinement_loop_agent = LoopAgent(
    name="recommendations_refinement_loop_agent",
    description="Handles all the recommendations, modifications of the dishes as per customers requirement",
    before_agent_callback=recommendation_model_init, # init recom object for guest
    sub_agents=[recommendation_agent, critique_agent],
    max_iterations=5
)