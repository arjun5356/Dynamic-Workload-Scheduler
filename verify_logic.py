from backend.simulation import SimulationState, Task
from backend.algorithms import Scheduler
import asyncio

# Mocking the loop logic from app.py to test logic in isolation
def run_test():
    print("--- Running Logic Verification ---")
    
    # Setup
    sim_state = SimulationState()
    sim_state.ticks = 0
    sim_state.algorithm = "rr"
    
    # Add a task with Arrival 5, Burst 1
    # We expect:
    # Tick 1..5: Idle
    # Tick 6: Runs (5->6)
    # Finish: 6
    # Turnaround: 6 - 5 = 1
    # Wait: 1 - 1 = 0
    
    t1 = Task("P1", 5, 1)
    sim_state.pending_tasks.append(t1)
    
    print(f"Goal: P1 (Arr: 5, Burst: 1). Expect Finish: 6, TA: 1.")

    # Loop for 10 ticks
    for i in range(10):
        # 1. Increment
        sim_state.tick_count += 1
        current_tick = sim_state.tick_count
        
        # 2. Process Arriving
        # Logic from app.py (currently uses <=)
        # We want to test if <= causes anomaly
        
        pending_to_remove = []
        to_schedule = []
        
        for t in sim_state.pending_tasks:
            # ORIGINAL LOGIC:
            if t.arrival_time <= current_tick:
                sim_state.active_tasks.append(t)
                to_schedule.append(t)
                pending_to_remove.append(t)
                print(f"Tick {current_tick}: P1 Arrived/Scheduled")
        
        for t in pending_to_remove:
            sim_state.pending_tasks.remove(t)
            
        # 3. Dispatch
        Scheduler.dispatch(sim_state, to_schedule)
        
        # 4. Processor Execution
        for p in sim_state.processors:
            events = p.tick(current_tick)
            if events:
                for e in events:
                    print(f"Tick {current_tick}: {e}")
                    
        # Update completed
        for t in sim_state.active_tasks[:]:
            if t.finish_time is not None:
                sim_state.completed_tasks.append(t)
                sim_state.active_tasks.remove(t)
                
    # Check Result
    if sim_state.completed_tasks:
        done = sim_state.completed_tasks[0]
        turnaround = done.finish_time - done.arrival_time
        print(f"Result: Finish={done.finish_time}, Turnaround={turnaround}")
        if turnaround == 0:
            print("FAILURE: Turnaround is 0. Logic needs correction (< instead of <=).")
        else:
            print("SUCCESS: Turnaround seems valid.")
    else:
        print("FAILURE: Task did not complete.")

if __name__ == "__main__":
    run_test()
