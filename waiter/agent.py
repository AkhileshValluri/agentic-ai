"""Demonstration of Travel AI Conceirge using Agent Development Kit"""

from google.adk.agents import LlmAgent

from waiter import prompt

from waiter.sub_agents.seating.agent import seating_agent
from waiter.sub_agents.recommendation.agent import recommendations_refinement_loop_agent
from waiter.sub_agents.ordering.agent import ordering_agent

from waiter.tools.memory import guest_model_init
from waiter.models.schema import Guest

root_agent = LlmAgent(
    model="gemini-2.0-flash",
    name="root_agent",
    description="A waiter in a restaurant, helping order dishes and seating guests.",
    instruction=prompt.ROOT_AGENT_INSTR,
    sub_agents=[
        seating_agent,
        recommendations_refinement_loop_agent,
        ordering_agent
    ],
    before_agent_callback=guest_model_init,
    tools=[Guest.new_guest, Guest.set_preferences, Guest.set_allergies]
)
