# Intelligent Personal Productivity Assistant - Comprehensive Documentation

**Version:** 2.0
**Last Updated:** December 14, 2025

This document serves as the **definitive technical guide** for the Intelligent Personal Productivity Assistant. It covers high-level architecture, detailed code logic, data flow, and the specific design patterns used to integrate Artificial Intelligence into a Streamlit application.

---

## 1. High-Level Architecture

The application follows a **Client-Server-AI** model, where the "Server" is the Streamlit backend running locally.

```mermaid
graph TD
    User([User]) <-->|Interacts via Browser| UI[Streamlit UI (App.py)]
    
    subgraph "Application Core"
        UI <-->|Read/Write State| SS[(Session State)]
        UI -->|Calls| Services[Service Layer]
        
        subgraph "Services"
            GS[GoalService]
            HS[HabitService]
            CS[CalendarService]
        end
        
        Services <-->|Persist Data| SS
    end
    
    subgraph "Intelligence Layer"
        UI -->|Sends History + Context| AI[AI Engine (utils/ai_engine.py)]
        AI <-->|API Call| Gemini[Google Gemini API]
        AI -->|Returns JSON| UI
    end
    
    AI -.->|Parses Response| UI
    UI -.->|Updates| Services
```

### Core Components:
1.  **Frontend (UI)**: The visual interface rendered by `app.py`.
2.  **State Management**: `st.session_state` acts as the temporary database, storing data in RAM while the app runs.
3.  **Service Layer**: Encapsulates business logic (CRUD operations) for Goals, Habits, and Events.
4.  **AI Engine**: A stateless module that constructs prompts and communicates with Google Gemini.

---

## 2. Directory & File Breakdown

### Root Directory
- **`app.py`**: The "Conductor". It sets up the page, initializes services, and controls the flow of data between the user, the AI, and the services.
- **`.env`**: Stores sensitive configuration, specifically `GOOGLE_API_KEY`.
- **`requirements.txt`**: Lists external Python libraries needed (`streamlit`, `google-generativeai`, `python-dotenv`, `plotly`, `pandas`).

### `services/` (The Business Logic)
These classes provide an abstraction layer over `st.session_state`. This ensures that `app.py` remains clean and doesn't directly manipulate raw data structures.

- **`goal_service.py`**:
    - Manage user goals.
    - *Storage*: `st.session_state.goals` (List of dicts).
- **`habit_service.py`**:
    - Manages daily habits.
    - *Storage*: `st.session_state.habits` (List of dicts).
- **`calendar_service.py`**:
    - Manages schedule/events.
    - *Storage*: `st.session_state.calendar_events` (List of dicts).

### `utils/` (Helper Modules)
- **`ai_engine.py`**: Contains `get_ai_response()`. This is the single point of contact with the LLM.

---

## 3. Deep Dive: AI Integration logic

The most complex part of the app is how it talks to Gemini. This is handled in `utils/ai_engine.py`.

### 3.1. The "System Prompt" Strategy
The file defines a constant `PRODUCTIVITY_SYSTEM_PROMPT`. This is **Prompt Engineering**.
It does three critical things:
1.  **Role Definition**: "You are an Intelligent Personal Productivity Assistant..."
2.  **Capability Definition**: It explicitly tells the AI what it can do (Actionable steps, Eisenhower Matrix, etc.).
3.  **Output Enforcement (JSON)**: This is the most important part. It forces the AI to reply in a strict JSON format so the code can read it programmatically.

```python
# Simplified view of the prompt enforcement
"""
IMPORTANT: You must ALWAYS respond in a JSON structure embedded in a Markdown block, like this:
```json
{
  "response_text": "...",
  "calendar_events": [...],
  "suggested_habits": [...]
}
```
"""
```

### 3.2. Context Injection
The AI needs to know *who* it's talking to and *what* their goals are. We achieve this by **Dynamic Context Injection**.

