from typing_extensions import TypedDict,List, Dict, Any, Annotated, Optional
from dataclasses import dataclass
from langgraph.graph import StateGraph, END
from langgraph.types import Command
from langgraph.runtime import Runtime
from app.agent_call.external import format_github_request
from langgraph.checkpoint.memory import MemorySaver
# import request
import os
from flask import jsonify,current_app


# ---- State Definition ----
def add(left, right):
    return left + right

# class RequestEntry(TypedDict):
#     id: str
#     data: Dict[str, Any]

# @dataclass
# class ContextSchema(TypedDict):
#     respond: bool = False


@dataclass
class AgentState(TypedDict):
    date: str
    commits:Annotated[List[dict],add]
    # requests: Annotated[list[RequestEntry], add]
    # selected_request: Optional[int] = None

def receiver_node(state:AgentState):
    payload = state['commits'][0]
    # date = state['date'] 
    formatted = format_github_request(payload=payload)
    print(formatted)
    return {}

# # ---- Node: Responder ----
# def responder(state: AgentState):
#     selected_request_id = state.get("selected_request", None)
#     if runtime.context.get("respond", False):
#         if selected_request_id is not None:
#             selected_request = state["requests"][selected_request_id]
#             response_stream_id = selected_request["data"]["reply_to"]
#             r.xadd(response_stream_id, {"response": "Yes"})
#             return {}
#     return {}

# ---- Graph Definition ----
builder = StateGraph(AgentState)
builder.add_node(receiver_node)
# builder.add_node("responder", responder)
builder.set_entry_point("receiver_node")
# builder.add_edge("responder", END)
checkpointer = MemorySaver()
graph = builder.compile(checkpointer=checkpointer)
