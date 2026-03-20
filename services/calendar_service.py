import streamlit as st
from datetime import datetime

class CalendarService:
    def __init__(self):
        if "calendar_events" not in st.session_state:
            st.session_state.calendar_events = []

    def add_event(self, title: str, date: str, time: str = None):
        """Adds a new event to the session state."""
        event = {
            "title": title,
            "date": date, # Format: YYYY-MM-DD
            "time": time, # Format: HH:MM or None
            "created_at": datetime.now().isoformat()
        }
        st.session_state.calendar_events.append(event)
        # Sort by date
        st.session_state.calendar_events.sort(key=lambda x: x['date'])

    def get_events(self):
        """Retrieves list of events."""
        return st.session_state.calendar_events
