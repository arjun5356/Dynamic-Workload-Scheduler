import random
from typing import List, Optional, Deque
from collections import deque
import enum

class Task:
    def __init__(self, pid: str, arrival_time: int, burst_time: int):
        self.pid = pid
        self.arrival_time = arrival_time
        self.burst_time = burst_time
        self.remaining_time = burst_time
        self.start_time: Optional[int] = None
        self.finish_time: Optional[int] = None

    def to_dict(self):
        return {
            "pid": self.pid,
            "arrival_time": self.arrival_time,
            "burst_time": self.burst_time,
            "remaining_time": self.remaining_time,
            "start_time": self.start_time,
            "finish_time": self.finish_time
        }

class Processor:
    def __init__(self, processor_id: int):
        self.processor_id = processor_id
        self.current_task: Optional[Task] = None
        self.queue: Deque[Task] = deque()
        self.executed_count = 0
        self.busy_ticks = 0

    def add_task(self, task: Task):
        self.queue.append(task)

    def tick(self, current_time: int) -> List[str]:
        """
        Executes one unit of work.
        Returns a list of event strings (e.g. task finished).
        """
        events = []
        
        # If no current task, try to fetch from queue
        if self.current_task is None:
            if self.queue:
                self.current_task = self.queue.popleft()
                if self.current_task.start_time is None:
                    self.current_task.start_time = current_time
            else:
                return events # Idle

        # Execute 1 unit
        if self.current_task:
            self.current_task.remaining_time -= 1
            self.busy_ticks += 1
            
            # Check completion
            if self.current_task.remaining_time <= 0:
                self.current_task.finish_time = current_time
                self.executed_count += 1
                finished_pid = self.current_task.pid
                events.append(f"Completed: {finished_pid}")
                
                self.current_task = None
                if self.queue:
                    self.current_task = self.queue.popleft()
                    if self.current_task.start_time is None:
                        self.current_task.start_time = current_time

        return events

    def to_dict(self):
        return {
            "id": self.processor_id,
            "current": self.current_task.pid if self.current_task else None,
            "queue_length": len(self.queue),
            "executed_count": self.executed_count
        }

class SimulationState:
    def __init__(self):
        self.processors = [Processor(i+1) for i in range(4)]
        self.tick_count = 0
        self.active_tasks: List[Task] = [] 
        self.pending_tasks: List[Task] = [] 
        self.completed_tasks: List[Task] = []
        self.log: List[str] = []
        self.current_tick_events: List[str] = []
        self.is_running = False
        self.is_finished = False
        self.algorithm = "rr"
        self.last_rr_cpu_index = 0
        self.pid_counter = 1
        self.metrics = {}

    def add_event(self, message: str):
        self.current_tick_events.append(message)

    def add_log(self, message: str):
        # Legacy support or direct log
        self.log.append(f"Tick {self.tick_count}: {message}")

    def flush_tick_logs(self):
        if not self.current_tick_events:
            return
        
        # Group events
        # Format:
        # Tick X:
        #   - Event 1
        #   - Event 2
        entry = f"Tick {self.tick_count}:"
        for evt in self.current_tick_events:
            entry += f"<br>&nbsp;&nbsp;- {evt}"
        self.log.append(entry)
        self.current_tick_events = []

    def reset(self):
        self.processors = [Processor(i+1) for i in range(4)]
        self.tick_count = 0
        self.active_tasks = []
        self.pending_tasks = []
        self.completed_tasks = []
        self.log = []
        self.current_tick_events = []
        self.is_running = False
        self.is_finished = False
        self.last_rr_cpu_index = 0
        self.pid_counter = 1
        self.metrics = {}
        self.log.append("Simulation reset.")

    def calculate_metrics(self):
        total_tasks = len(self.completed_tasks)
        if total_tasks == 0:
            return
        
        total_wait = 0
        total_turnaround = 0
        
        for t in self.completed_tasks:
            # Turnaround = Finish - Arrival
            turnaround = t.finish_time - t.arrival_time
            # Wait = Turnaround - Burst
            wait = turnaround - t.burst_time
            
            total_turnaround += turnaround
            total_wait += wait
            
        avg_wait = total_wait / total_tasks
        avg_turnaround = total_turnaround / total_tasks
        
        # CPU Utilization
        cpu_utils = []
        for p in self.processors:
            # If tick_count is 0, avoid div by zero, though unlikely if tasks finished
            util = (p.busy_ticks / self.tick_count * 100) if self.tick_count > 0 else 0
            cpu_utils.append(util)
            
        # Variance of Util
        mean_util = sum(cpu_utils) / len(cpu_utils)
        variance = sum((u - mean_util) ** 2 for u in cpu_utils) / len(cpu_utils)
        
        self.metrics = {
            "avg_waiting_time": round(avg_wait, 2),
            "avg_turnaround_time": round(avg_turnaround, 2),
            "cpu_utilization": [round(u) for u in cpu_utils],
            "variance": round(variance, 2)
        }

    def get_state(self):
        # Combine unfinished active tasks and pending tasks
        unfinished_active = [t.to_dict() for t in self.active_tasks if t.finish_time is None]
        pending = [t.to_dict() for t in self.pending_tasks]
        all_unfinished = unfinished_active + pending

        # Prepare completed details if finished
        completed_details = []
        if self.is_finished:
            for t in self.completed_tasks:
                if t.finish_time is not None and t.start_time is not None:
                    turnaround = t.finish_time - t.arrival_time
                    wait = turnaround - t.burst_time
                    completed_details.append({
                        "pid": t.pid,
                        "arrival": t.arrival_time,
                        "burst": t.burst_time,
                        "start": t.start_time,
                        "finish": t.finish_time,
                        "waiting": wait,
                        "turnaround": turnaround
                    })
        
        # Sort by PID or Finish Time? PID is standard for "per process" list.
        # Assuming PIDs are strings P1, P10 etc, sorting might be tricky but acceptable as is.
        # Let's sort by Arrival Time then PID to be deterministic
        completed_details.sort(key=lambda x: (x["arrival"], x["pid"]))

        return {
            "tick": self.tick_count,
            "processors": [p.to_dict() for p in self.processors],
            "active_tasks": all_unfinished,
            "log": self.log[-100:], 
            "running": self.is_running,
            "finished": self.is_finished,
            "metrics": self.metrics if self.is_finished else None,
            "completed_details": completed_details
        }
