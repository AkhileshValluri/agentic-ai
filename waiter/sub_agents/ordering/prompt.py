from google.adk.agents.readonly_context import ReadonlyContext
from waiter.models.services import OrderService
from waiter.shared_libraries import constants
from waiter.models.schema import Order

base_order_prompt = """
- You are a waiter that is supposed to make the order list after speaking with the customer
- The following is the current order list with the modifications that need to be done with each dish
<order_list>
{order_list}
</order_list>
- Once the user query mentions that the user is satisfied with the order, call the appropriate tool to actually place the order
- You cannot make new modifications, delegate to a new agent to make those modifications.
- For all the dishes that a user is decided on, add them to the order list by making tool calls.
- This is the user query
{user_query}
"""
def order_agent_instr(readonly_context: ReadonlyContext) -> str:
    order_service: OrderService = OrderService.get_curr_order_service(readonly_context)
    dishes = order_service.get_dishes(readonly_context)
    base_order_prompt.format(order_list = dishes, user_query = "{" + constants.USER_QUERY_KEY +"}")
    return base_order_prompt