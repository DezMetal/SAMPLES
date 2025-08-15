import os
import json
import subprocess
import time
import sys
import shutil
import venv
import logging
import shlex
import re
import uuid
import hashlib
import threading
from typing import Dict, Any, List, Tuple, Optional
from queue import Queue, Empty

# --- Third-party libraries ---
try:
    from dotenv import load_dotenv
    from flask import Flask, request, jsonify, render_template, send_from_directory
    import google.generativeai as genai
except ImportError as e:
    print(f"FATAL ERROR: A required library is not installed. Please run 'pip install google-generativeai python-dotenv Flask'. Details: {e}")
    sys.exit(1)

# --- Basic Configuration ---
load_dotenv()
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - [%(funcName)s] %(message)s')

# --- Constants & Configuration ---
BASE_PROJECTS_DIR = os.path.abspath("agent_projects")
SHARED_VENV_PATH = os.path.join(BASE_PROJECTS_DIR, "shared_agent_venv")
SHARED_TOOLS_PATH = os.path.join(BASE_PROJECTS_DIR, "tools")

# --- System Instruction for the AI Agent ---
# label: System instruction for the AI agent
SYSTEM_INSTRUCTION = """
You are an expert, autonomous software engineer agent. Your purpose is to solve complex software development tasks by writing and executing code. You are operating inside a web-based UI where a human user can observe your progress and provide feedback.

**Your Core Workflow: OODA Loop (Observe, Orient, Decide, Act)**
1.  **OBSERVE**: Critically analyze the `main_goal`, `project_file_listing`, `active_processes`, and `activity_log`. You MUST acknowledge the existing files and the user's goal in your thought process.
2.  **ORIENT**: Understand your situation. What is the most direct path to achieving the `main_goal`? If files already exist, how can you build upon them? If a server is running, what does its output tell you?
3.  **DECIDE**: Formulate a precise, step-by-step plan. **Do not default to a generic solution like making a Streamlit app unless it is explicitly requested or is the most logical tool for the job.** If a strategy fails, you MUST change your approach and explain *why* your new plan is better.
4.  **ACT**: Execute your plan using the available actions.

**Available Actions (JSON Response):**
Your response MUST be a single JSON object.
```json
{
  "thought": "Your detailed analysis and plan. I will start by analyzing the existing files to understand the current state of the project. Based on the main goal, I will then outline a plan to modify or add files to achieve the objective. I will validate my solution before finishing.",
  "actions": [
    { "type": "writeFile", "path": "path/to/file.py", "content": "Full file content." },
    { "type": "execute", "command": "python test_script.py" },
    { "type": "readFile", "path": "path/to/file.txt" },
    { "type": "requestFeedback", "details": "Use only as a last resort after multiple different strategies have failed." },
    { "type": "finishTask", "summary": "A summary of how you successfully completed and validated the task." }
  ]
}
```

**CRITICAL RULES for Success:**
- **CONTEXT IS KING**: Your primary directive is to work with the files provided in the `project_file_listing`. Your plan MUST incorporate and build upon existing code. Do not ignore the context.
- **NO LAZY FINISHES**: Do not use `finishTask` after just one or two cycles unless the goal is exceptionally trivial. A proper solution involves multiple steps: understanding, implementing, and **validating**.
- **VALIDATE YOUR WORK**: Before finishing, you MUST prove your solution works. This could mean executing a test script, writing a `README.md` explaining how to run the code, or analyzing the output of a server to confirm it's running correctly.
- **ANALYZE SERVER OUTPUT**: When running servers, you MUST check the `stdout` and `stderr` in `active_processes` in the next cycle. This is how you find the URL and diagnose errors.
- **STREAMLIT**: Only use Streamlit if it is the best tool for the job. If you do, you MUST use the `--server.headless true` flag to prevent it from getting stuck. Example: `streamlit run app.py --server.headless true`.
- **FILE PATHS**: All file paths for `writeFile` and `readFile` MUST be relative to the project root (e.g., `app.py`). Do NOT include the project folder name in the path.
"""

