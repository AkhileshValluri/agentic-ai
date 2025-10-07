# What are they
* Thinking part of the application 
* 2 types 
    1. Workflow Agents - Deterministic execution paths 
    2. Llm Agent - Non-Deterministic, uses LLM to interpret instructions and context

## Llm Agent 
* `from google.adk.agents import LlmAgent`
### 1. name (required) 
Unique string identifier 
### 2. description (optional) 
Used by other agents to understand what this agent is capable of doing 
### 3. model (required)

```python
# Example: Defining the basic identity
capital_agent = LlmAgent(
    model="gemini-2.0-flash",
    name="capital_agent",
    description="Answers user questions about the capital city of a given country."
    # instruction and tools will be added next
)
```

### 4. instruction 
1. *needs to be a function returning a string*. Mentions the core task / goal.
```
Examples: 
Its core task or goal.
Its personality or persona (e.g., "You are a helpful assistant," "You are a witty pirate").
Constraints on its behavior (e.g., "Only answer questions about X," "Never reveal Y").
```
2. State - instruction is a string template. Use `{var}` syntax to insert value of state variable named var. 
Use `{var?}` if the variable doesn't exist.

```python
instruction="""You are an agent that provides the capital city of a country.
When a user asks for the capital of a country:
1. Identify the country name from the user's query.
2. Use the `get_capital_city` tool to find the capital.
3. Respond clearly to the user, stating the capital city.
Example Query: "What's the capital of {country}?"
Example Response: "The capital of France is Paris."
"""
```

### 5. tool (optional)


### 6. generation config 
* `from google.genai.types import GenerateContentConfig, *`
1. Adjust LLM generated responses 
2. Control params like temp, max_output_tokens, etc
```python
agent = LlmAgent(
    # ... other params
    generate_content_config=GenerateContentConfig(
        temperature=0.2, # More deterministic output
        max_output_tokens=250,
        safety_settings=[
            SafetySetting(
                category=HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT,
                threshold=HarmBlockThreshold.BLOCK_LOW_AND_ABOVE,
            )
        ]
    )
)
```

### 7. structured data 
1. input_schema - json 
2. output_schema - json 
3. output_key - text content of agents resopnse is saved to sessions state dict under this key. For passing results 
between steps 

### 8. tool callbacks 
1. Attributes to execute before and after a tool of an agent is executed. 
    - `before_tool_callback`
    - `after_tool_callback`
2. The agents [ToolContext](./tools.md) is passed on to the function
3. The following is an example of how the callback is called in code
```python
callback(
            tool=tool, # BaseTool 
            args=function_args, # dict
            tool_context=tool_context, # ToolContext
            tool_response=function_response, # only passed onto after_tool_callbacks (dict)
        )
```

## Workflow Agent
* To orchestrate other agents to perform their jobs
### a. Sequential workflow agents
1. Iterates through sub-agents in order provided and calls the run_async method 
2. Wrapper for the `BaseAgent` class which already has the `sub_agents` attribute.
3. To store the output of the sequential agents you can use `output_key` and use them in the `instruction`
```python
code_pipeline_agent = SequentialAgent(
    name="CodePipelineAgent",
    sub_agents=[code_writer_agent, code_reviewer_agent, code_refactorer_agent],
    description="Executes a sequence of code writing, reviewing, and refactoring.",
    # The agents will run in the order provided: Writer -> Reviewer -> Refactorer
)
```

### b. Loop workflow agents
1. Executes the sub-agents in a loop (iteratively) until a termination condition is met
2. Iterates through the sub-agents and invokes the run_async method in order 
3. The `LoopAgent` itself doesn't decide when to stop the loop the following are the methods: 
    - a. Max iterations - Attribute 
    - b. Escalation from sub-agent. Following is the implementation in the ADK lib
    ```python
    if event.actions.escalate:
        should_exit = True

    if should_exit:
        return
    ```

```python
def exit_loop(tool_context: ToolContext):
  """Call this function ONLY when the critique indicates no further changes are needed, signaling the iterative process should end."""
  print(f"  [Tool Call] exit_loop triggered by {tool_context.agent_name}")
  tool_context.actions.escalate = True
  # Return empty dict as tools should typically return JSON-serializable output
  return {}

refiner_agent_in_loop = LlmAgent(
    name="RefinerAgent",
    # ... all other attributes
    tools=[exit_loop], # Provide the exit_loop tool
)
critic_agent_in_loop = LlmAgent(
    name="CriticAgent",
    # ... all other attributes
)

refinement_loop = LoopAgent(
    name="RefinementLoop",
    sub_agents=[
        critic_agent_in_loop,
        refiner_agent_in_loop,
    ],
    max_iterations=5 # Limit loops
)
```
### c. Parallel workflow agents
1. Executes sub-agents concurrently - to speed up workflows 
2. Independent branches: each sub-agent operates in its own execution branch. There is no automatic sharing of conversation history 
3. Result collection: the order of results may not be deterministic
4. If communication is needed:
    - a shared `InvocationContext` can be passed (will have to deal with race conditions)
    - eventual consistency
    - external state management (like db) using hooks 
```python
parallel_research_agent = ParallelAgent(
    name="ParallelWebResearchAgent",
    sub_agents=[researcher_agent_1, researcher_agent_2, researcher_agent_3],
    description="Runs multiple research agents in parallel to gather information."
)
```