# LangAdventure - AI-Powered Language Learning Game

LangAdventure is a web-based, interactive roleplaying game designed to help users practice their Japanese language skills in an immersive and engaging way. The application uses a generative AI to act as a story-driving Dungeon Master (DM) and a companion character, creating a dynamic narrative that responds to user input.

## Core Features

-   **Interactive Storytelling**: The user engages in a continuous roleplay scenario with an AI-controlled companion. The story is generated on-the-fly based on the user's actions and dialogue.
-   **Dual-Language Support**: Every piece of dialogue and narration from the AI is provided in both Japanese (with Furigana for Kanji) and English. This allows learners to read the Japanese text and immediately check their understanding with the English translation.
-   **Intelligent Context Management**: The application uses a custom `ContextManager` to intelligently summarize the conversation history. This ensures that the AI has the relevant context to maintain a coherent story, even over long conversations, while optimizing API usage.
-   **Customizable Experience**: Users can name their own character and the AI companion, personalizing the adventure from the start.

---
## Portfolio Highlight

### Use Cases
*   **Immersive Language Learning:** Provides a fun, low-pressure environment for language learners to practice reading and comprehension skills in a dynamic, story-driven context.
*   **Educational Technology:** Serves as a template for creating other AI-powered educational games for various subjects.
*   **Interactive Fiction:** A platform for creating and experiencing interactive stories where the user's choices genuinely shape the narrative.
*   **AI Chatbot Development:** Demonstrates a powerful architecture for building specialized, persona-driven chatbots.

### Proof of Concept
This project is a proof of concept for using a **Large Language Model (LLM) as a dynamic, stateful Dungeon Master (DM) for educational purposes**. It demonstrates:
*   **Advanced Prompt Engineering:** A meticulously crafted system prompt that directs the LLM to maintain a consistent persona, adhere to a strict dual-language output format, and apply specific linguistic rules (like Furigana).
*   **Intelligent Context Management:** A custom `ContextManager` that solves the challenge of ever-growing conversation histories. It uses a hybrid approach, keeping recent messages verbatim while using the LLM itself to recursively summarize older parts of the conversation, ensuring long-term narrative coherence while optimizing API calls.
*   **Structured Data Extraction:** A custom Python parser (`parse_response`) that reliably extracts and structures the dual-language text from the AI's response, turning unstructured text into usable data for the frontend.
*   **Stateful Web Applications:** Effective use of Flask sessions to manage individual user experiences and maintain the state of their unique adventure.

### Hireable Skills
*   **Python & Flask:** Building interactive, session-based web applications with Flask.
*   **AI/LLM Integration & Prompting:** Expertise in designing and implementing sophisticated prompting strategies to control AI behavior and generate structured, reliable output from models like Google Gemini.
*   **Full-Stack Development:** Experience creating a complete web application, from the Python backend to the HTML/CSS/JavaScript frontend.
*   **Algorithm & System Design:** Designed and built a custom, intelligent context management system to solve a key problem in stateful LLM applications.
*   **API Integration:** Proficient in using third-party APIs (Gemini API) within a web application.
*   **Problem Solving:** Identified the need for structured, dual-language output and engineered a complete pipeline (prompting, generation, and parsing) to achieve it.

---

## Technical Stack

-   **Backend**: Flask (Python)
-   **AI Model**: Google Gemini (`gemini-1.5-flash`)
-   **Frontend**: HTML, CSS, JavaScript

## How It Works

1.  The user starts a new adventure by providing a name for their character and the AI companion.
2.  The application initializes the story with a starting prompt and sends it to the Gemini API.
3.  The user interacts with the AI by typing messages in a chat interface.
4.  Each user message is sent to the Gemini API along with the managed conversation history.
5.  The AI, following a strict system prompt, generates the next part of the story, including dialogue for the companion character. The response is formatted with both Japanese and English text.
6.  The frontend parses this dual-language response and displays it in a structured, easy-to-read format.
7.  The custom `ContextManager` periodically creates a summary of the conversation to keep the context sent to the API concise and relevant.

## Visuals

*Coming Soon: A GIF showing a user interacting with the AI companion in the chat interface.*

## Getting Started

These instructions will get you a copy of the project up and running on your local machine.

### Prerequisites

*   Python 3.8+
*   An API key for Google Gemini

### Installation

1.  **Clone the repository:**
    ```sh
    git clone https://github.com/your-username/your-repository.git
    cd your-repository/LangAdventure
    ```

2.  **Create a virtual environment and install dependencies:**
    ```sh
    python -m venv venv
    source venv/bin/activate  # On Windows, use `venv\Scripts\activate`
    pip install -r requirements.txt
    ```

3.  **Set up your environment variables:**
    Create a file named `.env` in the `LangAdventure` directory and add your Gemini API key:
    ```
    GEMINI_API_KEY="YOUR_API_KEY"
    ```

4.  **Run the application:**
    ```sh
    python main.py
    ```

5.  Open your web browser and navigate to `http://127.0.0.1:5000`.
