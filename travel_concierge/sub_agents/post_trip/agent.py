"""Post-trip agent. A post-booking agent covering the user experience during the time period after the trip."""

from google.adk.agents import Agent

from travel_concierge.sub_agents.post_trip import prompt
from travel_concierge.tools.memory import memorize

post_trip_agent = Agent(
    model="gemini-2.5-flash",
    name="post_trip_agent",
    description="A follow up agent to learn from user's experience; In turn improves the user's future trips planning and in-trip experience.",
    instruction=prompt.POSTTRIP_INSTR,
    tools=[memorize],
)
