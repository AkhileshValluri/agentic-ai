from google.adk.agents import Agent
from waiter.sub_agents.seating import prompt
from waiter.tools.memory import seating_state_init
from waiter.models.schema import *


seating_agent = Agent(
    model="gemini-2.0-flash",
    name="seating_agent",
    description="Handles the table selection for incoming guests",
    instruction=prompt.seating_agent_instr,
    tools=[
        TableStore.allot_table,
        TableStore.get_tables
    ],
    before_agent_callback=seating_state_init
)
