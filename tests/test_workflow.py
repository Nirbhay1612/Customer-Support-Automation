
"""
Tests for the AI Customer Support Automation workflows.

Run:
    python -m pytest tests/test_workflow.py -v
"""

from automation.router import route_automation, WORKFLOW_MAP
from automation.order_workflow import handle_order_workflow
from automation.refund_workflow import (
    check_refund_eligibility,
    handle_refund_workflow,
)
from automation.escalation import handle_escalation


# ============================================================
# ORDER WORKFLOW TESTS
# ============================================================

def test_order_workflow_success(monkeypatch):
    """Order workflow should return order information successfully."""

    fake_order = {
        "order_id": "ORD-1001",
        "status": "shipped",
        "tracking_id": "TRK-12345",
        "estimated_delivery": "2026-10-05",
    }

    monkeypatch.setattr(
        "automation.order_workflow.get_order",
        lambda order_id: fake_order,
    )
    monkeypatch.setattr(
        "automation.order_workflow.send_email",
        lambda **kwargs: True,
    )

    result = handle_order_workflow({
        "order_id": "ORD-1001",
        "customer_email": "customer@example.com",
    })

    assert result["success"] is True
    assert result["order_id"] == "ORD-1001"
    assert result["status"] == "shipped"


def test_order_workflow_missing_order_id():
    """Missing order ID should be rejected."""

    result = handle_order_workflow({
        "customer_email": "customer@example.com",
    })

    assert result["success"] is False
    assert "error" in result
    assert "order_id" in result["error"].lower()


def test_order_workflow_order_not_found(monkeypatch):
    """Unknown orders should be handled safely."""

    monkeypatch.setattr(
        "automation.order_workflow.get_order",
        lambda order_id: None,
    )

    result = handle_order_workflow({
        "order_id": "ORD-9999",
        "customer_email": "customer@example.com",
    })

    assert result["success"] is False
    assert "not found" in result["error"].lower()


# ============================================================
# REFUND ELIGIBILITY TESTS
# ============================================================

def test_refund_eligibility_valid_order():
    """A delivered order with an amount should be eligible."""

    result = check_refund_eligibility({
        "order_id": "ORD-1001",
        "status": "delivered",
        "amount": 999.0,
    })

    assert result["eligible"] is True


def test_refund_already_refunded():
    """Already-refunded orders should not be eligible."""

    result = check_refund_eligibility({
        "order_id": "ORD-1001",
        "status": "refunded",
        "amount": 999.0,
    })

    assert result["eligible"] is False


def test_refund_cancelled_order():
    """Cancelled orders should not be eligible."""

    result = check_refund_eligibility({
        "order_id": "ORD-1001",
        "status": "cancelled",
        "amount": 999.0,
    })

    assert result["eligible"] is False


def test_refund_missing_amount():
    """Orders without an amount should fail eligibility checks."""

    result = check_refund_eligibility({
        "order_id": "ORD-1001",
        "status": "delivered",
    })

    assert result["eligible"] is False


# ============================================================
# REFUND WORKFLOW TESTS
# ============================================================

def test_refund_workflow_success(monkeypatch):
    """Refund workflow should create a refund request."""

    fake_order = {
        "order_id": "ORD-1001",
        "customer_id": "CUS-1001",
        "status": "delivered",
        "amount": 999.0,
    }

    monkeypatch.setattr(
        "automation.refund_workflow.create_refund",
        lambda **kwargs: {
            "success": True,
            "refund_id": "REF-1001",
            "status": "pending",
        },
    )
    monkeypatch.setattr(
        "automation.refund_workflow.get_order",
        lambda order_id: fake_order,
    )
    monkeypatch.setattr(
        "automation.refund_workflow.send_email",
        lambda **kwargs: True,
    )

    result = handle_refund_workflow({
        "order_id": "ORD-1001",
        "customer_id": "CUS-1001",
        "customer_email": "customer@example.com",
        "reason": "Product damaged",
    })

    assert result["success"] is True
    assert result.get("status") in {"pending", "refund_pending"}

    refund_request = result.get("refund_request", {})
    order_id = result.get("order_id", refund_request.get("order_id"))
    amount = result.get("amount", refund_request.get("amount"))

    assert order_id == "ORD-1001"
    assert amount == 999.0


def test_refund_workflow_missing_order_id():
    """Refund workflow should reject a missing order ID."""

    result = handle_refund_workflow({
        "customer_id": "CUS-1001",
        "customer_email": "customer@example.com",
        "reason": "Product damaged",
    })

    assert result["success"] is False
    assert "error" in result


