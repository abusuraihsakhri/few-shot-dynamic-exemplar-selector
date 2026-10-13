"""
FastAPI REST API Server for ExemplarSelector: Semantic Distance & Diversity Few-Shot Prompt Builder.
"""
from typing import Dict, Any, List, Optional
from .models import FrontierPayload
from .agents import ExemplarCoordinator
from .selection import select_exemplars

coordinator = ExemplarCoordinator()


def create_app():
    try:
        from fastapi import FastAPI, HTTPException
        from pydantic import BaseModel, Field

        app = FastAPI(
            title="ExemplarSelector: Semantic Distance & Diversity Few-Shot Prompt Builder",
            description="Selects optimal few-shot exemplars from golden datasets using maximal marginal relevance (MMR) to maximize prompt performance and diversity.",
            version="2.0.0-FRONTIER",
        )

        class TaskRequest(BaseModel):
            task_id: str = "TASK-2026-001"
            target_identifier: str = "TARGET-BIO-KEY"
            primary_metric: float = 28.5
            secondary_metric: float = 14.2
            status_descriptor: str = "DISCORDANT_ANOMALY"
            is_critical_flag: bool = True
            attributes: Dict[str, Any] = {}

        class SelectRequest(BaseModel):
            query: str = Field(..., min_length=1, max_length=10000)
            exemplars: List[Dict[str, Any]] = Field(..., max_length=1000)
            k: int = Field(default=3, ge=1, le=50)
            diversity: float = Field(default=0.65, ge=0, le=1, allow_inf_nan=False)
            token_budget: Optional[int] = Field(default=None, ge=1, le=100000)
            domain: Optional[str] = Field(default=None, max_length=100)

        class ChatRequest(BaseModel):
            query: str

        @app.post("/api/select")
        def api_select(req: SelectRequest):
            try:
                return select_exemplars(req.query, req.exemplars, k=req.k, diversity=req.diversity,
                                        token_budget=req.token_budget, domain=req.domain)
            except ValueError as exc:
                raise HTTPException(status_code=422, detail=str(exc)) from exc

        @app.get("/health")
        def health():
            return {"status": "HEALTHY", "system": "few-shot-dynamic-exemplar-selector", "domain": "Autonomous Context Management & State Engines", "version": "2.0.0-FRONTIER"}

        @app.post("/api/audit")
        def api_audit(req: TaskRequest):
            payload = FrontierPayload(
                task_id=req.task_id,
                target_identifier=req.target_identifier,
                primary_metric=req.primary_metric,
                secondary_metric=req.secondary_metric,
                status_descriptor=req.status_descriptor,
                is_critical_flag=req.is_critical_flag,
                attributes=req.attributes,
            )
            return coordinator.process(payload)

        @app.post("/api/chat")
        def api_chat(req: ChatRequest):
            return {"response": coordinator.query_supervisory_chat(req.query)}

        return app
    except ImportError:
        return None
