import json
from typing import Generator

import httpx

import config
import tools

SYSTEM_PROMPT = (
    "You are a concise concept explainer. The user has selected some text and wants to understand it. "
    "Explain clearly, using Markdown formatting. If it's code, explain what it does. "
    "If it's a term or concept, define and contextualize it. "
    "Use tools when you need to verify facts, look up current information, or perform calculations. "
    "Keep responses focused and under 500 words unless the topic requires more depth. "
    "Reply in the same language as the selected text."
)

MAX_TOOL_ROUNDS = 5


def _build_headers(api_key: str) -> dict:
    return {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }


def stream_explain(text: str) -> Generator[str, None, None]:
    cfg = config.load()
    api_key = cfg["api_key"]
    base_url = cfg["api_base_url"].rstrip("/")
    model = cfg["model"]
    max_tokens = cfg["max_tokens"]

    if not api_key:
        yield "⚠️ Please set your API key in settings (tray icon → Settings)."
        return

    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": f"Explain this:\n\n{text}"},
    ]

    headers = _build_headers(api_key)

    for _ in range(MAX_TOOL_ROUNDS):
        body = {
            "model": model,
            "messages": messages,
            "max_tokens": max_tokens,
            "stream": True,
            "tools": tools.TOOL_DEFS,
        }

        tool_calls_acc: dict[int, dict] = {}
        content_chunks = []
        finish_reason = None

        try:
            with httpx.Client(timeout=60) as client:
                with client.stream(
                    "POST", f"{base_url}/chat/completions",
                    json=body, headers=headers,
                ) as resp:
                    if resp.status_code != 200:
                        error_body = resp.read().decode()
                        yield f"⚠️ API error {resp.status_code}: {error_body[:200]}"
                        return

                    for line in resp.iter_lines():
                        if not line.startswith("data: "):
                            continue
                        data = line[6:]
                        if data.strip() == "[DONE]":
                            break
                        try:
                            chunk = json.loads(data)
                        except json.JSONDecodeError:
                            continue

                        delta = chunk.get("choices", [{}])[0].get("delta", {})
                        fr = chunk.get("choices", [{}])[0].get("finish_reason")
                        if fr:
                            finish_reason = fr

                        if "content" in delta and delta["content"]:
                            content_chunks.append(delta["content"])
                            yield delta["content"]

                        if "tool_calls" in delta:
                            for tc in delta["tool_calls"]:
                                idx = tc["index"]
                                if idx not in tool_calls_acc:
                                    tool_calls_acc[idx] = {
                                        "id": tc.get("id", ""),
                                        "function": {"name": "", "arguments": ""},
                                    }
                                if tc.get("id"):
                                    tool_calls_acc[idx]["id"] = tc["id"]
                                fn = tc.get("function", {})
                                if fn.get("name"):
                                    tool_calls_acc[idx]["function"]["name"] += fn["name"]
                                if fn.get("arguments"):
                                    tool_calls_acc[idx]["function"]["arguments"] += fn["arguments"]

        except httpx.ConnectError:
            yield "⚠️ Cannot connect to API. Check your API base URL and network."
            return
        except Exception as e:
            yield f"⚠️ Error: {e}"
            return

        if not tool_calls_acc:
            return

        assistant_msg: dict = {"role": "assistant"}
        if content_chunks:
            assistant_msg["content"] = "".join(content_chunks)
        else:
            assistant_msg["content"] = None

        tc_list = []
        for idx in sorted(tool_calls_acc):
            tc = tool_calls_acc[idx]
            tc_list.append({
                "id": tc["id"],
                "type": "function",
                "function": tc["function"],
            })
        assistant_msg["tool_calls"] = tc_list
        messages.append(assistant_msg)

        for tc in tc_list:
            fn_name = tc["function"]["name"]
            fn_args = tc["function"]["arguments"]
            yield f"\n\n🔍 *Calling {fn_name}...*\n\n"
            result = tools.execute(fn_name, fn_args)
            messages.append({
                "role": "tool",
                "tool_call_id": tc["id"],
                "content": result,
            })

    yield "\n\n⚠️ Reached maximum tool call rounds."
