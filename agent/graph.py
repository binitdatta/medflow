"""
Phase 1 roles: NURSE, PHARMACIST, ADMISSIONS.
Physician / Finance / Management / Legal are wired into ROLE_CONFIG as
placeholders -- see README "Phase 2" section for how to add a new subgraph
without touching this file's structure.

Each role subgraph is a small ReAct loop:

    agent (LLM decides: answer, or call a tool)
      -> tools (executes any requested tool calls against the Flask REST API)
      -> back to agent
      -> END once the LLM responds with no further tool calls

Role is fixed for the whole graph run (never re-derived from user text), and
is used only to (a) pick the toolset/system prompt and (b) populate the
identity contextvars that tools use when calling the REST API.
"""
import operator
import time
from typing import Annotated, TypedDict

from langchain_anthropic import ChatAnthropic
from langchain_core.messages import AIMessage, BaseMessage, HumanMessage, SystemMessage, ToolMessage
from langgraph.graph import StateGraph, END

from .context import set_identity, current_staff_id, current_role, current_chat_session_id
from .subgraphs.nurse import NURSE_TOOLS, NURSE_SYSTEM_PROMPT
from .subgraphs.pharmacy import PHARMACY_TOOLS, PHARMACY_SYSTEM_PROMPT
from .subgraphs.admissions import ADMISSIONS_TOOLS, ADMISSIONS_SYSTEM_PROMPT
from services.logging_service import log_llm_call

from .subgraphs.physician import PHYSICIAN_TOOLS, PHYSICIAN_SYSTEM_PROMPT
from .subgraphs.finance import FINANCE_TOOLS, FINANCE_SYSTEM_PROMPT
from .subgraphs.management import MANAGEMENT_TOOLS, MANAGEMENT_SYSTEM_PROMPT
from .subgraphs.legal import LEGAL_TOOLS, LEGAL_SYSTEM_PROMPT

import os

ANTHROPIC_MODEL = os.getenv("ANTHROPIC_MODEL", "claude-sonnet-4-6")


class AgentState(TypedDict):
    messages: Annotated[list[BaseMessage], operator.add]


ROLE_CONFIG = {
    "NURSE": (NURSE_TOOLS, NURSE_SYSTEM_PROMPT),
    "PHARMACIST": (PHARMACY_TOOLS, PHARMACY_SYSTEM_PROMPT),
    "ADMISSIONS": (ADMISSIONS_TOOLS, ADMISSIONS_SYSTEM_PROMPT),
    "PHYSICIAN": (PHYSICIAN_TOOLS, PHYSICIAN_SYSTEM_PROMPT),
    "FINANCE": (FINANCE_TOOLS, FINANCE_SYSTEM_PROMPT),
    "MANAGEMENT": (MANAGEMENT_TOOLS, MANAGEMENT_SYSTEM_PROMPT),
    "LEGAL": (LEGAL_TOOLS, LEGAL_SYSTEM_PROMPT),
}

_COMPILED_GRAPHS = {}


