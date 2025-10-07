from dotenv import load_dotenv
load_dotenv()
from google.genai import types
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.adk.agents import LoopAgent, LlmAgent, SequentialAgent
from google.adk.agents.callback_context import CallbackContext
from google.adk.tools.tool_context import ToolContext
from google.adk.tools import BaseTool

# --- Constants ---
APP_NAME = "doc_writing_app_v3" # New App Name
USER_ID = "dev_user_01"
SESSION_ID_BASE = "loop_exit_tool_session" # New Base Session ID
GEMINI_MODEL = "gemini-2.0-flash"
STATE_INITIAL_TOPIC = "initial_topic"

# --- State Keys ---
STATE_CURRENT_DOC = "current_document"
STATE_CRITICISM = "criticism"
# Define the exact phrase the Critic should use to signal completion
COMPLETION_PHRASE = "No major issues found."

# --- Tool Definition ---
def exit_loop(tool_context: ToolContext):
  """Call this function ONLY when the critique indicates no further changes are needed, signaling the iterative process should end."""
  print(f"  [Tool Call] exit_loop triggered by {tool_context.agent_name}")
  tool_context.actions.escalate = True
  # Return empty dict as tools should typically return JSON-serializable output
  return {}

# --- Agent Definitions ---

# STEP 1: Initial Writer Agent (Runs ONCE at the beginning)
initial_writer_agent = LlmAgent(
    name="InitialWriterAgent",
    model=GEMINI_MODEL,
    include_contents='none',
    # MODIFIED Instruction: Ask for a slightly more developed start
    instruction=f"""You are a Creative Writing Assistant tasked with starting a story.
    Write the *first draft* of a short story (aim for 2-4 sentences).
    Base the content *only* on the query of the user.
    Output *only* the story/document text. Do not add introductions or explanations.
""",
    description="Writes the initial document draft based on the topic, aiming for some initial substance.",
    output_key=STATE_CURRENT_DOC
)

def log_callback(context: CallbackContext): 
    return "".join([
            f"criticism - {context.state.get("criticism")}\n",
            f"current_document - {context.state.get("current_document")}\n"
        ])

def before_agent_log(callback_context: CallbackContext):
    with open("log.txt", "a") as f: 
        f.write("\n=================================\n")
        f.write(f"::START {callback_context.agent_name} START::\n")
        f.write("BEFORE AGENT RESPONSE\n")
        f.write(log_callback(callback_context))
        f.write("---------------------------------\n")

def after_agent_log(callback_context: CallbackContext):
    with open("log.txt", "a") as f: 
        f.write("AFTER AGENT RESPONSE\n")
        f.write(log_callback(callback_context))
        f.write(f"::END {callback_context.agent_name} END::\n")
        f.write("=================================\n")

def tool_log_callback(tool: BaseTool, context: ToolContext):
    return f"{tool.name}::escalate - {context.actions.escalate}\n"

def before_tool_log(tool: BaseTool, args: dict[str, any], tool_context: ToolContext):
    with open("log.txt", "a") as f: 
        f.write("\n=================================\n")
        f.write(f"::START TOOL {tool.name} TOOL START::\n")
        f.write("BEFORE TOOL INVOCATION\n")
        f.write(tool_log_callback(tool, tool_context))
        f.write("---------------------------------\n")

def after_tool_log(tool: BaseTool, args: dict[str, any], tool_context: ToolContext, tool_response: dict[str, str]):
    with open("log.txt", "a") as f: 
        f.write("AFTER TOOL INVOCATION\n")
        f.write(tool_log_callback(tool, tool_context))
        f.write(f"::END TOOL {tool.name} TOOL END::\n")
        f.write("=================================\n")

