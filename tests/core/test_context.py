import pytest
from aegis.core.context import Context
from aegis.core.models import Message

def test_context_initialization():
    ctx = Context(session_id="test_session", max_tokens=100)
    assert ctx.session_id == "test_session"
    assert ctx.max_tokens == 100
    assert len(ctx.messages) == 0

def test_add_message():
    ctx = Context(session_id="test_session", max_tokens=100)
    ctx.add_message(role="user", content="Hello")
    assert len(ctx.messages) == 1
    assert ctx.messages[0].role == "user"
    assert ctx.messages[0].content == "Hello"

def test_truncation():
    # 1 token = 4 chars. max_tokens = 10 -> max 40 chars.
    ctx = Context(session_id="test_session", max_tokens=10)
    ctx.add_message(role="user", content="A" * 20) # 5 tokens
    ctx.add_message(role="assistant", content="B" * 20) # 5 tokens
    assert len(ctx.messages) == 2
    
    ctx.add_message(role="user", content="C" * 20) # Mais 5 tokens -> Total 15. Deve truncar a primeira.
    assert len(ctx.messages) == 2
    assert ctx.messages[0].content == "B" * 20
    assert ctx.messages[1].content == "C" * 20

def test_serialization():
    ctx = Context(session_id="test_session", max_tokens=100)
    ctx.add_message(role="user", content="Hello")
    data = ctx.serialize()
    
    assert data["session_id"] == "test_session"
    assert len(data["messages"]) == 1
    assert data["messages"][0]["content"] == "Hello"

def test_deserialization():
    data = {
        "session_id": "serialized_session",
        "max_tokens": 50,
        "messages": [
            {"role": "user", "content": "Hi", "timestamp": 0.0, "metadata": {}}
        ]
    }
    ctx = Context.deserialize(data)
    assert ctx.session_id == "serialized_session"
    assert ctx.max_tokens == 50
    assert len(ctx.messages) == 1
    assert ctx.messages[0].content == "Hi"
