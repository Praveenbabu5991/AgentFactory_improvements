"""@tool wrapper for the response formatter (UI bridge)."""

import json

from langchain_core.tools import tool

from agent_factory_core.tools._internal import response_formatter as _impl


@tool
def format_response_for_user(
    response_text: str,
    force_choices: str = "",
    choice_type: str = "single_select",
    allow_free_input: bool = True,
    input_hint: str = "",
    input_placeholder: str = "",
) -> str:
    """Format agent response for the frontend with interactive choices.

    MUST be called before EVERY response to the user. Structures the
    response as JSON that the frontend renders as text + buttons.

    Args:
        response_text: Main message text (markdown supported).
        force_choices: JSON array of choice objects with id, label, value, icon, description.
        choice_type: Type of choice UI (single_select/multi_select/confirmation/menu).
        allow_free_input: Whether to show free text input alongside buttons.
        input_hint: Hint text below the input field.
        input_placeholder: Placeholder text in the input field.
    """
    result = _impl.format_response_for_user(
        response_text=response_text,
        force_choices=force_choices or None,
        choice_type=choice_type,
        allow_free_input=allow_free_input,
        input_hint=input_hint,
        input_placeholder=input_placeholder,
    )
    # Result is already JSON string from the internal implementation
    json_str = result if isinstance(result, str) else json.dumps(result)

    # Append a stop signal that the LLM sees in the ToolMessage.
    # This mechanically reinforces the prompt-level STOP instruction.
    # The streaming layer strips this suffix before sending to the frontend.
    return (
        json_str
        + "\n\n---\n"
        "IMPORTANT: This response has been delivered to the user's screen with interactive buttons. "
        "Your turn is COMPLETE. STOP IMMEDIATELY. "
        "Do NOT call any more tools, do NOT delegate to subagents, do NOT generate text. "
        "The user will click a button or type a response when ready."
    )
