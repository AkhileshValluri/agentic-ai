import dotenv
dotenv.load_dotenv("waiter/.env")

from google.adk.sessions import InMemorySessionService
from google.adk.runners import Runner
from google.genai import types
from waiter.agent import root_agent

import asyncio

# running session
APP_NAME = "waiter"
USER_ID = "akhilesh"
SESSION_ID = "session_akhilesh"

session_service = InMemorySessionService()
runner = Runner(agent=root_agent, app_name=APP_NAME, session_service=session_service)

async def call_agent(query: str):
    content = types.Content(role='user', parts=[types.Part(text=query)])
    async for event in runner.run_async(user_id=USER_ID, session_id=SESSION_ID, new_message=content):
        if event.is_final_response() and event.content is not None:
            try:
                print(f"\nAgent: {"".join([part.text for part in event.content.parts])}")
            except:
                continue

async def main():
    await session_service.create_session(app_name=APP_NAME, user_id=USER_ID, session_id=SESSION_ID)
    print("Welcome to XYZ hotel Agent! Type 'exit' to quit.\n")
    while True:
        query = input("You: ")
        if query.lower() in {"exit", "quit"}:
            print("Goodbye!")
            break
        await call_agent(query)

# Run the main loop
asyncio.run(main())
