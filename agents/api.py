"""
FastAPI REST API Server for Few Shot Dynamic Exemplar Selector.
"""
from typing import Dict, Any, List, Optional
from pathlib import Path
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse, FileResponse
from pydantic import BaseModel, Field, field_validator
from .base import AuditLogger, SecurityException
from exemplar_selector.selection import select_exemplars
from .models import SystemTaskPayload
from .supervisor import SystemSupervisor

supervisor = SystemSupervisor(model_provider="mock")

app = FastAPI(
    title="Few Shot Dynamic Exemplar Selector API",
    description="Enterprise Distributed Component Platform (Long-Horizon Agent Context & State Architecture)",
    version="3.0.0-ENTERPRISE",
)

# Maximum allowed request body size (1 MB)
MAX_REQUEST_SIZE = 1 * 1024 * 1024


class ChatRequest(BaseModel):
    query: str = Field(..., min_length=1, max_length=2000, description="Supervisory chat query")

    @field_validator("query")
    def validate_query(cls, v):
        if not v or not v.strip():
            raise ValueError("Query must not be empty or whitespace only")
        return v.strip()


@app.middleware("http")
async def limit_request_size(request: Request, call_next):
    """Reject requests with bodies exceeding MAX_REQUEST_SIZE."""
    content_length = request.headers.get("content-length")
    try:
        if content_length is not None and (int(content_length) < 0 or int(content_length) > MAX_REQUEST_SIZE):
            return JSONResponse(status_code=413, content={"error": "Request entity too large", "max_bytes": MAX_REQUEST_SIZE})
    except ValueError:
        return JSONResponse(status_code=400, content={"error": "Invalid content length"})

    body = bytearray()
    async for chunk in request.stream():
        body.extend(chunk)
        if len(body) > MAX_REQUEST_SIZE:
            return JSONResponse(status_code=413, content={"error": "Request entity too large", "max_bytes": MAX_REQUEST_SIZE})
    request._body = bytes(body)  # Starlette caches request body here for downstream parsing.
    return await call_next(request)


@app.exception_handler(SecurityException)
async def security_exception_handler(request: Request, exc: SecurityException):
    """Return 403 Forbidden for PHI/security violations."""
    return JSONResponse(
        status_code=403,
        content={"error": "Security policy violation", "detail": str(exc)},
    )




class SelectRequest(BaseModel):
    query: str = Field(..., min_length=1, max_length=10000)
    exemplars: List[Dict[str, Any]] = Field(..., max_length=1000)
    k: int = Field(default=3, ge=1, le=50)
    diversity: float = Field(default=0.65, ge=0, le=1, allow_inf_nan=False)
    token_budget: Optional[int] = Field(default=None, ge=1, le=100000)
    domain: Optional[str] = Field(default=None, max_length=100)


_WEB_DIR = Path(__file__).resolve().parent.parent / "web"

@app.get("/", include_in_schema=False)
def web_console():
    return FileResponse(_WEB_DIR / "index.html", media_type="text/html")

@app.get("/selector.js", include_in_schema=False)
def web_selector_script():
    return FileResponse(_WEB_DIR / "selector.js", media_type="text/javascript")

@app.get("/app.js", include_in_schema=False)
def web_application_script():
    return FileResponse(_WEB_DIR / "app.js", media_type="text/javascript")


@app.post("/api/select")
def api_select(req: SelectRequest):
    try:
        return select_exemplars(
            req.query, req.exemplars, k=req.k, diversity=req.diversity,
            token_budget=req.token_budget, domain=req.domain
        )
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc

@app.get("/health")
def health():
    return {"status": "HEALTHY", "service": "few-shot-dynamic-exemplar-selector", "domain": "Long-Horizon Agent Context & State Architecture", "standard": "Autonomous Agent State Machine & Token Economy RFC", "version": "3.0.0-ENTERPRISE"}


@app.get("/metrics")
def metrics():
    return {
        "dossiers_processed_total": len(supervisor.dossier_registry),
        "audit_blocks_total": len(AuditLogger.get_trail()),
        "system_status": "NOMINAL_OPTIMAL"
    }


@app.post("/api/audit")
def api_audit(payload: SystemTaskPayload):
    try:
        dossier = supervisor.process_task(payload)
        return dossier.to_dict()
    except SecurityException as e:
        raise HTTPException(status_code=403, detail=str(e))


@app.post("/api/chat")
def api_chat(req: ChatRequest):
    try:
        ans = supervisor.query_supervisory_chat(req.query)
        return {"response": ans}
    except SecurityException as e:
        raise HTTPException(status_code=403, detail=str(e))


@app.get("/api/audit/logs")
def api_audit_logs():
    return {"audit_trail": AuditLogger.get_trail(), "verified": AuditLogger.verify_integrity()}
