# Dynamic Load Balancing Simulator

A real-time web-based simulation of dynamic load balancing algorithms in multiprocessor systems. This project visualizes how tasks are distributed across 4 processors using Round Robin, Least Loaded, and Threshold-Based strategies.

![Project Status](https://img.shields.io/badge/Status-Complete-green)
![Tech Stack](https://img.shields.io/badge/Stack-FastAPI%20%7C%20VanillaJS-blue)

## 🌟 Features

*   **Real-time Visualization**: Watch tasks move through queues and execute on processors in real-time.
*   **Three Scheduling Algorithms**:
    *   **Round Robin**: Cyclical fair distribution.
    *   **Least Loaded**: Smart assignment to the shortest queue.
    *   **Threshold-Based**: Dynamic migration of tasks from overloaded to underloaded CPUs.
*   **Detailed Metrics**: Calculates Average Turnaround Time, Waiting Time, CPU Utilization, and Load Variance.
*   **Interactive Controls**: Pause, Resume, Reset, and Bulk Generate tasks.
*   **Premium UI**: Modern glassmorphism design with dark-mode logging and responsive layouts.

## 🛠️ Tech Stack

*   **Backend**: Python 3.10+, FastAPI, Uvicorn, Asyncio.
*   **Frontend**: HTML5, CSS3 (Modern Variables & Flexbox), Vanilla JavaScript (ES6).
*   **Communication**: REST API with Polling.

## 🚀 Installation & Run

### Prerequisites
*   Python 3.8 or higher installed.

### Steps

1.  **Clone the Repository**
    ```bash
    git clone <repository-url>
    cd OS_PROJECT
    ```

2.  **Create a Virtual Environment (Recommended)**
    ```bash
    python -m venv .venv
    # Windows
    .\.venv\Scripts\activate
    # Mac/Linux
    source .venv/bin/activate
    ```

3.  **Install Dependencies**
    ```bash
    python -m pip install -r requirements.txt
    ```

4.  **Run the Server**
    ```bash
    python -m uvicorn backend.app:app --reload
    ```

5.  **Open the Application**
    Open your browser and navigate to the local file `frontend/index.html`.
    *(Note: You can open the HTML file directly, or serve it via a simple HTTP server if preferred)*.

## 📖 Usage Guide

1.  **Select Algorithm**: Choose between Round Robin, Least Loaded, or Threshold using the dropdown at the top.
2.  **Add Processes**:
    *   **Manual**: Enter PID, Arrival Time, and Burst Time -> Click "Add Process".
    *   **Bulk**: Enter a number (e.g., 5) -> Click "Generate" to create random tasks.
3.  **Start Simulation**: Click the **Start** button.
4.  **Observe**: Watch the "Active Processes" list and the "CPU Grid". The "Tick" counter advances every 0.5s.
5.  **View Results**: Once all tasks are complete, an **Execution Summary** and **Per Process Details** table will appear at the bottom.

## 📂 Project Structure

```
OS_PROJECT/
├── backend/
│   ├── app.py           # Main FastAPI entry point & Simulation Loop
│   ├── simulation.py    # Data models (Task, Processor, State)
│   └── algorithms.py    # Scheduling logic implementation
├── frontend/
│   ├── index.html       # Main dashboard structure
│   ├── style.css        # Premium styling
│   └── script.js        # UI logic and API polling
└── README.md            # This file
```

## 📚 Documentation
For a deep dive into the code logic, algorithms, and mathematical formulas used, please read the **[Technical Report](project_explanation.md)**.

## 📄 License
This project is for educational purposes.
