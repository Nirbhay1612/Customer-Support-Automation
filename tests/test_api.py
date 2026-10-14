import pytest
from fastapi.testclient import TestClient

from main import app


client = TestClient(app)


# ============================================================
# BASIC API TESTS
# ============================================================

def test_root_endpoint():
    """Root endpoint should return application information."""

    response = client.get("/")

    assert response.status_code == 200

    data = response.json()

    assert data["name"] == "AI Automation System"
    assert data["status"] == "running"
    assert "version" in data


def test_health_endpoint():
    """Health endpoint should report healthy status."""

    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "healthy"}


# ============================================================
# API ROUTES TESTS
# ============================================================

def test_system_status():
    """System status endpoint should return operational status."""

    response = client.get("/api/status")

    assert response.status_code == 200

    data = response.json()

    assert data["success"] is True
    assert data["application"] == "AI Automation System"
    assert data["status"] == "operational"
    assert "version" in data
    assert "environment" in data


def test_api_health():
    """API health endpoint should return healthy."""

    response = client.get("/api/health")

    assert response.status_code == 200
    assert response.json() == {"status": "healthy"}


def test_system_info():
    """System info endpoint should return application details."""

    response = client.get("/api/info")

    assert response.status_code == 200

    data = response.json()

    assert data["name"] == "AI Automation System"
    assert "version" in data
    assert "environment" in data


# ============================================================
# WEBHOOK TESTS
# ============================================================

def test_webhook_order_created():
    """Valid order_created webhook should be accepted."""

    payload = {
        "event": "order_created",
        "data": {
            "order_id": "ORD-1001",
            "customer_id": "CUS-1001"
        }
    }

    response = client.post(
        "/webhooks/events",
        json=payload,
    )

    assert response.status_code == 200

    data = response.json()

    assert data["success"] is True
    assert data["event"] == "order_created"
    assert "message" in data


def test_webhook_refund_requested():
    """Valid refund webhook should be accepted."""

    payload = {
        "event": "refund_requested",
        "data": {
            "order_id": "ORD-1001",
            "reason": "Product damaged"
        }
    }

    response = client.post(
        "/webhooks/events",
        json=payload,
    )

    assert response.status_code == 200

    data = response.json()

    assert data["success"] is True
    assert data["event"] == "refund_requested"


def test_webhook_invalid_event():
    """Unsupported webhook events should be rejected."""

    payload = {
        "event": "invalid_event",
        "data": {}
    }

    response = client.post(
        "/webhooks/events",
        json=payload,
    )

    assert response.status_code == 400

    data = response.json()

    assert "Unsupported event" in data["detail"]


def test_webhook_missing_event():
    """Webhook without event should fail validation."""

    payload = {
        "data": {
            "order_id": "ORD-1001"
        }
    }

    response = client.post(
        "/webhooks/events",
        json=payload,
    )

    assert response.status_code == 422


def test_webhook_invalid_payload():
    """Webhook with invalid data type should fail validation."""

    payload = {
        "event": "order_created",
        "data": "invalid-data"
    }

    response = client.post(
        "/webhooks/events",
        json=payload,
    )

    assert response.status_code == 422


# ============================================================
# WEBHOOK SECURITY TEST
# ============================================================

def test_webhook_invalid_secret(monkeypatch):
    """Invalid webhook secret should be rejected when configured."""

    monkeypatch.setattr(
        "api.webhooks.settings.WEBHOOK_SECRET",
        "test-secret",
    )

    payload = {
        "event": "order_created",
        "data": {
            "order_id": "ORD-1001"
        }
    }

    response = client.post(
        "/webhooks/events",
        json=payload,
        headers={
            "X-Webhook-Secret": "wrong-secret"
        },
    )

    assert response.status_code == 401


def test_webhook_valid_secret(monkeypatch):
    """Correct webhook secret should be accepted."""

    monkeypatch.setattr(
        "api.webhooks.settings.WEBHOOK_SECRET",
        "test-secret",
    )

    payload = {
        "event": "order_created",
        "data": {
            "order_id": "ORD-1001"
        }
    }

    response = client.post(
        "/webhooks/events",
        json=payload,
        headers={
            "X-Webhook-Secret": "test-secret"
        },
    )

    assert response.status_code == 200
    assert response.json()["success"] is True