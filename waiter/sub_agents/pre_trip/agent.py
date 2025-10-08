"""Pre-trip agent. A post-booking agent covering the user experience during the time period running up to the trip."""

from google.adk.agents import Agent
from google.adk.tools.agent_tool import AgentTool
from travel_concierge.shared_libraries import types
from travel_concierge.sub_agents.pre_trip import prompt
from travel_concierge.tools.search import google_search_grounding


what_to_pack_agent = Agent(
    model="gemini-2.5-flash",
    name="what_to_pack_agent",
    description="Make suggestion on what to bring for the trip",
    instruction=prompt.WHATTOPACK_INSTR,
    disallow_transfer_to_parent=True,
    disallow_transfer_to_peers=True,
    output_key="what_to_pack",
    output_schema=types.PackingList,
)

pre_trip_agent = Agent(
    model="gemini-2.5-flash",
    name="pre_trip_agent",
    description="Given an itinerary, this agent keeps up to date and provides relevant travel information to the user before the trip.",
    instruction=prompt.PRETRIP_AGENT_INSTR,
    tools=[google_search_grounding, AgentTool(agent=what_to_pack_agent)],
)
