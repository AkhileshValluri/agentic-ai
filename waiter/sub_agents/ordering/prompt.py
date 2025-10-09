from google.adk.agents.readonly_context import ReadonlyContext
from waiter.shared_libraries import constants
from waiter.models.schema import Order

base_order_prompt = """
- You are a waiter that is supposed to make the order list after speaking with the customer
- The following is the current order list with the modifications that need to be done with each dish
<order_list>
{order_list}
</order_list>
- Once the user query mentions that the user is satisfied with the order, call the appropriate tool to actually place the order
"""
def order_agent_instr(readonly_context: ReadonlyContext) -> str:
    order_state: Order = readonly_context.state[constants.ORDER_KEY]
    base_order_prompt.format(order_list = order_state.dishes)
    return base_order_prompt