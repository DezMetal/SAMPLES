# Autonomous AI Agent Interface

This project is a web-based platform for interacting with an intelligent, autonomous AI agent powered by the Google Gemini API. The agent is designed to solve complex software development tasks by writing, modifying, and, most importantly, **executing** its own code in a dedicated workspace. It can also create and reuse its own library of Python tools to become more effective over time.

---

## Core Philosophy

The agent's primary method of validation is **direct execution**. Instead of relying heavily on unit tests, the agent is instructed to create runnable scripts (e.g., `run.py`) that execute the core functionality of the project. By analyzing the output (STDOUT and STDERR) of these scripts, the agent determines whether its code is working correctly and iterates until the goal is achieved.

---

## Features

-   **Execution-Driven Development**: The agent validates its work by running the code it writes, promoting a practical and results-oriented workflow.
-   **Reusable Tool Creation**: The agent can create and save its own Python scripts in a shared `/tools` directory, building a reusable library of functions that can be imported and used across any project.
-   **Enhanced Context & Intelligence**: In each cycle, the agent receives the full, up-to-date content of all project files, along with a summary of its past actions, enabling more informed and effective decision-making.
-   **Autonomous Operation**: The agent can run in a fully autonomous loop, continuously executing cycles until the task is complete, it requires feedback, or a cycle limit is reached.
-   **Interactive Control**: Users can pause the autonomous mode at any time to provide manual feedback, guidance, or corrections, which appear instantly in the activity feed.
-   **Project-Based Workspaces**: Each task is managed in a separate, sandboxed project directory.
-   **Live Activity Feed**: A detailed, real-time log of each cycle, including the agent's thought process, actions, tool usage, and execution results.
-   **Integrated File Explorer**: View, open, and manually execute files directly from the UI.

---

## How It Works

The system is built around an agent that operates in a **Think-Plan-Execute** loop.

1.  **Context Assembly**: At the start of each cycle, the backend assembles a rich JSON context. This includes the main goal, a summary of previous cycles, the **full content of all current project files**, a list of available tools, and the report from the last execution.
2.  **Think & Plan (Gemini API Call)**: The context is sent to the Gemini API. The agent analyzes this information and returns a JSON object containing its `thought` (its reasoning and plan) and a list of `actions` to perform.
3.  **Execute Actions**: The Flask backend parses the response and executes the specified actions:
    -   `writeFile`: Creates or overwrites a file. This can be a project file or a new script in the shared `tools` directory.
    -   `executeValidation`: The primary action for validation. It runs an execution script (like `run.py`) and captures the output.
    -   `requestFeedback`: Pauses the autonomous loop to ask the user for specific input or final approval.
4.  **Iterate and Learn**: The outcome of the execution step (STDOUT and STDERR) is recorded and becomes part of the context for the *next* cycle, allowing the agent to learn from its mistakes and successes.

---

## File Structure

The application organizes all projects and shared components within the `agent_projects/` directory:

-   `agent_projects/shared_agent_venv/`: A single Python virtual environment used by all projects.
-   `agent_projects/tools/`: A shared directory where the agent can create and store reusable Python tools (`.py` files). This directory is automatically added to the `PYTHONPATH`.
-   `agent_projects/<your-project-name>/`: Each new task gets its own dedicated workspace folder.

---

## Setup and Running

### Prerequisites

-   Python 3.7+
-   `pip` package manager

### Installation

1.  **Clone the repository:**
    ```bash
    git clone <repository-url>
    cd <repository-directory>
    ```

2.  **Install Python dependencies:**
    ```bash
    pip install google-generativeai python-dotenv Flask selenium webdriver-manager
    ```

### Configuration

1.  **Create an environment file:**
    Create a file named `.env` in the root of the project directory.

2.  **Set your API Key:**
    Add your Google Gemini API key to the `.env` file:
    ```
    GEMINI_API_KEY="YOUR_API_KEY_HERE"
    ```

### Running the Application

1.  **Start the Flask server:**
    ```bash
    python app.py
    ```
    The server will start and automatically create the `agent_projects`, `tools`, and `shared_agent_venv` directories on its first run.

2.  **Access the UI:**
    Open your web browser and navigate to:
    [http://127.0.0.1:5001](http://127.0.0.1:5001)