# --- HTML Content ---
# label: Main HTML content for the frontend UI
INDEX_HTML = """
<!DOCTYPE html>
<html lang="en" class="h-full">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Autonomous Agent UI</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Orbitron:wght@400;700&family=Roboto+Mono:wght@400;600&display=swap" rel="stylesheet">
    <style>
        :root {
            --font-header: 'Orbitron', sans-serif; --font-body: 'Roboto Mono', monospace;
            --bg-main: #f3f4f6; --bg-panel: #ffffff; --text-main: #111827;
            --text-light: #6b7280; --border-color: #e5e7eb; --accent-color: #4f46e5;
        }
        body { font-family: var(--font-header); background-color: var(--bg-main); color: var(--text-main); }
        .font-body { font-family: var(--font-body); }
        ::-webkit-scrollbar { width: 8px; }
        ::-webkit-scrollbar-track { background: var(--border-color); }
        ::-webkit-scrollbar-thumb { background: #9ca3af; border-radius: 4px; }
        .spinner-light { border-top-color: #fff; }
        @keyframes spin { to { transform: rotate(360deg); } }
        .spinner { border: 2px solid rgba(0,0,0,0.2); width: 16px; height: 16px; border-radius: 50%; border-top-color: var(--text-main); animation: spin 1s ease infinite; }
        .btn { transition: all 0.2s ease; }
        .btn:active { transform: scale(0.97); }
        .actions-bubble pre, .execution-bubble pre { white-space: pre-wrap; word-wrap: break-word; word-break: break-all; }
        .left-panel-collapsed { width: 4rem !important; }
        .left-panel-collapsed .nav-text, .left-panel-collapsed .project-list-header { display: none; }
        .left-panel-collapsed .nav-item { justify-content: center; }
        details > summary { cursor: pointer; }
        .toggle-checkbox:checked { right: 0; border-color: var(--accent-color); }
        .toggle-checkbox:checked + .toggle-label { background-color: var(--accent-color); }
    </style>
</head>
<body class="h-full">
    <div id="app" class="flex h-screen antialiased">

        <!-- Left Panel -->
        <aside id="left-panel" class="bg-gray-800 text-white p-4 flex flex-col shrink-0 transition-all duration-300 w-64">
            <div class="flex items-center justify-between mb-6">
                <div class="flex items-center nav-item">
                    <i class="fas fa-robot text-3xl text-indigo-400 mr-3"></i>
                    <h1 class="text-2xl font-bold nav-text">AutoAgent</h1>
                </div>
                <button id="toggle-nav-btn" class="text-gray-400 hover:text-white"><i class="fas fa-bars"></i></button>
            </div>
            <button id="new-project-btn" class="w-full bg-indigo-600 hover:bg-indigo-700 font-bold py-2 px-4 rounded-lg mb-4 flex items-center justify-center btn nav-item">
                <i class="fas fa-plus mr-2"></i><span class="nav-text">New Project</span>
            </button>
            <h2 class="text-xs font-bold uppercase text-gray-400 mb-2 px-2 project-list-header">Projects</h2>
            <div id="project-list" class="flex-grow overflow-y-auto pr-2"></div>
        </aside>

        <!-- Main Content -->
        <div class="flex-1 flex flex-col min-w-0">
            <main id="main-content" class="flex-grow p-4 md:p-6 flex flex-col bg-gray-100 overflow-y-auto">
                <div id="welcome-view" class="flex flex-col items-center justify-center h-full text-center">
                    <i class="fas fa-project-diagram text-6xl text-gray-400 mb-4"></i>
                    <h2 class="text-2xl font-bold text-gray-800">Welcome to AutoAgent</h2>
                    <p class="text-gray-500 font-body">Select a project or create a new one.</p>
                </div>

                <div id="project-view" class="hidden h-full flex flex-col">
                    <div id="control-header" class="bg-white rounded-lg shadow-lg p-4 mb-4 shrink-0"></div>
                    <div id="activity-feed" class="flex-grow overflow-y-auto mb-4 pr-2 font-body bg-white rounded-lg shadow-lg p-4"></div>
                    <div id="feedback-bar" class="shrink-0 pt-4">
                        <div class="flex gap-4">
                            <textarea id="feedback-input" class="w-full bg-white border border-gray-300 rounded-lg p-3 focus:ring-2 focus:ring-indigo-500 focus:outline-none font-body shadow-md" rows="1" placeholder="Provide guidance and press Enter..."></textarea>
                            <button id="send-feedback-btn" class="bg-indigo-600 hover:bg-indigo-700 text-white font-bold py-2 px-6 rounded-lg btn shadow-md">Send</button>
                        </div>
                    </div>
                </div>
            </main>
        </div>

        <!-- Right Panel -->
        <aside id="right-panel" class="w-96 bg-white p-4 flex-col shrink-0 border-l border-gray-200 shadow-lg hidden lg:flex">
            <div id="workspace-container" class="flex flex-col h-full">
                <h2 class="text-lg font-bold uppercase text-gray-800 mb-4">Workspace</h2>
                <div id="active-processes-container" class="mb-4"></div>
                <div id="file-listing" class="flex-grow overflow-y-auto font-mono text-sm pr-2 bg-gray-50 p-2 rounded-md min-h-0"></div>
                <div id="settings-container" class="pt-4 mt-4 border-t border-gray-200"></div>
                <div id="import-container" class="pt-4 mt-4 border-t border-gray-200">
                    <label class="text-sm font-bold text-gray-600">Import Source</label>
                    <div class="flex gap-2 mt-1">
                        <input id="source-path" type="text" placeholder="Absolute path to file/folder" class="w-full bg-gray-100 border border-gray-300 rounded-lg p-2 font-body text-xs">
                        <button id="import-btn" class="bg-gray-600 hover:bg-gray-700 text-white font-bold p-2 rounded-lg btn"><i class="fas fa-upload"></i></button>
                    </div>
                </div>
                <div id="project-actions" class="pt-4 mt-4 border-t border-gray-200 space-y-2"></div>
            </div>
        </aside>
    </div>

    <!-- Modals -->
    <div id="new-project-modal" class="fixed inset-0 bg-black bg-opacity-60 flex items-center justify-center hidden z-50">
        <div class="bg-white rounded-lg shadow-2xl p-8 w-full max-w-2xl text-gray-800">
            <h2 class="text-2xl font-bold mb-4">Create New Project</h2>
            <div class="mb-4">
                <label for="new-project-name" class="block text-sm font-medium text-gray-600 mb-1 font-body">Project Name</label>
                <input type="text" id="new-project-name" class="w-full bg-gray-100 border border-gray-300 rounded-lg p-2 focus:ring-2 focus:ring-indigo-500 focus:outline-none font-body" placeholder="e.g., flask-api-hello-world">
            </div>
            <div class="mb-6">
                <label for="new-project-prompt" class="block text-sm font-medium text-gray-600 mb-1 font-body">Main Goal</label>
                <textarea id="new-project-prompt" class="w-full bg-gray-100 border border-gray-300 rounded-lg p-2 focus:ring-2 focus:ring-indigo-500 focus:outline-none font-body" rows="5" placeholder="Describe the task for the agent..."></textarea>
            </div>
            <div class="flex justify-end gap-4">
                <button id="cancel-new-project" class="bg-gray-200 hover:bg-gray-300 text-gray-800 font-bold py-2 px-4 rounded-lg transition btn">Cancel</button>
                <button id="confirm-new-project" class="bg-indigo-600 hover:bg-indigo-700 text-white font-bold py-2 px-4 rounded-lg transition btn">Create</button>
            </div>
        </div>
    </div>
    <div id="file-content-modal" class="fixed inset-0 bg-black bg-opacity-60 flex items-center justify-center hidden z-50">
        <div class="bg-white rounded-lg shadow-2xl p-6 w-full max-w-4xl h-5/6 flex flex-col">
            <div class="flex justify-between items-center mb-4"><h2 id="file-modal-title" class="text-xl font-bold text-gray-800 font-mono"></h2><button id="close-file-modal" class="text-gray-400 hover:text-gray-800 text-2xl btn">&times;</button></div>
            <div class="flex-grow bg-gray-900 text-white rounded-md overflow-auto"><pre><code id="file-modal-content" class="text-sm p-4 block whitespace-pre-wrap font-body"></code></pre></div>
        </div>
    </div>

    <script>
    // label: Main application script
    document.addEventListener('DOMContentLoaded', () => {
        // label: Constants and state initialization
        const API_BASE = 'http://127.0.0.1:5001/api';
        let state = {
            projects: [],
            currentProject: null,
            agentStatus: {},
            isCycleRunning: false,
            autonomousState: 'idle', // 'idle', 'running', 'paused'
            statusPollId: null,
            openDetails: new Set(),
            openProcessDetails: new Set(),
        };

        // label: DOM element selectors
        const D = (id) => document.getElementById(id);
        const projectList = D('project-list'), newProjectBtn = D('new-project-btn'), newProjectModal = D('new-project-modal'),
              cancelNewProjectBtn = D('cancel-new-project'), confirmNewProjectBtn = D('confirm-new-project'),
              welcomeView = D('welcome-view'), projectView = D('project-view'), rightPanel = D('right-panel'),
              feedbackInput = D('feedback-input'), sendFeedbackBtn = D('send-feedback-btn'),
              fileContentModal = D('file-content-modal'), closeFileModalBtn = D('close-file-modal'),
              activityFeed = D('activity-feed'), controlHeader = D('control-header'), fileListing = D('file-listing'),
              projectActions = D('project-actions'), activeProcessesContainer = D('active-processes-container'),
              importBtn = D('import-btn'), sourcePathInput = D('source-path'), leftPanel = D('left-panel'),
              toggleNavBtn = D('toggle-nav-btn'), settingsContainer = D('settings-container');

        // label: API helper object
        const api = {
            get: (endpoint) => fetch(`${API_BASE}/${endpoint}`).then(res => res.ok ? res.json() : Promise.reject(res)),
            post: (endpoint, body) => fetch(`${API_BASE}/${endpoint}`, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(body) }).then(res => res.ok ? res.json() : Promise.reject(res)),
            delete: (endpoint) => fetch(`${API_BASE}/${endpoint}`, { method: 'DELETE' }).then(res => res.ok ? res.json() : Promise.reject(res)),
        };

        // label: Renders the list of projects
        const renderProjectList = () => {
            projectList.innerHTML = state.projects.length === 0 ? '<p class="text-sm text-gray-400 px-2 nav-text">No projects yet.</p>' : '';
            state.projects.forEach(p => {
                const el = document.createElement('div');
                el.className = `p-2 rounded-lg cursor-pointer mb-1 flex items-center nav-item ${state.currentProject === p.name ? 'bg-indigo-500' : 'hover:bg-gray-700'}`;
                el.innerHTML = `<i class="fas fa-folder mr-3"></i><span class="nav-text">${p.name}</span>`;
                el.onclick = () => selectProject(p.name);
                projectList.appendChild(el);
            });
        };

        // label: Renders the main control header
        const renderControlHeader = () => {
            if (!state.currentProject) { controlHeader.innerHTML = ''; return; }
            const status = state.agentStatus;
            const maxCycles = status.max_cycles || 15;
            state.autonomousState = status.autonomous_state || 'idle';

            let statusText = '';
            if (status.waiting_for_input) {
                statusText = `<div class="text-yellow-600 font-bold font-body text-sm mt-2"><i class="fas fa-pause-circle mr-2"></i>Agent is waiting for your feedback.</div>`;
            } else if (status.task_completed) {
                statusText = `<div class="text-green-600 font-bold font-body text-sm mt-2"><i class="fas fa-check-circle mr-2"></i>Task completed.</div>`;
            } else if (status.cycle_count >= maxCycles && state.autonomousState !== 'running') {
                statusText = `<div class="text-red-600 font-bold font-body text-sm mt-2"><i class="fas fa-stop-circle mr-2"></i>Cycle limit reached. Resume to add more cycles.</div>`;
            } else if (state.autonomousState === 'running' || status.is_cycle_running) {
                 statusText = `<div class="text-blue-600 font-bold font-body text-sm mt-2"><i class="fas fa-play-circle mr-2"></i>Autonomous mode running...</div>`;
            } else if (state.autonomousState === 'paused') {
                statusText = `<div class="text-gray-600 font-bold font-body text-sm mt-2"><i class="fas fa-pause-circle mr-2"></i>Autonomous mode paused.</div>`;
            } else if (state.autonomousState === 'idle') {
                statusText = `<div class="text-gray-600 font-bold font-body text-sm mt-2"><i class="fas fa-hourglass-start mr-2"></i>Agent idle. Engage to begin.</div>`;
            }

            const cycleDisplay = `<span class="font-body text-sm text-gray-500">Cycle ${status.cycle_count || 0} / ${maxCycles}</span>`;

            controlHeader.innerHTML = `
                <div class="flex justify-between items-start">
                    <div>
                        <h2 class="text-2xl font-bold text-gray-800">${status.project_name}</h2>
                        <p class="text-sm text-gray-500 max-w-2xl truncate font-body">${status.initial_prompt}</p>
                        ${statusText}
                    </div>
                    <div class="flex flex-col items-end gap-2">
                         <div class="flex items-center gap-4">
                            <div class="flex items-center gap-2 font-body text-sm">
                                <label for="max-cycles" class="text-gray-600">Max Cycles:</label>
                                <input id="max-cycles" type="number" value="${maxCycles}" class="bg-gray-100 w-16 text-center rounded-md border border-gray-300 p-1">
                            </div>
                            <button id="play-pause-btn" class="font-bold py-2 px-4 rounded-lg flex items-center justify-center w-36 btn"></button>
                        </div>
                        ${cycleDisplay}
                    </div>
                </div>`;
            D('play-pause-btn').onclick = handlePlayPause;
            D('max-cycles').onchange = () => handleUpdateSettings({ max_cycles: parseInt(D('max-cycles').value, 10) });
            updatePlayPauseButton();
            feedbackInput.disabled = !!status.is_cycle_running;
            sendFeedbackBtn.disabled = !!status.is_cycle_running;
            if (status.waiting_for_input && !status.is_cycle_running) {
                feedbackInput.focus();
            }
        };

        // label: Renders the settings panel
        const renderSettings = () => {
            if (!state.currentProject || !state.agentStatus.settings) { settingsContainer.innerHTML = ''; return; }
            const settings = state.agentStatus.settings;
            settingsContainer.innerHTML = `
                <h3 class="text-sm font-bold uppercase text-gray-600 mb-2">Agent Settings</h3>
                <div class="space-y-3 font-body text-sm">
                    <div class="flex items-center justify-between">
                        <label for="log-raw-model-io" class="text-gray-700">Log Raw Model I/O</label>
                        <div class="relative inline-block w-10 mr-2 align-middle select-none transition duration-200 ease-in">
                            <input type="checkbox" name="log_raw_model_io" id="log-raw-model-io" class="toggle-checkbox absolute block w-6 h-6 rounded-full bg-white border-4 appearance-none cursor-pointer" ${settings.log_raw_model_io ? 'checked' : ''}/>
                            <label for="log-raw-model-io" class="toggle-label block overflow-hidden h-6 rounded-full bg-gray-300 cursor-pointer"></label>
                        </div>
                    </div>
                    <div class="flex items-center justify-between">
                        <label for="max-log-entries" class="text-gray-700">Max Log Entries</label>
                        <input id="max-log-entries" type="number" value="${settings.max_log_entries_in_prompt}" class="bg-gray-100 w-20 text-center rounded-md border border-gray-300 p-1 text-xs">
                    </div>
                    <div class="flex items-center justify-between">
                        <label for="cycle-delay-ms" class="text-gray-700">Cycle Delay (ms)</label>
                        <input id="cycle-delay-ms" type="number" value="${settings.cycle_delay_ms}" class="bg-gray-100 w-20 text-center rounded-md border border-gray-300 p-1 text-xs">
                    </div>
                </div>
            `;
            D('log-raw-model-io').onchange = (e) => handleUpdateSettings({ log_raw_model_io: e.target.checked });
            D('max-log-entries').onchange = (e) => handleUpdateSettings({ max_log_entries_in_prompt: parseInt(e.target.value, 10) });
            D('cycle-delay-ms').onchange = (e) => handleUpdateSettings({ cycle_delay_ms: parseInt(e.target.value, 10) });
        };

        // label: Renders project action buttons
        const renderProjectActions = () => {
            if (!state.currentProject) { projectActions.innerHTML = ''; return; }
            projectActions.innerHTML = `
                <button id="finalize-btn" class="w-full bg-green-500 hover:bg-green-600 text-white font-bold py-2 px-4 rounded-lg btn"><i class="fas fa-check-circle mr-2"></i>Finalize Task</button>
                <button id="cleanup-btn" class="w-full bg-yellow-500 hover:bg-yellow-600 text-gray-800 font-bold py-2 px-4 rounded-lg btn"><i class="fas fa-broom mr-2"></i>Cleanup Task</button>
                <button id="delete-project-btn" class="w-full bg-red-600 hover:bg-red-700 text-white font-bold py-2 px-4 rounded-lg btn"><i class="fas fa-trash mr-2"></i>Delete Project</button>
            `;
            D('finalize-btn').onclick = handleFinalize;
            D('cleanup-btn').onclick = handleCleanup;
            D('delete-project-btn').onclick = handleDeleteProject;
        };

        // label: Updates the play/pause button UI
        const updatePlayPauseButton = () => {
            const btn = D('play-pause-btn');
            if (!btn) return;

            const isCycleRunning = state.agentStatus.is_cycle_running || state.isCycleRunning;
            btn.disabled = isCycleRunning;

            let icon, text, color, textColor = 'text-white';

            if (isCycleRunning) {
                text = 'Running...';
                icon = 'fa-spinner fa-spin';
                color = 'bg-indigo-700';
            } else if (state.agentStatus.task_completed) {
                text = 'Re-engage';
                icon = 'fa-redo';
                color = 'bg-blue-600 hover:bg-blue-700';
                btn.disabled = false;
            } else if (state.agentStatus.waiting_for_input) {
                text = 'Resume';
                icon = 'fa-play';
                color = 'bg-green-500 hover:bg-green-600';
            } else if (state.autonomousState === 'running') {
                text = 'Pause';
                icon = 'fa-pause';
                color = 'bg-yellow-500 hover:bg-yellow-600';
            } else { // idle or paused
                text = 'Engage';
                icon = 'fa-play';
                color = 'bg-indigo-600 hover:bg-indigo-700';
            }

            btn.innerHTML = `<i class="fas ${icon} mr-2"></i>${text}`;
            btn.className = `font-bold py-2 px-4 rounded-lg flex items-center justify-center w-36 btn ${color} ${textColor}`;
        };

        // label: Renders the agent's activity feed with state preservation
        const renderActivityFeed = () => {
            const history = state.agentStatus.cycle_history || [];

            const currentOpenDetails = new Set();
            activityFeed.querySelectorAll('details[open]').forEach(el => {
                const key = `${el.parentElement.dataset.cycleCount}-${el.querySelector('summary').textContent}`;
                currentOpenDetails.add(key);
            });
            state.openDetails = currentOpenDetails;

            activityFeed.innerHTML = ''; 
            if (history.length === 0) {
                activityFeed.innerHTML = '<div class="text-center text-gray-400 py-8">Agent is ready. Engage to begin.</div>';
                return;
            }

            history.forEach(cycle => {
                const cycleEl = document.createElement('div');
                cycleEl.className = 'mb-6';
                cycleEl.dataset.cycleCount = cycle.cycle_count;

                const feedbackHtml = cycle.feedback_received ? `<div class="p-3 bg-yellow-100 border border-yellow-200 rounded-md"><strong><i class="fas fa-comment-dots mr-2 text-yellow-500"></i>Human Feedback:</strong><div class="whitespace-pre-wrap mt-1 text-gray-700">${cycle.feedback_received}</div></div>` : '';
                const thoughtHtml = `<div class="p-3 bg-blue-100 border border-blue-200 rounded-md mt-2"><strong><i class="fas fa-lightbulb mr-2 text-blue-500"></i>Agent's Plan:</strong><div class="whitespace-pre-wrap mt-1 text-gray-700">${cycle.thought}</div></div>`;

                let actionsHtml = '';
                if(cycle.actions_taken && cycle.actions_taken.length > 0) {
                    const key = `${cycle.cycle_count}-Actions Taken`;
                    const isOpen = state.openDetails.has(key) ? 'open' : '';
                    const actionItems = cycle.actions_taken.map(action => {
                        const params = { ...action.action }; delete params.type;
                        const content = params.content ? `<pre class="text-xs p-2 bg-gray-800 text-white rounded-md mt-1">${JSON.stringify(params.content, null, 2)}</pre>` : ``;
                        return `<div class="mt-2 text-sm"><p class="font-bold text-purple-600">${action.action.type}: <span class="font-mono text-gray-700">${params.path || params.command || ''}</span></p>${content}</div>`;
                    }).join('');
                    actionsHtml = `<details ${isOpen} class="p-3 bg-purple-100 border border-purple-200 rounded-md mt-2"><summary class="font-bold"><i class="fas fa-cogs mr-2 text-purple-500"></i>Actions Taken</summary><div class="mt-2">${actionItems}</div></details>`;
                }

                let executionReportHtml = '';
                if (cycle.execution_report) {
                    const key = `${cycle.cycle_count}-Execution Report`;
                    const isOpen = state.openDetails.has(key) ? 'open' : '';
                    const isError = /failure/i.test(cycle.execution_report) || /error/i.test(cycle.execution_report) || /timeout/i.test(cycle.execution_report) || /exited early/i.test(cycle.execution_report);
                    executionReportHtml = `<details ${isOpen} class="p-3 bg-gray-800 rounded-md mt-2 text-white"><summary class="font-bold"><i class="fas fa-terminal mr-2 text-gray-400"></i>Execution Report</summary><pre class="text-xs mt-2 ${isError ? 'text-red-400' : 'text-green-400'}">${cycle.execution_report}</pre></details>`;
                }

                let modelIoHtml = '';
                if (cycle.log_entries) {
                    const modelLogs = cycle.log_entries.filter(log => log.startsWith('--- MODEL'));
                    if (modelLogs.length > 0) {
                        const key = `${cycle.cycle_count}-Model I/O`;
                        const isOpen = state.openDetails.has(key) ? 'open' : '';
                        modelIoHtml = `<details ${isOpen} class="p-3 bg-gray-200 rounded-md mt-2 text-gray-800"><summary class="font-bold"><i class="fas fa-exchange-alt mr-2 text-gray-500"></i>Model I/O</summary><pre class="text-xs mt-2 whitespace-pre-wrap">${modelLogs.join('\\n\\n')}</pre></details>`;
                    }
                }

                cycleEl.innerHTML = `<div class="flex items-center gap-4 mb-2"><span class="text-indigo-600 font-bold">Cycle ${cycle.cycle_count}</span><hr class="flex-grow border-gray-200"></div>${feedbackHtml}${thoughtHtml}${actionsHtml}${executionReportHtml}${modelIoHtml}`;
                activityFeed.appendChild(cycleEl);
            });
        };

        // label: Renders the file system view
        const renderFileSystem = () => {
            if (!state.agentStatus.file_listing) { fileListing.innerHTML = '<p class="text-gray-500">No files yet.</p>'; return; }
            const fileHtml = state.agentStatus.file_listing.split('\\n').map(line => {
                const trimmedLine = line.trim();
                const isFile = !line.trim().endsWith('/') && trimmedLine.length > 0;
                if (isFile) {
                    const isHtml = trimmedLine.endsWith('.html');
                    const isPy = trimmedLine.endsWith('.py');
                    const filePath = trimmedLine.replace(/^[\\\\/]/, '');
                    const fullPath = `agent_projects/${state.currentProject}/${filePath}`;
                    return `<div class="flex items-center justify-between hover:bg-gray-200 rounded p-1 group">
                                <span class="cursor-pointer truncate" onclick="window.app.viewFile('${filePath}')">${line}</span>
                                <div class="hidden group-hover:flex items-center gap-2">
                                    ${isPy ? `<i class="fas fa-play-circle text-green-500 cursor-pointer" title="Execute" onclick="window.app.executeFile('python ${filePath}')"></i>` : ''}
                                    ${isHtml ? `<a href="/${fullPath}" target="_blank"><i class="fas fa-external-link-alt text-blue-500 cursor-pointer" title="Launch in new tab"></i></a>` : ''}
                                </div>
                            </div>`;
                }
                return `<div class="text-gray-400">${line}</div>`;
            }).join('');
            fileListing.innerHTML = `<div class="whitespace-pre text-gray-700">${fileHtml}</div>`;
        };

        // label: Renders the list of active processes
        const renderActiveProcesses = () => {
            // FIX: Preserve open state for process details
            const currentOpenProcessDetails = new Set();
            activeProcessesContainer.querySelectorAll('details[open]').forEach(el => {
                const key = el.querySelector('summary').textContent;
                const pid = el.closest('[data-pid]').dataset.pid;
                currentOpenProcessDetails.add(`${pid}-${key}`);
            });
            state.openProcessDetails = currentOpenProcessDetails;

            const processes = state.agentStatus.active_processes || {};
            const hasProcesses = Object.keys(processes).length > 0;

            if (!hasProcesses) {
                activeProcessesContainer.innerHTML = '';
                return;
            }
            const processItems = Object.entries(processes).map(([pid, info]) => {
                const webLink = info.url ? `<a href="${info.url}" target="_blank" title="Open App at ${info.url}"><i class="fas fa-external-link-alt text-blue-500 ml-2 hover:text-blue-700"></i></a>` : '';

                const stdoutOpen = state.openProcessDetails.has(`${pid}-STDOUT`) ? 'open' : '';
                const stderrOpen = state.openProcessDetails.has(`${pid}-STDERR`) ? 'open' : '';

                const stdoutHtml = info.stdout ? `<details ${stdoutOpen} class="mt-2"><summary class="text-gray-600 font-bold text-sm">STDOUT</summary><pre class="text-xs bg-gray-700 text-white p-2 rounded-md overflow-auto max-h-48">${info.stdout}</pre></details>` : '';
                const stderrHtml = info.stderr ? `<details ${stderrOpen} class="mt-2"><summary class="text-gray-600 font-bold text-sm">STDERR</summary><pre class="text-xs bg-red-800 text-white p-2 rounded-md overflow-auto max-h-48">${info.stderr}</pre></details>` : '';

                return `
                <div class="flex flex-col bg-gray-100 p-2 rounded-md mb-2" data-pid="${pid}">
                    <div class="flex items-center justify-between">
                        <div class="text-xs truncate">
                            <span class="font-bold">${pid.substring(0,8)}</span>: ${info.command}
                        </div>
                        <div class="flex items-center">
                            ${webLink}
                            <button class="text-blue-500 hover:text-blue-700 ml-2" title="Restart" onclick="window.app.restartProcess('${pid}')"><i class="fas fa-sync-alt"></i></button>
                            <button class="text-red-500 hover:text-red-700 ml-2" title="Terminate" onclick="window.app.terminateProcess('${pid}')"><i class="fas fa-stop-circle"></i></button>
                        </div>
                    </div>
                    ${stdoutHtml}
                    ${stderrHtml}
                </div>
            `}).join('');

            activeProcessesContainer.innerHTML = `
                <div class="flex justify-between items-center mb-2">
                    <h3 class="text-sm font-bold uppercase text-gray-600">Active Processes</h3>
                    <button id="terminate-all-btn" class="text-xs bg-red-500 text-white font-bold py-1 px-2 rounded hover:bg-red-600 btn">Terminate All</button>
                </div>
                <div class="space-y-2">${processItems}</div>
            `;
            D('terminate-all-btn').onclick = handleTerminateAll;
        };

        // label: Loads all projects from the backend
        const loadProjects = async () => { try { state.projects = await api.get('projects'); renderProjectList(); } catch (err) { console.error("Failed to load projects", err); }};

        // label: Selects a project to view
        const selectProject = async (projectName) => {
            if (state.isCycleRunning) return;
            state.currentProject = projectName;
            state.openDetails.clear();
            state.openProcessDetails.clear();

            clearInterval(state.statusPollId);
            welcomeView.classList.add('hidden'); projectView.classList.remove('hidden'); rightPanel.classList.remove('hidden');
            renderProjectList();
            await updateAgentStatus();
            state.statusPollId = setInterval(updateAgentStatus, 3000);
        };

        // label: Fetches and updates the agent status, and triggers autonomous cycle if needed
        const updateAgentStatus = async () => {
            if (!state.currentProject) return;
            try {
                const newStatus = await api.get(`agent/status?project_name=${state.currentProject}`);

                state.agentStatus = newStatus;
                state.autonomousState = newStatus.autonomous_state;

                const scrollPosition = activityFeed.scrollTop;
                const isScrolledToBottom = activityFeed.scrollHeight - activityFeed.clientHeight <= activityFeed.scrollTop + 1;

                renderControlHeader();
                renderProjectActions();
                renderFileSystem();
                renderActiveProcesses();
                renderSettings();
                renderActivityFeed();

                if (isScrolledToBottom) {
                    activityFeed.scrollTop = activityFeed.scrollHeight;
                } else {
                    activityFeed.scrollTop = scrollPosition;
                }

                if (
                    state.autonomousState === 'running' &&
                    !newStatus.is_cycle_running &&
                    !newStatus.task_completed &&
                    !newStatus.waiting_for_input &&
                    newStatus.cycle_count < newStatus.max_cycles
                ) {
                    triggerCycle('');
                }

            } catch (err) {
                console.error("Failed to update agent status", err);
                clearInterval(state.statusPollId);
                state.currentProject = null;
                welcomeView.classList.remove('hidden'); projectView.classList.add('hidden'); rightPanel.classList.add('hidden');
                loadProjects();
            }
        };

        // label: Triggers a single agent cycle
        const triggerCycle = async (feedback = '') => {
            if (!state.currentProject || state.isCycleRunning) return;

            state.isCycleRunning = true;
            updatePlayPauseButton();

            try {
                await api.post('agent/run-cycle', { project_name: state.currentProject, feedback });
            } catch (err) {
                console.error("Failed to initiate cycle", err);
            } finally {
                state.isCycleRunning = false;
            }
        };

        // label: Handles play/pause button clicks
        const handlePlayPause = async () => {
            if (state.agentStatus.is_cycle_running) return;

            // FIX: Simplified resume/re-engage logic
            if (state.autonomousState === 'running') {
                 await handleUpdateSettings({ autonomous_state: 'paused' });
            } else { // Covers paused, idle, and completed states
                if (confirm("Engage or resume this task?")) {
                    try {
                        await api.post('agent/resume', { project_name: state.currentProject });
                        await updateAgentStatus();
                    } catch (e) { console.error("Failed to resume task", e); }
                }
            }
        };

        // label: Handles sending user feedback
        const handleSendFeedback = async () => {
            const feedback = feedbackInput.value.trim();
            if (feedback && !state.agentStatus.is_cycle_running) {
                feedbackInput.value = '';
                try {
                    // FIX: Use the resume endpoint to handle feedback submission
                    await api.post('agent/resume', { project_name: state.currentProject, feedback: feedback });
                    await updateAgentStatus(); // Refresh immediately to show feedback log
                } catch (e) { console.error("Failed to send feedback and resume", e); }
            }
        };

        // label: Handles updating agent settings
        const handleUpdateSettings = async (settings) => {
             if (!state.currentProject) return;
             try {
                 await api.post('agent/update-settings', { project_name: state.currentProject, settings: settings });
                 await updateAgentStatus();
             } catch (err) {
                 console.error("Failed to update settings", err);
             }
        };

        // label: Handles creating a new project
        const handleCreateProject = async () => {
            const name = D('new-project-name').value.trim(), prompt = D('new-project-prompt').value.trim();
            if (!name || !prompt) { alert("Project name and prompt are required."); return; }
            try { await api.post('projects', { project_name: name, prompt }); closeNewProjectModal(); await loadProjects(); await selectProject(name); }
            catch (err) { console.error("Failed to create project", err); }
        };

        // label: Handles deleting a project
        const handleDeleteProject = async () => {
            if (!state.currentProject || !confirm(`Delete "${state.currentProject}"? This will remove all files.`)) return;
            try {
                clearInterval(state.statusPollId);
                await api.delete(`projects/${state.currentProject}`);
                state.currentProject = null;
                state.agentStatus = {};
                state.openDetails.clear();
                state.openProcessDetails.clear();
                activityFeed.innerHTML = '';
                welcomeView.classList.remove('hidden'); projectView.classList.add('hidden'); rightPanel.classList.add('hidden');
                await loadProjects();
            } catch(err) { console.error("Failed to delete project", err); }
        };

        // label: Handles cleaning up a project
        const handleCleanup = async () => {
            if (!state.currentProject || !confirm(`Cleanup "${state.currentProject}"? This will reset the agent's progress but keep the files.`)) return;
            try {
                await api.post('agent/reset', { project_name: state.currentProject });
                state.openDetails.clear();
                state.openProcessDetails.clear();
                await updateAgentStatus();
            }
            catch(e) { console.error("Cleanup failed", e); }
        };

        // label: Handles finalizing a task
        const handleFinalize = async () => {
            if (!state.currentProject || !confirm(`Finalize task for "${state.currentProject}"?`)) return;
            try {
                await api.post('agent/finalize', { project_name: state.currentProject });
                await updateAgentStatus();
            }
            catch(e) { console.error("Finalize failed", e); }
        };

        // label: Handles terminating a process
        const handleTerminate = async (pid) => {
            try { await api.post('agent/terminate', { project_name: state.currentProject, pid }); await updateAgentStatus(); }
            catch(e) { console.error("Terminate failed", e); }
        };

        const handleTerminateAll = async () => {
            if (!state.currentProject || !confirm(`Terminate all active processes for "${state.currentProject}"?`)) return;
            try { await api.post('agent/terminate-all', { project_name: state.currentProject }); await updateAgentStatus(); }
            catch(e) { console.error("Terminate all failed", e); }
        };

        const restartProcess = async (pid) => {
             if (!state.currentProject || !confirm(`Restart process ${pid.substring(0,8)}?`)) return;
            try { await api.post('agent/restart-process', { project_name: state.currentProject, pid: pid }); await updateAgentStatus(); }
            catch(e) { console.error("Restart failed", e); }
        }

        // label: Executes a file from the UI
        const executeFile = async (command) => {
            try {
                await api.post('agent/execute', { project_name: state.currentProject, command });
                await updateAgentStatus();
            }
            catch(e) { console.error("Execute failed", e); }
        };

        // label: Handles importing source files/folders
        const handleImport = async () => {
            const sourcePath = sourcePathInput.value.trim();
            if (!sourcePath) { alert('Please provide a source path.'); return; }
            try {
                await api.post('agent/import-source', { project_name: state.currentProject, source_path: sourcePath });
                sourcePathInput.value = '';
                await updateAgentStatus();
            } catch(e) { console.error("Import failed", e); alert('Failed to import source.'); }
        };

        // label: Modal control functions
        const openNewProjectModal = () => { D('new-project-name').value = ''; D('new-project-prompt').value = ''; newProjectModal.classList.remove('hidden'); };
        const closeNewProjectModal = () => newProjectModal.classList.add('hidden');
        const viewFile = async (path) => {
            try { const data = await api.get(`agent/file-content?project_name=${state.currentProject}&path=${path}`); D('file-modal-title').textContent = data.path; D('file-modal-content').textContent = data.content; fileContentModal.classList.remove('hidden'); }
            catch (err) { console.error(`Failed to get content for ${path}`, err); }
        };
        const closeFileModal = () => fileContentModal.classList.add('hidden');

        // label: Initial event listeners setup
        newProjectBtn.onclick = openNewProjectModal;
        cancelNewProjectBtn.onclick = closeNewProjectModal;
        confirmNewProjectBtn.onclick = handleCreateProject;
        sendFeedbackBtn.onclick = handleSendFeedback;
        feedbackInput.addEventListener('keydown', (e) => { if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); handleSendFeedback(); } });
        closeFileModalBtn.onclick = closeFileModal;
        importBtn.onclick = handleImport;
        toggleNavBtn.onclick = () => leftPanel.classList.toggle('left-panel-collapsed');

        // label: Expose functions to global scope for inline HTML calls
        window.app = { viewFile, executeFile, terminateProcess: handleTerminate, restartProcess };
        // label: Initial project load
        loadProjects();
    });
    </script>
</body>
</html>
"""

