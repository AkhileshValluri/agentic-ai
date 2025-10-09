"""Inspiration agent. A pre-booking agent covering the ideation part of the trip."""

from google.adk.agents import LlmAgent
from waiter.sub_agents.ordering import prompt
from waiter.tools.places import map_tool
from waiter.models.schema import Order, DishStore
from waiter.tools.memory import order_model_init

ordering_agent = LlmAgent(
    model="gemini-2.0-flash",
    name="inspiration_agent",
    description="Agent which takes a customers order and places the order",
    instruction=prompt.order_agent_instr,
    tools=[Order.get_dishes, Order.update_dishes, Order.place_order],
    before_agent_callback=order_model_init
)
