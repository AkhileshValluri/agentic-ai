"""Inspiration agent. A pre-booking agent covering the ideation part of the trip."""

from google.adk.agents import LlmAgent
from waiter.sub_agents.ordering import prompt
from waiter.models.services import OrderService
from waiter.tools.memory import order_model_init
from waiter.sub_agents.recommendation.agent import instantiate_refinement_loop_agent

ordering_agent = LlmAgent(
    model="gemini-2.0-flash",
    name="ordering_agent",
    description="Agent which takes a customers order and places the order",
    instruction=prompt.order_agent_instr,
    tools=[OrderService.get_dishes, OrderService.update_dishes, OrderService.place_order],
    sub_agents=[instantiate_refinement_loop_agent()],
    before_agent_callback=order_model_init
)
