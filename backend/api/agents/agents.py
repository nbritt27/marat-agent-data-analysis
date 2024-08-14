from langchain_core.output_parsers import JsonOutputParser
from langchain_core.messages import HumanMessage, AIMessage

import traceback
import json
from models.openai_models import get_open_ai, get_open_ai_json
from models.ollama_models import OllamaModel, OllamaJSONModel
from models.vllm_models import VllmJSONModel, VllmModel
from models.groq_models import GroqModel, GroqJSONModel
from models.claude_models import ClaudModel, ClaudJSONModel
from langchain_experimental.agents.agent_toolkits.pandas.prompt import PREFIX_FUNCTIONS
# from models.gemini_models import GeminiModel, GeminiJSONModel
from langchain.agents.agent_types import AgentType
from langchain_experimental.agents.agent_toolkits import create_pandas_dataframe_agent
from prompts.prompts import (
    analysis_planner_prompt_template,
    executive_prompt_template,
    analysis_admin_prompt_template,
    insight_prompt_template,
    dataset_description_prompt_template,
    analysis_planner_prompt_template_feedback,
    code_reviewer_prompt_template,
    general_router_prompt,
    past_information_prompt_template,
    reviewer_prompt_template,
    router_prompt_template,
    coder_prompt_template
)
from utils.helper_functions import check_for_content
from states.state import AgentGraphState
parser=JsonOutputParser()
import pandas as pd
import os
class Agent:
    def __init__(self, state: AgentGraphState, model=None, server=None, md_file=None, dataset=None, temperature=0, model_endpoint=None, stop=None, guided_json=None, research_question=None, message_history=None):
        self.state = state
        self.model = model
        self.server = server
        self.temperature = temperature
        self.dataset=dataset
        self.model_endpoint = model_endpoint
        self.stop = stop
        self.guided_json = guided_json
        self.message_history=message_history

    def get_llm(self, json_model=True, model_name=None):
        if self.server == 'openai' and model_name==None:
            return get_open_ai_json(model=self.model, temperature=self.temperature) if json_model else get_open_ai(model=self.model, temperature=self.temperature)
        elif model_name=="coder":
            return get_open_ai_json(model='gpt-4o', temperature=self.temperature) if json_model else get_open_ai(model='gpt-4o', temperature=self.temperature)

        if self.server == 'ollama':
            return OllamaJSONModel(model=self.model, temperature=self.temperature) if json_model else OllamaModel(model=self.model, temperature=self.temperature)
        if self.server == 'vllm':
            return VllmJSONModel(
                model=self.model, 
                guided_json=self.guided_json,
                stop=self.stop,
                model_endpoint=self.model_endpoint,
                temperature=self.temperature
            ) if json_model else VllmModel(
                model=self.model,
                model_endpoint=self.model_endpoint,
                stop=self.stop,
                temperature=self.temperature
            )
        if self.server == 'groq':
            return GroqJSONModel(
                model=self.model,
                temperature=self.temperature
            ) if json_model else GroqModel(
                model=self.model,
                temperature=self.temperature
            )
        if self.server == 'claude':
            return ClaudJSONModel(
                model=self.model,
                temperature=self.temperature
            ) if json_model else ClaudModel(
                model=self.model,
                temperature=self.temperature
            )
        if self.server == 'gemini':
            return GeminiJSONModel(
                model=self.model,
                temperature=self.temperature
            ) if json_model else GeminiModel(
                model=self.model,
                temperature=self.temperature
            )      

    def update_state(self, key, value):
        try:
            self.state = {**self.state, key: value}
        except:
            pass
#Taking in a dataset and research question, it generatea a number of themes for analysis to answer the question
class AnalysisAdminAgent(Agent):
    def invoke(self, description, subject, columns=None,research_question=None, prompt=analysis_admin_prompt_template, feedback=None):

        feedback_value = feedback() if callable(feedback) else feedback
        feedback_value = check_for_content(feedback_value)

        planner_prompt = prompt.format(
            description=check_for_content(description),
            subject=check_for_content(subject),
            feedback=feedback_value,
            research_question=check_for_content(research_question),
            columns=columns[0].content
        )

        messages = [
            {"role": "system", "content": planner_prompt},
            {"role": "user", "content": "Begin"}
        ]

        llm = self.get_llm()
        ai_msg = llm.invoke(messages)
        response=check_for_content(ai_msg)
        

        self.update_state("analysis_admin_response", response)
        response=json.loads(response)

        self.update_state("todo_analysis", response["analysis_plan"])
        print(f"Analysis admin: {response}")
        return self.state

