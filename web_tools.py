"""Search and safely fetch public web pages for the research agent."""

from __future__ import annotations

import ipaddress
import socket
from typing import Type
from urllib.parse import urlparse

import requests
from bs4 import BeautifulSoup
from crewai.tools import BaseTool
from ddgs import DDGS
from pydantic import BaseModel, Field


class SearchInput(BaseModel):
    query: str = Field(..., description="Focused web search query")
    max_results: int = Field(5, ge=1, le=8, description="Maximum results to return")


class WebSearchTool(BaseTool):
    name: str = "Web Search"
    description: str = (
        "Search the public web for source candidates. Returns titles, URLs, and "
        "snippets; verify important results with the public page scraper."
    )
    args_schema: Type[BaseModel] = SearchInput

    def _run(self, query: str, max_results: int = 5) -> str:
        try:
            results = DDGS().text(query, max_results=max_results, safesearch="moderate")
        except Exception as exc:
            return f"Search failed: {type(exc).__name__}: {exc}"

        if not results:
            return "No search results were returned. Try a narrower or alternate query."

        lines = []
        for index, result in enumerate(results[:max_results], start=1):
            title = result.get("title", "Untitled")
            url = result.get("href", "")
            snippet = result.get("body", "")
            lines.append(f"{index}. {title}\nURL: {url}\nSnippet: {snippet}")
        return "\n\n".join(lines)


class ScrapeInput(BaseModel):
    url: str = Field(..., description="Public HTTP or HTTPS page URL to read")


class PublicPageScraperTool(BaseTool):
    name: str = "Public Page Scraper"
    description: str = (
        "Fetch and extract readable text from a public HTML page. Only public "
        "HTTP/HTTPS hosts are allowed; page size and request time are limited."
    )
    args_schema: Type[BaseModel] = ScrapeInput

    @staticmethod
    def _validate_public_url(url: str) -> str | None:
        parsed = urlparse(url)
        if parsed.scheme not in {"http", "https"} or not parsed.hostname:
            return "Only absolute HTTP or HTTPS URLs are allowed."
        if parsed.username or parsed.password:
            return "URLs containing credentials are not allowed."
        host = parsed.hostname.rstrip(".").lower()
        if host == "localhost" or host.endswith(".localhost") or host.endswith(".local"):
            return "Local and private hosts are not allowed."
        try:
            addresses = {ipaddress.ip_address(host)}
        except ValueError:
            try:
                addresses = {
                    ipaddress.ip_address(item[4][0])
                    for item in socket.getaddrinfo(host, parsed.port or (443 if parsed.scheme == "https" else 80))
                }
            except OSError:
                return "The host could not be resolved."
        if not addresses or any(
            not address.is_global for address in addresses
        ):
            return "Local, private, or reserved network addresses are not allowed."
        return None

    def _run(self, url: str) -> str:
        error = self._validate_public_url(url)
        if error:
            return error

        try:
            response = requests.get(
                url,
                headers={"User-Agent": "AssignmentResearchAgent/1.0 (+public academic research)"},
                timeout=(5, 15),
                allow_redirects=False,
                stream=True,
            )
            if 300 <= response.status_code < 400:
                return "The page redirects; search for its final public URL and try that URL."
            response.raise_for_status()
            content_type = response.headers.get("Content-Type", "").lower()
            if "text/html" not in content_type and "application/xhtml+xml" not in content_type:
                return f"Unsupported content type: {content_type or 'unknown'} (HTML only)."

            chunks = []
            size = 0
            for chunk in response.iter_content(chunk_size=8192):
                if not chunk:
                    continue
                size += len(chunk)
                if size > 1_500_000:
                    return "Page is larger than the 1.5 MB limit."
                chunks.append(chunk)
            html = b"".join(chunks)
            soup = BeautifulSoup(html, "html.parser")
            for node in soup(["script", "style", "noscript", "svg"]):
                node.decompose()
            title = soup.title.get_text(" ", strip=True) if soup.title else "Untitled page"
            text = " ".join(soup.stripped_strings)
            if not text:
                return f"No readable text found on {url}."
            return f"Title: {title}\nURL: {url}\n\n{text[:12000]}"
        except requests.RequestException as exc:
            return f"Page fetch failed: {type(exc).__name__}: {exc}"
        finally:
            if "response" in locals():
                response.close()
