

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from uuid import uuid4
from enum import Enum

app = FastAPI()

# --- Fake Database ---
tasks = {}

class TaskStatus(str, Enum):
    RUNNING = "running"
    WAITING_FOR_INPUT = "waiting_for_input"
    COMPLETED = "completed"

class Task(BaseModel):
    id: str
    status: TaskStatus
    data: dict = {}
    result: str | None = None

class UserInput(BaseModel):
    value: str

# 1. Start the workflow
@app.post("/workflow/start")
async def start_workflow():
    task_id = str(uuid4())
    # Do initial work...
    initial_data = {"step": 1, "info": "Initial calculation done"}
    
    # Save state: We are now pausing to wait for user
    tasks[task_id] = Task(
        id=task_id, 
        status=TaskStatus.WAITING_FOR_INPUT, 
        data=initial_data
    )
    
    return {"task_id": task_id, "message": "Workflow started. Waiting for user input.", "status": "waiting_for_input"}

# 2. Check status (Client polls this)
@app.get("/workflow/{task_id}")
async def get_status(task_id: str):
    if task_id not in tasks:
        raise HTTPException(status_code=404, detail="Task not found")
    return tasks[task_id]

# 3. Provide "In-Between" Input
@app.post("/workflow/{task_id}/input")
async def provide_input(task_id: str, user_input: UserInput):
    if task_id not in tasks:
        raise HTTPException(status_code=404, detail="Task not found")
    
    task = tasks[task_id]
    
    if task.status != TaskStatus.WAITING_FOR_INPUT:
        raise HTTPException(status_code=400, detail="Task is not waiting for input")
    
    # RESUME LOGIC HERE
    # Use the input to finish the job
    final_result = f"Processed {task.data['info']} with user value: {user_input.value}"
    
    # Update state
    task.result = final_result
    task.status = TaskStatus.COMPLETED
    
    return {"message": "Input received, workflow finished", "result": final_result}