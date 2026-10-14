
"""
Custom exception hierarchy for the AI Customer Support Automation system.

Provides consistent, domain-specific exceptions for validation, AI services,
RAG, integrations, orders, refunds, authentication, and workflows.
"""

from __future__ import annotations


# ============================================================
# Base Exception
# ============================================================

class AutomationSystemError(Exception):
    """Base exception for application-specific errors."""

    default_message = "An automation system error occurred."

    def __init__(self, message: str | None = None) -> None:
        self.message = message if message is not None else self.default_message
        super().__init__(self.message)


# ============================================================
# Configuration & Validation
# ============================================================

class ValidationError(AutomationSystemError):
    """Raised when input or business-rule validation fails."""

    default_message = "Validation failed."


class ConfigurationError(AutomationSystemError):
    """Raised when application configuration is invalid."""

    default_message = "Configuration error."


# ============================================================
# AI & RAG
# ============================================================

class AIServiceError(AutomationSystemError):
    """Raised when an AI or LLM service fails."""

    default_message = "AI service error."


class RAGError(AutomationSystemError):
    """Raised when a retrieval-augmented generation operation fails."""

    default_message = "RAG operation failed."


class VectorStoreError(AutomationSystemError):
    """Raised when vector-store operations fail."""

    default_message = "Vector store operation failed."


# ============================================================
# Integrations & Workflows
# ============================================================

class IntegrationError(AutomationSystemError):
    """Raised when an external service integration fails."""

    default_message = "External integration failed."


class WorkflowError(AutomationSystemError):
    """Raised when an automation workflow fails."""

    default_message = "Workflow execution failed."


class WebhookError(AutomationSystemError):
    """Raised when webhook validation or processing fails."""

    default_message = "Webhook processing failed."


# ============================================================
# Customers & Orders
# ============================================================

class OrderNotFoundError(AutomationSystemError):
    """Raised when an order cannot be found."""

    def __init__(self, order_id: str) -> None:
        self.order_id = order_id
        super().__init__(f"Order not found: {order_id}")


class CustomerNotFoundError(AutomationSystemError):
    """Raised when a customer cannot be found."""

    def __init__(self, customer_id: str) -> None:
        self.customer_id = customer_id
        super().__init__(f"Customer not found: {customer_id}")


# ============================================================
# Refunds
# ============================================================

class RefundError(AutomationSystemError):
    """Raised when a refund operation fails."""

    default_message = "Refund operation failed."


class RefundNotEligibleError(RefundError):
    """Raised when an order is not eligible for a refund."""

    default_message = "Order is not eligible for refund."


# ============================================================
# Security & Access Control
# ============================================================

class AuthenticationError(AutomationSystemError):
    """Raised when authentication fails."""

    default_message = "Authentication failed."


class AuthorizationError(AutomationSystemError):
    """Raised when an operation is not authorized."""

    default_message = "Authorization failed."