# takes a broad analysis area and recommends a specific analysis to be conducted    
class AnalysisPlannerAgent(Agent):
    def invoke(self, description, subject, past_themes=None, analysis_area=None, columns=None, past_analyses=None, research_question=None, prompt=analysis_planner_prompt_template, feedback=None):
        #Uncomment for code reviewer dialectic
        #self.update_state("code_reviewer_response", "")

        feedback_value = feedback() if callable(feedback) else feedback
        feedback_value = check_for_content(feedback_value)

        analysis_area=check_for_content(analysis_area)
        
        #Convert past analyses to a list and decode from HumanMessage if applicable
        if type(past_analyses)!=list:
            past_analyses=[past_analyses]
        for i in range(len(past_analyses)):
            past_analyses[i]=check_for_content(past_analyses[i])

        try:    
            analysis_area=analysis_area.split("|")[0]
        except:
            analysis_area=""

        planner_prompt=None
        if(feedback_value)!=None and feedback_value!="":

            prompt=analysis_planner_prompt_template_feedback
            planner_prompt=prompt.format(
                description=check_for_content(description),
                subject=check_for_content(subject),
                feedback=feedback_value,
                columns=check_for_content(columns[0]),
                analysis_area=analysis_area,
                analysis=json.loads(check_for_content(self.state["analysis_planner_response"]))["analyses"] 
            )


        else:
            planner_prompt = prompt.format(
                description=check_for_content(description),
                subject=check_for_content(subject),
                past_analyses=past_analyses,
                research_question=check_for_content(research_question),
                columns=check_for_content(columns[0]),
                analysis_area=analysis_area
            )
            if analysis_area!="":
                self.update_state("past_themes", analysis_area)
                past_themes=self.state["past_themes"]

                if type(past_themes)!=list:
                    past_themes=[past_themes]
                for i in range(len(past_themes)):
                    past_themes[i]=check_for_content(past_themes[i])

                if past_themes:
                    #>0 indicates only one operation per theme, increase for more
                    if(past_themes.count(analysis_area)>0):
                        try:
                            self.update_state("todo_analysis", "|".join(check_for_content(self.state["todo_analysis"]).split("|")[1:]))
                        except:
                            traceback.print_exc()
                        
            
        messages = [
            {"role": "system", "content": planner_prompt},
            {"role": "user", "content": "Begin"}
        ]
        llm = self.get_llm()
        ai_msg = llm.invoke(messages)
        response=check_for_content(ai_msg)
        print(f"analysis planner response {response}")
        self.update_state("analysis_planner_response", response)


        self.update_state("output", "")
        return self.state

#Uses a pandas dataframe agent to describe the dataset passed through by the user
class DatasetAgent(Agent):
    def invoke(self, dataset_name="",dataset=None, prompt=dataset_description_prompt_template, research_question=None, feedback=None):
        #Leaving feedback values in all methods in case you would lke to create a reviewer for any agent
        feedback_value = feedback() if callable(feedback) else feedback
        feedback_value = check_for_content(feedback_value)
        
        planner_prompt = prompt.format(
            feedback=feedback_value,
        )

        messages = [
            {"role": "system", "content": planner_prompt},
            {"role": "user", "content": f"Begin"}
        ]

        llm = create_pandas_dataframe_agent(
            self.get_llm(),
            dataset,
            verbose=True,
            agent_type=AgentType.OPENAI_FUNCTIONS,
            allow_dangerous_code=True,

        )
        
        ai_msg = llm.invoke(messages)
        response = check_for_content(ai_msg)
        response=json.loads(response["output"])

        self.update_state("description", response["description"])
        self.update_state("subject", response["subject"])
        self.update_state("Columns", str(response["columns"]))
        self.update_state("dataset_response", response)

        self.update_state("dataset_name", dataset_name)

        return self.state