# label: Main application configuration
CONFIG: Dict[str, Any] = {
    "gemini_api_key": os.environ.get("GEMINI_API_KEY"),
    "model_name": "gemini-1.5-flash-latest",
    "system_instruction": SYSTEM_INSTRUCTION,
    "base_projects_dir": BASE_PROJECTS_DIR,
}


# --- Helper function for threaded stream reading ---
def _stream_reader(stream, queue):
    """Reads a stream line by line and puts lines into a queue."""
    try:
        for line in iter(stream.readline, ''):
            queue.put(line)
    except Exception as e:
        logging.warning(f"Stream reader thread encountered an error: {e}")
    finally:
        stream.close()


# --- Agent Class ---
# label: Main class for the autonomous agent
class Agent:
    # label: Agent class constructor
    def __init__(self, project_name: str, venv_path: str, tools_path: str, config: Dict[str, Any]):
        self.project_name = project_name
        self.config = config
        self.project_path = os.path.join(config["base_projects_dir"], project_name)
        self.venv_path = venv_path
        self.tools_path = tools_path
        self.full_cycle_history: List[Dict[str, Any]] = []
        self.task_completed = False
        self.waiting_for_input = False
        self.cycle_count = 0
        self.initial_prompt = ""
        self.current_cycle_logs: List[str] = []
        self.requirements_hash = None
        self.max_cycles = 15
        self.autonomous_state = 'idle'  # 'idle', 'running', 'paused'
        self.active_processes: Dict[str, Any] = {}
        self.activity_log: List[Dict[str, Any]] = []
        self.settings: Dict[str, Any] = {
            "log_raw_model_io": False,
            "max_log_entries_in_prompt": 20,
            "cycle_delay_ms": 1500,  # FIX: Add cycle delay setting
        }
        self.lock = threading.RLock()
        self.is_cycle_running = False
        self._setup_workspace()
        self.load_project_state()

    # label: Sets up the agent's workspace directory
    def _setup_workspace(self):
        os.makedirs(self.project_path, exist_ok=True)
        os.makedirs(self.tools_path, exist_ok=True)

    # label: Gets the path to the agent's state file
    def _get_state_file_path(self) -> str:
        return os.path.join(self.project_path, '.agent_state.json')

    # label: Adds an event to the persistent activity log
    def _add_to_activity_log(self, summary: str):
        with self.lock:
            logging.info(f"Project '{self.project_name}': {summary}")
            self.activity_log.append({"timestamp": time.time(), "summary": summary})
            self.save_project_state()

    # label: Loads the agent's state from a file
    def load_project_state(self):
        state_path = self._get_state_file_path()
        if os.path.exists(state_path):
            try:
                with open(state_path, 'r', encoding='utf-8') as f:
                    state = json.load(f)
                with self.lock:
                    self.initial_prompt = state.get('initial_prompt', '')
                    self.full_cycle_history = state.get('full_cycle_history', [])
                    self.task_completed = state.get('task_completed', False)
                    self.cycle_count = state.get('cycle_count', 0)
                    self.waiting_for_input = state.get('waiting_for_input', False)
                    self.requirements_hash = state.get('requirements_hash', None)
                    self.max_cycles = state.get('max_cycles', 15)
                    self.autonomous_state = state.get('autonomous_state', 'idle')
                    self.activity_log = state.get('activity_log', [])
                    loaded_settings = state.get('settings', {})
                    self.settings.update(loaded_settings)
                    if state.get('is_cycle_running', False):
                        logging.warning(f"Project '{self.project_name}' was found in a running state. Resetting to prevent being stuck.")
                        self.is_cycle_running = False
                        self._add_to_activity_log("Agent recovered from a stale 'running' state.")

            except (json.JSONDecodeError, IOError) as e:
                logging.error(f"Error loading state for {self.project_name}, resetting: {e}")
                self.reset_task()

    # label: Saves the agent's state to a file
    def save_project_state(self):
        with self.lock:
            os.makedirs(self.project_path, exist_ok=True)
            state = {
                'project_name': self.project_name, 'initial_prompt': self.initial_prompt,
                'cycle_count': self.cycle_count, 'task_completed': self.task_completed,
                'waiting_for_input': self.waiting_for_input, 'full_cycle_history': self.full_cycle_history,
                'requirements_hash': self.requirements_hash,
                'max_cycles': self.max_cycles,
                'autonomous_state': self.autonomous_state,
                'activity_log': self.activity_log,
                'settings': self.settings,
                'is_cycle_running': self.is_cycle_running,
            }
            state_path = self._get_state_file_path()
            try:
                with open(state_path, 'w', encoding='utf-8') as f:
                    json.dump(state, f, indent=2)
            except IOError as e:
                logging.error(f"CRITICAL: Could not save state for project '{self.project_name}': {e}")

    # label: Resolves a relative path to an absolute path within the project directory
    def _resolve_path(self, relative_path: str) -> Optional[str]:
        if not relative_path or ".." in relative_path.split(os.path.sep): return None
        allowed_dir = os.path.realpath(self.project_path)
        target_path = os.path.realpath(os.path.join(allowed_dir, relative_path))
        if os.path.commonpath([allowed_dir, target_path]) != allowed_dir: return None
        return target_path

    # label: Saves content to a file in the project directory
    def _save_file(self, relative_path: str, content: str) -> str:
        max_size_bytes = self.settings.get('max_file_write_size_kb', 1024) * 1024
        if len(content.encode('utf-8')) > max_size_bytes:
            error_msg = f"ERROR: Content for '{relative_path}' is too large (>{max_size_bytes // 1024} KB)."
            self._add_to_activity_log(error_msg)
            return error_msg

        self.current_cycle_logs.append(f"Writing file: '{relative_path}'")
        full_path = self._resolve_path(relative_path)
        if not full_path: return f"ERROR: Invalid path: {relative_path}."
        try:
            os.makedirs(os.path.dirname(full_path), exist_ok=True)
            with open(full_path, 'w', encoding='utf-8') as f:
                f.write(content)
            self._add_to_activity_log(f"Wrote {len(content)} bytes to '{relative_path}'.")
            return f"Successfully wrote {len(content)} bytes to {relative_path}"
        except Exception as e:
            error_msg = f"ERROR: Could not save file: {e}"
            self._add_to_activity_log(error_msg)
            return error_msg

    # label: Reads content from a file in the project directory
    def _read_file(self, relative_path: str) -> str:
        self.current_cycle_logs.append(f"Reading file: '{relative_path}'")
        full_path = self._resolve_path(relative_path)
        if not full_path: return f"ERROR: Invalid path: {relative_path}."
        if not os.path.exists(full_path): return f"ERROR: File not found at '{relative_path}'."

        max_size_bytes = self.settings.get('max_file_read_size_kb', 1024) * 1024
        if os.path.getsize(full_path) > max_size_bytes:
            error_msg = f"ERROR: File '{relative_path}' is too large to read (>{max_size_bytes // 1024} KB)."
            self._add_to_activity_log(error_msg)
            return error_msg

        try:
            with open(full_path, 'r', encoding='utf-8') as f:
                return f.read()
        except Exception as e:
            return f"ERROR: Could not read file: {e}"

    # label: Gets a string representation of the file listing
    def get_file_listing(self) -> str:
        listing = []
        for root, dirs, files in os.walk(self.project_path, topdown=True):
            dirs[:] = [d for d in dirs if not d.startswith('.')]
            files = [f for f in files if not f.startswith('.')]

            relative_root = os.path.relpath(root, self.project_path)
            level = 0 if relative_root == '.' else len(relative_root.split(os.sep))
            indent = ' ' * 4 * level

            if relative_root != '.':
                listing.append(f"{indent[:-4]}{os.path.basename(root)}/")

            sub_indent = ' ' * 4 * (level)
            for f in sorted(files):
                listing.append(f"{sub_indent}{f}")

        return "\n".join(listing) if listing else "Project directory is empty."

    # label: Starts a new task for the agent, creating a clean project directory
    def start_task(self, initial_prompt: str):
        with self.lock:
            if os.path.exists(self.project_path):
                shutil.rmtree(self.project_path)
            self._setup_workspace()
            self.full_cycle_history = []
            self.task_completed = False
            self.waiting_for_input = False
            self.cycle_count = 0
            self.requirements_hash = None
            self.autonomous_state = 'idle'
            self.activity_log = []
            self.initial_prompt = initial_prompt
            self._add_to_activity_log(f"New task started. Goal: {initial_prompt}")
        return {"status": "Task started", "project_name": self.project_name}

    # label: Resets the agent's task progress but keeps files
    def reset_task(self):
        with self.lock:
            self.terminate_all_processes()
            self.full_cycle_history = []
            self.task_completed = False
            self.waiting_for_input = False
            self.cycle_count = 0
            self.requirements_hash = None
            self.autonomous_state = 'idle'
            self.activity_log = []
            self.save_project_state()
            self._add_to_activity_log("Agent state has been reset.")
        return {"status": "Project state has been reset."}

    # label: Deletes all files for the current project
    def delete_project_files(self):
        with self.lock:
            self.terminate_all_processes()
            if os.path.exists(self.project_path):
                shutil.rmtree(self.project_path)
        return {"status": f"Project '{self.project_name}' and all its files have been deleted."}

    # label: Imports source files into the project directory
    def import_source(self, source_path: str) -> Dict[str, str]:
        if not os.path.exists(source_path):
            return {"error": f"Source path does not exist: {source_path}"}

        try:
            if os.path.isdir(source_path):
                for item in os.listdir(source_path):
                    s = os.path.join(source_path, item)
                    d = os.path.join(self.project_path, item)
                    if os.path.isdir(s):
                        shutil.copytree(s, d, dirs_exist_ok=True)
                    else:
                        shutil.copy2(s, d)
            else:
                shutil.copy2(source_path, self.project_path)

            self._add_to_activity_log(f"Imported source code from '{source_path}'.")
            return {"status": f"Successfully imported content from '{source_path}'."}
        except Exception as e:
            logging.error(f"Error importing source '{source_path}': {e}")
            self._add_to_activity_log(f"Failed to import source: {e}")
            return {"error": f"Failed to import source: {e}"}

    # label: Calls the Gemini API with the given context
    def _call_gemini_api(self, prompt_context: Dict) -> str:
        api_key = self.config["gemini_api_key"]
        if not api_key: return '{"thought": "CRITICAL ERROR: API Key is missing.", "actions": []}'

        if self.settings.get("log_raw_model_io"):
            self.current_cycle_logs.append("--- MODEL INPUT ---\n" + json.dumps(prompt_context, indent=2))

        try:
            genai.configure(api_key=api_key)
            model = genai.GenerativeModel(model_name=self.config["model_name"], system_instruction=self.config["system_instruction"])
            response = model.generate_content([{"role": "user", "parts": [{"text": json.dumps(prompt_context, indent=2)}]}])

            if self.settings.get("log_raw_model_io"):
                self.current_cycle_logs.append("--- MODEL OUTPUT ---\n" + response.text)

            return response.text.strip()
        except Exception as e:
            return f'{{"thought": "{json.dumps(f"Error: API call failed: {e}")}", "actions": []}}'

    # label: Parses the JSON response from the AI model
    def _parse_ai_response(self, response: str) -> Tuple[str, List[Dict[str, Any]]]:
        match = re.search(r'```json\s*(\{.*?\})\s*```', response, re.DOTALL)
        json_str = match.group(1) if match else response[response.find('{'):response.rfind('}') + 1]
        try:
            data = json.loads(json_str)
            return data.get("thought", ""), data.get("actions", [])
        except json.JSONDecodeError as e:
            self._add_to_activity_log(f"CRITICAL JSON ERROR: Failed to decode AI response. Response: {response[:500]}")
            return f"CRITICAL JSON ERROR: Failed to decode AI response: {e}", []

    # label: Ensures dependencies from requirements.txt are installed
    def _ensure_dependencies_installed(self) -> Tuple[bool, str]:
        requirements_path = os.path.join(self.project_path, "requirements.txt")
        if not os.path.exists(requirements_path):
            return True, "No requirements.txt found."

        try:
            with open(requirements_path, 'rb') as f:
                current_hash = hashlib.sha256(f.read()).hexdigest()
        except IOError:
            return False, "Could not read requirements.txt to check for changes."

        if current_hash == self.requirements_hash:
            return True, "Dependencies are up to date."

        self.current_cycle_logs.append(f"New or modified requirements.txt detected. Installing dependencies...")
        python_executable = os.path.join(self.venv_path, "Scripts" if sys.platform == "win32" else "bin", "python")
        try:
            process = subprocess.Popen(
                [python_executable, "-m", "pip", "install", "-r", requirements_path],
                stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True,
                cwd=self.project_path,
                creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0
            )
            stdout, stderr = process.communicate(timeout=300)
            report = f"--- Installation Report ---\nSTDOUT:\n{stdout}\n\nSTDERR:\n{stderr}"
            if process.returncode == 0:
                self.current_cycle_logs.append("Dependencies installed successfully.")
                self._add_to_activity_log("Successfully installed dependencies from requirements.txt.")
                with self.lock:
                    self.requirements_hash = current_hash
                    self.save_project_state()
                return True, report
            else:
                self.current_cycle_logs.append(f"Installation failed. Full report:\n{report}")
                self._add_to_activity_log(f"Failed to install dependencies. Error: {stderr[:200]}")
                return False, report
        except Exception as e:
            return False, f"A critical error occurred during installation: {e}"

    # label: Executes a shell command in a non-blocking way
    def _execute_command(self, command: str) -> Tuple[bool, str, Optional[str]]:
        if not command:
            return False, "Error: No command provided.", None

        deps_ok, deps_report = self._ensure_dependencies_installed()
        if not deps_ok:
            return False, f"Could not execute command due to dependency installation failure:\n{deps_report}", None

        self.current_cycle_logs.append(f"Executing: `{command}`")
        env = os.environ.copy()
        venv_bin_path = os.path.join(self.venv_path, "Scripts" if sys.platform == "win32" else "bin")
        env["PATH"] = f"{venv_bin_path}{os.pathsep}{env['PATH']}"
        env["PYTHONPATH"] = f"{self.project_path}{os.pathsep}{self.tools_path}{os.pathsep}{env.get('PYTHONPATH', '')}"
        env["AGENT_PROJECT_PATH"] = os.path.abspath(self.project_path)

        try:
            args = shlex.split(command)
            if not args:
                return False, "Error: Empty command provided.", None

            if args[0].lower() in ['cd', 'source', 'export', 'set']:
                error_msg = f"Execution failed: Command '{args[0]}' is a shell built-in and cannot be executed directly."
                self._add_to_activity_log(error_msg)
                return False, error_msg, None

            python_executable = os.path.join(venv_bin_path, "python.exe" if sys.platform == "win32" else "python")
            if args[0] == "pip":
                full_command_args = [python_executable, "-m", "pip"] + args[1:]
            else:
                executable_path = shutil.which(args[0], path=venv_bin_path) or shutil.which(args[0])
                if not executable_path:
                    raise FileNotFoundError(f"Executable '{args[0]}' not found in the virtual environment or system path.")
                full_command_args = [executable_path] + args[1:]

            process = subprocess.Popen(
                full_command_args,
                stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True,
                cwd=self.project_path, env=env,
                creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0
            )
            process_id = str(uuid.uuid4())

            stdout_q = Queue()
            stderr_q = Queue()

            stdout_thread = threading.Thread(target=_stream_reader, args=(process.stdout, stdout_q))
            stderr_thread = threading.Thread(target=_stream_reader, args=(process.stderr, stderr_q))
            stdout_thread.daemon = True
            stderr_thread.daemon = True
            stdout_thread.start()
            stderr_thread.start()

            with self.lock:
                self.active_processes[process_id] = {
                    "process": process, "command": command,
                    "stdout_q": stdout_q, "stderr_q": stderr_q,
                    "stdout_buffer": [], "stderr_buffer": [],
                    "stdout_thread": stdout_thread, "stderr_thread": stderr_thread,
                }

            report = f"Process '{command}' started in the background with ID {process_id}. Its status will be updated in the next cycle."
            self._add_to_activity_log(f"Started command: `{command}` (PID: {process_id}).")
            return True, report, process_id

        except FileNotFoundError as e:
            error_msg = f"Execution failed: {e}"
            self._add_to_activity_log(error_msg)
            return False, error_msg, None
        except Exception as e:
            error_msg = f"Execution failed with an unexpected error: {e}"
            self._add_to_activity_log(f"Failed to execute command `{command}`. Error: {e}")
            return False, error_msg, None

    # label: Terminates a running process
    def terminate_command(self, process_id: str) -> Dict[str, str]:
        with self.lock:
            process_info = self.active_processes.pop(process_id, None)
        if not process_info: return {"status": "Process not found."}
        process = process_info["process"]
        try:
            process.terminate()
            process.wait(timeout=5)
            self._add_to_activity_log(f"Terminated process {process_id}.")
            return {"status": f"Process {process_id} terminated."}
        except subprocess.TimeoutExpired:
            process.kill()
            self._add_to_activity_log(f"Forcefully killed process {process_id}.")
            return {"status": f"Process {process_id} forcefully killed."}
        except Exception as e:
            with self.lock:
                self.active_processes[process_id] = process_info
            return {"error": f"Error terminating process: {e}"}

    def terminate_all_processes(self) -> Dict[str, Any]:
        with self.lock:
            terminated_pids = list(self.active_processes.keys())
            for pid in terminated_pids:
                self.terminate_command(pid)
        return {"status": "All active processes terminated.", "terminated_pids": terminated_pids}

    def restart_process(self, pid: str) -> Dict[str, Any]:
        with self.lock:
            process_info = self.active_processes.get(pid)
            if not process_info:
                return {"error": "Process not found."}
            command_to_restart = process_info["command"]

        self.terminate_command(pid)
        time.sleep(1)

        success, report, new_pid = self._execute_command(command_to_restart)
        return {"status": "Restart initiated.", "success": success, "report": report, "new_pid": new_pid}

    # label: Runs a single cycle of the agent's operation
    def run_cycle(self, feedback: str = ""):
        with self.lock:
            if self.is_cycle_running: return
            self.is_cycle_running = True
            self.save_project_state()

        try:
            time.sleep(self.settings.get('cycle_delay_ms', 1500) / 1000.0)

            with self.lock:
                self.waiting_for_input = False
                self.cycle_count += 1
                self.current_cycle_logs = [f"Starting Cycle {self.cycle_count}."]

                max_logs = self.settings.get('max_log_entries_in_prompt', 20)

                active_processes_summary = {}
                for pid, info in self.active_processes.items():
                    active_processes_summary[pid] = {
                        "command": info["command"],
                        "stdout": "".join(info["stdout_buffer"]),
                        "stderr": "".join(info["stderr_buffer"])
                    }

                prompt_context = {
                    "main_goal": self.initial_prompt,
                    "project_file_listing": self.get_file_listing(),
                    "active_processes": active_processes_summary,
                    "cycle_count": self.cycle_count,
                    "max_cycles": self.max_cycles,
                    "activity_log": self.activity_log[-max_logs:],
                    "new_human_feedback": feedback or None
                }

            ai_response_str = self._call_gemini_api(prompt_context)
            thought, actions = self._parse_ai_response(ai_response_str)
            self.current_cycle_logs.append("Plan received. Starting actions.")

            with self.lock:
                has_execute = any(a.get("type") == "execute" for a in actions)
                if has_execute:
                    actions = [a for a in actions if a.get("type") != "finishTask"]

                cycle_data = {"cycle_count": self.cycle_count, "thought": thought, "raw_ai_response": ai_response_str, "actions_taken": [], "execution_report": None,
                              "feedback_received": feedback or None, "log_entries": []}

                for action in actions:
                    action_result = {"action": action, "result": "PENDING"}
                    cycle_data["actions_taken"].append(action_result)
                    action_type = action.get("type")
                    if action_type == "writeFile":
                        action_result["result"] = self._save_file(action.get("path"), action.get("content", ""))
                    elif action_type == "readFile":
                        action_result["result"] = self._read_file(action.get("path"))
                    elif action_type == "requestFeedback":
                        self.waiting_for_input = True
                        self.autonomous_state = 'paused'
                        details = action.get('details')
                        action_result["result"] = f"Agent requested feedback: {details}"
                        self._add_to_activity_log(f"Requested human feedback: {details}")
                    elif action_type == "finishTask":
                        self.task_completed = True
                        self.autonomous_state = 'idle'
                        summary = action.get('summary')
                        action_result["result"] = f"Task marked as complete. Summary: {summary}"
                        self._add_to_activity_log(f"Task marked as complete. Summary: {summary}")
                    elif action_type == "execute":
                        success, report, pid = self._execute_command(action.get("command"))
                        cycle_data["execution_report"] = report
                        action_result["result"] = f"SUCCESS (PID: {pid})" if success else "FAILURE"

                cycle_data["log_entries"] = self.current_cycle_logs
                self.full_cycle_history.append(cycle_data)
        finally:
            with self.lock:
                self.is_cycle_running = False
                self.save_project_state()

    # label: Finalizes the agent's task
    def finalize_task(self):
        with self.lock:
            self.task_completed = True
            self.autonomous_state = 'idle'
            self._add_to_activity_log("Task manually marked as complete by user.")
            self.save_project_state()
        return {"status": "Task marked as complete."}

    # FIX: Unified resume/re-engage method
    def resume_task(self, feedback: str = ""):
        with self.lock:
            self.task_completed = False
            self.autonomous_state = 'running'
            if feedback:
                self._add_to_activity_log(f"Task resumed with new feedback: '{feedback}'")
            else:
                self._add_to_activity_log("Task resumed by user.")

            if not self.is_cycle_running:
                thread = threading.Thread(target=self.run_cycle, args=(feedback,))
                thread.daemon = True
                thread.start()
                return {"status": "Task resumed and cycle initiated."}
            else:
                return {"status": "Cycle already in progress."}

    # label: Updates the agent's settings
    def update_settings(self, settings: Dict[str, Any]):
        with self.lock:
            for key, value in settings.items():
                if key in self.settings:
                    try:
                        self.settings[key] = type(self.settings[key])(value)
                    except (ValueError, TypeError):
                        logging.warning(f"Could not cast setting '{key}'")
                elif key == 'autonomous_state':
                    self.autonomous_state = str(value)
                elif key == 'max_cycles':
                    self.max_cycles = int(value)
                else:
                    self.settings[key] = value
            self.save_project_state()
            full_settings = self.settings.copy()
            full_settings['autonomous_state'] = self.autonomous_state
            full_settings['max_cycles'] = self.max_cycles
        return {"status": "Settings updated.", "new_settings": full_settings}


