"""Data agent — read-only Q&A over the knowledge base (LangGraph ReAct)."""
from __future__ import annotations

from langchain_core.tools import StructuredTool
from langgraph.prebuilt import create_react_agent

from agent.llm import get_chat_model
from skills.rag_answer import answer_with_sources
from tools import READONLY_TOOLS

DATA_AGENT_SYSTEM_MESSAGE = """\
你是 HH-Research 的 **Data Agent（只读）**。

你只能查询知识库，**不能**创建、修改或删除任何数据。
使用提供的工具回答投研问题；优先 semantic_search / ask 做语义检索与 RAG。
回答要简洁、有据，引用来源 URL 或实体名。
"""


def _build_readonly_tools():
    tools = []
    for fn in READONLY_TOOLS:
        tools.append(
            StructuredTool.from_function(
                coroutine=fn,
                name=fn.__name__,
                description=(fn.__doc__ or fn.__name__)[:800],
            )
        )
    tools.append(
        StructuredTool.from_function(
            coroutine=answer_with_sources,
            name="answer_with_sources",
            description=(answer_with_sources.__doc__ or "")[:800],
        )
    )
    return tools


def build_data_agent():
    """Create a read-only ReAct agent for Q&A."""
    llm = get_chat_model(temperature=0.2)
    tools = _build_readonly_tools()
    return create_react_agent(llm, tools, state_modifier=DATA_AGENT_SYSTEM_MESSAGE)


async def ask_data_agent(question: str) -> str:
    """Run a single Q&A turn and return the final answer text."""
    agent = build_data_agent()
    result = await agent.ainvoke({"messages": [("user", question)]})
    messages = result.get("messages", [])
    if not messages:
        return ""
    last = messages[-1]
    content = getattr(last, "content", None) or (last.get("content") if isinstance(last, dict) else None)
    return content or str(last)


__all__ = ["build_data_agent", "ask_data_agent", "DATA_AGENT_SYSTEM_MESSAGE"]