#Takes plan for a specific analysis and reviews it for specificity
class ReviewerAgent(Agent):
    def invoke(self, themes=None, description=None, subject=None, prompt=reviewer_prompt_template, analysis_agent=None, feedback=None):
        reporter_value = analysis_agent() if callable(analysis_agent) else analysis_agent
        feedback_value = feedback() if callable(feedback) else feedback
        
        theme=check_for_content(themes)
        try:
            theme=themes.split("|")[0]
        except:
            theme=""
        reporter_value = check_for_content(reporter_value)
        for i in range(len(feedback_value)):
            feedback_value[i]=check_for_content(feedback_value[i])
        if len(feedback_value)>3:
            feedback_value=feedback_value[3:]
        reporter_value=json.loads(reporter_value)["analyses"]
        reviewer_prompt = prompt.format(
            reporter=reporter_value,
            theme=theme,
            description= description,
            subject=subject,
            columns=check_for_content(self.state["Columns"][0]),
            feedback=feedback_value,
        )

        messages = [
            {"role": "system", "content": reviewer_prompt},
            {"role": "user", "content": f"Begin"}
        ]

        llm = self.get_llm()
        ai_msg = llm.invoke(messages)
        response=check_for_content(ai_msg)

        response_json=json.loads(response)
        
        if response_json["pass_review"]=="True":
            self.update_state("output",reporter_value + "\n" + str(response_json["helpfulness"]))
        else:
            self.update_state("output", "")

        self.update_state("reviewer_response", response)
        print(f"Reporter: {response}")
        return self.state
    
#Routes the reviewer response to the appropriate agent
class RouterAgent(Agent):
    def invoke(self, feedback=None, research_question=None, subject=None, description=None, prompt=router_prompt_template):
        feedback_value = feedback() if callable(feedback) else feedback
        feedback_value = check_for_content(feedback_value)
        
        router_prompt = prompt.format(feedback=feedback_value)

        messages = [
            {"role": "system", "content": router_prompt},
            {"role": "user", "content": f"Begin"}
        ]

        llm = self.get_llm()
        ai_msg = llm.invoke(messages)
        response=check_for_content(ai_msg)
        self.update_state("router_response", response)
        print(f"Router: {response}")
        return self.state

#Presently inactive, reviews proposed code for validity and accuracy
class CodeReviewAgent(Agent):
    def invoke(self, dataset=None, analysis=None,code=None, dataset_name="", columns=None, research_question=None, feedback=None, prompt=code_reviewer_prompt_template):

        analysis = json.loads(check_for_content(analysis))["analyses"]

        self.dataset=self.state["dataset"]
        code_review_prompt = prompt.format(analysis=analysis, code=code, columns=self.state["Columns"])
        prefix = (
            f"{PREFIX_FUNCTIONS} "+code_review_prompt
        )
        dataset.columns = dataset.columns.str.strip()
        agent_llm = create_pandas_dataframe_agent(
            self.get_llm(json_model=False),
            dataset,
            verbose=True,
            agent_type=AgentType.OPENAI_FUNCTIONS,
            allow_dangerous_code=True,
            max_iterations=20,
            max_execution_time=30,
            prefix=prefix, 
            agent_executor_kwargs={"handle_parsing_errors":True},
            return_intermediate_steps=True,
            number_of_head_rows=10,
        )
        ai_msg=agent_llm.invoke(analysis)
        response=check_for_content(ai_msg)
        response_json=None
        try:
            response_json=json.loads(str(response["output"]).replace('```json','').replace("```",""))
        except:
            traceback.print_exc()
            response_json=response["output"]

        self.update_state("code_reviewer_response", response["output"])
        if response_json["pass_review"]=="True":

            self.update_state("reviewer_response", "")
            self.update_state("output", code)
        else:

            self.update_state("output", "")

        print(f"Code reviewer: {response['output']}")
        return self.state
    
