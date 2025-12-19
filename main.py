import os
from uuid import uuid4
from dotenv import load_dotenv
from scraper import NaurkiScraper, HiristScraper
from typing import TypedDict, Literal
from langgraph.checkpoint.redis import RedisSaver  
from langgraph.graph import StateGraph, END,START
from langgraph.types import interrupt, Command
from utils import parsed_user_data, llm_structure

load_dotenv()

class AgentState(TypedDict):
    initialise : bool
    user_requirements: dict | None
    scrape_query: dict | None
    scraped_data: list | None
    result: str | None

req : str | None = None
DB_URI = os.getenv("REDIS_URI")

with RedisSaver.from_conn_string(DB_URI) as checkpointer: 

    checkpointer.setup()

    def initialise_state(state :AgentState ):
        print("Initialising state")
        state["initialise"] = True
        return state

    def has_required_data(state:AgentState) -> Literal["collect_requirements", "prepare_scraping_query"]:
        print("Checking requirements")
        data = state.get("user_requirements")
        if data is None:
            return "collect_requirements"
        
        return "prepare_scraping_query"

    def collect_user_requirements(state:AgentState):
        print("Collecting user requirements")
        data = interrupt("\nCan you share your data which profile, yoe, package, location, job type like 'WFH, Remote, Hybrid' etc. \n>> ")
        parsed_data  = parsed_user_data(data)
        state["user_requirements"] = parsed_data
        return state


    def prepare_scraping_query(state:AgentState):
        print("Preparing scraping query")
        prompt = f"""Based on the share user requirements. Write search query which target all the user's job requirements correctly. 
                    User requirements: {state.get("user_requirements")}
                    
                    note :
                    - Use this to identify the job_type option only :"Work from office","Remote","Hybrid" 
    
                    - Response format must be JSON.
                    {{
                        "query": "", (designation of the job, simple and short)
                        "location": "", 
                        "job_type": "", (string value)
                        "experience": "" (must be an Integer str value, like '2')
                    }}
                """
        response = llm_structure(prompt)
        state["scrape_query"] = response

        return state

    def scape_jobs(state:AgentState):
        print("Scraping jobs")
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

        naukri_response = naukri_scrapper.scrape(location, query, job_type, experience, 2)
        
        hirist_response = hirist_scrapper.scrape(query=query, location_str=location, min_exp=experience, max_exp=int(experience)+2, page_count=3)
        
        state["scraped_data"] = naukri_response + hirist_response

        return state

    def refine_scape_jobs_data(state:AgentState):
        print("Refining scraped jobs data")
        scaped_jobs = state["scraped_data"]

        if scaped_jobs is None:
            raise Exception("Invalid scraped data")
        
        def get_experience(job):
            import re
            exp_str = str(job.get("experience", ""))
            match = re.search(r'\d+', exp_str)
            return int(match.group()) if match else 100

        # Sort by experience in ascending order
        data = sorted(scaped_jobs, key=get_experience)

        state["scraped_data"] = data
        return state

    

    def format_job_data(state:AgentState):
        print("Formatting job data")
        jobs = state.get("scraped_data", [])
        
        if not jobs:
            state["result"] = "No jobs found matching your criteria."
            return state

        formatted_res = f"Found {len(jobs)} jobs based on your requirements:\n\n"
        
        for i, job in enumerate(jobs, 1):
            formatted_res += f"Job {i}:\n"
            formatted_res += f"Title: {job.get('title', 'N/A')}\n"
            formatted_res += f"Company: {job.get('company', 'N/A')}\n"
            formatted_res += f"Location: {job.get('location', 'N/A')}\n"
            formatted_res += f"Experience: {job.get('experience', 'N/A')}\n"
            formatted_res += f"Salary: {job.get('salary', 'N/A')}\n"
            formatted_res += f"URL: {job.get('url', 'N/A')}\n"
            formatted_res += "-" * 30 + "\n"

        state["result"] = formatted_res
        return state

    def share_job_results_with_user(state:AgentState):
        print("Sharing job results with user")
        print(state.get("result"))
        return state

    graph  = StateGraph(AgentState)
    graph.add_node("initialise",initialise_state)
    graph.add_node("collect_requirements",collect_user_requirements)
    graph.add_node("prepare_scraping_query",prepare_scraping_query)
    graph.add_node("scape_jobs",scape_jobs)
    graph.add_node("refine_scape_jobs_data",refine_scape_jobs_data)
    graph.add_node("format_job_data",format_job_data)
    graph.add_node("share_job_results_with_user",share_job_results_with_user)


    graph.add_edge(START, "initialise")
    graph.add_conditional_edges("initialise", has_required_data)
    graph.add_edge("collect_requirements", "prepare_scraping_query")
    graph.add_edge("prepare_scraping_query", "scape_jobs")
    graph.add_edge("scape_jobs", "refine_scape_jobs_data")
    graph.add_edge("refine_scape_jobs_data", "format_job_data")
    graph.add_edge("format_job_data", "share_job_results_with_user")
    graph.add_edge("share_job_results_with_user", END)

    builder  = graph.compile(checkpointer=checkpointer)
    id = "thread011"
    config = {"configurable": {"thread_id": id}}

    # graph_png_bytes = builder.get_graph(xray=True).draw_mermaid_png()
    # with open("graph_xray.png", "wb") as f:
    #     f.write(graph_png_bytes)

    print("FOR USER id : ",id)
    for event in builder.stream(input=AgentState(initialise=True), config=config, stream_mode="values"):
        if "__interrupt__" in event:
            q = event["__interrupt__"]
            req =  input(q[0].value)
        else :
            pass

    if req:
        for event in builder.stream(Command(resume={"user_requirements":req}), config=config, stream_mode="values"):
            pass
