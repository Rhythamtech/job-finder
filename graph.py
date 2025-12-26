import os
import json
from uuid import uuid4
from dotenv import load_dotenv
from scraper import NaurkiScraper, HiristScraper
from typing import TypedDict, Literal, Annotated
import operator
from langgraph.types import Send
from langgraph.checkpoint.redis import RedisSaver  
from langgraph.graph import StateGraph, END, START
from langgraph.types import interrupt, Command
from utils import parsed_user_data, llm_structure, llm, convert_json_to_toon

load_dotenv()

class AgentState(TypedDict):
    initialise : bool
    preference: dict | None
    scrape_query: dict | None
    scraped_data: list | None
    evaluated_jobs: Annotated[list, operator.add]
    result: str | None

class BatchState(TypedDict):
    jobs: list[dict]
    preference: dict

req : str | None = None
DB_URI = os.getenv("DB_URI")


def initialise_state(state: AgentState):
    print("Initialising state")
    state["initialise"] = True
    state["scraped_data"] = []
    state["evaluated_jobs"] = []
    return state
def prepare_scraping_query(state:AgentState):
    print("Preparing scraping query")
    prompt = f"""Based on the user requirements, create a simple and effective job search query. 
                
                User requirements: {state.get("preference")}
                
                IMPORTANT INSTRUCTIONS:
                - The 'query' field should be SIMPLE - use only the job designation/title (e.g., "Software Engineer", "Python Developer")
                - DO NOT include all skills in the query - job search APIs work better with simple queries
                - The skills will be used for filtering results later, not for the initial search
                - Keep the query concise and focused on the job role
                
                In the response i need these fields only:
                - query (simple job title/designation only, e.g., "Software Engineer" or "Python Developer")
                - location (location of the job)
                - job_type (string value like "Work from office","Remote","Hybrid")
                - experience (must be an Integer str value)
                
                Note:
                - Use this to identify the job_type option only: "Work from office","Remote","Hybrid" 

                - Response format must be JSON.
                {{
                    "query": "", 
                    "location": "", 
                    "job_type": "", 
                    "experience": "" 
                }}
            """
    response = llm_structure(prompt)
    state["scrape_query"] = response
    return state
def scape_jobs(state:AgentState):
    print("Scraping jobs")
    page_count =  os.getenv("MAX_PAGE_COUNT", 2)
    naukri_scrapper = NaurkiScraper()
    hirist_scrapper = HiristScraper()
    q = state["scrape_query"]
    
    query = q["query"]
    location = q["location"]
    job_type = q["job_type"]
    experience = q["experience"]
    if query is None or location is None or job_type is None or experience is None:
        raise Exception("Invalid scrape query")
    
    if query == "" or location == "" or job_type == "" or experience == "":
        raise Exception("Opps!! Invalid scrape query")
    naukri_response = naukri_scrapper.scrape(location=location,
                                            search_term=query,
                                            job_type=job_type,
                                            experience=experience,
                                            page_count=int(page_count))
    hirist_response = hirist_scrapper.scrape(query=query,
                                        location=location,
                                        min_exp=experience,
                                        max_exp=int(experience)+2,
                                        page_count=int(page_count))       
    state["scraped_data"].extend(naukri_response)
    state["scraped_data"].extend(hirist_response)
    return state
def refine_scape_jobs_data(state:AgentState):
    print("Refining scraped jobs data")
    scaped_jobs = state["scraped_data"]
    if not scaped_jobs:
        return {"scraped_data": []}
    
    def get_experience(job):
        import re
        exp_str = str(job.get("experience", ""))
        match = re.search(r'\d+', exp_str)
        return int(match.group()) if match else 100
    # Sort by experience in ascending order
    data = sorted(scaped_jobs, key=get_experience)
    return {"scraped_data": data}

def route_to_evaluate_jobs(state: AgentState):
    data = state["scraped_data"]
    preference = state["preference"]
    sends = []
    chunk_size = 10
    for i in range(0, len(data), chunk_size):
        chunk = data[i:i + chunk_size]
        job_payload = []
        for job in chunk:
            job_payload.append({
                "job_id": job.get("job_id"),
                "description": job.get("description")
            })
        
        sends.append(Send("evaluate_jobs", {"jobs": job_payload, "preference": preference}))
        
    return sends
def evaluate_jobs(state : BatchState):
    print("Evaluating jobs")
    jobs = state.get("jobs", [])
    preference = state.get("preference", {})
    
    instruction = f"""
    Evaluate the following jobs based on the user's preferences.
    User preferences: \n{preference}
    Jobs: \n{jobs}
    Response format must be JSON.
    {{
        "jobs": [
            {{
                "job_id": "",
                "score": 0 (score must be 0-10 scale)
            }}
        ]
    }}
    """
    
    response = llm_structure(instruction)
    return {"evaluated_jobs": response["jobs"]}
    
def format_job_data(state:AgentState):
    print("Formatting job data")
    prompt = """ You are a frontend UI engineer.
            Convert the given JSON array of job listings (same fields in each item) into ONE self-contained HTML file (HTML + CSS + JS in a single file) with CTA buttons.
            Input data:
            """
    jobs = state.get("scraped_data", [])
    evaluated_jobs = state.get("evaluated_jobs", [])
    job_list = []
    
    if not jobs:
        state["result"] = "No jobs found matching your criteria."
        return state
    eval_lookup = {item["job_id"]: item for item in evaluated_jobs}
    for i, job in enumerate(jobs, 1):
        eval_data = eval_lookup.get(job.get("job_id"), {})
        score = eval_data.get("score", "N/A")
    
        if score >=5 :
            job_list.append(job.pop("description"))
    response = llm(prompt+ convert_json_to_toon(job_list))
    state["result"] = response.split("```html")[1].split("```")[0]
    return state

def share_job_results_with_user(state:AgentState):
    try:
        with open("index.html", "w") as f:
            f.write(state.get("result"))
    except Exception as e:
        print(f"Error writing to file: {e}")
    return state

graph = StateGraph(AgentState)
graph.add_node("initialise", initialise_state)
graph.add_node("prepare_scraping_query", prepare_scraping_query)
graph.add_node("scape_jobs", scape_jobs)
graph.add_node("refine_scape_jobs_data", refine_scape_jobs_data)
graph.add_node("evaluate_jobs", evaluate_jobs)
graph.add_node("format_job_data", format_job_data)
graph.add_node("share_job_results_with_user", share_job_results_with_user)
graph.add_edge(START, "initialise")
graph.add_edge("initialise", "prepare_scraping_query")
graph.add_edge("prepare_scraping_query", "scape_jobs")
graph.add_edge("scape_jobs", "refine_scape_jobs_data")

graph.add_conditional_edges("refine_scape_jobs_data", route_to_evaluate_jobs, ["evaluate_jobs"])

graph.add_edge("evaluate_jobs", "format_job_data")
graph.add_edge("format_job_data", "share_job_results_with_user")
graph.add_edge("share_job_results_with_user", END)

class JobAgent:
    def __init__(self):
        self.builder = self.build()

    def build(self):
        builder  = graph.compile()
        return builder
    
    def run(self, state : AgentState):
        self.builder.invoke(state)