# --- Agent Manager (Singleton) ---
# label: Manages all agent instances
class AgentManager:
    _instance = None

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super(AgentManager, cls).__new__(cls)
            cls._instance.agents: Dict[str, Agent] = {}
            cls._instance.lock = threading.RLock()
            cls._instance.venv_path = SHARED_VENV_PATH
            cls._instance.tools_path = SHARED_TOOLS_PATH
            cls._instance.config = CONFIG
            cls._instance._setup_shared_environment()
        return cls._instance

    def _setup_shared_environment(self):
        os.makedirs(self.config["base_projects_dir"], exist_ok=True)
        os.makedirs(self.tools_path, exist_ok=True)
        python_executable = os.path.join(self.venv_path, "Scripts" if sys.platform == "win32" else "bin", "python")

        if not os.path.exists(self.venv_path):
            logging.info(f"Creating shared virtual environment at: {self.venv_path}")
            venv.create(self.venv_path, with_pip=True)
            try:
                subprocess.run([python_executable, "-m", "pip", "install", "--upgrade", "pip"], check=True)
                logging.info("Shared virtual environment created.")
            except subprocess.CalledProcessError as e:
                logging.error(f"Failed to upgrade pip in new venv: {e.stderr}")
        else:
            logging.info(f"Shared virtual environment already exists at: {self.venv_path}")

    def get_agent(self, project_name: str) -> Agent:
        with self.lock:
            if project_name not in self.agents:
                self.agents[project_name] = Agent(project_name, self.venv_path, self.tools_path, self.config)
            return self.agents[project_name]

    def list_projects(self) -> List[Dict[str, Any]]:
        with self.lock:
            base_dir = self.config["base_projects_dir"]
            projects = []
            if not os.path.exists(base_dir): return []
            excluded_dirs = {os.path.basename(self.venv_path), os.path.basename(self.tools_path)}
            for d in os.listdir(base_dir):
                if os.path.isdir(os.path.join(base_dir, d)) and d not in excluded_dirs:
                    agent = self.get_agent(d)
                    projects.append({"name": d, "status": "Completed" if agent.task_completed else "In Progress", "cycles": agent.cycle_count})
            return projects


