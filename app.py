import streamlit as st
import os
from dotenv import load_dotenv
from services.goal_service import GoalService
from services.calendar_service import CalendarService
from services.habit_service import HabitService

load_dotenv()

st.set_page_config(
    page_title="Asistente Inteligente De Productividad Personal",
    page_icon="🚀",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown("""
<style>
    .stApp {
        background-color: #0e1117;
    }
    .stChatMessage {
        background-color: #1e2329;
        border-radius: 10px;
        padding: 10px;
    }
    h1, h2, h3 {
        color: #f0f2f6;
    }
    .stButton>button {
        background-color: #4CAF50;
        color: white;
        border-radius: 8px;
    }
</style>
""", unsafe_allow_html=True)

st.title(" Asistente Inteligente De Productividad Personal")
st.markdown("Tu agente impulsado por IA para objetivos, hábitos y planificación.")

goal_service = GoalService()
calendar_service = CalendarService()
habit_service = HabitService()

with st.sidebar:
    st.header("Configuración & Historial")
    api_key = st.text_input("Clave API de Gemini", type="password", help="Ingresa tu clave API de Google Gemini")
    if api_key:
        os.environ["GOOGLE_API_KEY"] = api_key
    
    st.divider()
    st.write("Próximamente: Historial & Configuración avanzada")

tab1, tab2 = st.tabs(["💬 Asistente", "📅 Centro de Productividad"])

with tab1:
    if "messages" not in st.session_state:
        st.session_state.messages = []

    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    if prompt := st.chat_input("¿Cómo puedo ayudarte a ser más productivo hoy?"):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        with st.chat_message("assistant"):
            message_placeholder = st.empty()
            with st.spinner("Analizando..."):
                from utils.ai_engine import get_ai_response
                chat_history = st.session_state.messages
                
                current_goals = goal_service.get_goals()
                
                ai_data = get_ai_response(chat_history, goals=current_goals)
                
                response_text = ai_data.get("text", "Lo siento, no pude procesar eso.")
                calendar_events = ai_data.get("calendar_events")
                suggested_habits = ai_data.get("suggested_habits")
                
                if calendar_events:
                    for event in calendar_events:
                        calendar_service.add_event(event.get("title"), event.get("date"), event.get("time"))
                    st.toast(f"Scheduled {len(calendar_events)} new event(s)!")
                
                if suggested_habits:
                     for habit in suggested_habits:
                         habit_service.add_habit(habit.get("habit"), habit.get("related_goal"))
                     st.toast(f"Added {len(suggested_habits)} new habit(s)!")
            
            message_placeholder.markdown(response_text)
        
        st.session_state.messages.append({"role": "assistant", "content": response_text})

with tab2:
    st.header("Centro de Productividad")
    
    st.subheader("Objetivos")
    col_goal_input, col_goal_btn = st.columns([3, 1])
    with col_goal_input:
        new_goal = st.text_input("Agregar un nuevo objetivo", label_visibility="collapsed", placeholder="E.g., Finalizar informe del proyecto")
    with col_goal_btn:
        if st.button("Add Goal"):
            goal_service.add_goal(new_goal)
            st.rerun()

    goals = goal_service.get_goals()
    if not goals:
        st.info("No hay metas para añadir. ¡Comienza por definir sus metas!")
    else:
        for i, goal in enumerate(goals):
            cols = st.columns([0.1, 0.9])
            with cols[0]:
                is_checked = st.checkbox("", value=goal["completed"], key=f"goal_{i}")
                if is_checked != goal["completed"]:
                    goal_service.mark_goal_complete(i, is_checked)
                    st.rerun()
            with cols[1]:
                st.write(f"**{goal['text']}**" if not goal["completed"] else f"~~{goal['text']}~~")

    st.divider()
    
    st.subheader("Tu Tablero de Hábitos")
    
    habits = habit_service.get_habits()
    if not habits:
        st.info("No hábitos para añadir. Pide al IA sugerir hábitos para tus objetivos!")
    else:
        # Group habits by related goal
        habits_by_goal = {}
        for i, habit in enumerate(habits):
            goal = habit.get('related_goal') or "General"
            if goal not in habits_by_goal:
                habits_by_goal[goal] = []
            habits_by_goal[goal].append((i, habit))
        
        # Display habits in cards
        for goal_title, goal_habits in habits_by_goal.items():
            with st.container():
                st.markdown(f"""
                <div style="
                    background-color: #262730; 
                    padding: 15px; 
                    border-radius: 10px; 
                    margin-bottom: 20px; 
                    border: 1px solid #4CAF50;
                    box-shadow: 0 4px 6px rgba(0,0,0,0.1);
                ">
                    <h4 style="margin-bottom: 15px; color: #4CAF50; display: flex; align-items: center; gap: 10px;">
                        🎯 {goal_title}
                    </h4>
                </div>
                """, unsafe_allow_html=True)
                
                # Render checkboxes inside the card visual context
                # Note: Streamlit widgets cannot be strictly nested inside HTML, 
                # but we visually group them by rendering them immediately after the header.
                for i, habit in goal_habits:
                    cols = st.columns([0.05, 0.95])
                    with cols[0]:
                        is_done = st.checkbox("", value=habit["completed_today"], key=f"habit_{i}")
                    with cols[1]:
                        st.markdown(f"<div style='font-size: 16px; padding-top: 2px;'>{habit['text']}</div>", unsafe_allow_html=True)
                        
                    if is_done != habit["completed_today"]:
                        habit_service.toggle_habit(i, is_done)
                        st.rerun()
                
                st.markdown("<div style='margin-bottom: 20px;'></div>", unsafe_allow_html=True)
    st.divider()

    st.subheader("Calendario y Horarios")
    
    events = calendar_service.get_events()
    
    if not events:
        st.info("No eventos programados. Pide al IA programar una reunión!")
    else:
        for event in events:
            with st.container():
                st.markdown(f"""
                <div style="background-color: #1e2329; padding: 10px; border-radius: 5px; margin-bottom: 10px; border-left: 4px solid #4CAF50;">
                    <h4 style="margin: 0; color: #fff;">{event['title']}</h4>
                    <p style="margin: 0; color: #aaa;">📅 {event['date']} {f'⏰ {event['time']}' if event['time'] else ''}</p>
                </div>
                """, unsafe_allow_html=True)

