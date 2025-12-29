from graph import JobAgent, AgentState


response  = JobAgent().run(
        AgentState(
            initialise=True,
            preference= {
                "designation": "Software Engineer",
                "location": "Delhi, Gurugram, Noida, Haryana", 
                "skills": "Python, langchain, langgraph,FastAPI, GenAI, AI Agents",
                "job_type": "Hybrid", 
                "experience": "2"
            }))