# --- Flask App ---
app = Flask(__name__)
agent_manager = AgentManager()


def get_agent_from_request() -> Optional[Agent]:
    project_name = request.args.get('project_name') or (request.is_json and request.get_json().get('project_name'))
    if not project_name: return None
    return agent_manager.get_agent(project_name)


@app.route('/')
def index(): return INDEX_HTML


@app.route('/agent_projects/<path:project_path>')
def serve_project_file(project_path):
    return send_from_directory(CONFIG['base_projects_dir'], project_path)


@app.route('/api/projects', methods=['GET'])
def list_projects_route(): return jsonify(agent_manager.list_projects())


@app.route('/api/projects', methods=['POST'])
def create_project_route():
    data = request.get_json()
    project_name, prompt = data.get('project_name'), data.get('prompt')
    if not project_name or not prompt: return jsonify({"error": "project_name and prompt are required"}), 400
    agent = agent_manager.get_agent(project_name)
    return jsonify(agent.start_task(prompt))


@app.route('/api/projects/<project_name>', methods=['DELETE'])
def delete_project_route(project_name):
    agent = agent_manager.get_agent(project_name)
    result = agent.delete_project_files()
    with agent_manager.lock:
        if project_name in agent_manager.agents:
            del agent_manager.agents[project_name]
    return jsonify(result)


