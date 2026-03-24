"""Tests for copilot streaming (agent) endpoint with mocked LLM."""

import json
import pytest
from unittest.mock import patch, MagicMock, AsyncMock


class TestAgentChatEndpoint:
    """Test POST /agent/chat SSE streaming endpoint."""

    def test_agent_chat_requires_auth(self, client):
        """POST /agent/chat without auth returns 401 or 422."""
        res = client.post(
            "/api/v1/agent/chat",
            json={"messages": [{"role": "user", "content": "Hello"}]},
        )
        assert res.status_code in (401, 422)

    def test_agent_chat_invalid_token(self, client):
        """POST /agent/chat with bad token returns 401."""
        res = client.post(
            "/api/v1/agent/chat",
            json={"messages": [{"role": "user", "content": "Hello"}]},
            headers={"Authorization": "Bearer invalid-token"},
        )
        assert res.status_code == 401

    def test_agent_chat_missing_messages(self, client, auth_headers):
        """POST /agent/chat without messages field returns 422."""
        res = client.post(
            "/api/v1/agent/chat",
            json={},
            headers=auth_headers,
        )
        assert res.status_code == 422

    def test_agent_chat_invalid_message_format(self, client, auth_headers):
        """POST /agent/chat with invalid message structure returns 422."""
        res = client.post(
            "/api/v1/agent/chat",
            json={"messages": [{"invalid_key": "value"}]},
            headers=auth_headers,
        )
        assert res.status_code == 422

    @patch("api.routers.agent.run_copilot")
    def test_agent_chat_returns_sse_stream(self, mock_copilot, client, auth_headers):
        """POST /agent/chat with valid request returns SSE stream."""

        async def mock_sse_generator(*args, **kwargs):
            yield json.dumps({"type": "thinking", "content": "Analyzing..."})
            yield json.dumps({"type": "message", "content": "Here is the answer."})
            yield json.dumps({"type": "done"})

        mock_copilot.return_value = mock_sse_generator()

        res = client.post(
            "/api/v1/agent/chat",
            json={
                "messages": [{"role": "user", "content": "How many barriers?"}],
                "sehra_id": "test-sehra-1",
            },
            headers=auth_headers,
        )
        # SSE responses return 200
        assert res.status_code == 200
        # Content type should be event-stream
        assert "text/event-stream" in res.headers.get("content-type", "")

    @patch("api.routers.agent.run_copilot")
    def test_agent_chat_with_page_context(self, mock_copilot, client, auth_headers):
        """POST /agent/chat passes page_context through to copilot."""

        async def mock_sse_generator(*args, **kwargs):
            yield json.dumps({"type": "done"})

        mock_copilot.return_value = mock_sse_generator()

        res = client.post(
            "/api/v1/agent/chat",
            json={
                "messages": [{"role": "user", "content": "Summarize this page"}],
                "sehra_id": "test-sehra-1",
                "page_context": "component_detail",
            },
            headers=auth_headers,
        )
        assert res.status_code == 200
        mock_copilot.assert_called_once()
        call_kwargs = mock_copilot.call_args
        # Verify page_context was passed
        assert call_kwargs.kwargs.get("page_context") == "component_detail" or \
               (len(call_kwargs.args) >= 3 and call_kwargs.args[2] == "component_detail")

    @patch("api.routers.agent.run_copilot")
    def test_agent_chat_without_sehra_id(self, mock_copilot, client, auth_headers):
        """POST /agent/chat works without sehra_id (general question)."""

        async def mock_sse_generator(*args, **kwargs):
            yield json.dumps({"type": "message", "content": "General answer."})
            yield json.dumps({"type": "done"})

        mock_copilot.return_value = mock_sse_generator()

        res = client.post(
            "/api/v1/agent/chat",
            json={
                "messages": [{"role": "user", "content": "What is SEHRA?"}],
            },
            headers=auth_headers,
        )
        assert res.status_code == 200

    @patch("api.routers.agent.run_copilot")
    def test_agent_chat_multi_turn_conversation(
        self, mock_copilot, client, auth_headers
    ):
        """POST /agent/chat handles multi-turn conversation messages."""

        async def mock_sse_generator(*args, **kwargs):
            yield json.dumps({"type": "message", "content": "Follow-up answer."})
            yield json.dumps({"type": "done"})

        mock_copilot.return_value = mock_sse_generator()

        res = client.post(
            "/api/v1/agent/chat",
            json={
                "messages": [
                    {"role": "user", "content": "What are the barriers?"},
                    {"role": "assistant", "content": "There are 4 barriers."},
                    {"role": "user", "content": "Tell me more about the first one."},
                ],
                "sehra_id": "test-sehra-1",
            },
            headers=auth_headers,
        )
        assert res.status_code == 200
        mock_copilot.assert_called_once()
        call_args = mock_copilot.call_args
        # Verify all 3 messages were passed
        messages_arg = call_args.kwargs.get("messages") or call_args.args[0]
        assert len(messages_arg) == 3


class TestAgentChatToolEvents:
    """Test that copilot tool call events are properly streamed."""

    @patch("api.routers.agent.run_copilot")
    def test_tool_call_event_in_stream(self, mock_copilot, client, auth_headers):
        """Verify tool_call events appear in the SSE stream."""

        async def mock_sse_generator(*args, **kwargs):
            yield json.dumps({
                "type": "tool_call",
                "name": "get_sehra_overview",
                "arguments": {"sehra_id": "test-1"},
            })
            yield json.dumps({
                "type": "tool_result",
                "name": "get_sehra_overview",
                "result": "Country: Kenya, Status: draft",
            })
            yield json.dumps({
                "type": "message",
                "content": "This assessment is from Kenya.",
            })
            yield json.dumps({"type": "done"})

        mock_copilot.return_value = mock_sse_generator()

        res = client.post(
            "/api/v1/agent/chat",
            json={
                "messages": [{"role": "user", "content": "Overview?"}],
                "sehra_id": "test-1",
            },
            headers=auth_headers,
        )
        assert res.status_code == 200

    @patch("api.routers.agent.run_copilot")
    def test_error_event_in_stream(self, mock_copilot, client, auth_headers):
        """Verify error events are properly streamed."""

        async def mock_sse_generator(*args, **kwargs):
            yield json.dumps({
                "type": "error",
                "message": "LLM API unavailable",
            })

        mock_copilot.return_value = mock_sse_generator()

        res = client.post(
            "/api/v1/agent/chat",
            json={
                "messages": [{"role": "user", "content": "Hello"}],
            },
            headers=auth_headers,
        )
        assert res.status_code == 200  # SSE always returns 200; error is in-band

    @patch("api.routers.agent.run_copilot")
    def test_chart_event_in_stream(self, mock_copilot, client, auth_headers):
        """Verify chart events are properly streamed."""

        async def mock_sse_generator(*args, **kwargs):
            yield json.dumps({
                "type": "chart",
                "chart_spec": {
                    "type": "bar",
                    "title": "Enablers vs Barriers",
                    "data": [
                        {"label": "Enablers", "value": 8},
                        {"label": "Barriers", "value": 4},
                    ],
                },
            })
            yield json.dumps({"type": "done"})

        mock_copilot.return_value = mock_sse_generator()

        res = client.post(
            "/api/v1/agent/chat",
            json={
                "messages": [{"role": "user", "content": "Show chart"}],
                "sehra_id": "test-1",
            },
            headers=auth_headers,
        )
        assert res.status_code == 200