#Takes a specific analysis from the anaalysis planner and runs the analysis using python
class CoderAgent(Agent):
    def invoke(self, dataset=None, analysis=None,dataset_name="", columns=None, research_question=None, feedback=None, prompt=coder_prompt_template):
        #Temporary for removal of code reviewer
        # feedback_value = feedback() if callable(feedback) else feedback
        # feedback_value = check_for_content(feedback_value)
        feedback_value=""
        self.update_state("reviewer_response", "")

        self.dataset=dataset
        dataset_name=self.state["dataset_name"]
        if feedback_value==None or feedback_value=="":
            prefix = (
                f"{PREFIX_FUNCTIONS} You are tasked with running a particular analysis. You have access to the dataset, and can use it to find information about "
                f"certain columns. If asked to generate a plot, the Python code should generate an appropriate plotly figure named fig, but should not attempt to "
                f"visualize it. "
                f"Ensure that you use the dataset provided as the data source. You should never create sample data, and only use data from the source. "
                f"If you encounter issues with the names of the columns, consider creating an understanding of what each column represents and reformulate the code using the exact column names. "
                f"Ensure any data cleaning and operations on the dataframe are included in each re-run of the code, and all variables are redefined so that any attempt to fix an error includes all."
                f"If it ever seems you have removed elements of the dataframe that should not be moved, restore the dataframe and start over. "
                f" Ensure columns mean what you think they do (differences between percentages and other numerical representations, numberic values "
                f"representing quantities or just presence in a category, etc.). Any statistical analyses (model summaries, confusion matrixes,etc) should have results converted to html, with that html then being passed to the user through a print statement. Only the final results"
                f" should be passed through in the final code (do not print data cleaning operations, missing values, etc., just the final results. NEVER call a print statement to display anything about a figure or plotly visualization. )"
                f"remember any visualization should be presented using plotly but never attempt to visualize the final fig variable. Any long print statement should not be passed back to the LLM, but the code for it should be returned in the final code."
                f" Any visualizations you do create a variable for (but of course do not show) should have all elements JSON serializable (dates should be converted to strings, etc.) The fig variable should also have an explicitly defined color sequence. Do NOT forget this"
                f" NEVER produce a plot or chart variable with a name other than fig. Any plot should be named fig, nothing else."
                f"NEVER remove rows in the dataframe. The"
                f" If you ever lose access to the dataframe, you can reimport it assuming it has the name {dataset_name}. Do NOT under any circumstances attempt to display or return the resulting figure. Attempt to fix all prevoius errors of previous runs."
            )
            self.update_state("past_analyses", json.loads(check_for_content(analysis))["analyses"])

        else:
            feedback_value=json.loads(feedback_value.replace('```json','').replace("```",""))
            prefix=(
                f"{PREFIX_FUNCTIONS} You will receive an element of Python code along with feedback that was provided for that code. You have access to a Python Repl to help you if you need to check any variables or test any code. You are to implement the changes to the Python code suggested in the feedback."
                f" If asked to generate a plot, the Python code should generate an appropriate plotly figure named fig with an explicitly defined color sequence, but should not attempt to visualize it. Do NOT under any circumstances attempt to display or return the resulting figure. "
                f" Any visualizations you do create a variable for (but of course do not show) should have all elements JSON serializable (dates should be converted to strings, etc.)  Python code: {self.state['coder_response'][-1]} \n Feedback: {feedback_value['feedback']} "
                f" Remember to NEVER attempt to show the figure."

            )
        
        agent_llm = create_pandas_dataframe_agent(
            self.get_llm(json_model=False),
            self.dataset,
            verbose=True,
            agent_type=AgentType.OPENAI_FUNCTIONS,
            allow_dangerous_code=True,
            max_iterations=20,
            max_execution_time=30,
            max_retries=2,
            prefix=prefix, 
            agent_executor_kwargs={"handle_parsing_errors":True},
            suffix=f"If the resulting code handles dates or times, ensure they are parsed properly for the "
            f"returned figure (e.g. in Plotly objects of type Period are not JSON serializable, so should be converted)."
            f"Return only the complete python code and nothing else. ",
            
            return_intermediate_steps=True,
            number_of_head_rows=10,
        )
        #Occasionally, the Python repl will esnd printed output back into its own input, causing an error. This attempts to try again given an error response
        for i in range(3):
            try:
                ai_msg=agent_llm.invoke(json.loads(check_for_content(analysis))["analyses"])
                break
            except:
                traceback.format_exc()
                pass
        if "Agent stopped" in ai_msg["output"]:
            self.update_state("coder_response", ai_msg["intermediate_steps"][-1][0].tool_input["query"])
        else:
            self.update_state("coder_response", ai_msg["output"])
        self.update_state("output", "")
        print(f"Coder: {ai_msg['output']}")
        return self.state
#Presently a placeholder for sending final results to the end of the chain
class ExecutiveReportAgent(Agent):
    def invoke(self, dataset=None, analysis=None,dataset_name="", columns=None, research_question=None, feedback=None, prompt=coder_prompt_template):
        analysis_format={}

        if self.state["analysis_admin_response"]:

            for i in self.state["past_themes"]:
                analysis_format[check_for_content(i)]=[]
            for i in range(len(self.state["insights_response"])):
                analysis_format[check_for_content(self.state["themes"][i])].append(
                    {
                        "Analysis": check_for_content(self.state["past_analyses"][i]),
                        "Results": check_for_content(self.state["insights_response"][i]),
                        "Figure": check_for_content(self.state["figures"][i])
                    }
                )
        else:
            analysis_format={
                "Analysis": check_for_content(self.state["past_analyses"]),
                "Results": check_for_content(self.state["insights_response"]),
                "Figure": check_for_content(self.state["figures"])
            }
        self.update_state("report_complete", str(analysis_format))
        if self.state["analysis_admin_response"]:
            llm=self.get_llm(json_model=False)
            ai_msg=llm.invoke(str(analysis_format))

            self.update_state("final_reports", check_for_content(ai_msg))

            with open("executive_report.md", "w") as f:
                f.write(check_for_content(ai_msg))
                f.close()
        else:
            self.update_state("final_reports", str(analysis_format))
        return self.state
    