@app.route('/api/agent/reset', methods=['POST'])
def reset_agent_route():
    agent = get_agent_from_request()
    if not agent: return jsonify({"error": "project_name is required"}), 400
    return jsonify(agent.reset_task())


@app.route('/api/agent/status', methods=['GET'])
def get_agent_status_route():
    agent = get_agent_from_request()
    if not agent: return jsonify({"error": "project_name is required"}), 400

    with agent.lock:
        active_processes_info = {}
        for pid, info in list(agent.active_processes.items()):
            while not info["stdout_q"].empty():
                info["stdout_buffer"].append(info["stdout_q"].get_nowait())
            while not info["stderr_q"].empty():
                info["stderr_buffer"].append(info["stderr_q"].get_nowait())

            if info["process"].poll() is not None:
                logging.info(f"Process {pid} ({info['command']}) terminated.")
                info["stdout_thread"].join(timeout=1)
                info["stderr_thread"].join(timeout=1)
                agent.active_processes.pop(pid)
                continue

            stdout_str = "".join(info["stdout_buffer"])
            stderr_str = "".join(info["stderr_buffer"])
            active_processes_info[pid] = {
                "command": info["command"],
                "stdout": stdout_str,
                "stderr": stderr_str
            }
            url_match = re.search(r'(https?://\S+)', stdout_str + stderr_str)
            if url_match:
                active_processes_info[pid]["url"] = url_match.group(1)

        status_data = {
            "project_name": agent.project_name, "initial_prompt": agent.initial_prompt,
            "cycle_history": agent.full_cycle_history, "task_completed": agent.task_completed,
            "waiting_for_input": agent.waiting_for_input, "cycle_count": agent.cycle_count,
            "file_listing": agent.get_file_listing(), "max_cycles": agent.max_cycles,
            "autonomous_state": agent.autonomous_state, "active_processes": active_processes_info,
            "settings": agent.settings, "is_cycle_running": agent.is_cycle_running
        }
    return jsonify(status_data)


