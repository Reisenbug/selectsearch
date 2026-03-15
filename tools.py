import json
import urllib.parse

import httpx
from bs4 import BeautifulSoup
from simpleeval import simple_eval

TOOL_DEFS = [
    {
        "type": "function",
        "function": {
            "name": "web_search",
            "description": "Search the web for current information using DuckDuckGo.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "Search query"}
                },
                "required": ["query"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "wikipedia_lookup",
            "description": "Look up a concept or term on Wikipedia.",
            "parameters": {
                "type": "object",
                "properties": {
                    "title": {"type": "string", "description": "Article title"}
                },
                "required": ["title"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "calculate",
            "description": "Evaluate a mathematical expression.",
            "parameters": {
                "type": "object",
                "properties": {
                    "expression": {"type": "string", "description": "Math expression, e.g. '2**10 + 3*5'"}
                },
                "required": ["expression"],
            },
        },
    },
]

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"
}


def web_search(query: str) -> str:
    url = "https://html.duckduckgo.com/html/"
    try:
        r = httpx.post(url, data={"q": query}, headers=HEADERS, timeout=10, follow_redirects=True)
        soup = BeautifulSoup(r.text, "html.parser")
        results = []
        for item in soup.select(".result")[:3]:
            title_el = item.select_one(".result__title a")
            snippet_el = item.select_one(".result__snippet")
            if title_el:
                title = title_el.get_text(strip=True)
                snippet = snippet_el.get_text(strip=True) if snippet_el else ""
                href = title_el.get("href", "")
                results.append(f"**{title}**\n{snippet}\n{href}")
        return "\n\n".join(results) if results else "No results found."
    except Exception as e:
        return f"Search error: {e}"


def wikipedia_lookup(title: str) -> str:
    slug = urllib.parse.quote(title.replace(" ", "_"))
    url = f"https://en.wikipedia.org/api/rest_v1/page/summary/{slug}"
    try:
        r = httpx.get(url, headers=HEADERS, timeout=10, follow_redirects=True)
        if r.status_code == 404:
            return f"No Wikipedia article found for '{title}'."
        data = r.json()
        extract = data.get("extract", "")
        page_url = data.get("content_urls", {}).get("desktop", {}).get("page", "")
        return f"{extract}\n\nSource: {page_url}" if extract else "No content found."
    except Exception as e:
        return f"Wikipedia error: {e}"


def calculate(expression: str) -> str:
    try:
        result = simple_eval(expression)
        return str(result)
    except Exception as e:
        return f"Calculation error: {e}"


EXECUTORS = {
    "web_search": lambda args: web_search(args["query"]),
    "wikipedia_lookup": lambda args: wikipedia_lookup(args["title"]),
    "calculate": lambda args: calculate(args["expression"]),
}


def execute(name: str, arguments: str) -> str:
    try:
        args = json.loads(arguments)
    except json.JSONDecodeError:
        return f"Invalid JSON arguments: {arguments}"
    executor = EXECUTORS.get(name)
    if not executor:
        return f"Unknown tool: {name}"
    return executor(args)
