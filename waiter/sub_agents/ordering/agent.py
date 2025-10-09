"""Inspiration agent. A pre-booking agent covering the ideation part of the trip."""

from google.adk.agents import LlmAgent
from google.adk.tools.agent_tool import AgentTool
from waiter.shared_libraries.types import DestinationIdeas, POISuggestions, json_response_config
from waiter.sub_agents.inspiration import prompt
from waiter.tools.places import map_tool


place_agent = LlmAgent(
    model="gemini-2.5-flash",
    name="place_agent",
    instruction=prompt.PLACE_AGENT_INSTR,
    description="This agent suggests a few destination given some user preferences",
    disallow_transfer_to_parent=True,
    disallow_transfer_to_peers=True,
    output_schema=DestinationIdeas,
    output_key="place",
    generate_content_config=json_response_config,
)

poi_agent = LlmAgent(
    model="gemini-2.5-flash",
    name="poi_agent",
    description="This agent suggests a few activities and points of interests given a destination",
    instruction=prompt.POI_AGENT_INSTR,
    disallow_transfer_to_parent=True,
    disallow_transfer_to_peers=True,
    output_schema=POISuggestions,
    output_key="poi",
    generate_content_config=json_response_config,
)

preference_agent = LlmAgent(
    model="gemini-2.5-flash",
    name="inspiration_agent",
    description="Agent which speaks with the customer and figures out their preferences and allergies.",
    instruction=prompt.INSPIRATION_AGENT_INSTR,
    tools=[AgentTool(agent=place_agent), AgentTool(agent=poi_agent), map_tool],
)
