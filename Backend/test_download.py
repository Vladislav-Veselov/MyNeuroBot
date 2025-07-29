#!/usr/bin/env python3
"""
Test script for the download functionality
"""

import json
import os
from pathlib import Path

def test_download_endpoint():
    """Test the download endpoint functionality"""
    
    # Create a test session
    test_session = {
        "session_id": "test-session-123",
        "created_at": "2025-01-15T10:30:00.000000",
        "messages": [
            {
                "id": "msg-1",
                "role": "user",
                "content": "Привет! Как дела?",
                "timestamp": "2025-01-15T10:30:00.000000"
            },
            {
                "id": "msg-2", 
                "role": "assistant",
                "content": "Привет! У меня все хорошо, спасибо! Как я могу вам помочь?",
                "timestamp": "2025-01-15T10:30:05.000000"
            },
            {
                "id": "msg-3",
                "role": "user", 
                "content": "Расскажите о ваших услугах",
                "timestamp": "2025-01-15T10:31:00.000000"
            },
            {
                "id": "msg-4",
                "role": "assistant",
                "content": "Конечно! Мы предоставляем следующие услуги:\n1. Консультации\n2. Разработка проектов\n3. Техническая поддержка\n\nЧто именно вас интересует?",
                "timestamp": "2025-01-15T10:31:10.000000"
            }
        ],
        "metadata": {
            "total_messages": 4,
            "last_updated": "2025-01-15T10:31:10.000000",
            "unread": False,
            "potential_client": True,
            "ip_address": "192.168.1.100"
        }
    }
    
    # Format the dialogue as text (same as in the endpoint)
    dialogue_text = f"Сессия: {test_session['session_id']}\n"
    dialogue_text += f"Создано: {test_session['created_at']}\n"
    dialogue_text += f"Обновлено: {test_session['metadata']['last_updated']}\n"
    dialogue_text += f"IP адрес: {test_session['metadata'].get('ip_address', 'Неизвестно')}\n"
    dialogue_text += f"Всего сообщений: {test_session['metadata']['total_messages']}\n"
    dialogue_text += "=" * 50 + "\n\n"
    
    if test_session['messages']:
        for message in test_session['messages']:
            role = "Пользователь" if message['role'] == 'user' else "Бот"
            timestamp = message['timestamp']
            content = message['content']
            dialogue_text += f"[{timestamp}] {role}:\n{content}\n\n"
    else:
        dialogue_text += "Нет сообщений в этой сессии.\n"
    
    # Save the test file
    test_file_path = Path("test_dialogue_output.txt")
    with open(test_file_path, 'w', encoding='utf-8') as f:
        f.write(dialogue_text)
    
    print("✅ Test completed successfully!")
    print(f"📄 Test file created: {test_file_path}")
    print(f"📏 File size: {test_file_path.stat().st_size} bytes")
    
    # Display the first few lines
    print("\n📋 Preview of the generated file:")
    print("-" * 50)
    with open(test_file_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()
        for i, line in enumerate(lines[:10]):
            print(f"{i+1:2d}: {line.rstrip()}")
        if len(lines) > 10:
            print("...")
    
    # Clean up
    test_file_path.unlink()
    print(f"\n🧹 Test file cleaned up")

if __name__ == "__main__":
    test_download_endpoint() 