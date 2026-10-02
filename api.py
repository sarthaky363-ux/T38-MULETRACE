"""
MuleTrace REST API Application
FastAPI service exposing graph analytics, alert feeds, forensic replays,
chase prioritization, Ring DNA autopsies, and SAR dossier generation.
"""

from contextlib import asynccontextmanager
from typing import Any, Dict, List, Optional
from fastapi import FastAPI, File, HTTPException, Query, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from backend.store import store
from backend.schemas import (
    QuantumWalkResponse,
    QuantumInterdictionResponse,
    QuantumRingFidelityResponse,
)


class VerdictRequest(BaseModel):
    verdict: str = Field(..., description="'confirmed_mule' or 'cleared_benign'")
    analyst_notes: Optional[str] = Field("", description="Optional analyst audit notes")


class ReplayRequest(BaseModel):
    source_account: str = Field(..., description="Root entry account ID")
    start_time: str = Field(..., description="ISO 8601 timestamp string")
    initial_amount: float = Field(100000.0, description="Initial illicit fund injection")
    freeze_hour: Optional[float] = Field(None, description="Optional hour elapsed before freezing")


class FreezeRequest(BaseModel):
    source_account: str = Field(..., description="Root entry account ID")
    start_time: str = Field(..., description="ISO 8601 timestamp string")
    initial_amount: float = Field(100000.0, description="Initial illicit fund injection")


