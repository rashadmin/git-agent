from typing_extensions import TypedDict,List
from langgraph.graph import StateGraph, END
from langchain_core.prompts import ChatPromptTemplate
from flask import current_app
from langchain.chat_models import init_chat_model
import os
from pydantic import BaseModel,Field

class TwitterThread(BaseModel):
    tweets: List[str] = Field(description='You are to contain a list of threads which will be of type str, plain text only ')


class ComposeState(TypedDict):
    day:int
    commit_logs: list[str]
    previous_summary: str
    summary: str
    twitter_thread: list[str]
    facebook_post: str
    linkedin_post: str


summary_prompt = ChatPromptTemplate([("system",
                "You are an assistant that writes daily coding summaries."
                "Input: A list of commit logs containing commit messages and details of additions, deletions, or modifications."
                "Task: Summarize (under 280 characters) these commits in plain English as if you were a developer recounting what was done. for day {Day}" 
                "Focus on intent (bug fixes, feature additions, refactoring, experiments), not raw numbers." 
                "Do not use bullet points or lists. "
                "Yesterday's summary: {previous_summary}"
                "Return a single coherent paragraph summary.Commits:"
                " Write a human-like summary of today's progress, showing continuity from yesterday, however if there are no history from yesterday, then it's the beginning."
                "Tone: clear, narrative, natural, like a dev journaling their progress.Return plain text paragraphs."),
                ('human',"Today's commits: {commit_logs}")])

twitter_prompt = ChatPromptTemplate([("system",
                                      ("You are an assistant that writes Twitter threads." 
                                      " Input: A daily summary of coding work."
                                      "Task: Write a thread of tweets (each under 280 characters) that tell a story of what was done. "
                                      "Using an informative,conversational and approachable tone"
                                      "- Start with a strong hook in Tweet 1."
                                      "- Follow with short, engaging updates explaining progress."
                                      " - End with a closing reflection or teaser."
                                      "- No hashtags, no emojis, no links."
                                      "Return your output strictly as a valid JSON array of strings, where each string is one tweet."
                                      "Summary:")),('human',"Summary: {summary}")])


facebook_prompt = ChatPromptTemplate([("system",
                                       ("You are an assistant that writes casual Facebook status updates."
                                        "Input: A daily coding summary."
                                        "Task: Write a short post in a friendly, conversational tone. "
                                        "It should feel personal, like sharing your day with friends." 
                                        "Avoid lists, hashtags, or emojis. Just plain text paragraphs."
                                        "Summary:")),('human',"Summary: {summary}")])

linkedin_prompt = ChatPromptTemplate([("system",
                                        ("You are an assistant that writes professional LinkedIn updates." 
                                        "Input: A daily coding summary."
                                        "Task: Write a LinkedIn post describing what was achieved, highlighting the skills, tools, or lessons learned. "
                                        "Use a professional yet informative, conversational and approachable tone." 
                                        "Do not use hashtags, lists, or emojis. "
                                        "Write in clear paragraphs, as if sharing progress with your professional network."
                                        "Summary:")),('human',"Summary: {summary}")])


def summary_node(state:ComposeState):
    os.environ["GOOGLE_API_KEY"] = current_app.config['GOOGLE_API_KEY']# 
    llm = init_chat_model("gemini-2.5-flash-lite", model_provider="google_genai")
    summary_prompt_text = summary_prompt.invoke({'Day':state['day'],'previous_summary':state['previous_summary'],'commit_logs':state['commit_logs']})
    summary = llm.invoke(summary_prompt_text)
    return {'summary':summary}

def twitter_node(state:ComposeState):
    os.environ["GOOGLE_API_KEY"] = current_app.config['GOOGLE_API_KEY']# 
    llm = init_chat_model("gemini-2.5-flash-lite", model_provider="google_genai")
    structured_llm = llm.with_structured_output(schema=TwitterThread)
    twitter_prompt_text = twitter_prompt.invoke({'summary':state['summary']})
    twitter_thread = structured_llm.invoke(twitter_prompt_text)
    return {'twitter_thread':twitter_thread.model_dump()}


def facebook_node(state:ComposeState):
    os.environ["GOOGLE_API_KEY"] = current_app.config['GOOGLE_API_KEY']# 
    llm = init_chat_model("gemini-2.5-flash-lite", model_provider="google_genai")
    facebook_prompt_text=facebook_prompt.invoke({'summary':state['summary']})
    facebook_post = llm.invoke(facebook_prompt_text)
    return {'facebook_post':facebook_post}

def linkedin_node(state:ComposeState):
    os.environ["GOOGLE_API_KEY"] = current_app.config['GOOGLE_API_KEY']# 
    llm = init_chat_model("gemini-2.5-flash-lite", model_provider="google_genai")
    linkedin_prompt_text=linkedin_prompt.invoke({'summary':state['summary']})
    linkedin_post = llm.invoke(linkedin_prompt_text)
    return {'linkedin_post':linkedin_post}


builder = StateGraph(ComposeState)
builder.add_node("summarize", summary_node)
builder.add_node("twitter", twitter_node)
builder.add_node("facebook", facebook_node)
builder.add_node("linkedin", linkedin_node)

builder.set_entry_point('summarize')
builder.add_edge("summarize", "twitter")
builder.add_edge("summarize", "facebook")
builder.add_edge("summarize", "linkedin")
builder.add_edge("twitter", END)
builder.add_edge("facebook", END)
builder.add_edge("linkedin", END)

graph = builder.compile()

def run_compose(day:int,commit_logs: list[str], previous_summary: str = "") -> ComposeState:
    init_state: ComposeState = {
        "day":day,
        "commit_logs": commit_logs,
        "previous_summary": previous_summary,
        "summary": "",
        "twitter_thread": [],
        "facebook_post": "",
        "linkedin_post": "",
    }
    return graph.invoke(init_state)