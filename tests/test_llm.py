import pytest
from unittest.mock import patch, MagicMock
import os
from app.llm_agent import ask_gemini, tool_detect_hys_law

@patch.dict(os.environ, {"GEMINI_API_KEY": "test_key"}, clear=True)
@patch("app.llm_agent.genai.Client")
def test_ask_gemini_initializes_and_calls(mock_client_class):
    mock_client = MagicMock()
    mock_client_class.return_value = mock_client
    
    mock_chats = MagicMock()
    mock_client.chats = mock_chats
    
    mock_chat = MagicMock()
    mock_chats.create.return_value = mock_chat
    
    mock_response = MagicMock()
    mock_response.text = "Subject 042-S01-001 was returned as a protocol-defined screening signal."
    mock_chat.send_message.return_value = mock_response
    
    response = ask_gemini("What Hy's Law signals were found at cut 12?")
    
    # Verify client was called with the key
    mock_client_class.assert_called_once_with(api_key="test_key")
    
    # Verify chat was started and message was sent
    mock_chats.create.assert_called_once()
    kwargs = mock_chats.create.call_args.kwargs
    assert kwargs["model"] == "gemini-3.6-flash"
    assert "config" in kwargs
    
    config = kwargs["config"]
    # Verify tool is passed
    assert tool_detect_hys_law in config.tools
    
    mock_chat.send_message.assert_called_once_with("What Hy's Law signals were found at cut 12?")
    
    # Verify response
    assert "protocol-defined screening signal" in response

@patch.dict(os.environ, {}, clear=True)
def test_ask_gemini_missing_key():
    response = ask_gemini("Test")
    assert response == "Gemini is not configured. Set GEMINI_API_KEY in the backend environment."

@patch.dict(os.environ, {"GEMINI_API_KEY": "test_key", "GEMINI_MODEL": "gemini-2.5-flash"}, clear=True)
@patch("app.llm_agent.genai.Client")
def test_ask_gemini_uses_configured_model(mock_client_class):
    mock_client = MagicMock()
    mock_client_class.return_value = mock_client
    mock_chat = MagicMock()
    mock_client.chats.create.return_value = mock_chat
    mock_response = MagicMock()
    mock_response.text = "configured model response"
    mock_chat.send_message.return_value = mock_response

    response = ask_gemini("Use configured model")

    assert response == "configured model response"
    kwargs = mock_client.chats.create.call_args.kwargs
    assert kwargs["model"] == "gemini-2.5-flash"

@patch.dict(os.environ, {"GEMINI_API_KEY": "test_key"}, clear=True)
@patch("app.llm_agent.genai.Client")
def test_ask_gemini_api_failure(mock_client_class):
    mock_client_class.side_effect = Exception("API down")
    response = ask_gemini("Test")
    assert response == "The deterministic analysis service could not be reached."

def test_tool_detect_hys_law():
    res = tool_detect_hys_law(cut=12)
    assert "data" in res
    assert "evidence" in res
    assert "metadata" in res