def _build_graph(tools):
    llm = ChatAnthropic(model=ANTHROPIC_MODEL, temperature=0).bind_tools(tools)
    tool_map = {t.name: t for t in tools}

    def agent_node(state: AgentState):
        start = time.time()
        response = llm.invoke(state["messages"])
        latency_ms = int((time.time() - start) * 1000)

        usage = getattr(response, "usage_metadata", None) or {}
        input_tokens = usage.get("input_tokens")
        output_tokens = usage.get("output_tokens")
        if input_tokens is None or output_tokens is None:
            # Fallback for LangChain/langchain-anthropic versions that only
            # populate the raw provider usage block rather than the
            # standardized usage_metadata attribute.
            raw_usage = (getattr(response, "response_metadata", None) or {}).get("usage", {})
            input_tokens = input_tokens if input_tokens is not None else raw_usage.get("input_tokens")
            output_tokens = output_tokens if output_tokens is not None else raw_usage.get("output_tokens")

        try:
            log_llm_call(
                staff_id=current_staff_id.get(),
                actor_role=current_role.get(),
                chat_session_id=current_chat_session_id.get(),
                model=ANTHROPIC_MODEL,
                request_messages=state["messages"],
                response_message=response,
                input_tokens=input_tokens,
                output_tokens=output_tokens,
                latency_ms=latency_ms,
            )
        except Exception:
            pass  # logging must never break the chat turn itself

        return {"messages": [response]}

    def tools_node(state: AgentState):
        last = state["messages"][-1]
        results = []
        for call in last.tool_calls:
            tool_fn = tool_map[call["name"]]
            try:
                output = tool_fn.invoke(call["args"])
            except Exception as exc:  # keep the loop alive, surface the error to the LLM
                output = {"status": 500, "error": str(exc)}
            results.append(ToolMessage(content=str(output), tool_call_id=call["id"], name=call["name"]))
        return {"messages": results}

    def should_continue(state: AgentState):
        last = state["messages"][-1]
        if isinstance(last, AIMessage) and getattr(last, "tool_calls", None):
            return "tools"
        return "end"

    graph = StateGraph(AgentState)
    graph.add_node("agent", agent_node)
    graph.add_node("tools", tools_node)
    graph.set_entry_point("agent")
    graph.add_conditional_edges("agent", should_continue, {"tools": "tools", "end": END})
    graph.add_edge("tools", "agent")
    return graph.compile()


def _get_graph_for_role(role):
    if role not in _COMPILED_GRAPHS:
        tools, _ = ROLE_CONFIG[role]
        _COMPILED_GRAPHS[role] = _build_graph(tools)
    return _COMPILED_GRAPHS[role]


def run_agent(user_query: str, staff_id: int, role: str, hospital_scope: int = None,
              chat_history: list = None, chat_session_id: int = None) -> dict:
    if role not in ROLE_CONFIG:
        return {
            "response": (
                f"The '{role}' role doesn't have a chat assistant configured "
                "(this is expected for service/testing accounts like ADMIN, "
                "which use the REST API directly rather than the chat UI)."
            ),
            "tool_results": [],
        }

    set_identity(staff_id, role, hospital_scope, chat_session_id)
    tools, system_prompt = ROLE_CONFIG[role]
    graph = _get_graph_for_role(role)

    # chat_history is a list of {"sender": "USER"|"ASSISTANT", "content": str}
    # for prior turns in this session, oldest first. We reconstruct it as plain
    # Human/AI text turns -- NOT the raw intermediate tool_use/tool_result
    # messages from those turns (only the final response text of each turn is
    # stored in chat_messages). This is enough for the LLM to resolve a
    # follow-up like "yes please" against what it just asked, which is the
    # gap that caused HITL confirmations to silently lose context before this
    # fix. It does NOT give the LLM visibility into exactly which tools ran
    # in prior turns -- if that turns out to matter, upgrade to a LangGraph
    # checkpointer (e.g. MemorySaver keyed by session_id) instead.
    history_messages = []
    for turn in (chat_history or []):
        if turn["sender"] == "USER":
            history_messages.append(HumanMessage(content=turn["content"]))
        elif turn["sender"] == "ASSISTANT":
            history_messages.append(AIMessage(content=turn["content"]))

    initial_state = {
        "messages": [SystemMessage(content=system_prompt)] + history_messages + [HumanMessage(content=user_query)]
    }
    final_state = graph.invoke(initial_state, config={"recursion_limit": 12})

    final_ai_message = next(
        (m for m in reversed(final_state["messages"]) if isinstance(m, AIMessage)), None
    )
    tool_calls_used = [
        {"tool_name": m.name} for m in final_state["messages"] if isinstance(m, ToolMessage)
    ]

    return {
        "response": final_ai_message.content if final_ai_message else "No response generated.",
        "tool_results": tool_calls_used,
    }