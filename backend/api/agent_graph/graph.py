import json
from langgraph.graph import StateGraph

from states.state import AgentGraphState, get_agent_graph_state, state
import pandas as pd

from utils.helper_functions import check_for_content
from agents.agents import (
    ExecutiveReportAgent,
    ReviewerAgent,
    FirstRouterAgent,
    PastInformationAgent,
    RouterAgent,
    DatasetAgent,
    AnalysisAdminAgent,
    AnalysisPlannerAgent,
    CoderAgent,
    CodeReviewAgent,
    InsightAgent,
    FinalReportAgent,
    EndNodeAgent
)
from prompts.prompts import (
    reviewer_prompt_template, 
    code_reviewer_prompt_template,
    coder_prompt_template,
    analysis_admin_prompt_template,
    insight_prompt_template,
    past_information_prompt_template,
    general_router_prompt,
    analysis_planner_prompt_template,
    executive_prompt_template,
    router_prompt_template,
    reviewer_guided_json,
    general_router_guided_json,
    coder_guided_json,
    analysis_planner_guided_json,
    code_reviewer_guided_json,
    dataset_guided_json,
    code_router_guided_json,
    coder_router_prompt_template,
    router_guided_json,
    analysis_admin_guided_json

)

def create_graph(server=None, model=None, dataset_name=None, stop=None, model_endpoint=None, temperature=0.3, research_question=None, dataset=None, message_history=None):
    
    graph = StateGraph(AgentGraphState)

    graph.add_node(
        "start",
        lambda state: FirstRouterAgent(
                state=state,
                model=model,
                server=server,
                guided_json=analysis_admin_guided_json,
                stop=stop,
                model_endpoint=model_endpoint,
                temperature=temperature
            ).invoke(
                prompt=general_router_prompt,
                research_question=state["research_question"],
                message_history=state["message_history"]
            )
    )

    graph.add_node(
        "past_info_agent",
        lambda state: PastInformationAgent(
                state=state,
                model=model,
                server=server,
                guided_json=past_information_prompt_template,
                stop=stop,
                model_endpoint=model_endpoint,
                temperature=temperature
            ).invoke(
                prompt=past_information_prompt_template,
                research_question=state["research_question"],
                message_history=state["message_history"]
            )
    )
    graph.add_node(
        "analysis_admin", 
        lambda state: AnalysisAdminAgent(
            state=state,
            model=model,
            server=server,
            guided_json=analysis_admin_guided_json,
            stop=stop,
            model_endpoint=model_endpoint,
            temperature=temperature
        ).invoke(
            description=get_agent_graph_state(state=state, state_key="description"),
            subject=get_agent_graph_state(state=state, state_key="subject"),
            research_question=state["research_question"],
            columns=get_agent_graph_state(state=state, state_key="Columns"),
            feedback=lambda: get_agent_graph_state(state=state, state_key="reviewer_latest"),
            prompt=analysis_admin_prompt_template,
        )
    )
    graph.add_node(
        "analysis_planner", 
        lambda state: AnalysisPlannerAgent(
            state=state,
            model=model,
            server=server,
            guided_json=analysis_planner_guided_json,
            stop=stop,
            model_endpoint=model_endpoint,
            temperature=temperature
        ).invoke(
            description=get_agent_graph_state(state=state, state_key="description"),
            subject=get_agent_graph_state(state=state, state_key="subject"),
            past_analyses=get_agent_graph_state(state=state, state_key="past_analyses"),
            research_question=state["research_question"],
            columns=get_agent_graph_state(state=state, state_key="Columns"),
            past_themes=get_agent_graph_state(state=state, state_key="past_themes_all"),
            feedback=lambda: get_agent_graph_state(state=state, state_key="reviewer_latest"),
            prompt=analysis_planner_prompt_template,
            analysis_area=get_agent_graph_state(state=state, state_key="todo_analysis_latest")
        )
    )



    graph.add_node(
        "reviewer", 
        lambda state: ReviewerAgent(
            state=state,
            model=model,
            server=server,
            guided_json=reviewer_guided_json,
            stop=stop,
            dataset=dataset,
            model_endpoint=model_endpoint,
            temperature=temperature
        ).invoke(
            description=get_agent_graph_state(state=state, state_key="description"),
            subject=get_agent_graph_state(state=state, state_key="subject"),           
            themes=get_agent_graph_state(state=state, state_key="todo_analysis_latest"),
            feedback=lambda: get_agent_graph_state(state=state, state_key="reviewer_all"),
           
            analysis_agent=lambda: get_agent_graph_state(state=state, state_key="analysis_planner_latest"),
           
            prompt=reviewer_prompt_template
        )
    )

    graph.add_node(
        "router", 
        lambda state: RouterAgent(
            state=state,
            model=model,
            server=server,
            guided_json=router_guided_json,
            stop=stop,
            model_endpoint=model_endpoint,
            temperature=temperature
        ).invoke(

            research_question=state["research_question"],
            feedback=lambda: get_agent_graph_state(state=state, state_key="reviewer_latest"),
            prompt=router_prompt_template
        )
    )
    graph.add_node(
        "coder_agent",
        lambda state: CoderAgent(
            state=state,
            model=model,
            server=server,
            stop=stop,
            model_endpoint=model_endpoint,
            temperature=temperature,
        ).invoke(
            analysis=get_agent_graph_state(state=state, state_key="analysis_planner_latest"),
            columns=get_agent_graph_state(state=state, state_key="Columns"),
            feedback=lambda: get_agent_graph_state(state=state, state_key="code_reviewer_latest"),
            prompt=coder_prompt_template,
            dataset_name=state["dataset_name"],
            dataset=dataset
        )
    )
    graph.add_node(
        "code_reviewer",
        lambda state: CodeReviewAgent(
            state=state,
            model=model,
            server=server,
            stop=stop,
            model_endpoint=model_endpoint,
            temperature=temperature,
            dataset=dataset,
            guided_json=code_reviewer_guided_json
        ).invoke(
            analysis=get_agent_graph_state(state=state, state_key="analysis_planner_latest"),
            prompt=code_reviewer_prompt_template,
            dataset_name=get_agent_graph_state(state=state, state_key="dataset_name"),
            dataset=dataset,
            code=get_agent_graph_state(state=state, state_key="coder_latest")
        )
        )
    graph.add_node(
        "code_router", 
        lambda state: RouterAgent(
            state=state,
            model=model,
            server=server,
            guided_json=code_router_guided_json,
            stop=stop,
            model_endpoint=model_endpoint,
            temperature=temperature
        ).invoke(

            research_question=state["research_question"],
            feedback=lambda: get_agent_graph_state(state=state, state_key="code_reviewer_latest"),
            prompt=coder_router_prompt_template
        )
    )
    graph.add_node(
        "insights_agent",
        lambda state: InsightAgent(
            state=state,
            model=model,
            server=server,
            guided_json=router_guided_json,
            stop=stop,
            model_endpoint=model_endpoint,
            temperature=temperature
        ).invoke(

            research_question=state["research_question"],
            feedback=lambda: get_agent_graph_state(state=state, state_key="code_reviewer_latest"),
            prompt=insight_prompt_template,
            dataset=dataset
        )
    )    
   
    graph.add_node("end", lambda state:EndNodeAgent(state).invoke())

    def first_assignment(state: AgentGraphState):

        return check_for_content(state["start_node"])
    def pass_review(state: AgentGraphState):
        review_list = state["router_response"]
        return json.loads(check_for_content(review_list))["next_agent"]
    
    def finish_review(state:AgentGraphState):

        if state["finished"]=="True":
            return "end"
        else:
            return "analysis_planner"

    graph.set_entry_point("start")
    graph.set_finish_point("end")
    
    graph.add_edge("past_info_agent", "end")
    graph.add_edge("analysis_admin", "analysis_planner")
    graph.add_edge("analysis_planner", "reviewer")
    graph.add_edge("reviewer", "router")
    graph.add_edge("coder_agent", "insights_agent")
    graph.add_edge("code_reviewer", "code_router")


    graph.add_conditional_edges(
        "router",
        lambda state: pass_review(state=state),
    )
    graph.add_conditional_edges(
        "code_router",
        lambda state: pass_review(state=state),
    )
    graph.add_conditional_edges(
        "insights_agent",
        lambda state: finish_review(state=state),
    )
    graph.add_conditional_edges(
        "start", 
        lambda state: first_assignment(state=state),
    )
    print("returning graph")
    return graph

def compile_workflow(graph):
    workflow = graph.compile()
    return workflow