class PresetRequest(BaseModel):
    preset: str = Field(..., description="'relaxed', 'balanced', or 'strict'")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup lifecycle: Attempt to auto-load demo data if available."""
    try:
        store.load_demo_data()
        print("[MuleTrace API] Successfully auto-loaded demo dataset on startup.")
    except Exception as e:
        print(f"[MuleTrace API] Demo data not auto-loaded ({e}). Ready for upload or explicit load.")
    yield


app = FastAPI(
    title="MuleTrace Forensic Engine API",
    version="1.0.0",
    description="Autonomous Money-Mule & Layering Ring Detection System",
    lifespan=lifespan
)

# Enable CORS for frontend dev servers
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/api/health")
def get_health() -> Dict[str, Any]:
    """Health check endpoint indicating active preset and ingestion status."""
    return {
        "status": "ok",
        "dataset_loaded": store.dataset_loaded,
        "active_preset": store.engine.preset_name,
        "account_count": len(store.engine.graph.account_lookup) if store.engine.graph else 0,
        "timestamp": "2026-10-02T00:00:00Z"
    }


@app.post("/api/load-demo")
def load_demo() -> Dict[str, Any]:
    """Loads the pre-generated synthetic benchmark dataset."""
    try:
        summary = store.load_demo_data()
        return {
            "success": True,
            "message": "Demo dataset successfully ingested and analyzed.",
            "summary": summary
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to load demo data: {str(e)}")


@app.post("/api/upload")
async def upload_dataset(
    accounts: UploadFile = File(...),
    transactions: UploadFile = File(...),
    ground_truth: Optional[UploadFile] = File(None)
) -> Dict[str, Any]:
    """Upload custom CSV files for ingestion and analysis."""
    try:
        acc_bytes = await accounts.read()
        txn_bytes = await transactions.read()
        gt_bytes = await ground_truth.read() if ground_truth else None

        summary = store.load_uploaded_files(acc_bytes, txn_bytes, gt_bytes)
        return {
            "success": True,
            "message": "Uploaded files successfully ingested and analyzed.",
            "summary": summary
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to process uploaded files: {str(e)}")


@app.get("/api/summary")
def get_summary() -> Dict[str, Any]:
    """Retrieves high-level dashboard metrics and KPIs."""
    return store.get_summary()


def _val(param: Any, default: Any = None) -> Any:
    """Unwraps default Query param if invoked directly as a Python function."""
    if hasattr(param, "default"):
        return default if param.default is ... else param.default
    return param if param is not None else default


@app.get("/api/alerts")
def get_alerts(
    risk_band: Optional[str] = Query(None, description="critical, medium, safe, or all"),
    detector: Optional[str] = Query(None, description="Detector filter"),
    search: Optional[str] = Query(None, description="Account search query"),
    limit: int = Query(50, ge=1, le=500),
    offset: int = Query(0, ge=0)
) -> Dict[str, Any]:
    """Retrieves priority sorted alerts queue."""
    return store.get_alerts(
        risk_band=_val(risk_band),
        detector=_val(detector),
        search=_val(search),
        limit=_val(limit, 50),
        offset=_val(offset, 0)
    )


@app.get("/api/accounts/{account_id}")
def get_account_detail(account_id: str) -> Dict[str, Any]:
    """Retrieves in-depth investigation profile for a specific account."""
    detail = store.get_account_detail(account_id)
    if not detail:
        raise HTTPException(status_code=404, detail=f"Account '{account_id}' not found.")
    return detail


@app.get("/api/graph")
def get_graph(
    center_id: Optional[str] = Query(None, description="Center node for BFS subgraph"),
    depth: int = Query(2, ge=1, le=4),
    max_nodes: int = Query(150, ge=10, le=300)
) -> Dict[str, Any]:
    """
    Returns Cytoscape-formatted graph elements with strict 150-node safety cap.
    """
    return store.get_graph_elements(
        center_id=_val(center_id),
        depth=_val(depth, 2),
        max_nodes=_val(max_nodes, 150)
    )


@app.get("/api/rings")
def get_rings() -> List[Dict[str, Any]]:
    """Returns all discovered fraud rings and syndicate groupings."""
    return store.get_rings()


@app.get("/api/rings/{ring_id}")
def get_ring_detail(ring_id: str) -> Dict[str, Any]:
    """Returns detailed forensic autopsy for a single fraud ring."""
    ring = store.get_ring_detail(ring_id)
    if not ring:
        raise HTTPException(status_code=404, detail=f"Ring '{ring_id}' not found.")
    return ring


@app.post("/api/accounts/{account_id}/verdict")
def record_verdict(account_id: str, payload: VerdictRequest) -> Dict[str, Any]:
    """Submits human analyst feedback (confirmed mule / cleared benign)."""
    res = store.record_verdict(
        account_id=account_id,
        verdict=payload.verdict,
        notes=payload.analyst_notes or ""
    )
    if not res.get("success"):
        raise HTTPException(status_code=400, detail=res.get("message", "Verdict submission failed."))
    return res


@app.post("/api/replay")
def run_replay(payload: ReplayRequest) -> Dict[str, Any]:
    """Simulates illicit funds flow and generates temporal scrubber frames."""
    return store.run_replay(
        source_account=payload.source_account,
        start_time=payload.start_time,
        initial_amount=payload.initial_amount,
        freeze_hour=payload.freeze_hour
    )


@app.post("/api/freeze")
def run_freeze_simulation(payload: FreezeRequest) -> Dict[str, Any]:
    """Simulates capital recovery decay curve across hourly freeze windows."""
    return store.run_freeze_simulation(
        source_account=payload.source_account,
        start_time=payload.start_time,
        initial_amount=payload.initial_amount
    )


@app.get("/api/chase")
def get_chase_list() -> List[Dict[str, Any]]:
    """Retrieves ranked Chase List of accounts for urgent interdiction."""
    return store.get_chase_list()


@app.get("/api/presets")
def get_presets() -> Dict[str, Any]:
    """Returns available configuration presets and active thresholds."""
    return store.get_presets()


@app.post("/api/preset")
def set_preset(payload: PresetRequest) -> Dict[str, Any]:
    """Switches active detection preset ('relaxed', 'balanced', 'strict')."""
    try:
        new_summary = store.set_preset(payload.preset)
        return {
            "success": True,
            "active_preset": payload.preset,
            "summary": new_summary
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to change preset: {str(e)}")


@app.get("/api/metrics")
def get_metrics() -> Dict[str, Any]:
    """Returns offline benchmark performance metrics against ground truth."""
    return store.get_metrics()


@app.get("/api/early-warning")
def get_early_warning() -> List[Dict[str, Any]]:
    """Returns pre-transaction Day-Zero mule warnings."""
    return store.get_early_warnings()


@app.get("/api/case/{ring_id}/dossier")
def get_case_dossier(ring_id: str) -> Dict[str, Any]:
    """Generates standardized SAR regulatory dossier for print or PDF export."""
    dossier = store.get_case_dossier(ring_id)
    if not dossier:
        raise HTTPException(status_code=404, detail=f"Ring '{ring_id}' not found.")
    return dossier


@app.get("/api/evasion-test")
def get_evasion_test() -> Dict[str, Any]:
    """Runs sensitivity analysis comparing preset behavior against evasion techniques."""
    return store.run_evasion_test()


# =========================================================================
# MuleTrace Ω: Quantum-Inspired Classical Simulation Endpoints
# Simulated on a classical computer. Synthetic demonstration data.
# =========================================================================

@app.get("/api/quantum/walk", response_model=QuantumWalkResponse)
def get_quantum_walk(
    ring_id: Optional[str] = Query(None, description="Ring ID to simulate walk on"),
    steps: Optional[int] = Query(None, ge=10, le=200, description="Simulation step count (default 60)")
) -> Dict[str, Any]:
    """
    Executes continuous-time quantum walk and classical Laplacian diffusion
    on the selected ring's subgraph to forecast fund propagation velocity.
    """
    try:
        return store.get_quantum_walk(ring_id=ring_id, steps=steps)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Quantum walk simulation failed: {str(e)}")


@app.get("/api/quantum/interdiction", response_model=QuantumInterdictionResponse)
def get_quantum_interdiction(
    ring_id: Optional[str] = Query(None, description="Ring ID to optimize interdiction on"),
    budget: int = Query(5, ge=1, le=50, description="Freeze intervention budget K")
) -> Dict[str, Any]:
    """
    Solves binary network interdiction minimizing walk flow escape and innocence cost,
    and compares against the existing greedy Chase List.
    """
    try:
        return store.get_quantum_interdiction(ring_id=ring_id, budget=budget)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Interdiction optimization failed: {str(e)}")


@app.get("/api/quantum/ring-fidelity", response_model=QuantumRingFidelityResponse)
def get_quantum_ring_fidelity() -> Dict[str, Any]:
    """
    Computes pairwise quantum state fidelities |<a|b>|^2 across discovered rings
    and known typologies from normalized 6D Ring DNA feature vectors.
    """
    try:
        return store.get_quantum_ring_fidelity()
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Ring fidelity computation failed: {str(e)}")


# Serve frontend static assets and SPA fallback
from pathlib import Path
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

frontend_dist = Path(__file__).resolve().parent.parent / "frontend" / "dist"
if frontend_dist.exists():
    assets_dir = frontend_dist / "assets"
    if assets_dir.exists():
        app.mount("/assets", StaticFiles(directory=str(assets_dir)), name="assets")

    @app.get("/{full_path:path}", include_in_schema=False)
    def serve_frontend_spa(full_path: str):
        if full_path.startswith("api/") or full_path == "api":
            raise HTTPException(status_code=404, detail="API endpoint not found")
        target_file = frontend_dist / full_path
        if target_file.is_file():
            return FileResponse(target_file)
        return FileResponse(frontend_dist / "index.html")

