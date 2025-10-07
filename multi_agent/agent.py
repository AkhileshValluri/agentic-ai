from dotenv import load_dotenv
load_dotenv()
import datetime
from google.genai import types
from google.adk.agents.llm_agent import LlmAgent
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.adk.artifacts.in_memory_artifact_service import InMemoryArtifactService # Optional
from google.adk.planners import BasePlanner, BuiltInPlanner, PlanReActPlanner
from google.adk.models import LlmRequest
from google.adk.tools import FunctionTool

from google.genai.types import ThinkingConfig
from google.genai.types import GenerateContentConfig

# Tools
def mock_get_weather(city: str): 
    """
    params: 
        city: str - name of the city
    returns: 
        str: information about the weather
    Gets the weather for a city
    """
    if city.lower().startswith("a"): 
        return "Nice weather"
    else: 
        return "bad weather"
    
def mock_get_time(): 
    """
    returns: 
        str: information about time
    """
    return str(datetime.datetime.now())

get_weather = FunctionTool(func=mock_get_weather)
get_time = FunctionTool(func=mock_get_time)

# Sub-agents
weather_agent = LlmAgent(
    name="weather_agent",
    model="gemini-2.0-flash",
    instruction="Answer weather-related questions using the get_weather tool.",
    description="Gets the weather for any city",
    tools=[get_weather]
)

poetry_agent = LlmAgent(
    name="poetry_agent",
    model="gemini-2.0-flash",
    instruction="Generate poems or critique poetry.",
    description="Generate poems or critique poetry.",
    tools=[]
)

# Main agent (delegator)
root_agent = LlmAgent(
    name="main_agent",
    model="gemini-2.0-flash",
    instruction="You are a helpful assistant who delegates tasks to sub-agents.",
    sub_agents=[weather_agent, poetry_agent],
    tools=[get_time]
)
async def call_agent(query):
    APP_NAME = "weather_app"
    USER_ID = "1234"
    SESSION_ID = "session1234"

    session_service = InMemorySessionService()
    await session_service.create_session(app_name=APP_NAME, user_id=USER_ID, session_id=SESSION_ID)
    runner = Runner(agent=root_agent, app_name=APP_NAME, session_service=session_service)

    content = types.Content(role='user', parts=[types.Part(text=query)])
    async for event in runner.run_async(user_id=USER_ID, session_id=SESSION_ID, new_message=content):
        if event.is_final_response():
            print(f"FINAL OUTPUT:: {"".join([part.text for part in event.content.parts])}")

import asyncio
asyncio.run(call_agent("Hello I'm living in Amsterdam what is the weather. Also what is the time"))