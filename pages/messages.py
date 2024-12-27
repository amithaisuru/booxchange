# pages/messages.py
import streamlit as st

from database import get_db_connection, get_dict_cursor_connection


def get_user_conversations(user_id):
    conn, cur = get_dict_cursor_connection()
    try:
        cur.execute('''
            SELECT DISTINCT 
                CASE 
                    WHEN m.sender_id = %s THEN m.receiver_id 
                    ELSE m.sender_id 
                END as other_user_id,
                u.name as other_user_name
            FROM messages m
            JOIN users u ON (
                CASE 
                    WHEN m.sender_id = %s THEN m.receiver_id 
                    ELSE m.sender_id 
                END = u.user_id
            )
            WHERE m.sender_id = %s OR m.receiver_id = %s
        ''', (user_id, user_id, user_id, user_id))
        return cur.fetchall()
    finally:
        cur.close()
        conn.close()

def get_conversation_messages(user_id, other_user_id):
    conn, cur = get_dict_cursor_connection()
    try:
        cur.execute('''
            SELECT m.*, 
                   u_sender.name as sender_name,
                   u_receiver.name as receiver_name
            FROM messages m
            JOIN users u_sender ON m.sender_id = u_sender.user_id
            JOIN users u_receiver ON m.receiver_id = u_receiver.user_id
            WHERE (m.sender_id = %s AND m.receiver_id = %s)
               OR (m.sender_id = %s AND m.receiver_id = %s)
            ORDER BY m.timestamp ASC
        ''', (user_id, other_user_id, other_user_id, user_id))
        return cur.fetchall()
    finally:
        cur.close()
        conn.close()

def send_message(sender_id, receiver_id, message_text):
    conn = get_db_connection()
    cur = conn.cursor()
    try:
        cur.execute('''
            INSERT INTO messages (sender_id, receiver_id, message, timestamp)
            VALUES (%s, %s, %s, CURRENT_TIMESTAMP)
        ''', (sender_id, receiver_id, message_text))
        conn.commit()
        return True
    except Exception as e:
        st.error(f"Error sending message: {str(e)}")
        return False
    finally:
        cur.close()
        conn.close()

def messages_page():
    st.title("Messages")
    
    if 'user_id' not in st.session_state:
        st.warning("Please login first")
        return
    
    # Initialize session state for selected conversation
    if 'selected_conversation' not in st.session_state:
        st.session_state.selected_conversation = None
    
    # Get user's conversations
    conversations = get_user_conversations(st.session_state.user_id)
    
    # Sidebar for conversation selection
    st.sidebar.subheader("Conversations")
    for conv in conversations:
        if st.sidebar.button(conv['other_user_name'], 
                           key=f"conv_{conv['other_user_id']}"):
            st.session_state.selected_conversation = conv['other_user_id']
    
    # Main chat area
    if st.session_state.selected_conversation:
        messages = get_conversation_messages(
            st.session_state.user_id, 
            st.session_state.selected_conversation
        )
        
        # Display messages
        for msg in messages:
            is_own_message = msg['sender_id'] == st.session_state.user_id
            col1, col2 = st.columns([3, 1])
            
            with col1:
                st.container().markdown(
                    f"<div style='text-align: {'right' if is_own_message else 'left'};'>"
                    f"<p style='background-color: {'#e3f2fd' if is_own_message else '#f5f5f5'};"
                    f"padding: 10px; border-radius: 10px; display: inline-block;'>"
                    f"{msg['message']}</p></div>",
                    unsafe_allow_html=True
                )
            
        # Message input
        with st.container():
            message_text = st.text_input("Type your message", key="message_input")
            if st.button("Send"):
                if message_text.strip():
                    if send_message(st.session_state.user_id, 
                                 st.session_state.selected_conversation, 
                                 message_text):
                        st.rerun()