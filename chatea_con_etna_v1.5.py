#!/usr/bin/env python3
# chatea_con_simur-etna_v1.3.py
import os
import datetime
from dotenv import load_dotenv
import streamlit as st
from openai import OpenAI

# ——— Cargar variables de entorno ———
load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
if not OPENAI_API_KEY:
    st.error("No se encontró la variable OPENAI_API_KEY en el archivo .env")
    st.stop()
ASSISTANT_ID = os.getenv("ASSISTANT_ID")
if not ASSISTANT_ID:
    try:
        with open("assistant_id.txt") as f:
            ASSISTANT_ID = f.read().strip()
    except FileNotFoundError:
        st.error("No se encontró ASSISTANT_ID en .env ni en assistant_id.txt")
        st.stop()

# ——— Inicializar cliente OpenAI ———
client = OpenAI(api_key=OPENAI_API_KEY)

# ——— Configuración de la página ———
st.set_page_config(
    page_title="Chatear con Simur",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# ——— Estilos ———
st.markdown(
    """
    <style>
    [data-testid="stAppViewContainer"] {background-color: #000; color: #fff;}
    [data-testid="stAppViewContainer"] * {color: #fff !important;}
    .ch-title {color: #0f0 !important;}
    /* Botones principales */
    div.stButton > button {
        background-color: #1e40af !important;
        color: #fff !important;
        border-radius: 0.75rem !important;
        padding: 0.5em 1em !important;
        font-weight: bold !important;
        font-size: 1rem !important;
    }
    /* Botón Cerrar (✖) */
    .terminate-button > button {
        background-color: #dc2626 !important;
        color: #fff !important;
        border-radius: 0.75rem !important;
        padding: 0.25em 1em !important;
        font-weight: bold !important;
        font-size: 1.25rem !important;
        min-width: 60px !important;
        text-align: center !important;
    }
    .stChatMessage {border-radius: 1rem; padding: 0.75rem 1rem; margin: 0.25rem 0;}
    .stChatMessage-user {background: #333 !important; align-self: flex-end;}
    .stChatMessage-assistant {background: #111 !important; border: 1px solid #444 !important;}
    </style>
    """,
    unsafe_allow_html=True
)

# ——— Logos y Título ———
col1, col2, _ = st.columns([1,1,1])
with col1:
    st.image("Logo_BrainPower_1.jpg", width=100)
with col2:
    st.image("logo_etna_1.png", width=100)
st.markdown(
    '## <span class="ch-title">Chatear con Simur, el agente de Soporte de Etna Educación</span>',
    unsafe_allow_html=True
)

# ——— Estado de la sesión ———
if 'thread_id' not in st.session_state:
    st.session_state.thread_id = None
if 'chat_started' not in st.session_state:
    st.session_state.chat_started = False
if 'messages' not in st.session_state:
    st.session_state.messages = []

# ——— Funciones auxiliares ———
def log_event(event_type, _id):
    with open("chat_logs.txt", "a", encoding="utf-8") as log:
        log.write(f"{datetime.datetime.now().isoformat()} - {event_type}: {_id}\n")

def stop_chat_state():
    st.session_state.chat_started = False
    st.session_state.thread_id = None
    st.session_state.messages = []

# ——— Iniciar chat ———
if not st.session_state.chat_started:
    if st.button("Comenzar a chatear"):
        thread = client.beta.threads.create()
        st.session_state.thread_id = thread.id
        log_event("THREAD_ID", thread.id)
        run = client.beta.threads.runs.create_and_poll(
            thread_id=thread.id,
            assistant_id=ASSISTANT_ID
        )
        log_event("RUN_ID", run.id)
        msgs = list(client.beta.threads.messages.list(
            thread_id=thread.id,
            run_id=run.id
        ))
        greeting = msgs[0].content[0].text.value
        st.session_state.messages.append({"role": "assistant", "content": greeting})
        st.session_state.chat_started = True

# ——— Chat activo ———
if st.session_state.chat_started:
    # Mostrar historial
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.write(msg["content"])

    # Botón Cerrar (✖) abajo a la derecha
    cols = st.columns([9,1])
    with cols[1]:
        st.markdown('<div class="terminate-button">', unsafe_allow_html=True)
        if st.button("✖", key="terminate", help='o escribir "salir" o "exit"'):
            stop_chat_state()
            st.stop()
        st.markdown('</div>', unsafe_allow_html=True)

    # Entrada de usuario
    user_input = st.chat_input("Escribe tu mensaje aquí…")
    if user_input:
        txt = user_input.strip().lower()
        if txt in ("salir", "exit", "chau"):
            stop_chat_state()
            st.stop()
        # Registrar mensaje de usuario
        st.session_state.messages.append({"role": "user", "content": user_input})
        with st.chat_message("user"):
            st.write(user_input)
        client.beta.threads.messages.create(
            thread_id=st.session_state.thread_id,
            role="user",
            content=user_input
        )
        run = client.beta.threads.runs.create_and_poll(
            thread_id=st.session_state.thread_id,
            assistant_id=ASSISTANT_ID
        )
        log_event("RUN_ID", run.id)
        msgs = list(client.beta.threads.messages.list(
            thread_id=st.session_state.thread_id,
            run_id=run.id
        ))
        ai_text = msgs[0].content[0].text.value
        st.session_state.messages.append({"role": "assistant", "content": ai_text})
        with st.chat_message("assistant"):
            st.write(ai_text)