# STEP 2a: Critic Agent (Inside the Refinement Loop)
critic_agent_in_loop = LlmAgent(
    name="CriticAgent",
    model=GEMINI_MODEL,
    include_contents='none',
    # MODIFIED Instruction: More nuanced completion criteria, look for clear improvement paths.
    instruction=f"""You are a Constructive Critic AI reviewing a short document draft (typically 2-6 sentences). Your goal is balanced feedback.

    **Document to Review:**
    ```
    {{current_document}}
    ```

    **Task:**
    Review the document for clarity, engagement, and basic coherence according to the initial topic (if known).

    IF you identify 1-2 *clear and actionable* ways the document could be improved to better capture the topic or enhance reader engagement (e.g., "Needs a stronger opening sentence", "Clarify the character's goal"):
    Provide these specific suggestions concisely. Output *only* the critique text.

    ELSE IF the document is coherent, addresses the topic adequately for its length, and has no glaring errors or obvious omissions:
    Respond *exactly* with the phrase "{COMPLETION_PHRASE}" and nothing else. It doesn't need to be perfect, just functionally complete for this stage. Avoid suggesting purely subjective stylistic preferences if the core is sound.

    Do not add explanations. Output only the critique OR the exact completion phrase.
""",
    description="Reviews the current draft, providing critique if clear improvements are needed, otherwise signals completion.",
    output_key=STATE_CRITICISM,
    before_agent_callback=before_agent_log,
    after_agent_callback=after_agent_log,
)


# STEP 2b: Refiner/Exiter Agent (Inside the Refinement Loop)
refiner_agent_in_loop = LlmAgent(
    name="RefinerAgent",
    model=GEMINI_MODEL,
    # Relies solely on state via placeholders
    include_contents='none',
    instruction=f"""You are a Creative Writing Assistant refining a document based on feedback OR exiting the process.
    **Current Document:**
    ```
    {{current_document}}
    ```
    **Critique/Suggestions:**
    {{criticism}}

    **Task:**
    Analyze the 'Critique/Suggestions'.
    IF the critique is *exactly* "{COMPLETION_PHRASE}":
    You MUST call the 'exit_loop' function. Do not output any text.
    ELSE (the critique contains actionable feedback):
    Carefully apply the suggestions to improve the 'Current Document'. Output *only* the refined document text.

    Do not add explanations. Either output the refined document OR call the exit_loop function.
""",
    description="Refines the document based on critique, or calls exit_loop if critique indicates completion.",
    tools=[exit_loop], # Provide the exit_loop tool
    output_key=STATE_CURRENT_DOC, # Overwrites state['current_document'] with the refined version
    before_agent_callback=before_agent_log,
    after_agent_callback=after_agent_log,
    before_tool_callback=before_tool_log,
    after_tool_callback=after_tool_log
)


# STEP 2: Refinement Loop Agent
refinement_loop = LoopAgent(
    name="RefinementLoop",
    # Agent order is crucial: Critique first, then Refine/Exit
    sub_agents=[
        critic_agent_in_loop,
        refiner_agent_in_loop,
    ],
    max_iterations=5, # Limit loops
)

# STEP 3: Overall Sequential Pipeline
# For ADK tools compatibility, the root agent must be named `root_agent`
root_agent = SequentialAgent(
    name="IterativeWritingPipeline",
    sub_agents=[
        initial_writer_agent, # Run first to create initial doc
        refinement_loop       # Then run the critique/refine loop
    ],
    description="Writes an initial document and then iteratively refines it with critique using an exit tool."
)
async def call_agent(query): 
    APP_NAME = "weather_app"
    USER_ID = "1234"
    SESSION_ID = "session1234"


    # Session and Runner
    session_service = InMemorySessionService()
    await session_service.create_session(app_name=APP_NAME, user_id=USER_ID, session_id=SESSION_ID)
    runner = Runner(agent=root_agent, app_name=APP_NAME, session_service=session_service)

    content = types.Content(role='user', parts=[types.Part(text=query)])
    async for event in runner.run_async(user_id=USER_ID, session_id=SESSION_ID, new_message=content):
        pass

import asyncio
asyncio.run(call_agent("Write a professional letter to my boss explaining that I'm not enjoying my work here"))