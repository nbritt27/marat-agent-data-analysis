from langchain_openai import ChatOpenAI




def get_open_ai(temperature=0.2, model='gpt-4o-mini'):

    llm = ChatOpenAI(
    model=model,
    temperature = temperature,
)
    return llm

def get_open_ai_json(temperature=0.2, model='gpt-4o-mini'):
    llm = ChatOpenAI(
    model=model,
    temperature = temperature,
    model_kwargs={"response_format": {"type": "json_object"}},
)
    return llm
