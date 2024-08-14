from agent_graph.graph import create_graph, compile_workflow
from utils.helper_functions import check_for_content
import pandas as pd
import plotly
from pathlib import Path
import pdfkit
import markdown
import json
from models.openai_models import get_open_ai, get_open_ai_json
import traceback
import re
import os
import traceback
from models.openai_models import get_open_ai, get_open_ai_json
from models.ollama_models import OllamaModel, OllamaJSONModel
from models.vllm_models import VllmJSONModel, VllmModel
from models.groq_models import GroqModel, GroqJSONModel
from models.claude_models import ClaudModel, ClaudJSONModel
from langchain.agents.agent_types import AgentType

from langchain_experimental.agents.agent_toolkits import create_pandas_dataframe_agent


from prompts.prompts import (
    
    dataset_description_prompt_template,
    dataset_guided_json,
    executive_prompt_template,
)
server = 'openai'
model = 'gpt-4o-mini'
model_endpoint = None
temperature=0.2
def get_llm(json_model=True, model_name=None):
    if server == 'openai' and model_name==None:
        return get_open_ai_json(model=model, temperature=temperature) if json_model else get_open_ai(model=model, temperature=temperature)
    elif model_name=="coder":
        return get_open_ai_json(model='gpt-4o', temperature=temperature) if json_model else get_open_ai(model='gpt-4o', temperature=temperature)

    if server == 'ollama':
        return OllamaJSONModel(model=model, temperature=temperature) if json_model else OllamaModel(model=model, temperature=temperature)
    if server == 'vllm':
        return VllmJSONModel(
            model=model, 
            guided_json=guided_json,
            stop=stop,
            model_endpoint=model_endpoint,
            temperature=temperature
        ) if json_model else VllmModel(
            model=model,
            model_endpoint=model_endpoint,
            stop=stop,
            temperature=temperature
        )
    if server == 'groq':
        return GroqJSONModel(
            model=model,
            temperature=temperature
        ) if json_model else GroqModel(
            model=model,
            temperature=temperature
        )
    if server == 'claude':
        return ClaudJSONModel(
            model=model,
            temperature=temperature
        ) if json_model else ClaudModel(
            model=model,
            temperature=temperature
        )
    if server == 'gemini':
        return GeminiJSONModel(
            model=model,
            temperature=temperature
        ) if json_model else GeminiModel(
            model=model,
            temperature=temperature
        )      

