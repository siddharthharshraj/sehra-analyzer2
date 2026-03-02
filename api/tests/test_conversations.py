"""Tests for conversation persistence, feedback, and correction endpoints."""

import pytest
from unittest.mock import patch


MOCK_CONVERSATION = {
    "id": "conv-123",
    "title": "Test conversation",
    "sehra_id": "sehra-1",
    "sehra_label": "Kenya - Nairobi",
    "messages": [
        {"id": "msg-1", "role": "user", "content": "Hello"},
        {"id": "msg-2", "role": "assistant", "content": "Hi there!"},
    ],
    "created_at": "2025-06-01T10:00:00",
    "updated_at": "2025-06-01T10:05:00",
}

MOCK_CONVERSATION_SUMMARY = {
    "id": "conv-123",
    "title": "Test conversation",
    "sehra_id": "sehra-1",
    "sehra_label": "Kenya - Nairobi",
    "message_count": 2,
    "created_at": "2025-06-01T10:00:00",
    "updated_at": "2025-06-01T10:05:00",
}

MOCK_CORRECTION = {
    "id": "corr-1",
    "user": "testuser",
    "sehra_id": "sehra-1",
    "original_text": "The barrier count is 5",
    "corrected_text": "The barrier count is 7",
    "context": "copilot_message",
    "message_id": "msg-2",
    "created_at": "2025-06-01T10:10:00",
}


# --- Conversation CRUD ---

class TestSaveConversation:
    @patch("api.routers.conversations.db")
    def test_save_success(self, mock_db, client, auth_headers):
        mock_db.save_conversation.return_value = "conv-123"
        mock_db.get_conversation.return_value = MOCK_CONVERSATION

        res = client.post(
            "/api/v1/conversations",
            json={
                "id": "conv-123",
                "title": "Test conversation",
                "messages": MOCK_CONVERSATION["messages"],
                "sehra_id": "sehra-1",
                "sehra_label": "Kenya - Nairobi",
            },
            headers=auth_headers,
        )
        assert res.status_code == 200
        data = res.json()
        assert data["id"] == "conv-123"
        assert data["title"] == "Test conversation"
        assert len(data["messages"]) == 2
        mock_db.save_conversation.assert_called_once()

    @patch("api.routers.conversations.db")
    def test_save_internal_error(self, mock_db, client, auth_headers):
        mock_db.save_conversation.return_value = "conv-123"
        mock_db.get_conversation.return_value = None

        res = client.post(
            "/api/v1/conversations",
            json={"id": "conv-123", "title": "Test", "messages": []},
            headers=auth_headers,
        )
        assert res.status_code == 500

    def test_save_no_auth(self, client):
        res = client.post("/api/v1/conversations", json={"id": "x", "title": "t"})
        assert res.status_code in (401, 422)


class TestListConversations:
    @patch("api.routers.conversations.db")
    def test_list_empty(self, mock_db, client, auth_headers):
        mock_db.list_conversations.return_value = []
        res = client.get("/api/v1/conversations", headers=auth_headers)
        assert res.status_code == 200
        assert res.json() == []

    @patch("api.routers.conversations.db")
    def test_list_returns_conversations(self, mock_db, client, auth_headers):
        mock_db.list_conversations.return_value = [MOCK_CONVERSATION_SUMMARY]
        res = client.get("/api/v1/conversations", headers=auth_headers)
        assert res.status_code == 200
        data = res.json()
        assert len(data) == 1
        assert data[0]["id"] == "conv-123"
        assert data[0]["message_count"] == 2

    def test_list_no_auth(self, client):
        res = client.get("/api/v1/conversations")
        assert res.status_code in (401, 422)


class TestGetConversation:
    @patch("api.routers.conversations.db")
    def test_get_success(self, mock_db, client, auth_headers):
        mock_db.get_conversation.return_value = MOCK_CONVERSATION
        res = client.get("/api/v1/conversations/conv-123", headers=auth_headers)
        assert res.status_code == 200
        data = res.json()
        assert data["id"] == "conv-123"
        assert len(data["messages"]) == 2

    @patch("api.routers.conversations.db")
    def test_get_not_found(self, mock_db, client, auth_headers):
        mock_db.get_conversation.return_value = None
        res = client.get("/api/v1/conversations/nonexistent", headers=auth_headers)
        assert res.status_code == 404


