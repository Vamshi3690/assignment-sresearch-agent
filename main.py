"""Three-agent assignment research workflow built with CrewAI."""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

from dotenv import load_dotenv

# CrewAI emits Unicode status icons; force UTF-8 so Windows legacy consoles
# don't turn event logging into additional errors.
for output_stream in (sys.stdout, sys.stderr):
    if hasattr(output_stream, "reconfigure"):
        try:
            output_stream.reconfigure(encoding="utf-8", errors="replace")
        except (OSError, ValueError):
            pass

PROJECT_DIR = Path(__file__).resolve().parent
load_dotenv(PROJECT_DIR / ".env")

from crewai import Agent, Crew, LLM, Process, Task
from web_tools import PublicPageScraperTool, WebSearchTool


def build_crew(topic: str, level: str, citation_style: str, output_path: Path) -> Crew:
    """Build a sequential research, synthesis, and writing crew."""
    api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
    if not api_key:
        raise RuntimeError("Set GEMINI_API_KEY (or GOOGLE_API_KEY) in .env first.")
    llm = LLM(
        model=os.getenv("GEMINI_MODEL_NAME", "gemini/gemini-3.6-flash"),
        api_key=api_key,
    )

    search_specialist = Agent(
        role="Search Specialist",
        goal=(
            "Find credible, relevant sources for the assignment topic and capture "
            "verifiable evidence with accurate source details."
        ),
        backstory=(
            "You are a careful academic researcher. You search broadly, prioritize "
            "primary and scholarly sources, inspect source pages, and distinguish "
            "evidence from search-result snippets."
        ),
        tools=[WebSearchTool(), PublicPageScraperTool()],
        llm=llm,
        allow_delegation=False,
        verbose=True,
        max_iter=8,
    )

    data_synthesizer = Agent(
        role="Data Synthesizer",
        goal=(
            "Organize the retrieved evidence into themes, compare findings, and "
            "identify limitations and disagreements without adding unsupported claims."
        ),
        backstory=(
            "You are an evidence analyst who traces every claim to the supplied "
            "sources, separates consensus from disagreement, and flags gaps."
        ),
        llm=llm,
        allow_delegation=False,
        verbose=True,
        max_iter=6,
    )

    academic_writer = Agent(
        role="Academic Writer",
        goal=(
            "Turn the evidence synthesis into a clear, well-structured research "
            "brief and outline that helps a student develop their own assignment."
        ),
        backstory=(
            "You write academically, cite only sources provided by the research "
            "team, avoid invented references, and clearly label uncertainty."
        ),
        llm=llm,
        allow_delegation=False,
        verbose=True,
        max_iter=6,
    )

    research_task = Task(
        description=(
            f"Research this assignment topic: {topic}\n"
            f"Intended academic level: {level}.\n\n"
            "Use web search to identify 5–8 useful sources. Prefer peer-reviewed "
            "research, public institutions, and primary sources. Open relevant "
            "public pages with the scraper and capture each source's title, author "
            "or organization, publication date when visible, URL, and the specific "
            "evidence it supports. Search snippets alone are not evidence. Exclude "
            "sources you could not verify. Return structured notes and flag gaps."
        ),
        expected_output=(
            "A source list with title, author/organization, date if available, URL, "
            "and concise evidence notes for each verified source, followed by gaps."
        ),
        agent=search_specialist,
    )

    synthesis_task = Task(
        description=(
            "Synthesize the preceding research notes. Group evidence into 3–5 "
            "themes, compare agreement and disagreement, note limitations and "
            "missing evidence, and map each factual point to source URLs. Do not "
            "introduce claims or references that are absent from the research notes."
        ),
        expected_output=(
            "An evidence synthesis with themes, supporting source URLs, areas of "
            "disagreement, limitations, and unanswered questions."
        ),
        agent=data_synthesizer,
        context=[research_task],
    )

    writing_task = Task(
        description=(
            f"Write a student-facing research brief for: {topic}\n"
            f"Academic level: {level}. Citation style: {citation_style}.\n\n"
            "Use the synthesis and its verified source details to produce: (1) a "
            "concise overview, (2) thematic evidence notes, (3) a balanced outline "
            "the student can develop, (4) open questions/limitations, and (5) a "
            "references list. Cite claims in the requested style where source data "
            "allows; include direct URLs. Never invent authors, dates, findings, or "
            "citations. This is a research aid, not a completed assignment."
        ),
        expected_output=(
            "A Markdown research brief with evidence-linked themes, an assignment "
            "outline, limitations, and references with URLs."
        ),
        agent=academic_writer,
        context=[synthesis_task],
        output_file=str(output_path),
    )

    return Crew(
        agents=[search_specialist, data_synthesizer, academic_writer],
        tasks=[research_task, synthesis_task, writing_task],
        process=Process.sequential,
        verbose=True,
    )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Create a cited research brief using a three-agent CrewAI workflow."
    )
    parser.add_argument("topic", help="Assignment topic or research question")
    parser.add_argument("--level", default="undergraduate", help="Academic level")
    parser.add_argument("--citation-style", default="APA 7", help="Citation style")
    parser.add_argument(
        "--output",
        type=Path,
        default=PROJECT_DIR / "output" / "research_brief.md",
        help="Where to save the Markdown research brief",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if not (os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")):
        print(
            "GEMINI_API_KEY is missing. Add your Google AI Studio key to .env.",
            file=sys.stderr,
        )
        return 2

    output_path = args.output.expanduser().resolve()
    output_path.parent.mkdir(parents=True, exist_ok=True)

    try:
        result = build_crew(
            topic=args.topic,
            level=args.level,
            citation_style=args.citation_style,
            output_path=output_path,
        ).kickoff()
    except Exception as exc:  # provide a concise CLI error while preserving traceback on debug
        print(f"Research run failed: {exc}", file=sys.stderr)
        if os.getenv("DEBUG"):
            raise
        return 1

    print(f"\nResearch brief saved to: {output_path}")
    print(result)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
