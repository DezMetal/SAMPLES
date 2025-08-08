# LangAdventure - AI-Powered Language Learning Game

LangAdventure is a web-based, interactive roleplaying game designed to help users practice their Japanese language skills in an immersive and engaging way. The application uses a generative AI to act as a story-driving Dungeon Master (DM) and a companion character, creating a dynamic narrative that responds to user input.

## Core Features

-   **Interactive Storytelling**: The user engages in a continuous roleplay scenario with an AI-controlled companion. The story is generated on-the-fly based on the user's actions and dialogue.
-   **Dual-Language Support**: Every piece of dialogue and narration from the AI is provided in both Japanese (with Furigana for Kanji) and English. This allows learners to read the Japanese text and immediately check their understanding with the English translation.
-   **Intelligent Context Management**: The application uses a custom `ContextManager` to intelligently summarize the conversation history. This ensures that the AI has the relevant context to maintain a coherent story, even over long conversations, while optimizing API usage.
-   **Customizable Experience**: Users can name their own character and the AI companion, personalizing the adventure from the start.

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
