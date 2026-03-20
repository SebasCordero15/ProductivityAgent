import streamlit as st

class GoalService:
    def __init__(self):
        if "goals" not in st.session_state:
            st.session_state.goals = []

    def add_goal(self, goal_text: str):
        """Adds a new goal to the session state."""
        if goal_text:
            st.session_state.goals.append({"text": goal_text, "completed": False})

    def get_goals(self):
        """Retrieves the list of goals."""
        return st.session_state.goals

    def mark_goal_complete(self, index: int, completed: bool):
        """Updates the completion status of a goal."""
        if 0 <= index < len(st.session_state.goals):
            st.session_state.goals[index]["completed"] = completed
