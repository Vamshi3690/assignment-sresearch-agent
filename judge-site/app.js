const agents = {
  search: {
    number: "AGENT 01",
    chip: "SOURCE DISCOVERY",
    symbol: "⌕",
    title: "Search Specialist",
    description: "Searches for useful public sources, then opens relevant pages to check what they actually say. Search snippets are leads, not evidence.",
    output: "A source list with URLs, visible author and date details, evidence notes, and gaps.",
    footer: "Search results are verified against page content."
  },
  synthesis: {
    number: "AGENT 02",
    chip: "EVIDENCE MAPPING",
    symbol: "⌘",
    title: "Data Synthesizer",
    description: "Groups findings into themes, compares agreement and disagreement, and names limitations or missing evidence without adding unsupported claims.",
    output: "An evidence map that connects each theme and open question to its supporting source URLs.",
    footer: "The synthesis works from the researcher’s source notes."
  },
  writer: {
    number: "AGENT 03",
    chip: "STUDENT-LED WRITING",
    symbol: "¶",
    title: "Academic Writer",
    description: "Turns the evidence synthesis into a clear brief and an outline the student can develop in their own words.",
    output: "A Markdown brief with evidence notes, an outline, limitations, and references.",
    footer: "The output is a research aid, not a finished assignment."
  }
};

const tabs = Array.from(document.querySelectorAll(".agent-tab"));
const panel = document.getElementById("agent-panel");

function selectAgent(key, focusTab = false) {
  const agent = agents[key];
  if (!agent) return;

  tabs.forEach((tab) => {
    const selected = tab.dataset.agent === key;
    tab.classList.toggle("is-active", selected);
    tab.setAttribute("aria-selected", String(selected));
    tab.tabIndex = selected ? 0 : -1;
    if (selected && focusTab) tab.focus();
  });

  panel.setAttribute("aria-labelledby", `tab-${key}`);
  document.getElementById("panel-number").textContent = agent.number;
  document.getElementById("panel-chip").textContent = agent.chip;
  document.getElementById("panel-symbol").textContent = agent.symbol;
  document.getElementById("panel-title").textContent = agent.title;
  document.getElementById("panel-description").textContent = agent.description;
  document.getElementById("panel-output").textContent = agent.output;
  document.getElementById("panel-footer").textContent = agent.footer;
}

tabs.forEach((tab, index) => {
  tab.addEventListener("click", () => selectAgent(tab.dataset.agent));
  tab.addEventListener("keydown", (event) => {
    if (!["ArrowDown", "ArrowUp", "Home", "End"].includes(event.key)) return;
    event.preventDefault();
    let nextIndex = index;
    if (event.key === "ArrowDown") nextIndex = (index + 1) % tabs.length;
    if (event.key === "ArrowUp") nextIndex = (index - 1 + tabs.length) % tabs.length;
    if (event.key === "Home") nextIndex = 0;
    if (event.key === "End") nextIndex = tabs.length - 1;
    selectAgent(tabs[nextIndex].dataset.agent, true);
  });
});

async function copyText(text, successMessage) {
  const status = document.getElementById("copy-status");
  try {
    await navigator.clipboard.writeText(text);
    status.textContent = successMessage;
  } catch {
    status.textContent = "Copy was blocked by the browser. Select the text and copy it manually.";
  }
  window.setTimeout(() => { status.textContent = ""; }, 3600);
}

document.getElementById("copy-command").addEventListener("click", () => {
  copyText(document.getElementById("demo-command").textContent.trim(), "Command copied.");
});

document.getElementById("copy-pitch").addEventListener("click", () => {
  copyText(document.getElementById("pitch-text").textContent.trim(), "Pitch copied.");
});
