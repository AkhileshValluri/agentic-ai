"""Demonstration of Travel AI Conceirge using Agent Development Kit"""

from google.adk.agents import Agent

from waiter import prompt

from waiter.sub_agents.booking.agent import booking_agent
from waiter.sub_agents.in_trip.agent import in_trip_agent
from waiter.sub_agents.inspiration.agent import inspiration_agent
from waiter.sub_agents.planning.agent import planning_agent
from waiter.sub_agents.post_trip.agent import post_trip_agent
from waiter.sub_agents.pre_trip.agent import pre_trip_agent

from waiter.tools.memory import _load_precreated_itinerary


root_agent = Agent(
    model="gemini-2.5-flash",
    name="root_agent",
    description="A Travel Conceirge using the services of multiple sub-agents",
    instruction=prompt.ROOT_AGENT_INSTR,
    sub_agents=[
        inspiration_agent,
        planning_agent,
        booking_agent,
        pre_trip_agent,
        in_trip_agent,
        post_trip_agent,
    ],
    before_agent_callback=_load_precreated_itinerary,
)
