# Assignment Research Agent

A small CrewAI project that creates an evidence-linked research brief from an assignment prompt. It uses three sequential agents:

1. **Search Specialist** — searches the public web and inspects relevant public pages.
2. **Data Synthesizer** — groups findings, compares evidence, and flags limitations.
3. **Academic Writer** — writes a cited research brief and outline for the student to develop.

The project uses CrewAI custom tools with `ddgs` search and a bounded HTML page scraper. Search results are leads; the researcher is instructed to verify sources by opening their pages. The scraper only fetches public HTTP/HTTPS HTML pages, rejects non-public host addresses, limits request duration and page size, and does not follow redirects.

## Requirements

- Python 3.10–3.13
- A Google AI Studio Gemini API key
- Internet access for search and public-page retrieval

## Setup on Windows

From this folder in PowerShell:

```powershell
py -3.13 -m venv .venv
.\.venv\Scripts\python.exe -m pip install --upgrade pip
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
if (-not (Test-Path .env)) { Copy-Item .env.example .env }
```

Edit `.env` and set `GEMINI_API_KEY` to your Google AI Studio key. The default model is `gemini/gemini-3.6-flash`; change `GEMINI_MODEL_NAME` if you want another Gemini model supported by CrewAI.

## Run

```powershell
.\.venv\Scripts\python.exe main.py "How does urban green space affect public health?" --level undergraduate --citation-style "APA 7"
```

The Markdown brief is written to `output/research_brief.md` by default. Choose another destination with `--output`.

## Judge presentation site

The static, interactive presentation is in `judge-site/`. It explains the agent handoffs, shows the structure of the brief, and includes a copyable judge pitch and demo command. It does not run Gemini in the browser.

To preview it locally on Windows, open PowerShell in `judge-site/` and run:

```powershell
py -3.13 -m http.server 8000
```

Then visit `http://localhost:8000` in your browser.

## Notes

- Live model calls require a valid API key and may incur provider charges.
- Public websites can block automated requests, change their markup, or return incomplete content. Review every citation and source yourself.
- The output is a research aid and outline, not a finished assignment.