In `get_ai_response(messages, api_key, goals)`, lines 73-76:
```python
context_prompt = PRODUCTIVITY_SYSTEM_PROMPT
if goals:
    # Converts the list of goal objects into a string list
    goals_list = "\n".join([f"- {g['text']} ({'Completed' if g['completed'] else 'Pending'})" for g in goals])
    # Appends this list to the system prompt
    context_prompt += f"\n\nCURRENT USER GOALS:\n{goals_list}\n"
```
**Why do this?**
If a user asks "What should I do today?", the AI can look at the injected `CURRENT USER GOALS` list and say "You still need to finish your Project Report" instead of giving generic advice.

### 3.3. Response Parsing (The "Handshake")
When Gemini replies, it sends back a big string. The app needs to extract the JSON part. This happens in lines 88-96:

```python
# Regex looks for content between ```json and ```
match = re.search(r"```json\s*({.*?})\s*```", raw_text, re.DOTALL)
if match:
    json_str = match.group(1)
    data = json.loads(json_str) # Convert string to Python Dictionary
```

---

## 4. Deep Dive: The Application Loop (`app.py`)

Streamlit works differently from traditional web frameworks like Flask or Django. **The entire script runs from top to bottom every time the user interacts with the UI.**

### 4.1. Initialization (Run once per session state)
```python
# Lines 41-43
goal_service = GoalService()
calendar_service = CalendarService()
habit_service = HabitService()
```
These lines instantiate the services. Inside their `__init__` methods, they check if their specific keys exist in `st.session_state`. If not, they create empty lists. This ensures data survives the "Rerun".

### 4.2. Handling User Input
When the user types a message and hits Enter (Line 64):
1.  **Append to History**: Message is added to `st.session_state.messages`.
2.  **Call AI**: `ai_engine.get_ai_response` is called.
3.  **Process "Side Effects"**:
    The AI returns a dictionary. The app checks for "side effects" (events or habits to create) *before* displaying the text response.

    ```python
    # Lines 83-86 (Simplified)
    if calendar_events:
        for event in calendar_events:
            # The AI suggested an event, so we physically add it to our database (session_state)
            calendar_service.add_event(...)
    ```
    This is how the AI "takes action". It doesn't modify the database itself; it *suggests* an action in the JSON, and the Python code executes it.

### 4.3. The Rendering Phase
After the logic runs, `app.py` continues down to render the UI.
- **Tabs**: The `st.tabs` command splits the view.
- **Productivity Hub**: It loops through `goal_service.get_goals()` and `habit_service.get_habits()` to draw checkboxes and cards.

---

## 5. Key Classes Reference

### `GoalService`
| Method | Description |
| :--- | :--- |
| `__init__` | Initializes `st.session_state.goals = []` if needed. |
| `add_goal(text)` | Appends `{"text": text, "completed": False}`. |
| `mark_goal_complete(idx, bool)` | Updates the `completed` status at specific index. |

### `HabitService`
| Method | Description |
| :--- | :--- |
| `add_habit(text, goal)` | Appends `{"text": text, "related_goal": goal, "completed_today": False}`. |
| `toggle_habit(idx, bool)` | Updates `completed_today` status. |

### `CalendarService`
| Method | Description |
| :--- | :--- |
| `add_event(title, date, time)` | Appends event dict and **sorts the list by date**. |

---

## 6. Setup & Execution Guide

### Prerequisites
1.  **Python 3.8+**
2.  **Google Gemini API Key**: Get one from [Google AI Studio](https://aistudio.google.com/).

### Installation
```bash
# 1. Clone/Download the repository
# 2. Open terminal in the project folder
pip install -r requirements.txt
```

### Configuration
Create a file named `.env` in the root folder:
```text
GOOGLE_API_KEY=your_api_key_here
```
*Alternatively, you can skip this and enter the key in the App Sidebar every time you run it.*

### Running
```bash
streamlit run app.py
```
This will launch a local web server (usually `http://localhost:8501`) and open it in your browser.
