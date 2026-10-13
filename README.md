# Few-shot Dynamic Exemplar Selector

Select examples for in-context prompts using local, deterministic **TF-IDF cosine similarity** and **maximal marginal relevance (MMR)**. An optional domain filter, maximum-example count and approximate token budget constrain selection. The implementation requires no embeddings API, hosted model or account.

## Main features

- Browser application in `web/`: paste or import a JSON exemplar pool, choose a query, inspect relevance/MMR scores, download selected JSON or a prompt text file.
- Python `select_exemplars()` API and `few-shot-dynamic-exemplar-selector select` CLI.
- `POST /api/select` endpoint on both FastAPI server implementations.
- Separate legacy threshold-audit tools (`cli.py`, `agents/`, `exemplar_selector/agents.py`), retained for compatibility.
- Automated Python and JavaScript regression tests and dependency-security auditing in GitHub Actions.

## Use the browser application

Serve `web/` with any static file server, or use the GitHub Pages deployment when available.

```bash
python -m http.server 8080 --directory web
```

Open `http://localhost:8080`, enter a query and an array of exemplars, then select examples. The included sample can be loaded with **Load sample**. Data remains in the browser; the web interface performs no network requests.

An exemplar has this shape:

```json
[
  {"id": "kidney-1", "domain": "clinical", "input": "What is an AKI?", "output": "An acute decline in kidney function."},
  {"id": "python-1", "domain": "coding", "input": "How do I read JSON?", "output": "Use json.load or json.loads."}
]
```

Required fields: `id`, `input`, `output`. Optional: `domain`. IDs must be unique. Maximum pool size: 1,000.

## Python installation and CLI

Python 3.9 or newer is supported by the package metadata; automated CI covers 3.10–3.12.

```bash
python -m pip install -e .
few-shot-dynamic-exemplar-selector select --query "kidney function" --pool pool.json -k 3 --diversity 0.65 --token-budget 220
```

The command emits structured JSON with selected examples, ranking scores and estimated token use. `--domain clinical` filters candidates before ranking. The `--diversity` argument is the **query relevance weight** in MMR: 1.0 prioritizes relevance, 0.0 emphasizes nonredundancy after the first selection.

Python usage:

```python
from exemplar_selector.selection import select_exemplars

result = select_exemplars(
    "kidney function",
    [{"id": "sample", "input": "kidney function test", "output": "Review kidney function."}],
    k=1,
)
print(result["selected"])
```

## API and existing audit workflows

```bash
python -m pip install -e ".[api]"
python cli.py serve --host 127.0.0.1 --port 8000
```

Open `http://127.0.0.1:8000/` for the same browser UI or `/docs` for REST documentation. `POST /api/select` accepts the selection parameters above, with the exemplar pool under `exemplars`. The original `audit`, `chat`, `batch` and `verify-audit` operations remain available through `python cli.py --help`. The separately packaged `few-shot-dynamic-exemplar-selector serve` uses the legacy `exemplar_selector.server` implementation and also exposes selection.

```bash
python cli.py audit --task-id DEMO-1 --target KEY-01 --primary 28.5 --secondary 14.2
python cli.py batch -i sample.csv -o results.csv
python cli.py verify-audit
```

The threshold-audit system is an **illustrative software workflow**, not a validated clinical decision tool. Audit entries are HMAC-chained and verified, but are **in-memory only** and are not durable across restarts. A persistent `AUDIT_SECRET_KEY` is required for a stable process-level signing key. Regex identifier checks are incomplete and do not establish de-identification or regulatory compliance.

## Algorithm and limitations

TF-IDF uses lowercase ASCII alphanumeric terms from the query and each exemplar's `input`. It computes document-frequency-weighted cosine relevance and iteratively selects the item maximizing:

```text
MMR = relevance_weight × similarity(query, candidate)
    − (1 − relevance_weight) × max_similarity(candidate, already_selected)
```

This is lexical matching, **not semantic embedding retrieval**. No model calls are made. Token estimates use `ceil((input + newline + output).length / 4)` and are not actual tokenizer counts. Neither automated selection nor the demo examples constitute clinical guidance.

## Development and deployment

```bash
python -m pip install -e ".[api,test]"
python -m pytest -q
node --test web/test_selector.cjs
```

A GitHub Actions workflow builds and deploys `web/` to GitHub Pages on pushes to `master` where Pages Actions deployment is enabled. The browser version uses plain JavaScript rather than Pyodide to avoid a large interpreter download; the Python selection algorithm is independently accessible via CLI/API.

For containers, run `docker compose up --build`. Avoid binding the unauthenticated demonstration API to a public network without adding access controls, rate limiting and operational safeguards.

**Technology:** Python, Pydantic, optional FastAPI/Uvicorn, standard HTML/CSS/JavaScript. **Browser compatibility:** modern browsers supporting ES2020, File API and Blob downloads. **License:** [MIT](LICENSE).
