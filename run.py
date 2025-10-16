import dotenv
dotenv.load_dotenv("waiter/.env")

from datetime import datetime
from google.adk.sessions import InMemorySessionService
from google.adk.runners import Runner
from google.adk.events import Event
from google.genai.types import Content, Part
from waiter.agent import root_agent

import asyncio

# running session
APP_NAME = "waiter"
USER_ID = "akhilesh"
SESSION_ID = "session_akhilesh"

session_service = InMemorySessionService()
runner = Runner(agent=root_agent, app_name=APP_NAME, session_service=session_service)


class C:
    HEADER = "\033[95m"
    BLUE = "\033[94m"
    CYAN = "\033[96m"
    GREEN = "\033[92m"
    YELLOW = "\033[93m"
    RED = "\033[91m"
    END = "\033[0m"
    BOLD = "\033[1m"
    DIM = "\033[2m"

def log_line(prefix: str, msg: str, color: str = C.END, indent: int = 0):
    pad = "    " * indent
    timestamp = datetime.now().strftime("%H:%M:%S")
    print(f"{pad}{color}{prefix:<12}{C.END} {C.DIM}[{timestamp}]{C.END} {msg}")

async def call_agent(query: str):
    content = Content(role="user", parts=[Part(text=query)])

    async for event in runner.run_async(
        user_id=USER_ID,
        session_id=SESSION_ID,
        new_message=content,
    ):
        agent_name = event.author or "agent"
        indent = 0

        # 🧠 Handle model output (final or partial)
        if event.is_final_response():
            if event.content and hasattr(event.content, "parts"):
                text_parts = [
                    getattr(p, "text", None)
                    for p in event.content.parts
                    if getattr(p, "text", None)
                ]
                if text_parts:
                    text = "".join(text_parts)
                    log_line(f"{agent_name} ✅", text, C.GREEN, indent)
                else:
                    log_line(
                        f"{agent_name} ⚙️",
                        "Final response contained no text parts (likely function call or escalation).",
                        C.DIM,
                        indent,
                    )
            else:
                log_line(
                    f"{agent_name} ⚙️",
                    "Final response had no content (likely loop exit or escalation).",
                    C.DIM,
                    indent,
                )

        # 🧩 Tool / function calls
        function_calls = event.get_function_calls()
        if function_calls:
            for fn in function_calls:
                log_line(
                    f"{agent_name} 🧩",
                    f"Function call → {fn.name}({fn.args})",
                    C.YELLOW,
                    indent,
                )

        # 🧰 Tool / function responses
        function_responses = event.get_function_responses()
        if function_responses:
            for fnr in function_responses:
                log_line(
                    f"{agent_name} 🔧",
                    f"Function response ← {fnr.name}: {fnr.response}",
                    C.BLUE,
                    indent,
                )

        # 🗂️ State or artifact updates
        if event.actions.state_delta:
            log_line(
                f"{agent_name} 🗂️",
                f"State delta: {event.actions.state_delta}",
                C.CYAN,
                indent,
            )
        if event.actions.artifact_delta:
            log_line(
                f"{agent_name} 📦",
                f"Artifact delta: {event.actions.artifact_delta}",
                C.CYAN,
                indent,
            )

        # 🔁 Escalation or transfer
        if event.actions.transfer_to_agent:
            log_line(
                f"{agent_name} 🔁",
                f"Transferred to agent: {event.actions.transfer_to_agent}",
                C.HEADER,
                indent,
            )
        if event.actions.escalate:
            log_line(
                f"{agent_name} ⤴️",
                "Escalated to higher-level agent (loop exit triggered).",
                C.HEADER,
                indent,
            )

        # ℹ️ Debug fallback for unhandled events
        if not (
            event.is_final_response()
            or function_calls
            or function_responses
            or event.actions.state_delta
            or event.actions.artifact_delta
            or event.actions.transfer_to_agent
            or event.actions.escalate
        ):
            log_line(
                f"{agent_name} ℹ️",
                f"Event (unhandled): {event.model_dump(exclude_none=True)}",
                C.DIM,
                indent,
            )


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
