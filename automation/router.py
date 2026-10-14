
"""
Automation router.

Routes validated customer intents to their corresponding workflows
and returns a consistent result structure.
"""

import logging
from typing import Any, Callable

from automation.order_workflow import handle_order_workflow
from automation.refund_workflow import handle_refund_workflow
from automation.escalation import handle_escalation


logger = logging.getLogger(__name__)

Workflow = Callable[[dict[str, Any]], dict[str, Any]]


# ============================================================
# Intent -> Workflow Mapping
# ============================================================

WORKFLOW_MAP: dict[str, Workflow] = {
    "order_status": handle_order_workflow,
    "order_issue": handle_order_workflow,
    "refund_request": handle_refund_workflow,
    "return_request": handle_refund_workflow,
    "escalation": handle_escalation,
    "complaint": handle_escalation,
}


# ============================================================
# Result Helpers
# ============================================================

def _routing_result(
    *,
    success: bool,
    intent: str,
    action: str,
    message: str,
    result: Any = None,
) -> dict[str, Any]:
    """Build a consistent router response."""

    response: dict[str, Any] = {
        "success": success,
        "intent": intent,
        "action": action,
        "message": message,
    }

    if result is not None:
        response["result"] = result

    return response


# ============================================================
# Main Router
# ============================================================

def route_automation(
    intent: str,
    data: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """
    Route a customer intent to the appropriate workflow.

    Returns a consistent dictionary containing success, intent,
    action, message, and optionally the workflow result.
    """

    # --------------------------------------------------------
    # Validate intent
    # --------------------------------------------------------

    if not isinstance(intent, str) or not intent.strip():
        return _routing_result(
            success=False,
            intent="unknown",
            action="invalid_input",
            message="A valid intent is required.",
        )

    normalized_intent = intent.strip().lower()

    # --------------------------------------------------------
    # Validate workflow data
    # --------------------------------------------------------

    if data is None:
        workflow_data: dict[str, Any] = {}
    elif isinstance(data, dict):
        workflow_data = data
    else:
        return _routing_result(
            success=False,
            intent=normalized_intent,
            action="invalid_input",
            message="Workflow data must be a dictionary.",
        )

    logger.info(
        "Routing automation. intent=%s",
        normalized_intent,
    )

    # --------------------------------------------------------
    # FAQ
    # --------------------------------------------------------

    if normalized_intent == "faq":
        return _routing_result(
            success=True,
            intent=normalized_intent,
            action="rag_response",
            message="Route request to RAG.",
        )

    # --------------------------------------------------------
    # Unknown intent
    # --------------------------------------------------------

    if normalized_intent in {"unknown", "unknown_intent"}:
        return _routing_result(
            success=True,
            intent=normalized_intent,
            action="clarification_required",
            message="Additional information is required.",
        )

    # --------------------------------------------------------
    # Resolve workflow
    # --------------------------------------------------------

    workflow = WORKFLOW_MAP.get(normalized_intent)

    if workflow is None:
        logger.warning(
            "No workflow registered for intent=%s",
            normalized_intent,
        )

        return _routing_result(
            success=False,
            intent=normalized_intent,
            action="unsupported",
            message="No workflow available for this intent.",
        )

    # --------------------------------------------------------
    # Execute workflow
    # --------------------------------------------------------

    try:
        workflow_result = workflow(workflow_data)

        if not isinstance(workflow_result, dict):
            logger.error(
                "Workflow returned an invalid result type. intent=%s",
                normalized_intent,
            )

            return _routing_result(
                success=False,
                intent=normalized_intent,
                action="workflow_failed",
                message="The workflow returned an invalid response.",
            )

        if workflow_result.get("success") is not True:
            logger.warning(
                "Workflow reported failure. intent=%s",
                normalized_intent,
            )

            return _routing_result(
                success=False,
                intent=normalized_intent,
                action="workflow_failed",
                message="The workflow could not be completed.",
                result=workflow_result,
            )

        return _routing_result(
            success=True,
            intent=normalized_intent,
            action="workflow_executed",
            message="Workflow executed successfully.",
            result=workflow_result,
        )

    except Exception as exc:
        # Avoid logging customer data or exception messages.
        logger.error(
            "Workflow execution failed. intent=%s error_type=%s",
            normalized_intent,
            type(exc).__name__,
        )

        return _routing_result(
            success=False,
            intent=normalized_intent,
            action="workflow_failed",
            message="The workflow could not be completed.",
        )
