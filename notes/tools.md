- Tools are a capability outside of text gen that are provided to agents
- LLM chooses to invoke tools through the *tools* docstring and its information attribute
- Types of tools
    1. Function / Methods | `google.adk.tools.FunctionTool`
    2. Agents as tools - specialized agents as a tool to parent agent | `google.adk.tools.AgentTool`
    3. Long running function tools
# Tool context
- The context of the tool.
- This class provides the context for a tool invocation.
- Inherrits from `CallbackContext` which in turn inherits from `ReadonlyContext`because of which it has access to:
    1. `_invocation_context: InvocationContext` - this also has access to 
        - a. `session: Session`
        - b. `session_service: BaseSessionService`
        - c. All the auth and other information
    2. function call ID
    3. event actions
    5. `agent: BaseAgent`

- *Changes made to the state of the tool context will persist across queries within the session*
- It also provides methods for requesting credentials, retrieving authentication responses, listing artifacts, and searching memory.

## 1. FunctionTool 
- Before invoking the function, we check for if the list of args passed has all the mandatory arguments or not.
- If the check fails, then we don't invoke the tool and let the Agent know so the underlying model can fix the issue and retry.
- `ToolContext` can also be a valid param here
```python
class FunctionTool(BaseTool):
  def __init__(
      self,
      func: Callable[..., Any],
      *,
      require_confirmation: Union[bool, Callable[..., bool]] = False,
  ):
    """Initializes the FunctionTool. Extracts metadata from a callable object.

    Args:
      func: The function to wrap.
      require_confirmation: Wether this tool requires confirmation. A boolean or
        a callable that takes the function's arguments and returns a boolean. If
        the callable returns True, the tool will require confirmation from the
        user.
    """
```

- Example usage
```python
def get_weather(city: str) -> dict:
    """Retrieves the current weather report for a specified city.

    Args:
        city (str): The name of the city for which to retrieve the weather report.

    Returns:
        dict: status and result or error msg.
    """
    if city.lower() == "new york":
        return {
            "status": "success",
            "report": (
                "The weather in New York is sunny with a temperature of 25 degrees"
                " Celsius (77 degrees Fahrenheit)."
            ),
        }
    else:
        return {
            "status": "error",
            "error_message": f"Weather information for '{city}' is not available.",
        }

tool = FunctionTool(func = get_weather)
```
### Confirmation
- Invocaions of tools may require confirmation
- `require_confirmation: Union[bool | Callable]`
- If advanced confirmation is needed instead of boolean (entitlement instead of just authorization) 
```python
    self._event_actions.requested_tool_confirmations[self.function_call_id] = ...
```

2. BaseTool
```python
class BaseTool:
  def __init__(
      self,
      *,
      name,
      description,
      is_long_running: bool = False, # if tool is long op, it will return resource id first and resource later
      custom_metadata: Optional[dict[str, Any]] = None, # key-value pair for storing and retrieving tool-specific data
  ):
```
3. AgentTool
```python
class AgentTool(BaseTool):
  def __init__(self, agent: BaseAgent, skip_summarization: bool = False):
```
