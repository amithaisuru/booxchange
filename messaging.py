from datetime import datetime

from sqlalchemy.orm import Session

from database import get_db
from models import Conversation, Message, User


def get_or_create_conversation(db: Session, user1_id: int, user2_id: int):
    """Get an existing conversation between two users or create a new one."""
    conversation = (
        db.query(Conversation)
        .filter(
            ((Conversation.user1_id == user1_id) & (Conversation.user2_id == user2_id)) |
            ((Conversation.user1_id == user2_id) & (Conversation.user2_id == user1_id))
        )
        .first()
    )
    if not conversation:
        conversation = Conversation(user1_id=user1_id, user2_id=user2_id)
        db.add(conversation)
        db.commit()
        db.refresh(conversation)
    return conversation


def send_message(db: Session, sender_id: int, receiver_id: int, content: str):
    """Send a message between two users, creating a conversation if needed."""
    conversation = get_or_create_conversation(db, sender_id, receiver_id)
    message = Message(
        conversation_id=conversation.conversation_id,
        sender_id=sender_id,
        content=content,
    )
    db.add(message)
    db.commit()
    db.refresh(message)
    return message


def get_user_conversations(db: Session, user_id: int):
    """Fetch all conversations for a user with the latest message preview."""
    conversations = (
        db.query(Conversation)
        .filter((Conversation.user1_id == user_id) | (Conversation.user2_id == user_id))
        .all()
    )
    result = []
    for conv in conversations:
        latest_message = (
            db.query(Message)
            .filter(Message.conversation_id == conv.conversation_id)
            .order_by(Message.sent_at.desc())
            .first()
        )
        other_user_id = conv.user2_id if conv.user1_id == user_id else conv.user1_id
        other_user = db.query(User).filter(User.user_id == other_user_id).first()
        result.append({
            "conversation_id": conv.conversation_id,
            "other_user_id": other_user_id,  # Add this
            "other_user": other_user.user_name,
            "latest_message": latest_message.content if latest_message else "No messages yet",
            "latest_message_time": latest_message.sent_at if latest_message else conv.created_at,
            "unread_count": db.query(Message).filter(
                Message.conversation_id == conv.conversation_id,
                Message.sender_id != user_id,
                Message.is_read == False
            ).count()
        })
    return sorted(result, key=lambda x: x["latest_message_time"], reverse=True)


def get_conversation_messages(db: Session, conversation_id: int, user_id: int):
    """Fetch all messages in a conversation and mark unread messages as read."""
    messages = (
        db.query(Message)
        .filter(Message.conversation_id == conversation_id)
        .order_by(Message.sent_at.asc())
        .all()
    )
    # Mark unread messages from the other user as read
    for msg in messages:
        if msg.sender_id != user_id and not msg.is_read:
            msg.is_read = True
    db.commit()
    return [
        {"sender": db.query(User).filter(User.user_id == msg.sender_id).first().user_name,
         "content": msg.content,
         "sent_at": msg.sent_at,
         "is_sent_by_user": msg.sender_id == user_id}
        for msg in messages
    ]