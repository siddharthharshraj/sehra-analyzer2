"""Tests for codebook admin endpoints."""

import pytest
from unittest.mock import patch, MagicMock

MOCK_ITEM = {
    "id": "item-1",
    "section": "context",
    "question": "Test question?",
    "type": "yes_no",
    "has_scoring": True,
    "is_reverse": False,
    "score_yes": 1,
    "score_no": 0,
}


class TestListSections:
    @patch("api.routers.codebook.get_sections")
    def test_list_sections(self, mock_fn, client, auth_headers):
        mock_fn.return_value = ["context", "policy", "service_delivery"]
        res = client.get("/api/v1/codebook/sections", headers=auth_headers)
        assert res.status_code == 200
        assert "context" in res.json()


class TestListItems:
    @patch("api.routers.codebook.get_items_by_section")
    def test_list_items(self, mock_fn, client, auth_headers):
        mock_fn.return_value = [MOCK_ITEM]
        res = client.get(
            "/api/v1/codebook/items?section=context",
            headers=auth_headers,
        )
        assert res.status_code == 200
        assert len(res.json()) == 1


class TestCreateItem:
    @patch("api.routers.codebook.add_item")
    def test_create_requires_admin(self, mock_fn, client, auth_headers):
        res = client.post(
            "/api/v1/codebook/items",
            json={"section": "context", "question": "New?"},
            headers=auth_headers,  # analyst, not admin
        )
        assert res.status_code == 403

    @patch("api.routers.codebook.add_item")
    def test_create_success(self, mock_fn, client, admin_headers):
        mock_fn.return_value = MOCK_ITEM
        res = client.post(
            "/api/v1/codebook/items",
            json={"section": "context", "question": "New question?"},
            headers=admin_headers,
        )
        assert res.status_code == 200
        assert res.json()["question"] == "Test question?"


class TestDeleteItem:
    @patch("api.routers.codebook.remove_item")
    def test_delete_requires_admin(self, mock_fn, client, auth_headers):
        res = client.delete(
            "/api/v1/codebook/items/item-1",
            headers=auth_headers,
        )
        assert res.status_code == 403

    @patch("api.routers.codebook.remove_item")
    def test_delete_not_found(self, mock_fn, client, admin_headers):
        mock_fn.return_value = False
        res = client.delete(
            "/api/v1/codebook/items/nonexistent",
            headers=admin_headers,
        )
        assert res.status_code == 404

    @patch("api.routers.codebook.remove_item")
    def test_delete_success(self, mock_fn, client, admin_headers):
        mock_fn.return_value = True
        res = client.delete(
            "/api/v1/codebook/items/item-1",
            headers=admin_headers,
        )
        assert res.status_code == 204