#Takes the result returned by the coder and generates key takeaways
class InsightAgent(Agent):
    def invoke(self, dataset=None, analysis=None,dataset_name="", columns=None, research_question=None, feedback=None, prompt=coder_prompt_template):

        feedback_value = feedback() if callable(feedback) else feedback
        feedback_value = check_for_content(feedback_value)

        self.dataset=dataset
        self.dataset.columns = self.dataset.columns.str.strip()
        prefix = (
            f"{PREFIX_FUNCTIONS} {prompt.format(code=check_for_content(self.state['coder_response']), analysis=check_for_content(self.state['past_analyses'][-1]))}"
        )
            
        agent_llm = create_pandas_dataframe_agent(
            self.get_llm(json_model=False),
            self.dataset,
            verbose=True,
            agent_type=AgentType.OPENAI_FUNCTIONS,
            allow_dangerous_code=True,
            max_iterations=40,
            max_execution_time=30,
            max_retries=2,
            prefix=prefix, 
            agent_executor_kwargs={"handle_parsing_errors":True},
            suffix=f"Return only the resulting insights ",
            
            return_intermediate_steps=False,
            number_of_head_rows=10,
        )
        ai_msg=agent_llm.invoke("Begin")

        self.update_state("output", check_for_content(self.state["coder_response"]))
        self.update_state("insights_response", ai_msg["output"])
        if self.state["past_themes"]:
            self.update_state("themes", check_for_content(self.state["past_themes"]))
       
        # Given the graph is re-executed with each prompt, this processes whether the insight is
        # for the last theme or if there is no theme to process
        try:
            if len(check_for_content(self.state["todo_analysis"]).split('|'))==1:
                self.update_state("finished", "True")
        except:
            self.update_state("finished", "True")
        print(f"Insights: {ai_msg['output']}")
        return self.state
    
#Determines where to pass the prompt to (admin, analysis planner, past information)    
class FirstRouterAgent(Agent):
    def invoke(self, message_history=None, feedback=None, research_question=None, subject=None, description=None, prompt=general_router_prompt):
        
        router_prompt = prompt.format(history=self.state["message_history"], research_question=self.state["research_question"])
        messages = [
            {"role": "system", "content": router_prompt},
            {"role": "user", "content": f"Begin"}
        ]

        llm = self.get_llm()
        ai_msg = llm.invoke(messages)
        response=check_for_content(ai_msg)
        
        self.update_state("start_node", json.loads(response)["next_agent"])
        print(f"First Router: {response}")
        return self.state
#Uses past stored information to generate an answer
class PastInformationAgent(Agent):
    def invoke(self, message_history=None, feedback=None, research_question=None, subject=None, description=None, prompt=past_information_prompt_template):
        prompt = prompt.format(history=self.state["message_history"], research_question=check_for_content(self.state["research_question"]))

        messages = [
            {"role": "system", "content": prompt},
            {"role": "user", "content": f"Begin"}
        ]

        llm = self.get_llm(json_model=False)
        ai_msg = llm.invoke(messages)
        response=check_for_content(ai_msg)
       

        self.update_state("final_reports", response)
        print(f"Past Information: {response}")
        return self.state
    
    
#Presently a placeholder for returning responses, can be modified to generate a summary of all information in the response
class FinalReportAgent(Agent):
    def invoke(self, research_question=None, final_response=None, prompt=executive_prompt_template):
        final_response_value = final_response() if callable(final_response) else final_response
        response = final_response_value.content

        self.update_state("final_reports", response)

        router_prompt = prompt.format(feedback=feedback_value)

        messages = [
            {"role": "system", "content": router_prompt},
            {"role": "user", "content": f"Begin"}
        ]

        llm = self.get_llm()
        ai_msg = llm.invoke(messages)
        response=ai_msg
        return self.state

#Ends the process
class EndNodeAgent(Agent):
    def invoke(self):
        self.update_state("end_chain", "end_chain")
        return self.state
    
