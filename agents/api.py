"""
FastAPI REST API Server for Few Shot Dynamic Exemplar Selector.
"""
from typing import Dict, Any
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field, validator
from .base import AuditLogger, SecurityException
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

    @validator("query")
    def validate_query(cls, v):
        if not v or not v.strip():
            raise ValueError("Query must not be empty or whitespace only")
        return v.strip()


@app.middleware("http")
async def limit_request_size(request: Request, call_next):
    """Reject requests with bodies exceeding MAX_REQUEST_SIZE."""
    content_length = request.headers.get("content-length")
    if content_length and int(content_length) > MAX_REQUEST_SIZE:
        return JSONResponse(
            status_code=413,
            content={"error": "Request entity too large", "max_bytes": MAX_REQUEST_SIZE},
        )
    response = await call_next(request)
    return response


@app.exception_handler(SecurityException)
async def security_exception_handler(request: Request, exc: SecurityException):
    """Return 403 Forbidden for PHI/security violations."""
    return JSONResponse(
        status_code=403,
        content={"error": "Security policy violation", "detail": str(exc)},
    )


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
