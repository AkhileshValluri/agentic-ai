"""Demonstration of Travel AI Conceirge using Agent Development Kit"""

from google.adk.agents import LlmAgent

from waiter import prompt

from waiter.models.schema import *
from waiter.sub_agents.booking.agent import booking_agent
from waiter.sub_agents.in_trip.agent import in_trip_agent
from waiter.sub_agents.inspiration.agent import preference_agent
from waiter.sub_agents.planning.agent import planning_agent
from waiter.sub_agents.post_trip.agent import post_trip_agent
from waiter.sub_agents.pre_trip.agent import pre_trip_agent

from waiter.tools.memory import root_agent_init


root_agent = LlmAgent(
    model="gemini-2.0-flash",
    name="root_agent",
    description="A waiter in a restaurant, helping order dishes and seating guests.",
    instruction=prompt.ROOT_AGENT_INSTR,
    # sub_agents=[
    #     preference_agent,
    #     planning_agent,
    #     booking_agent,
    #     pre_trip_agent,
    #     in_trip_agent,
    #     post_trip_agent,
    # ],
    before_agent_callback=root_agent_init,
    tools=[Guest.new_guest, Guest.set_preferences, Guest.set_allergies]
)