class TestDeleteConversation:
    @patch("api.routers.conversations.db")
    def test_delete_success(self, mock_db, client, auth_headers):
        mock_db.delete_conversation.return_value = True
        res = client.delete("/api/v1/conversations/conv-123", headers=auth_headers)
        assert res.status_code == 204
        mock_db.delete_conversation.assert_called_once_with("conv-123", "testuser")

    @patch("api.routers.conversations.db")
    def test_delete_not_found(self, mock_db, client, auth_headers):
        mock_db.delete_conversation.return_value = False
        res = client.delete("/api/v1/conversations/nonexistent", headers=auth_headers)
        assert res.status_code == 404


# --- Feedback ---

class TestSubmitFeedback:
    @patch("api.routers.conversations.db")
    def test_feedback_up(self, mock_db, client, auth_headers):
        mock_db.save_ai_feedback.return_value = "fb-1"
        res = client.post(
            "/api/v1/feedback",
            json={
                "message_id": "msg-2",
                "conversation_id": "conv-123",
                "rating": "up",
            },
            headers=auth_headers,
        )
        assert res.status_code == 201
        assert res.json()["id"] == "fb-1"
        mock_db.save_ai_feedback.assert_called_once()

    @patch("api.routers.conversations.db")
    def test_feedback_down(self, mock_db, client, auth_headers):
        mock_db.save_ai_feedback.return_value = "fb-2"
        res = client.post(
            "/api/v1/feedback",
            json={"message_id": "msg-2", "rating": "down"},
            headers=auth_headers,
        )
        assert res.status_code == 201

    @patch("api.routers.conversations.db")
    def test_feedback_invalid_rating(self, mock_db, client, auth_headers):
        res = client.post(
            "/api/v1/feedback",
            json={"message_id": "msg-2", "rating": "invalid"},
            headers=auth_headers,
        )
        assert res.status_code == 400

    def test_feedback_no_auth(self, client):
        res = client.post(
            "/api/v1/feedback",
            json={"message_id": "msg-2", "rating": "up"},
        )
        assert res.status_code in (401, 422)


# --- Corrections ---

class TestSubmitCorrection:
    @patch("api.routers.conversations.db")
    def test_submit_correction(self, mock_db, client, auth_headers):
        mock_db.save_ai_correction.return_value = "corr-1"
        res = client.post(
            "/api/v1/corrections",
            json={
                "original_text": "The barrier count is 5",
                "corrected_text": "The barrier count is 7",
                "context": "copilot_message",
                "sehra_id": "sehra-1",
                "message_id": "msg-2",
            },
            headers=auth_headers,
        )
        assert res.status_code == 201
        assert res.json()["id"] == "corr-1"
        mock_db.save_ai_correction.assert_called_once()

    def test_submit_correction_no_auth(self, client):
        res = client.post(
            "/api/v1/corrections",
            json={"original_text": "a", "corrected_text": "b"},
        )
        assert res.status_code in (401, 422)


class TestGetCorrections:
    @patch("api.routers.conversations.db")
    def test_get_corrections(self, mock_db, client, auth_headers):
        mock_db.get_ai_corrections.return_value = [MOCK_CORRECTION]
        res = client.get("/api/v1/corrections", headers=auth_headers)
        assert res.status_code == 200
        data = res.json()
        assert len(data) == 1
        assert data[0]["id"] == "corr-1"
        assert data[0]["corrected_text"] == "The barrier count is 7"

    @patch("api.routers.conversations.db")
    def test_get_corrections_with_sehra_filter(self, mock_db, client, auth_headers):
        mock_db.get_ai_corrections.return_value = [MOCK_CORRECTION]
        res = client.get(
            "/api/v1/corrections?sehra_id=sehra-1", headers=auth_headers
        )
        assert res.status_code == 200
        mock_db.get_ai_corrections.assert_called_once_with(
            user=None, sehra_id="sehra-1", limit=50
        )

    @patch("api.routers.conversations.db")
    def test_get_corrections_empty(self, mock_db, client, auth_headers):
        mock_db.get_ai_corrections.return_value = []
        res = client.get("/api/v1/corrections", headers=auth_headers)
        assert res.status_code == 200
        assert res.json() == []
