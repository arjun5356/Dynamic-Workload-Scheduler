from .simulation import SimulationState, Task, Processor
import random

def assign_task_round_robin(state: SimulationState, task: Task):
    # Assigns to CPUs in circular order: 1 -> 2 -> 3 -> 4 -> 1 ...
    # We use state.last_rr_cpu_index to track.
    
    cpu_index = state.last_rr_cpu_index
    target_cpu = state.processors[cpu_index]
    
    target_cpu.add_task(task)
    state.add_event(f"Assigned: {task.pid} to CPU {target_cpu.processor_id} (Round Robin)")
    
    # Update index
    state.last_rr_cpu_index = (state.last_rr_cpu_index + 1) % 4

def assign_task_least_loaded(state: SimulationState, task: Task):
    # Assign to CPU with smallest queue length
    # Tie-breaking: lower ID
    
    best_cpu = min(state.processors, key=lambda p: len(p.queue))
    best_cpu.add_task(task)
    state.add_event(f"Assigned: {task.pid} to CPU {best_cpu.processor_id} (Least Loaded: {len(best_cpu.queue)} in Q)")

def check_migration_threshold(state: SimulationState):
    """
    Threshold-Based:
    Each CPU has a queue threshold.
    When a CPU's queue exceeds threshold, tasks are migrated to less-loaded CPUs.
    """
    THRESHOLD = 2 # Arbitrary threshold, or can be passed.
    
    # Identify overloaded CPUs
    overloaded = [p for p in state.processors if len(p.queue) > THRESHOLD]
    if not overloaded:
        return

    # Identify underloaded CPUs (e.g., empty queue or significantly less)
    # Simple strategy: Find CPU with min queue.
    
    for producer in overloaded:
        while len(producer.queue) > THRESHOLD:
            # Pick a task to migrate (last one in queue is easiest to move)
            if not producer.queue:
                break
                
            # Find candidate receiver
            receiver = min(state.processors, key=lambda p: len(p.queue))
            
            # Prevent ping-pong: only move if receiver has markedly less load
            if len(receiver.queue) >= len(producer.queue) - 1:
                # No good receiver
                break
            
            task_to_move = producer.queue.pop() # Take from end
            receiver.add_task(task_to_move)
            state.add_event(f"Migration: {task_to_move.pid} CPU {producer.processor_id} -> CPU {receiver.processor_id}")

def assign_task_threshold(state: SimulationState, task: Task):
    # Initial assignment for threshold algorithm can be RR or Least Loaded?
    # Usually "Threshold" implies dynamic balancing, but initial placement matters.
    # prompt says "Scheduler that picks target CPU(s) based on algorithm".
    # We'll use Least Loaded for initial placement as it compliments threshold balancing well, 
    # OR Round Robin. Least Loaded makes more sense for a "Dynamic Load Balancing" vibe.
    # Let's stick to Least Loaded for placement, and the specific "Threshold" logic runs periodically.
    
    # However, strictly following prompts: "Algorithms... 3. Threshold-Based". 
    # Just doing migration isn't an assignment and placement strategy. 
    # Let's use Round Robin for initial placement to *force* imbalances, so the Threshold logic has something to do.
    
    assign_task_round_robin(state, task)
    
    # Check for migrations immediately or at tick end? 
    # Usually done at tick, but we can check here too.
    # We will call check_migration_threshold in the main loop for this mode.

class Scheduler:
    @staticmethod
    def dispatch(state: SimulationState, new_tasks: list[Task]):
        algo = state.algorithm
        
        for task in new_tasks:
            if algo == "rr":
                assign_task_round_robin(state, task)
            elif algo == "least":
                assign_task_least_loaded(state, task)
            elif algo == "threshold":
                assign_task_threshold(state, task)
                
    @staticmethod
    def run_balancing(state: SimulationState):
        if state.algorithm == "threshold":
            check_migration_threshold(state)
