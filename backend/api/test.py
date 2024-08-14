from fastapi import FastAPI, HTTPException, File, Query, Form, UploadFile, Body
from fastapi.responses import StreamingResponse, FileResponse
from uuid import uuid4
import os
import sys
from io import StringIO
import pandas as pd
from dotenv import load_dotenv
import logging
import traceback
from langchain_base.langchain import LangChainBase
from fastapi import FastAPI, HTTPException, File, Form, UploadFile
from fastapi.responses import StreamingResponse
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()
origins = ["http://localhost:3000", "http://127.0.0.1:3000"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
load_dotenv()
# URL of the FastAPI endpoint

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
user_sessions={}
dataset=None
reports = {}

def get_dataset():
    return dataset
def get_user_instance(session_id: str) -> LangChainBase:
    print(user_sessions)
    print(session_id)
    if session_id in user_sessions:
        print("found user instance")
        return user_sessions[session_id]
    else:
        raise HTTPException(status_code=404, detail="Session not found")
@app.get("/ping")
async def ping():
    sys.exit(4)
@app.post("/session_start")

async def start_session(file_input: UploadFile = File(...)):
    try:
        contents=await file_input.read()

        file_str=StringIO(contents.decode("utf-8"))
        save_path = os.path.join("uploads", file_input.filename)  # Assuming you have an 'uploads' directory

        # Ensure the directory exists
        os.makedirs(os.path.dirname(save_path), exist_ok=True)

        # Write the file contents to a new file with the same name
        with open(save_path, "wb") as f:
            f.write(contents)
        df=pd.read_csv(file_str)

        langchain_instance = LangChainBase()

        user_sessions["0"] = langchain_instance
        langchain_instance.create_workflow(dataset_name=save_path, research_question="", dataset=df)
        return_dict=langchain_instance.get_dataset_description(df=df)
        return f"{return_dict}"
    except:
        return traceback.format_exc()

@app.post("/api")
async def chat(prompt: str = Query(...)):
    print(prompt)
    
    try:
        langchain_instance = get_user_instance("0")

        # Run the workflow
        workflow_generator = langchain_instance.start_workflow(prompt=prompt, df=get_dataset())

        return StreamingResponse(workflow_generator, media_type="application/json")
    except:

        return traceback.format_exc()
    
@app.post("/report")
async def generate_report(ids: str=Query(...)):
    print(ids)
    md_report_path=get_user_instance("0").generate_report(ids=ids.split(" "))
    md_report_path=md_report_path.split("/")[-1]
    reports[md_report_path]=md_report_path
    return {"report_id": md_report_path, "report_filename": md_report_path}

@app.get("/list-reports")
async def list_reports():
    return [{"report_id": k, "report_filename": v} for k, v in reports.items()]
@app.get("/get-report/{report_id}")
async def get_report(report_id: str):
    print(report_id)
    report_filename = reports.get(report_id)

    if report_filename:
        return FileResponse(f"./temp_outputs/{report_filename}", media_type='application/pdf', filename=report_filename)
    else:
        raise HTTPException(status_code=404, detail="Report not found")
