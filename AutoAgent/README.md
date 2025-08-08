# AutoAgent - Autonomous AI Agent Framework

AutoAgent is a sophisticated, self-contained web application that provides a user interface for managing and interacting with an autonomous AI software engineering agent. It allows a user to define a high-level software development task, and the AI agent will then autonomously create a plan, write code, execute it, and debug its own work until the goal is achieved.

## Core Features

-   **Autonomous Task Completion**: The agent operates on an OODA (Observe, Orient, Decide, Act) loop. It analyzes the user's goal, observes the current state of the project (file listing, process output), and decides on a course of action, which it executes through writing files or running commands.
-   **Web-Based UI**: The entire system is managed through a clean, intuitive web interface built with Flask and Tailwind CSS. It provides a real-time view of the agent's activity, the project's file system, running processes, and the agent's thought process.
-   **Project-Based Workflow**: Each task is managed as a separate project. The agent's state, including its history, files, and running processes, is sandboxed within its project directory.
-   **Interactive Feedback Loop**: While the agent is autonomous, the user can pause its operation, provide feedback or guidance, and then resume the task.
-   **Code Execution and Environment Management**: The agent executes code within a shared Python virtual environment, which it manages automatically. It can install dependencies from a `requirements.txt` file, run scripts, and start servers.
-   **Stateful and Persistent**: The agent's progress and history are saved to a `.agent_state.json` file within the project, allowing tasks to be stopped and resumed later.

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
