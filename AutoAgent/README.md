# AutoAgent - Autonomous AI Agent Framework

AutoAgent is a sophisticated, self-contained web application that provides a user interface for managing and interacting with an autonomous AI software engineering agent. It allows a user to define a high-level software development task, and the AI agent will then autonomously create a plan, write code, execute it, and debug its own work until the goal is achieved.

## Core Features

-   **Autonomous Task Completion**: The agent operates on an OODA (Observe, Orient, Decide, Act) loop. It analyzes the user's goal, observes the current state of the project (file listing, process output), and decides on a course of action, which it executes through writing files or running commands.
-   **Web-Based UI**: The entire system is managed through a clean, intuitive web interface built with Flask and Tailwind CSS. It provides a real-time view of the agent's activity, the project's file system, running processes, and the agent's thought process.
-   **Project-Based Workflow**: Each task is managed as a separate project. The agent's state, including its history, files, and running processes, is sandboxed within its project directory.
-   **Interactive Feedback Loop**: While the agent is autonomous, the user can pause its operation, provide feedback or guidance, and then resume the task.
-   **Code Execution and Environment Management**: The agent executes code within a shared Python virtual environment, which it manages automatically. It can install dependencies from a `requirements.txt` file, run scripts, and start servers.
-   **Stateful and Persistent**: The agent's progress and history are saved to a `.agent_state.json` file within the project, allowing tasks to be stopped and resumed later.

---
## Portfolio Highlight

### Use Cases
*   **Automated Software Development:** Provide a high-level goal (e.g., "create a website with a login page") and have the agent autonomously write, test, and debug the code.
*   **Rapid Prototyping:** Quickly scaffold new applications or microservices. The agent can generate boilerplate code, set up servers, and install dependencies in minutes.
*   **Automated Research & Scripting:** Ask the agent to perform research tasks that involve writing and running scripts, such as web scraping or data analysis.
*   **Educational Tool:** An excellent tool for learning about AI agent architecture, prompt engineering, and human-computer interaction.

### Proof of Concept
This project is a proof of concept for a **self-contained, autonomous software engineering agent with a human-in-the-loop interface**. It demonstrates:
*   **Agentic AI Architecture:** A practical implementation of the **OODA (Observe, Orient, Decide, Act)** loop, where the AI makes decisions based on its environment (file system, running processes) to achieve a goal.
*   **Full-Stack Integration:** A complete, end-to-end system built with a Python/Flask backend serving a dynamic vanilla JavaScript frontend.
*   **Robust Environment Management:** The agent operates within a sandboxed project directory and manages its own Python virtual environment, including automated dependency installation from `requirements.txt`.
*   **Asynchronous Process Handling:** The backend uses threading and queues to manage and monitor long-running subprocesses (like web servers) without blocking the main application, feeding their `stdout` and `stderr` back to the UI in real-time.
*   **Advanced Prompt Engineering:** The system dynamically constructs a detailed JSON context for the AI, including file listings, process status, and logs, enabling the model to make informed, context-aware decisions.

### Hireable Skills
*   **Python & Flask:** Proficient in building robust backend services and REST APIs with Flask.
*   **AI/LLM Integration:** Deep experience in integrating and prompting large language models (Google Gemini) for complex, multi-step tasks.
*   **Full-Stack Development:** Ability to design and build a complete web application, including frontend development with vanilla JavaScript and styling with Tailwind CSS.
*   **System Architecture:** Designed and implemented a complex, event-driven, and stateful application.
*   **Concurrency:** Practical application of Python's `threading` and `queue` modules for managing asynchronous operations.
*   **Process Management:** Expertise in using Python's `subprocess` module to create, monitor, and manage external processes in a secure and reliable manner.
*   **DevOps & Automation:** Created a tool that automates the software development lifecycle, demonstrating a strong understanding of automation principles.

---

## Technical Stack

-   **Backend**: Flask (Python)
-   **Frontend**: Vanilla JavaScript, Tailwind CSS
-   **AI Model**: Google Gemini (specifically `gemini-1.5-flash-latest`)
-   **Environment**: Manages a shared `venv` for all projects.

## How It Works

1.  The user creates a new project and provides a high-level prompt (e.g., "create a Flask API with a /hello endpoint").
2.  The `Agent` class is instantiated for the project.
3.  The agent enters its main loop, constructing a detailed prompt for the Gemini API that includes the main goal, file listing, active processes, and recent activity logs.
4.  The Gemini API returns a JSON object containing the agent's `thought` process and a list of `actions` (e.g., `writeFile`, `execute`).
5.  The agent parses this response and executes the actions in a secure, sandboxed manner.
6.  The UI polls the backend for status updates and displays the agent's progress in real-time.
7.  This cycle continues until the agent determines the task is complete (`finishTask`), the cycle limit is reached, or the user intervenes.

## Visuals

*Coming Soon: A video demonstrating the agent creating a simple web application from scratch.*

## Getting Started

These instructions will get you a copy of the project up and running on your local machine for development and testing purposes.

### Prerequisites

*   Python 3.8+
*   An API key for Google Gemini

### Installation

1.  **Clone the repository:**
    ```sh
    git clone https://github.com/your-username/your-repository.git
    cd your-repository/AutoAgent
    ```

2.  **Create a virtual environment and install dependencies:**
    ```sh
    python -m venv venv
    source venv/bin/activate  # On Windows, use `venv\Scripts\activate`
    pip install -r requirements.txt
    ```

3.  **Set up your environment variables:**
    Create a file named `.env` in the `AutoAgent` directory and add your Gemini API key:
    ```
    GEMINI_API_KEY="YOUR_API_KEY"
    ```

4.  **Run the application:**
    ```sh
    python app.py
    ```

5.  Open your web browser and navigate to `http://127.0.0.1:5001`.
