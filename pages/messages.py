import streamlit as st

from database import get_db
from messaging import get_conversation_messages, get_user_conversations, send_message


def messages_page():
    if 'user_id' not in st.session_state or not st.session_state.user_id:
        st.warning("Please login to access messages.")
        return

    st.title("Messages")

    # Initialize session state for selected conversation
    if 'selected_conversation' not in st.session_state:
        st.session_state.selected_conversation = None

    with get_db() as db:
        # Fetch user's conversations
        conversations = get_user_conversations(db, st.session_state.user_id)

        if not conversations:
            st.info("You have no conversations yet.")
            return

        # Sidebar: List of conversations
        st.sidebar.subheader("Conversations")
        for conv in conversations:
            unread_badge = f" ({conv['unread_count']})" if conv['unread_count'] > 0 else ""
            if st.sidebar.button(f"{conv['other_user']} - {conv['latest_message'][:20]}{unread_badge}",
                                key=f"conv_{conv['conversation_id']}"):
                st.session_state.selected_conversation = conv['conversation_id']

        # Main area: Selected conversation
        if st.session_state.selected_conversation:
            messages = get_conversation_messages(db, st.session_state.selected_conversation, st.session_state.user_id)
            other_user = next(conv['other_user'] for conv in conversations 
                            if conv['conversation_id'] == st.session_state.selected_conversation)
            
            st.subheader(f"Chat with: {other_user}")
            
            # Display messages
            for msg in messages:
                if msg['is_sent_by_user']:
                    st.write(f"You ({msg['sent_at']}): {msg['content']}")
                else:
                    st.write(f"{msg['sender']} ({msg['sent_at']}): {msg['content']}")

            # Send new message
            with st.form(key="send_message_form", clear_on_submit=True):
                new_message = st.text_area("Type your message")
                if st.form_submit_button("Send"):
                    if new_message.strip():
                        send_message(db, st.session_state.user_id, 
                                   next(conv for conv in conversations 
                                        if conv['conversation_id'] == st.session_state.selected_conversation)['other_user_id'],
                                   new_message)
                        st.success("Message sent!")
                        st.rerun()
                    else:
                        st.error("Message cannot be empty.")
        else:
            st.info("Select a conversation from the sidebar to start chatting.")

if __name__ == "__main__":
    messages_page()