@app.route('/api/agent/run-cycle', methods=['POST'])
def run_agent_cycle_route():
    agent = get_agent_from_request()
    if not agent: return jsonify({"error": "project_name is required"}), 400

    with agent.lock:
        if agent.is_cycle_running:
            return jsonify({"status": "Cycle already in progress."}), 429

    data = request.get_json()
    feedback = data.get('feedback', '')

    thread = threading.Thread(target=agent.run_cycle, args=(feedback,))
    thread.daemon = True
    thread.start()

    return jsonify({"status": "Cycle initiated."})


@app.route('/api/agent/file-content', methods=['GET'])
def get_file_content_route():
    agent = get_agent_from_request()
    if not agent: return jsonify({"error": "project_name is required"}), 400
    file_path = request.args.get('path')
    if not file_path: return jsonify({"error": "path is required"}), 400
    content = agent._read_file(file_path)
    if content.startswith("ERROR"): return jsonify({"error": content}), 404
    return jsonify({"path": file_path, "content": content})


@app.route('/api/agent/execute', methods=['POST'])
def execute_file_route():
    agent = get_agent_from_request()
    if not agent: return jsonify({"error": "project_name is required"}), 400
    data = request.get_json()
    command = data.get('command')
    if not command: return jsonify({"error": "command is required"}), 400
    success, report, pid = agent._execute_command(command)
    return jsonify({"success": success, "report": report, "pid": pid})


