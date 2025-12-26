from graph import JobAgent, AgentState


response  = JobAgent().run(
        AgentState(
            initialise=True,
            preference= {
                "designation": "Software Engineer",
                "location": "Delhi", 
                "skills": "Python, langchain, langgraph,FastAPI, GenAI, AI Agents",
                "job_type": "Hybrid", 
                "experience": "2"
            }))
