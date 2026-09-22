import streamlit as st
from chatbot_backend import chatbot
from langchain_core.messages import HumanMessage
import uuid


# **************************************** Utility Functions *************************

def generate_thread_id():
    return str(uuid.uuid4())


def reset_chat():
    thread_id = generate_thread_id()

    st.session_state['thread_id'] = thread_id

    add_thread(thread_id)

    # New conversation ka default title
    st.session_state['chat_titles'][thread_id] = "New Conversation"

    st.session_state['message_history'] = []


def add_thread(thread_id):
    if thread_id not in st.session_state['chat_threads']:
        st.session_state['chat_threads'].append(thread_id)


def load_conversation(thread_id):
    return chatbot.get_state(
        config={'configurable': {'thread_id': thread_id}}
    ).values['messages']


# **************************************** Session State *************************

if 'message_history' not in st.session_state:
    st.session_state['message_history'] = []


if 'thread_id' not in st.session_state:
    st.session_state['thread_id'] = generate_thread_id()


if 'chat_threads' not in st.session_state:
    st.session_state['chat_threads'] = []


# thread_id -> conversation title
if 'chat_titles' not in st.session_state:
    st.session_state['chat_titles'] = {}


# Current thread ko list me add karo
add_thread(st.session_state['thread_id'])


# Current thread ka default title
if st.session_state['thread_id'] not in st.session_state['chat_titles']:
    st.session_state['chat_titles'][st.session_state['thread_id']] = "New Conversation"


# **************************************** Config *************************

CONFIG = {
    'configurable': {
        'thread_id': st.session_state['thread_id']
    }
}


# **************************************** Sidebar UI *************************

st.sidebar.title('LangGraph Chatbot')


# New Chat button
if st.sidebar.button('New Chat', key='new_chat_button'):
    reset_chat()
    st.rerun()


st.sidebar.header('My Conversations')


# Show conversations
for thread_id in st.session_state['chat_threads'][::-1]:

    title = st.session_state['chat_titles'].get(
        thread_id,
        "New Conversation"
    )

    if st.sidebar.button(
        title,
        key=f"chat_{thread_id}"
    ):

        st.session_state['thread_id'] = thread_id

        messages = load_conversation(thread_id)

        temp_messages = []

        for message in messages:

            if isinstance(message, HumanMessage):
                role = 'user'
            else:
                role = 'assistant'

            temp_messages.append({
                'role': role,
                'content': message.content
            })

        st.session_state['message_history'] = temp_messages

        st.rerun()


# **************************************** Load Conversation History *************************

for message in st.session_state['message_history']:

    with st.chat_message(message['role']):
        st.text(message['content'])


# **************************************** Chat Input *************************

user_input = st.chat_input('Type here')


if user_input:

    # ------------------------------------------------
    # Generate conversation title from first message
    # ------------------------------------------------

    if len(st.session_state['message_history']) == 0:

        title = user_input.strip()

        # Make title short
        if len(title) > 30:
            title = title[:30] + "..."

        st.session_state['chat_titles'][
            st.session_state['thread_id']
        ] = title


    # ------------------------------------------------
    # Add user message to message history
    # ------------------------------------------------

    st.session_state['message_history'].append({
        'role': 'user',
        'content': user_input
    })


    # ------------------------------------------------
    # Display user message
    # ------------------------------------------------

    with st.chat_message('user'):
        st.text(user_input)


    # ------------------------------------------------
    # Generate AI response
    # ------------------------------------------------

    with st.chat_message('assistant'):

        ai_message = st.write_stream(
            message_chunk.content
            for message_chunk, metadata in chatbot.stream(
                {
                    'messages': [
                        HumanMessage(content=user_input)
                    ]
                },
                config=CONFIG,
                stream_mode='messages'
            )
        )


    # ------------------------------------------------
    # Add AI response to history
    # ------------------------------------------------

    st.session_state['message_history'].append({
        'role': 'assistant',
        'content': ai_message
    })