def test_refund_workflow_order_not_found(monkeypatch):
    """Refund workflow should handle orders that do not exist."""

    monkeypatch.setattr(
        "automation.refund_workflow.get_order",
        lambda order_id: None,
    )

    result = handle_refund_workflow({
        "order_id": "ORD-9999",
        "customer_id": "CUS-1001",
        "customer_email": "customer@example.com",
        "reason": "Product damaged",
    })

    assert result["success"] is False
    assert "not found" in result["error"].lower()


def test_refund_workflow_customer_mismatch(monkeypatch):
    """Refund should not be processed for another customer."""

    fake_order = {
        "order_id": "ORD-1001",
        "customer_id": "CUS-9999",
        "status": "delivered",
        "amount": 999.0,
    }

    monkeypatch.setattr(
        "automation.refund_workflow.get_order",
        lambda order_id: fake_order,
    )

    result = handle_refund_workflow({
        "order_id": "ORD-1001",
        "customer_id": "CUS-1001",
        "customer_email": "customer@example.com",
        "reason": "Product damaged",
    })

    assert result["success"] is False


# ============================================================
# ESCALATION TESTS
# ============================================================

def test_escalation_success(monkeypatch):
    """Escalation should create a nested escalation record."""

    monkeypatch.setattr(
        "automation.escalation.handle_notification",
        lambda data: {
            "success": True,
            "channel": "email",
        },
    )

    result = handle_escalation({
        "customer_id": "CUS-1001",
        "reason": "Customer requested human support",
        "priority": "high",
    })

    assert result["success"] is True
    assert "escalation" in result

    escalation = result["escalation"]

    assert escalation["customer_id"] == "CUS-1001"
    assert escalation["priority"] == "high"
    assert escalation["status"] == "pending"
    assert escalation["escalation_id"].startswith("ESC-")


def test_escalation_default_priority(monkeypatch):
    """Escalation should default to medium priority."""

    monkeypatch.setattr(
        "automation.escalation.handle_notification",
        lambda data: {"success": True},
    )

    result = handle_escalation({
        "customer_id": "CUS-1001",
        "reason": "Complex customer issue",
    })

    assert result["success"] is True
    assert result["escalation"]["priority"] == "medium"


# ============================================================
# ROUTER TESTS
# ============================================================

def test_router_order_status(monkeypatch):
    """Order-status requests should reach the mocked workflow."""

    expected = {
        "success": True,
        "workflow": "order",
    }

    monkeypatch.setitem(
        WORKFLOW_MAP,
        "order_status",
        lambda data: expected,
    )

    result = route_automation(
        "order_status",
        {"order_id": "ORD-1001"},
    )

    assert result["success"] is True
    assert result["action"] == "workflow_executed"
    assert result["result"] == expected


def test_router_refund(monkeypatch):
    """Refund requests should reach the mocked workflow."""

    expected = {
        "success": True,
        "workflow": "refund",
    }

    monkeypatch.setitem(
        WORKFLOW_MAP,
        "refund_request",
        lambda data: expected,
    )

    result = route_automation(
        "refund_request",
        {"order_id": "ORD-1001"},
    )

    assert result["success"] is True
    assert result["action"] == "workflow_executed"
    assert result["result"] == expected


def test_router_escalation(monkeypatch):
    """Escalation requests should reach the mocked workflow."""

    expected = {
        "success": True,
        "workflow": "escalation",
    }

    monkeypatch.setitem(
        WORKFLOW_MAP,
        "escalation",
        lambda data: expected,
    )

    result = route_automation(
        "escalation",
        {
            "customer_id": "CUS-1001",
            "reason": "Human support requested",
        },
    )

    assert result["success"] is True
    assert result["action"] == "workflow_executed"
    assert result["result"] == expected


def test_router_faq():
    """FAQ intent should return the RAG response action."""

    result = route_automation(
        "faq",
        {"message": "What is your refund policy?"},
    )

    assert result["success"] is True
    assert result["intent"] == "faq"
    assert result["action"] == "rag_response"


def test_router_unknown_intent():
    """Unknown intent should request clarification."""

    result = route_automation("unknown", {})

    assert result["success"] is True
    assert result["action"] == "clarification_required"


def test_router_unsupported_intent():
    """Unsupported intents should fail safely."""

    result = route_automation("invalid_intent", {})

    assert result["success"] is False
    assert result["action"] == "unsupported"