#Main class for accessing the agent workflow
class LangChainBase:
    def __init__(self, temperature=0, dataset_name=None,server="openai",model='gpt-4o-mini'):

        self.server = server
        self.model = model
        self.model_endpoint = None
        self.temperature=0.2
        self.dict_inputs={
            "research_question": "",
            "description": "",
            "subject": "",
            "Columns": "",
            "dataset_name": dataset_name
        }
        self.question=""
        self.graph=None
        self.workflow=None
        self.chunk_size=60000
        self.node_id=0
        self.current_theme_id=None
        self.current_analysis_id=None
        self.past_statements={}
        self.past_analyses=[]
        self.report_id=0

    def get_llm(self, json_model=True, model_name=None):
        if self.server == 'openai':
            return get_open_ai_json(model=model, temperature=temperature) if json_model else get_open_ai(model=model, temperature=temperature)
        elif model_name=="coder":
            return get_open_ai_json(model='gpt-4o', temperature=temperature) if json_model else get_open_ai(model='gpt-4o', temperature=temperature)

        if self.server == 'ollama':
            return OllamaJSONModel(model=model, temperature=temperature) if json_model else OllamaModel(model=model, temperature=temperature)
        if self.server == 'vllm':
            return VllmJSONModel(
                model=model, 
                guided_json=guided_json,
                stop=stop,
                model_endpoint=model_endpoint,
                temperature=temperature
            ) if json_model else VllmModel(
                model=model,
                model_endpoint=model_endpoint,
                stop=stop,
                temperature=temperature
            )
        if self.server == 'groq':
            return GroqJSONModel(
                model=model,
                temperature=temperature
            ) if json_model else GroqModel(
                model=model,
                temperature=temperature
            )
        if self.server == 'claude':
            return ClaudJSONModel(
                model=model,
                temperature=temperature
            ) if json_model else ClaudModel(
                model=model,
                temperature=temperature
            )
        if self.server == 'gemini':
            return GeminiJSONModel(
                model=model,
                temperature=temperature
            ) if json_model else GeminiModel(
                model=model,
                temperature=temperature
            )      





    def get_dataset_description(self, df):
        messages = [
            {"role": "system", "content": dataset_description_prompt_template},
            {"role": "user", "content": f"Begin"}
        ]
        llm = create_pandas_dataframe_agent(
            get_llm(),
            df,
            verbose=True,
            agent_type=AgentType.OPENAI_FUNCTIONS,
            allow_dangerous_code=True,

        )
        ai_msg = llm.invoke(messages)
        response = ai_msg
        response=json.loads(response["output"])
        self.dict_inputs["description"]=response["description"]
        self.dict_inputs["subject"]=response["subject"]
        self.dict_inputs["Columns"]=str(response["columns"])
        
        return_dict={"content": []}
        return_dict["content"].append({
            "id": str(self.node_id),
            "category": "dataset",
            "type": "markdown",
            "content": f"{response['description']}\n{response['subject']}"
            
        })
        self.node_id+=1
        return return_dict
    def generate_report(self, ids=None, research_question=None):
        prompt=executive_prompt_template
        prompt = prompt.format(dataset_description=self.dict_inputs["description"], dataset_subject=self.dict_inputs["subject"], research_question="")
        filtered_data={key: self.past_statements[key] for key in ids if key in self.past_statements}
        print("Filtered Data")
        print(filtered_data)
        messages = [
            {"role": "system", "content": prompt},
            {"role": "user", "content": f"{filtered_data}"}
        ]

        llm = self.get_llm(json_model=False)
        ai_msg = llm.invoke(messages)
        response=check_for_content(ai_msg)
        print(response)
        Path("./temp_outputs").mkdir(parents=True, exist_ok=True)
        path_abs=os.getcwd().replace("\\","/")
        markdown_content=response.replace("mage](.",f'mage]({path_abs}')
        html_content=markdown.markdown(markdown_content)
        pdfkit.from_string(html_content, f"./temp_outputs/report_{self.report_id}.pdf", options={"enable-local-file-access": ""})
        self.report_id+=1

        return f"./temp_outputs/report_{self.report_id-1}.pdf"

       
    def create_workflow(self, dataset_name=None, research_question=None, dataset=None):
        print ("Creating graph and compiling workflow...")
        self.graph = create_graph(server=self.server, dataset_name=dataset_name, model=model, model_endpoint=model_endpoint, dataset=dataset, message_history=self.past_statements)
        self.workflow = compile_workflow(self.graph)
        print ("Graph and workflow created.")
        self.dict_inputs["dataset_name"]=dataset_name
        return self.workflow
    async def start_workflow(self, prompt,df):
        Path("./temp_outputs").mkdir(parents=True, exist_ok=True)

        self.dict_inputs["research_question"]= prompt
        self.dict_inputs["message_history"]=str(self.past_statements)
        self.dict_inputs["past_analyses"]=self.past_analyses

        limit = {"recursion_limit": 150}

        past_themes=[]
        outputs=[]
        final_report=""


        for event in self.workflow.stream(self.dict_inputs, limit):

            list_key = list(event.keys())[0]
            state_dict = event[list_key]

            if list_key == "analysis_planner":
                theme = check_for_content(state_dict["past_themes"])
                if theme and theme not in past_themes and theme != "None":
                    past_themes.append(theme)
                    return_dict={"content": []}

                    return_dict["content"].append({
                            "id": str(self.node_id),
                            "category": "theme",
                            "type": "theme",
                            "connecting": "0",
                            "content": f"{theme}"
                            
                        })
                    self.past_statements[str(self.node_id)]={
                        "type": "theme",
                        "content": f"{theme}"
                    }
                    self.current_theme_id=str(self.node_id)
                    self.node_id+=1
                    yield json.dumps(return_dict)+"\n\n\n\n"

            elif list_key == "reporter":
                reporter_response = check_for_content(state_dict["reporter_response"])
                yield f"data: {{\"reporter_response\": \"{reporter_response}\"}}\n\n\n\n"

            elif list_key == "end":
                self.past_analyses=state_dict["past_analyses"]
                return

            elif list_key == "past_info_agent":
                final_report = check_for_content(state_dict["final_reports"])
                return_dict={"content": []}

                return_dict["content"].append({
                    "id": str(self.node_id),
                    "category": "general info",
                    "type": "markdown",
                    "content": f"{final_report}"
                            
                })
                self.past_statements[str(self.node_id)]={
                    "type": "Info",
                    "figure": None,
                    "content": f"{final_report}",
                    "insight": None

                }
                self.node_id+=1
                yield json.dumps(return_dict)+"\n\n\n\n"

            if "output" in state_dict and state_dict["output"]:
                output_content = state_dict["output"]
                if not isinstance(output_content, list):
                    output_content = [output_content]
                output_content = check_for_content(output_content)

                if output_content != "":
                    if list_key == "analysis_planner":
                        return_dict={"content": []}

                        return_dict["content"].append({
                            "id": str(self.node_id),
                            "category": "analysis",
                            "type": "markdown",
                            "content": f"{output_content}"
                            
                        })

                        self.node_id+=1
                        yield json.dumps(return_dict) + "\n\n\n\n"

                    elif list_key == "insights_agent":
                        
                        returned_code = check_for_content(state_dict["coder_response"]).replace(r'```python', "").replace(r'```', '')
                        pattern = r'st\.plotly_chart\([^)]*\)'
                        returned_code = re.sub(pattern, '', returned_code).strip()
                        #Code generation may fail, last attempt using an LLM to correct any issues
                        for i in range(5):
                            try:
                                print(returned_code)
                                has_visualization=False
                                returned_old=returned_code
                                if "plotly" in check_for_content(state_dict["coder_response"]):
                                    plots__=[] #holds all generated figures 
                                    returned_code+="\nplots__.append(fig)" # LLM is told to name any plotly variable fig

                                    exec(returned_code)
                                    if(plots__[0]): #If the returned code contains a plotly image
                                        graphJSON = plotly.io.to_json(plots__[0], pretty=False)
                                        #Acts as a placeholder to send to the frontend, indicating more information is coming
                                        return_dict={"content": []}
                                        return_dict["content"].append({
                                            "id": str(self.node_id),
                                            "category": "analysis",
                                            "type": "plotly",
                                            "connecting": self.current_theme_id if self.current_theme_id else "0",
                                            "content": "",
                                                
                                        })

                                        self.current_analysis_id=str(self.node_id)
                                        yield json.dumps(return_dict)+"\n\n\n\n"
                                        # Given the post limits, send batches of the json data
                                        for i in range(0, len(graphJSON), self.chunk_size):
                                            yield graphJSON[i:i+self.chunk_size]+"\n\n\n\n"
                                        return_dict={"content": []}
                                        returned_old=returned_old.replace("'",'"')
                                        #Yields the final code, signifying the end of a plotly variable
                                        return_dict["content"].append({
                                            "id": str(self.node_id),
                                            "category": "code",
                                            "type": "code",
                                            "content": f"```python\n{returned_old}\n```",
                                                
                                        })
                                        yield "done"+json.dumps(return_dict)+"\n\n\n\n"
                                        plotly.io.write_image(plots__[0], f"./temp_outputs/figure_{self.node_id}.png", "png")
                                        self.past_statements[str(self.node_id)]={
                                            "theme": self.past_statements[self.current_theme_id]["content"] if self.current_theme_id else None,
                                            "type": "Analysis",
                                            "figure": f"./temp_outputs/figure_{self.node_id}.png",
                                            "content": None,
                                            "insight": None
                                        }
                                        self.node_id+=1
                                        has_visualization=True

                                    #If there are supposed to be plotly figures but none are added to the list
                                    else:
                                        return_dict["content"].append({
                                            "id": str(self.node_id),
                                            "category": "analysis",
                                            "type": "markdown",
                                            "connecting": self.current_theme_id if self.current_theme_id else "0",
                                            "content": "Error generating plotly figure. Please try again",
                                                
                                        })

                                        self.current_analysis_id=str(self.node_id)
                                        self.node_id+=1
                                        print(return_dict)
                                        yield json.dumps(return_dict)+"\n\n\n\n"
                                        
                                
                                outputs__=[] #holds all print() outputs, with the LLM being told to place all analysis summaries inside a print statement
                                returned_code=returned_code.replace("print", "outputs__.append")

                                exec(returned_code)
                                for i in range(len(outputs)):
                                    outputs[i]=str(outputs[i])
                                if len(outputs__):
                                    return_dict={"content": []}

                                    return_dict["content"].append({
                                        "id": str(self.node_id),
                                        "category": "analysis",
                                        "type": "html",
                                        "connecting": self.current_analysis_id if has_visualization else self.current_theme_id if self.current_theme_id else "0",
                                        "content": "<br>".join(outputs__),
                                        
                                    })
                                    returned_old=returned_old.replace("'",'"')
                                    print("returned old")
                                    print(returned_old)
                                    return_dict["content"].append({
                                        "id": str(self.node_id),
                                        "category": "code",
                                        "type": "code",
                                        "content": f"```python\n{returned_old}\n```",
                                            
                                    })
                                    print(json.dumps("<br>".join(outputs__)))

                                    self.node_id+=1
                                    yield json.dumps(return_dict)+"\n\n\n\n"
                                    if(has_visualization):
                                        self.past_statements[str(self.current_analysis_id)]["content"]=json.dumps("<br>".join(outputs__))
                                    else: 
                                        self.past_statements[str(self.node_id)]={
                                            "theme": self.past_statements[self.current_theme_id]["content"] if self.current_theme_id else None,
                                            "type": "Analysis",
                                            "figure": None,
                                            "content": json.dumps("<br>".join(outputs__)),
                                            "insight": None

                                        }
                                        
                                        self.current_analysis_id=str(self.node_id-1)

                                #Adds an insight to the frontend, connected to the previous data analysis
                                return_dict={"content": []}
                                return_dict["content"].append({
                                    "id": str(self.node_id),
                                    "category": "insight",
                                    "type": "markdown",
                                    "connecting": self.current_analysis_id,

                                    "content": json.dumps(check_for_content(state_dict['insights_response'])).replace("'","")
                                    
                                })
                                self.past_statements[str(self.current_analysis_id)]["insight"]=check_for_content(state_dict['insights_response'])
                                self.node_id+=1
                                yield json.dumps(return_dict)+"\n\n\n\n"
                                break
                            except:
                                traceback.print_exc()
                                llm = get_open_ai()
                                messages = [
                                    {"role": "system", "content": f"Python code: {returned_old}\n\n Error: {str(traceback.format_exc(chain=False))}"},
                                    {"role": "user", "content": f"Return ONLY the fixed code and NOTHING else."}
                                ]
                                ai_msg = llm.invoke(messages)
                                returned_code = check_for_content(ai_msg).replace(r'```python', "").replace(r'```', '')

                    verbose=False
                    if verbose:
                        print("\nState Dictionary:", event)
                    else:
                        print("\n")






