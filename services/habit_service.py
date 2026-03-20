import streamlit as st

class HabitService:
    def __init__(self):
        if "habits" not in st.session_state:
            st.session_state.habits = []

    def add_habit(self, text: str, related_goal: str = None):
        """Adds a new habit to the session state."""
        habit = {
            "text": text,
            "related_goal": related_goal,
            "completed_today": False
        }
        st.session_state.habits.append(habit)

    def get_habits(self):
        """Retrieves list of habits."""
        return st.session_state.habits

    def toggle_habit(self, index: int, completed: bool):
        """Toggles the completion status of a habit."""
        if 0 <= index < len(st.session_state.habits):
            st.session_state.habits[index]["completed_today"] = completed
