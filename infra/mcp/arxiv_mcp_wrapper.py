#!/usr/bin/env python3
"""
arXiv MCP Server Wrapper
Fixes an issue where MCP clients (like Antigravity IDE, Cursor, Claude Code)
request prompts without arguments (prompts/get) when selecting them from the UI menu,
which previously caused arxiv-mcp-server to crash with ValueError:
"No arguments provided for prompt: <name>".

This wrapper supplies sensible default placeholders when arguments are omitted,
while preserving all custom arguments when provided by the client/user.
"""

import sys
from arxiv_mcp_server import main as arxiv_main
from arxiv_mcp_server import server
from arxiv_mcp_server.prompts.prompts import PROMPTS

# Make prompt arguments non-mandatory in metadata so client menus don't fail validation
for p in PROMPTS.values():
    if p.arguments:
        for arg in p.arguments:
            arg.required = False

orig_handler_get_prompt = server.handler_get_prompt


async def patched_get_prompt(
    name: str,
    arguments: dict[str, str] | None = None,
    session_id: str | None = None,
):
    if arguments is None:
        arguments = {}

    defaults = {
        "topic": "[Nhập chủ đề nghiên cứu / Research topic, ví dụ: Machine Learning for Stock Trend Prediction]",
        "paper_id": "[Nhập mã arXiv, ví dụ: 2301.12345]",
        "paper_ids": "[Nhập danh sách mã arXiv cách nhau bởi dấu phẩy, ví dụ: 2301.12345, 2402.67890]",
        "expertise_level": "intermediate",
        "time_period": "last 5 years",
        "domain": "cs.AI, q-fin",
        "synthesis_type": "comprehensive",
    }

    merged_args = {}
    for k, v in defaults.items():
        val = arguments.get(k)
        merged_args[k] = val if val else v
    for k, v in arguments.items():
        if v:
            merged_args[k] = v

    return await orig_handler_get_prompt(name, merged_args, session_id)


server.handler_get_prompt = patched_get_prompt

if __name__ == "__main__":
    arxiv_main()
