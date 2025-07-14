#!/usr/bin/env python3
"""
Test script to create a long dialogue for testing scrolling in analytics modal
"""

import json
import time
from datetime import datetime

def create_long_dialogue():
    """Create a dialogue with many messages to test scrolling"""
    
    # Load existing dialogues
    try:
        with open('dialogues.json', 'r', encoding='utf-8') as f:
            dialogues = json.load(f)
    except FileNotFoundError:
        dialogues = {}
    
    # Create a test session with many messages
    session_id = f"test_long_session_{int(time.time())}"
    
    messages = []
    
    # Add many messages to test scrolling
    for i in range(50):
        if i % 2 == 0:
            # User message
            messages.append({
                "role": "user",
                "content": f"Это тестовое сообщение пользователя номер {i+1}. Это длинное сообщение для проверки прокрутки в модальном окне аналитики. Сообщение содержит достаточно текста, чтобы проверить, как работает прокрутка при длинных диалогах.",
                "timestamp": datetime.now().isoformat()
            })
        else:
            # Assistant message
            messages.append({
                "role": "assistant", 
                "content": f"Это ответ бота на сообщение номер {i}. Бот предоставляет подробный ответ с дополнительной информацией, чтобы создать достаточно контента для проверки прокрутки. Ответ включает в себя различные детали и объяснения.",
                "timestamp": datetime.now().isoformat()
            })
    
    # Create session data
    session_data = {
        "session_id": session_id,
        "created_at": datetime.now().isoformat(),
        "last_updated": datetime.now().isoformat(),
        "messages": messages,
        "total_messages": len(messages)
    }
    
    # Add to dialogues
    dialogues[session_id] = session_data
    
    # Save back to file
    with open('dialogues.json', 'w', encoding='utf-8') as f:
        json.dump(dialogues, f, ensure_ascii=False, indent=2)
    
    print(f"Created long dialogue with {len(messages)} messages")
    print(f"Session ID: {session_id}")
    print("You can now test scrolling in the analytics page")

if __name__ == "__main__":
    create_long_dialogue() 