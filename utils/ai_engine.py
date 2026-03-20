import google.generativeai as genai
import os

import json
import re

PRODUCTIVITY_SYSTEM_PROMPT = """
You are an Intelligent Personal Productivity Assistant. Your goal is to help the user organize their life, achieve their goals, and improve their habits.

You should be analyzing the user's input to identify:
1. To-do items
2. Goals (Short-term and Long-term)
3. Calendar events (Meetings, Deadlines, Reminders)
4. Habits to track

When the user provides a list or a plan, offer:
- Prioritization suggestions (e.g., Eisenhower Matrix).
- Actionable steps.
- Constructive feedback on feasibility.
- Encouraging and motivating tone.

IMPORTANT: You must ALWAYS respond in a JSON structure embedded in a Markdown block, like this:
```json
{
  "response_text": "Your natural language response here...",
  "calendar_events": [
      {
          "title": "Meeting with Bob",
          "date": "YYYY-MM-DD",
          "time": "HH:MM" (optional)
      }
  ],
  "suggested_habits": [
      {
          "habit": "Read 10 pages daily",
          "related_goal": "Learn new things"
      }
  ]
}
```
If there are no new events or habits, the lists should be empty.
Ensure the JSON is valid.
"""

def get_ai_response(messages, api_key=None, goals=None):
    """
    Generates a response from Gemini based on the conversation history.
    Returns a dict with 'text', 'calendar_events', and 'suggested_habits'.
    """
    if not api_key:
        api_key = os.getenv("GOOGLE_API_KEY")
    
    if not api_key:
        return {"text": "Please provide a valid Google Gemini API Key in the sidebar or .env file.", "calendar_events": None, "suggested_habits": None}
    
    try:
        genai.configure(api_key=api_key)
        
        gemini_history = []
        for msg in messages[:-1]:
             role = "user" if msg["role"] == "user" else "model"
             gemini_history.append({"role": role, "parts": [msg["content"]]})

        try:
            model = genai.GenerativeModel('gemini-2.5-flash')
        except:
             model = genai.GenerativeModel('gemini-2.5-pro')
        
        chat = model.start_chat(history=gemini_history)
        
        current_prompt = messages[-1]["content"]
        
        context_prompt = PRODUCTIVITY_SYSTEM_PROMPT
        if goals:
            goals_list = "\n".join([f"- {g['text']} ({'Completed' if g['completed'] else 'Pending'})" for g in goals])
            context_prompt += f"\n\nCURRENT USER GOALS:\n{goals_list}\n"
        
        if len(messages) == 1:
            current_prompt = f"{context_prompt}\n\nUser: {current_prompt}"
        else:
            # Prepend context to the latest message as we use a stateless wrapper logic
            current_prompt = f"System Note: {context_prompt}\n\nUser: {current_prompt}"
            
        response = chat.send_message(current_prompt)
        raw_text = response.text
        
        try:
            match = re.search(r"```json\s*({.*?})\s*```", raw_text, re.DOTALL)
            if match:
                json_str = match.group(1)
                data = json.loads(json_str)
                return {
                    "text": data.get("response_text", raw_text), 
                    "calendar_events": data.get("calendar_events"),
                    "suggested_habits": data.get("suggested_habits")
                }
            else:
                 # Try parsing raw text if no code block
                 data = json.loads(raw_text)
                 return {
                     "text": data.get("response_text", raw_text), 
                     "calendar_events": data.get("calendar_events"),
                     "suggested_habits": data.get("suggested_habits")
                 }
        except:
            return {"text": raw_text, "calendar_events": None, "suggested_habits": None}

    except Exception as e:
        error_msg = str(e)
        if "403" in error_msg or "leaked" in error_msg.lower() or "invalid" in error_msg.lower():
             return {
                 "text": "⚠️ **Critical Error**: Your Google Gemini API Key is invalid or has been revoked (leaked). Please generate a new key at [Google AI Studio](https://aistudio.google.com/) and update your `.env` file or sidebar input.", 
                 "calendar_events": None, 
                 "suggested_habits": None
             }
        return {"text": f"Error connecting to AI: {error_msg}", "calendar_events": None, "suggested_habits": None}
