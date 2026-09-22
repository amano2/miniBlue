"""Enterprise Session Memory & Contextual Repair Module.

Maintains multi-turn conversation context and active action states keyed by session_id,
enabling conversational parameter repair and follow-up adjustments.
"""

from __future__ import annotations

from typing import Any


class SessionMemory:
    """Enterprise session state manager holding conversation turns and active action context."""

    def __init__(self, max_turns: int = 8) -> None:
        self.max_turns = max_turns
        self._sessions: dict[str, list[dict[str, Any]]] = {}
        self._action_context: dict[str, dict[str, Any]] = {}

    def get_history(self, session_id: str) -> list[dict[str, Any]]:
        """Returns the conversation history for a given session."""
        return self._sessions.get(session_id, [])

    def add_turn(
        self,
        session_id: str,
        user_message: str,
        assistant_response: str,
        agent_used: str,
        governance_decision: str | None = None,
        action_payload: dict[str, Any] | None = None,
    ) -> None:
        """Appends a turn to the session history, trimming to max_turns."""
        if session_id not in self._sessions:
            self._sessions[session_id] = []

        self._sessions[session_id].append(
            {
                "user": user_message,
                "assistant": assistant_response,
                "agent_used": agent_used,
                "governance_decision": governance_decision,
            }
        )

        if len(self._sessions[session_id]) > self.max_turns:
            self._sessions[session_id] = self._sessions[session_id][-self.max_turns :]

        if action_payload:
            self._action_context[session_id] = {
                "agent_used": agent_used,
                "governance_decision": governance_decision,
                "payload": action_payload,
            }

    def get_last_action_context(self, session_id: str) -> dict[str, Any] | None:
        """Retrieves the most recent action context for conversational negotiation/repair."""
        return self._action_context.get(session_id)

    def clear(self, session_id: str) -> None:
        """Clears session history and action context."""
        if session_id in self._sessions:
            del self._sessions[session_id]
        if session_id in self._action_context:
            del self._action_context[session_id]


# Global session memory singleton
memory_store = SessionMemory()