@app.route('/api/agent/terminate', methods=['POST'])
def terminate_process_route():
    agent = get_agent_from_request()
    if not agent: return jsonify({"error": "project_name is required"}), 400
    data = request.get_json()
    pid = data.get('pid')
    if not pid: return jsonify({"error": "pid is required"}), 400
    return jsonify(agent.terminate_command(pid))


@app.route('/api/agent/terminate-all', methods=['POST'])
def terminate_all_processes_route():
    agent = get_agent_from_request()
    if not agent: return jsonify({"error": "project_name is required"}), 400
    return jsonify(agent.terminate_all_processes())


@app.route('/api/agent/restart-process', methods=['POST'])
def restart_process_route():
    agent = get_agent_from_request()
    if not agent: return jsonify({"error": "project_name is required"}), 400
    data = request.get_json()
    pid = data.get('pid')
    if not pid: return jsonify({"error": "pid is required"}), 400
    return jsonify(agent.restart_process(pid))


@app.route('/api/agent/resume', methods=['POST'])
def resume_task_route():
    agent = get_agent_from_request()
    if not agent: return jsonify({"error": "project_name is required"}), 400

    with agent.lock:
        if agent.is_cycle_running:
            return jsonify({"status": "Cycle already in progress."}), 429

    data = request.get_json()
    feedback = data.get('feedback', '')
    return jsonify(agent.resume_task(feedback))


@app.route('/api/agent/finalize', methods=['POST'])
def finalize_task_route():
    agent = get_agent_from_request()
    if not agent: return jsonify({"error": "project_name is required"}), 400
    return jsonify(agent.finalize_task())


@app.route('/api/agent/import-source', methods=['POST'])
def import_source_route():
    agent = get_agent_from_request()
    if not agent: return jsonify({"error": "project_name is required"}), 400
    data = request.get_json()
    source_path = data.get('source_path')
    if not source_path: return jsonify({"error": "source_path is required"}), 400
    result = agent.import_source(source_path)
    if "error" in result: return jsonify(result), 400
    return jsonify(result)


@app.route('/api/agent/update-settings', methods=['POST'])
def update_settings_route():
    agent = get_agent_from_request()
    if not agent: return jsonify({"error": "project_name is required"}), 400
    data = request.get_json()
    settings = data.get('settings')
    if not settings: return jsonify({"error": "settings are required"}), 400
    return jsonify(agent.update_settings(settings))


# label: Main entry point of the application
if __name__ == "__main__":
    app.run(host='0.0.0.0', debug=True, port=5001, use_reloader=False)
