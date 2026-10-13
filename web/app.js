"use strict";

const byId = id => document.getElementById(id);
const demo = [
  { id: "renal-1", domain: "clinical", input: "What does elevated serum creatinine suggest?", output: "Assess renal function and compare with baseline." },
  { id: "renal-2", domain: "clinical", input: "How should creatinine elevation be assessed?", output: "Review trends, urine output and potential causes." },
  { id: "renal-3", domain: "clinical", input: "What indicates acute kidney injury?", output: "Use serial creatinine and urine output criteria." },
  { id: "cardiac-1", domain: "clinical", input: "How is troponin interpreted?", output: "Interpret serial changes alongside symptoms and ECG findings." },
  { id: "code-1", domain: "coding", input: "How do I parse JSON in Python?", output: "Use json.loads and handle JSONDecodeError." },
  { id: "code-2", domain: "coding", input: "How do I validate CSV input in Python?", output: "Use csv.DictReader with schema and field checks." }
];

let lastResult = null;

function status(message, isError = false) {
  byId("status").textContent = message;
  byId("status").classList.toggle("error", isError);
}

function addText(parent, tag, content, className) {
  const element = document.createElement(tag);
  if (className) element.className = className;
  element.textContent = content;
  parent.appendChild(element);
  return element;
}

function render(result) {
  const container = byId("results");
  const stats = byId("stats");
  container.replaceChildren();
  stats.replaceChildren();
  for (const value of [
    result.candidate_count + " candidates",
    result.selected.length + " selected",
    result.estimated_tokens + " estimated tokens"
  ]) addText(stats, "span", value, "stat");
  if (!result.selected.length) {
    addText(container, "p", "No examples match the domain and available budget.", "empty");
    return;
  }
  for (const item of result.selected) {
    const article = document.createElement("article");
    article.className = "result";
    addText(article, "h3", "#" + item.rank + " — " + item.id);
    addText(article, "div", "Domain: " + (item.domain || "not specified") +
      " · Relevance: " + item.relevance.toFixed(4) +
      " · MMR: " + item.mmr_score.toFixed(4) +
      " · ~" + item.estimated_tokens + " tokens", "meta");
    addText(article, "p", "Input: " + item.input);
    addText(article, "p", "Output: " + item.output);
    container.appendChild(article);
  }
}

function runSelection() {
  try {
    const pool = JSON.parse(byId("pool").value);
    const budgetText = byId("budget").value.trim();
    const result = ExemplarSelector.selectExemplars(byId("query").value, pool, {
      k: Number(byId("k").value),
      diversity: Number(byId("diversity").value),
      token_budget: budgetText ? Number(budgetText) : null,
      domain: byId("domain").value.trim() || null
    });
    lastResult = result;
    render(result);
    byId("export").disabled = false;
    byId("prompt").disabled = result.selected.length === 0;
    status("Selection complete. All processing occurred locally.");
  } catch (error) {
    lastResult = null;
    byId("export").disabled = true;
    byId("prompt").disabled = true;
    byId("stats").replaceChildren();
    byId("results").replaceChildren();
    addText(byId("results"), "p", "Correct the input and try again.", "empty");
    status(error instanceof Error ? error.message : "Invalid input", true);
  }
}

function download(content, name, type) {
  const url = URL.createObjectURL(new Blob([content], { type }));
  const link = document.createElement("a");
  link.href = url;
  link.download = name;
  document.body.appendChild(link);
  link.click();
  link.remove();
  setTimeout(() => URL.revokeObjectURL(url), 0);
}

function exportJson() {
  if (lastResult) download(JSON.stringify(lastResult, null, 2) + "\n", "selected-exemplars.json", "application/json");
}

function exportPrompt() {
  if (!lastResult || !lastResult.selected.length) return;
  const examples = lastResult.selected.map((e, i) =>
    "Example " + (i + 1) + "\nInput: " + e.input + "\nOutput: " + e.output
  ).join("\n\n");
  const prompt = examples + "\n\nTarget query:\n" + byId("query").value + "\n";
  download(prompt, "few-shot-prompt.txt", "text/plain;charset=utf-8");
}

function loadSample() {
  byId("query").value = "How should an elevated serum creatinine be evaluated?";
  byId("pool").value = JSON.stringify(demo, null, 2);
  byId("domain").value = "";
  status("Sample pool loaded.");
}

byId("run").addEventListener("click", runSelection);
byId("sample").addEventListener("click", loadSample);
byId("export").addEventListener("click", exportJson);
byId("prompt").addEventListener("click", exportPrompt);
byId("diversity").addEventListener("input", () => {
  byId("weight").value = byId("diversity").value;
});
byId("upload").addEventListener("change", async event => {
  const file = event.target.files[0];
  if (!file) return;
  if (file.size > 2_000_000) {
    status("JSON file exceeds the 2 MB upload limit.", true);
    event.target.value = "";
    return;
  }
  try {
    byId("pool").value = await file.text();
    status("File loaded locally. Run selection to validate the pool.");
  } catch (_) {
    status("Unable to read this file.", true);
  } finally {
    event.target.value = "";
  }
});
loadSample();
