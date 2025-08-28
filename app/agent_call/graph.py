from typing_extensions import TypedDict,List, Dict, Any, Annotated, Optional
from dataclasses import dataclass
from langgraph.graph import StateGraph, END
from langgraph.types import Command
from langgraph.runtime import Runtime
from app.agent_call.external import format_github_request
from langgraph.checkpoint.memory import MemorySaver
# import request
import os
from langchain_core.prompts import ChatPromptTemplate
from flask import jsonify,current_app
from langchain.chat_models import init_chat_model
import os
from pydantic import BaseModel,Field
from typing import Optional,List,Set




# ---- State Definition ----
def add(left, right):
    left.extend(right)
    return left


from datetime import datetime
def add_time(file):
    timestamp = datetime.now()
    file.update({'timestamp':timestamp})
    return file

class File(BaseModel):
    repo : str = Field(description='The Name of the repository ')
    filename : str = Field(description='The name of the file that changes is being made to')
    Patch : Optional[str] = Field(default=None,description='A list of the key points of the changes made as shown in the patch')

class Repository(BaseModel):
    repository:List[File]

@dataclass
class AgentState(TypedDict):
    formatted_commits:List[dict]
    extracted_commits:Annotated[List[dict],add]
    # requests: Annotated[list[RequestEntry], add]
    # selected_request: Optional[int] = None




prompt_template = ChatPromptTemplate([('system',
    "You will be given a text string containing the name of a repository , a filename on which the changes occurred, this changes could be"
    "addition of a file which is the filename or addition of some line of codes in the file, same for the removal and modification this is according"
    "to. Also we can also get the number of addition,deletion from the no of addition, deletion"
    "A commit message will be specified which describe what commit was made, a brief description about what the commit is about."
    "The patch - is the main information body we will be using :"
    "A patch is a text-based file that records the differences between two versions of code or documents. Instead of copying the entire new version, "
    "it shows what changed: which lines were added, which were removed, and where in the file the changes occurred. Each section of a patch, called a hunk,"
    " begins with a header (e.g., @@ -3,6 +3,7 @@) that indicates the line numbers in the old and new files. Lines starting with - represent deletions, lines "
    "with + represent additions, and unchanged lines provide context. This structure allows information to be passed efficiently: anyone with the old file can "
    "apply the patch and reconstruct the new version. Patches are widely used in version control systems like Git to share updates, review changes, or apply fixes"
    " across codebases without replacing entire files. In essence, a patch is a compact set of instructions that describe how one version of a file transforms into another."
    "Your job is to extract a list of key summary point of what happened in each patch given for each file. Make it detailed yet concise, that mean it should contain keywords"
    "that can be used to generate a report about the changes that occured in this file."
                        ),
    ('human','{text_string}')])



def receiver_node(state:AgentState):
    payload = state['commits']
    formatted = format_github_request(payload=payload)
    return {'formatted_commits':formatted}

def extraction_node(state:AgentState):
    os.environ["GOOGLE_API_KEY"] = current_app.config['GOOGLE_API_KEY']# 
    llm = init_chat_model("gemini-2.5-flash", model_provider="google_genai")
    commit_prompt = prompt_template.invoke({'text_string':state['formatted_commits']})
    structured_llm = llm.with_structured_output(schema=Repository)
    extracted_commit = structured_llm.invoke(commit_prompt)
    extracted_commit = [add_time(file) for file in extracted_commit.model_dump()['repository']]
    return {'extracted_commits':extracted_commits}

# ---- Graph Definition ----
builder = StateGraph(AgentState)
builder.add_node(receiver_node)
builder.add_node(extraction_node)
# builder.add_node("responder", responder)
builder.set_entry_point("receiver_node")
builder.add_edge("receiver_node", "extraction_node")
checkpointer = MemorySaver()
graph = builder.compile(checkpointer=checkpointer)
