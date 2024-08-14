from typing import TypedDict, Annotated
from langgraph.graph.message import add_messages
import pandas as pd
from langchain_core.messages import RemoveMessage

# Define the state object for the agent graph
class AgentGraphState(TypedDict):
    description: Annotated[list, add_messages]
    subject:Annotated[list, add_messages]
    dataset_name: Annotated[list, add_messages]
    Columns: Annotated[list, add_messages]
    themes: Annotated[list, add_messages]
    report_complete:Annotated[list, add_messages]
    message_history:Annotated[list, add_messages]
    figures: Annotated[list, add_messages]
    finished: str
    start_node: Annotated[list, add_messages]
    dataset_name: str
    dataset: Annotated[list, add_messages]
    research_question: Annotated[list, add_messages]
    dataset_response=Annotated[list, add_messages]
    planner_response: Annotated[list, add_messages]
    analysis_planner_response:Annotated[list, add_messages]
    todo_analysis:Annotated[list, add_messages]
    analysis_admin_response:Annotated[list, add_messages]
    selector_response: Annotated[list, add_messages]
    reporter_response: Annotated[list, add_messages]
    reviewer_response: Annotated[list, add_messages]
    router_response: Annotated[list, add_messages]
    code_reviewer_response:Annotated[list,add_messages]
    insights_response:Annotated[list, add_messages]
    final_reports: Annotated[list, add_messages]
    end_chain: Annotated[list, add_messages]
    past_analyses: Annotated[list, add_messages]
    past_themes:Annotated[list, add_messages]
    output:Annotated[list, add_messages]
    code_output:Annotated[list,add_messages]
    coder_response: Annotated[list, add_messages]
    def __init__(self):
        from langgraph.checkpoint.sqlite import SqliteSaver
        import sqlite3
        
        def from_conn_stringx(cls, conn_string: str,) -> "SqliteSaver":
            return SqliteSaver(conn=sqlite3.connect(conn_string, check_same_thread=False))
        SqliteSaver.from_conn_stringx=classmethod(from_conn_stringx)
        self.memory=SqliteSaver.from_conn_stringx=classmethod(from_conn_stringx)
# Define the nodes in the agent graph
def get_agent_graph_state(state:AgentGraphState, state_key:str):
    if state_key == "planner_all":
        return state["planner_response"]
    elif state_key == "planner_latest":
        if state["planner_response"]:
            return state["planner_response"][-1]
        else:
            return state["planner_response"]
    if state_key == "past_themes_all":
        return state["past_themes"]
    elif state_key == "past_themes_latest":
        if state["past_themes"]:
            return state["past_themes"][-1]
        else:
            return state["past_themes"]
        
    if state_key == "analysis_admin_all":
        return state["analysis_admin_response"]
    elif state_key == "analysis_admin_latest":
        if state["analysis_admin_response"]:
            return state["analysis_admin_response"][-1]
        else:
            return state["analysis_admin_response"]
    if state_key == "todo_analysis_all":
        return state["todo_analysis"]
    elif state_key == "todo_analysis_latest":
        if state["todo_analysis"]:
            return state["todo_analysis"][-1]
        else:
            return state["todo_analysis"]
    if state_key == "analysis_planner_all":
        return state["analysis_planner_response"]
    elif state_key == "analysis_planner_latest":
        if state["analysis_planner_response"]:
            return state["analysis_planner_response"][-1]
        else:
            return state["analysis_planner_response"]
    
    if state_key == "dataset_all":
        return state["dataset_response"]
    elif state_key == "dataset_latest":
        if state["dataset_response"]:
            return state["dataset_response"][-1]
        else:
            return state["dataset_response"]
        
    if state_key == "coder_all":
        return state["coder_response"]
    elif state_key == "coder_latest":
        if state["coder_response"]:
            return state["coder_response"][-1]
        else:
            return state["coder_response"]
    if state_key == "code_reviewer_all":
        return state["code_reviewer_response"]
    elif state_key == "code_reviewer_latest":
        if state["code_reviewer_response"]:
            return state["code_reviewer_response"][-1]
        else:
            return state["code_reviewer_response"]


    elif state_key == "selector_all":
        return state["selector_response"]
    elif state_key == "selector_latest":
        if state["selector_response"]:
            return state["selector_response"][-1]
        else:
            return state["selector_response"]
    
    elif state_key == "reporter_all":
        return state["reporter_response"]
    elif state_key == "reporter_latest":
        if state["reporter_response"]:
            return state["reporter_response"][-1]
        else:
            return state["reporter_response"]
    
    elif state_key == "reviewer_all":
        return state["reviewer_response"]
    elif state_key == "reviewer_latest":
        if state["reviewer_response"]:
            return state["reviewer_response"][-1]
        else:
            return state["reviewer_response"]
    elif state_key=="dataset_name":
        if state["dataset_name"]:
            return state["dataset_name"]
    elif state_key == "serper_all":
        return state["serper_response"]
    elif state_key == "serper_latest":
        if state["serper_response"]:
            return state["serper_response"][-1]
        else:
            return state["serper_response"]
    
    elif state_key == "scraper_all":
        return state["scraper_response"]
    elif state_key == "scraper_latest":
        if state["scraper_response"]:
            return state["scraper_response"][-1]
        else:
            return state["scraper_response"]
    elif state_key == "Columns":
        return state["Columns"]
    elif state_key == "description":
        return state["description"]
    elif state_key=="research_question":
        return state["research_question"]
    elif state_key == "subject":
        return state["subject"]
    elif state_key == "past_analyses":
        return state["past_analyses"]
    else:
        return None
state = {
    "dataset_name": "test_data.csv",
    "description": "",
    "subject": "",
    "Columns": [],
    "start_node": "",
    "report_complete": [],
    "research_question":"",
    "planner_response": [],
    "output": [],
    "selector_response": [],
    "dataset_response": [],
    "reporter_response": [],
    "dataset_name":"",
    "reviewer_response": [],
    "analysis_planner_response": [],
    "analysis_admin_response": [],
    "finished": "",
    "todo_analysis": [],
    "message_history": "",
    "router_response": [],
    "serper_response": [],
    "coder_output":[],
    "scraper_response": [],
    "insights_response": [],
    "code_reviewer_response": [],
    "final_reports": [],
    "coder_response": [],
    "past_analyses": [],
    "themes": [],
    "past_themes": [],
    "end_chain": []
}