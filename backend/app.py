from fastapi import FastAPI, BackgroundTasks, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List
import asyncio
import random

from .simulation import SimulationState, Task
from .algorithms import Scheduler

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global State
sim_state = SimulationState()

# Background Loop
async def simulation_loop():
    while True:
        if sim_state.is_running:
            # 1. Increment Tick
            sim_state.tick_count += 1
            current_tick = sim_state.tick_count
            
            # 2. Process arriving tasks
            # In our model, tasks are added successfully via API to 'active_tasks' 
            # but might be waiting for "arrival_time".
            # Let's check pending_tasks if we had them.
            # Currently /add_process inserts directly. 
            # Let's assume we handle "arrival" by checking arrival_time vs current_tick.
            
            arrived_tasks = [t for t in sim_state.active_tasks 
                             if t.arrival_time == current_tick and t.start_time is None and t not in [curr.current_task for curr in sim_state.processors if curr.current_task] and all(t not in p.queue for p in sim_state.processors)]
            
            # Wait, the logic above is complex. 
            # Better: When adding a task, if arrival <= tick, queue it. If arrival > tick, put in pending list.
            # Let's adjust add_process logic later. 
            # For now, let's assume 'pending_tasks' holds tasks waiting for arrival time.
            
            pending_to_remove = []
            to_schedule = []
            
            for t in sim_state.pending_tasks:
                # Use < to ensures task arriving at T runs in T+1 (interval T->T+1)
                # giving min Turnaround of 1.
                if t.arrival_time < current_tick:
                    sim_state.active_tasks.append(t)
                    to_schedule.append(t)
                    pending_to_remove.append(t)
                    sim_state.add_event(f"Arrived: {t.pid} (Burst {t.burst_time})")
            
            for t in pending_to_remove:
                sim_state.pending_tasks.remove(t)
            
            # 3. Scheduler Dispatch
            Scheduler.dispatch(sim_state, to_schedule)
            
            # 4. Processor Execution
            for p in sim_state.processors:
                events = p.tick(current_tick)
                # Check if task completed (Task object tracking)
                # We need to track completions for metrics.
                # The Processor.tick returns strings, but we need the Task object for stats?
                # The Processor.tick updates finished_time, remaining_time.
                # We need to move finished tasks from active_tasks to completed_tasks.
                
                # Refactoring note: Processor.tick modifies state. We simply log events here.
                for e in events:
                    sim_state.add_event(e)
                    
            # Update completed_tasks list helper
            # Any active task with finish_time != None should be moved to completed_tasks
            for t in sim_state.active_tasks[:]:
                if t.finish_time is not None:
                    sim_state.completed_tasks.append(t)
                    sim_state.active_tasks.remove(t)
            
            # 5. Load Balancing (Threshold)
            Scheduler.run_balancing(sim_state)
            
            # 6. Check for Completion
            # Completed: No pending tasks AND No unfinished active tasks
            # Wait, active_tasks only holds unfinished/running now because we moved completed?
            # Yes, lines above move finished tasks out.
            
            if not sim_state.pending_tasks and not sim_state.active_tasks:
                sim_state.is_running = False
                sim_state.is_finished = True
                sim_state.calculate_metrics()
                sim_state.add_log("All processes completed. Simulation stopped.")
                # Force flush here if needed, but the tick flush below handles events.
                # Auto-completed message is "Log final message", so add_log is fine (it appends directly).
                
            sim_state.flush_tick_logs()
            
        await asyncio.sleep(0.5) # 0.5 second per tick

@app.on_event("startup")
async def startup_event():
    asyncio.create_task(simulation_loop())

# Pydantic Models
class StartRequest(BaseModel):
    selected_algorithm: str # "rr", "least", "threshold"

class AddProcessRequest(BaseModel):
    pid: str
    arrival_time: int
    burst_time: int
    
class GenerateProcessRequest(BaseModel):
    count: int

# Endpoints

@app.post("/start")
def start_simulation(req: StartRequest):
    if req.selected_algorithm not in ["rr", "least", "threshold"]:
        raise HTTPException(status_code=400, detail="Invalid algorithm")
    
    sim_state.algorithm = req.selected_algorithm
    sim_state.is_running = True
    sim_state.add_log(f"Simulation started/resumed with algorithm: {req.selected_algorithm}")
    return {"status": "started", "algorithm": req.selected_algorithm}

@app.post("/pause")
def pause_simulation():
    sim_state.is_running = False
    sim_state.add_log("Simulation paused.")
    return {"status": "paused"}

@app.post("/reset")
def reset_simulation():
    sim_state.reset()
    return {"status": "reset"}

@app.post("/add_process")
def add_process(req: AddProcessRequest):
    new_task = Task(req.pid, req.arrival_time, req.burst_time)
    
    # If arrival time is in future relative to current tick, add to pending
    # If arrival time is now or past, add to pending (to be picked up by loop immediately)
    # Actually, to make it instant for "Manual Add" if arrival <= tick,
    # we can put it in pending_tasks and let the loop pick it up (latency < 0.5s).
    # That is cleaner thread-safety wise.
    
    sim_state.pending_tasks.append(new_task)
    # If arrival is way in past, just log it now? 
    # The loop handles arrival <= current_tick.
    
    return {"status": "added", "pid": req.pid}

@app.post("/generate_processes")
def generate_processes(req: GenerateProcessRequest):
    count = req.count
    created = []
    current = sim_state.tick_count
    
    for i in range(count):
        pid = f"P{sim_state.pid_counter}"
        sim_state.pid_counter += 1
        
        # Random arrival: between now and now+10
        arrival = current + random.randint(0, 5)
        burst = random.randint(2, 10)
        
        t = Task(pid, arrival, burst)
        sim_state.pending_tasks.append(t)
        created.append(pid)
        
    sim_state.add_log(f"Generated {count} processes.")
    return {"status": "generated", "count": count, "pids": created}

@app.get("/state")
def get_state():
    return sim_state.get_state()
