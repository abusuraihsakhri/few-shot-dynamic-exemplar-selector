# Few Shot Dynamic Exemplar Selector

> **Domain:** Autonomous Agent Systems & Context State Architecture
> **Reference Guidelines & Standards:** `Distributed Systems RFC & State Machine Verification`

<div align="center">

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
![Python](https://img.shields.io/badge/Python-3.10%20%7C%203.11%20%7C%203.12-3776AB.svg?logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-0.111-009688.svg?logo=fastapi&logoColor=white)
![Audit Trail](https://img.shields.io/badge/Audit-HMAC--SHA256_Tamper--Evident-brightgreen.svg)
![Zero-PHI Guard](https://img.shields.io/badge/Guard-Zero--PHI_Outbound-blue.svg)
![Docker](https://img.shields.io/badge/Docker-Ready-2496ED.svg?logo=docker&logoColor=white)

</div>

---

## 📖 What It Does

**Few Shot Dynamic Exemplar Selector** is an advanced analytical and computational platform implementing Maximal Marginal Relevance (MMR) few-shot prompt exemplar selector. It provides a multi-worker evaluation system with cryptographic audit trails and PHI (Protected Health Information) outbound protection.

---

## ⚙️ Key Capabilities & Algorithmic Modules

- **Deterministic Calculation Engine**: Strict compliance with standard reference formulations and thresholds.
- **Risk & Urgency Classification**: Multi-tier categorization with automated clinical/operational action recommendations.
- **Validation & Guardrails**: Rigorous input bounds checking and anomaly detection.
- **Multi-Worker Architecture**: Specialized workers for invariant QC, safety escalation, and protocol conformance.
- **HMAC-SHA256 Audit Trail**: Tamper-evident cryptographic logging of all operations.
- **Zero-PHI Outbound Guard**: Prevents sensitive data leakage via regex pattern detection.

---

## 🚀 Quickstart

### Installation

```bash
pip install -e .
```

Or with dependencies:
```bash
pip install fastapi uvicorn pydantic pytest
```

### CLI Usage

The CLI provides several subcommands:

#### 1. Run Single Task Evaluation
```bash
python cli.py audit --task-id TASK-001 --target KEY-01 --primary 28.5 --secondary 14.2 --critical --status DISCORDANT
```

#### 2. Supervisory Chat Query
```bash
python cli.py chat "What is the system status?"
```

#### 3. Batch Process CSV Records
```bash
python cli.py batch -i sample.csv -o results.csv
```

#### 4. Verify Audit Trail Integrity
```bash
python cli.py verify-audit
```

#### 5. Launch REST API Server
```bash
python cli.py serve --host 127.0.0.1 --port 8000
```

### Parameter Reference
- `--task-id`: Unique task/case identifier
- `--target`: Target entity or key
- `--primary`: Primary metric value (float)
- `--secondary`: Secondary metric value (float)
- `--critical`: Flag for critical/emergency status
- `--status`: Status descriptor string

---

## 🛡️ Security & Enterprise Architecture

* **Zero-PHI Outbound Interceptor:** Active regex inspection blocking SSNs, MRNs, phone numbers, emails, and patient identifiers.
* **Tamper-Evident HMAC-SHA256 Audit Trail:** Chained, cryptographically signed logs for every evaluation and state transition.
* **Secure Key Management:** Uses `AUDIT_SECRET_KEY` environment variable or generates a cryptographically secure random key.
* **Request Size Limiting:** API rejects request bodies larger than 1 MB.
* **FastAPI & Prometheus Telemetry:** Exposes OpenAPI 3.1 REST endpoints and operational Prometheus metrics (`/metrics`).

### Setting the Audit Secret Key

For production deployments, always set a persistent secret key:

```bash
# Linux/macOS
export AUDIT_SECRET_KEY="your-secure-random-key"

# Windows PowerShell
$env:AUDIT_SECRET_KEY = "your-secure-random-key"
```

---

## 🧪 Testing & Verification

Run the automated test suite:

```bash
pytest -v
```

Execute high-throughput batch simulation benchmarks:

```bash
python simulator.py 100
```

---

## 🐳 Container Deployment

```bash
docker build -t few-shot-dynamic-exemplar-selector .
docker run -p 8000:8000 -e AUDIT_SECRET_KEY="your-key" few-shot-dynamic-exemplar-selector
```

Or using Docker Compose:

```bash
AUDIT_SECRET_KEY="your-key" docker-compose up -d
```

---

## 📁 Project Structure

```
few-shot-dynamic-exemplar-selector/
├── agents/                     # Core agent system modules
│   ├── __init__.py
│   ├── api.py                  # FastAPI REST server
│   ├── base.py                 # Security, PHI guard, HMAC audit
│   ├── learning.py             # Bayesian calibration engine
│   ├── llm_factory.py          # LLM provider factory
│   ├── metrics.py              # Prometheus metrics collector
│   ├── models.py               # Pydantic data models
│   ├── streamer.py             # WebSocket telemetry streamer
│   ├── supervisor.py           # Master orchestrator
│   └── workers.py              # Specialized evaluation workers
├── exemplar_selector/          # Exemplar selection engine
│   ├── __init__.py
│   ├── agents.py               # Sub-agent coordination
│   ├── cli.py                  # CLI for exemplar operations
│   ├── engine.py               # Core algorithmic engine
│   ├── models.py               # Data models
│   └── server.py               # FastAPI server factory
├── tests/                      # Test suite
│   ├── test_enrichment.py
│   ├── test_exemplar_selector.py
│   └── test_few_shot_dynamic_exemplar_selector.py
├── web/                        # Web operations console
│   └── index.html
├── .github/workflows/ci.yml   # CI/CD pipeline
├── cli.py                      # Main CLI entry point
├── enrichment.py               # Feature enrichment modules
├── simulator.py                # Load/stress testing simulator
├── pyproject.toml              # Project metadata & dependencies
├── Dockerfile                  # Container image definition
├── docker-compose.yml          # Multi-container orchestration
├── sample.csv                  # Sample batch input data
├── sample_payload.json         # Sample API payload
├── benchmark_dataset.json      # Benchmark test cases
└── openapi_spec.json           # OpenAPI 3.1 specification
```
