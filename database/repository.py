
"""
Database repository layer.

Provides database operations for customers, orders, refunds,
escalations, and automation logs.
"""

import logging
import uuid
from typing import Optional, TypeVar

from sqlalchemy.orm import Session

from database.models import (
    AutomationLog,
    Customer,
    Escalation,
    Order,
    RefundRequest,
)


logger = logging.getLogger(__name__)

ModelT = TypeVar(
    "ModelT",
    Customer,
    Order,
    RefundRequest,
    Escalation,
    AutomationLog,
)


# ============================================================
# Shared Database Helpers
# ============================================================

def _save(
    db: Session,
    instance: ModelT,
    operation: str,
) -> ModelT:
    """
    Commit a database write and refresh the saved instance.

    Roll back the session and re-raise the original exception
    if the operation fails.
    """

    try:
        db.add(instance)
        db.commit()
        db.refresh(instance)

        return instance

    except Exception:
        try:
            db.rollback()
        except Exception:
            logger.exception(
                "Rollback failed after database operation: %s",
                operation,
            )

        logger.exception(
            "Database operation failed: %s",
            operation,
        )
        raise


# ============================================================
# Customer
# ============================================================

def create_customer(
    db: Session,
    customer_id: str,
    name: Optional[str] = None,
    email: Optional[str] = None,
    phone: Optional[str] = None,
) -> Customer:
    """Create and return a customer."""

    customer = Customer(
        customer_id=customer_id,
        name=name,
        email=email,
        phone=phone,
    )

    return _save(db, customer, "create_customer")


def get_customer(
    db: Session,
    customer_id: str,
) -> Optional[Customer]:
    """Retrieve a customer by its external customer ID."""

    return (
        db.query(Customer)
        .filter(Customer.customer_id == customer_id)
        .first()
    )


# ============================================================
# Orders
# ============================================================

def create_order(
    db: Session,
    order_id: str,
    customer_id: int,
    status: str = "pending",
    amount: float = 0.0,
    tracking_id: Optional[str] = None,
    estimated_delivery: Optional[str] = None,
) -> Order:
    """Create and return an order."""

    order = Order(
        order_id=order_id,
        customer_id=customer_id,
        status=status,
        amount=amount,
        tracking_id=tracking_id,
        estimated_delivery=estimated_delivery,
    )

    return _save(db, order, "create_order")


def get_order(
    db: Session,
    order_id: str,
) -> Optional[Order]:
    """Retrieve an order by its external order ID."""

    return (
        db.query(Order)
        .filter(Order.order_id == order_id)
        .first()
    )


def update_order_status(
    db: Session,
    order_id: str,
    status: str,
) -> Optional[Order]:
    """Update an order's status."""

    order = get_order(db, order_id)

    if order is None:
        return None

    order.status = status

    return _save(db, order, "update_order_status")


# ============================================================
# Refund Requests
# ============================================================

def create_refund_request(
    db: Session,
    order_id: int,
    customer_id: int,
    reason: str,
    amount: float,
) -> RefundRequest:
    """Create and return a refund request."""

    refund = RefundRequest(
        refund_id=f"REF-{uuid.uuid4().hex[:8].upper()}",
        order_id=order_id,
        customer_id=customer_id,
        reason=reason,
        amount=amount,
        status="pending",
    )

    saved_refund = _save(
        db,
        refund,
        "create_refund_request",
    )

    logger.info(
        "Refund request created: %s",
        saved_refund.refund_id,
    )

    return saved_refund


def get_refund_request(
    db: Session,
    refund_id: str,
) -> Optional[RefundRequest]:
    """Retrieve a refund request by its external refund ID."""

    return (
        db.query(RefundRequest)
        .filter(RefundRequest.refund_id == refund_id)
        .first()
    )


def update_refund_status(
    db: Session,
    refund_id: str,
    status: str,
) -> Optional[RefundRequest]:
    """Update a refund request's status."""

    refund = get_refund_request(db, refund_id)

    if refund is None:
        return None

    refund.status = status

    return _save(db, refund, "update_refund_status")


# ============================================================
# Escalations
# ============================================================

def create_escalation(
    db: Session,
    customer_id: int,
    reason: str,
    priority: str = "medium",
) -> Escalation:
    """Create and return a support escalation."""

    escalation = Escalation(
        escalation_id=f"ESC-{uuid.uuid4().hex[:8].upper()}",
        customer_id=customer_id,
        reason=reason,
        priority=priority,
        status="pending",
    )

    saved_escalation = _save(
        db,
        escalation,
        "create_escalation",
    )

    logger.info(
        "Escalation created: %s",
        saved_escalation.escalation_id,
    )

    return saved_escalation


def get_escalation(
    db: Session,
    escalation_id: str,
) -> Optional[Escalation]:
    """Retrieve an escalation by its external escalation ID."""

    return (
        db.query(Escalation)
        .filter(Escalation.escalation_id == escalation_id)
        .first()
    )


def update_escalation_status(
    db: Session,
    escalation_id: str,
    status: str,
) -> Optional[Escalation]:
    """Update an escalation's status."""

    escalation = get_escalation(db, escalation_id)

    if escalation is None:
        return None

    escalation.status = status

    return _save(
        db,
        escalation,
        "update_escalation_status",
    )


# ============================================================
# Automation Logs
# ============================================================

def create_automation_log(
    db: Session,
    event_type: str,
    customer_id: Optional[str] = None,
    intent: Optional[str] = None,
    status: str = "success",
    message: Optional[str] = None,
    execution_time: Optional[float] = None,
) -> AutomationLog:
    """Create and return an automation execution log."""

    log_entry = AutomationLog(
        event_type=event_type,
        customer_id=customer_id,
        intent=intent,
        status=status,
        message=message,
        execution_time=execution_time,
    )

    return _save(
        db,
        log_entry,
        "create_automation_log",
    )
