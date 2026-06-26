from fastapi import APIRouter
from backend.api.models import GenerateRequest
from backend.api.stream import stream_graph
from fastapi.responses import StreamingResponse , Response
from backend.database.sessions_db import get_session
from backend.database.generation_cache import check_cache
import asyncio
router = APIRouter()

@router.post("/generate")
async def generate(req: GenerateRequest):
   return StreamingResponse(
        stream_graph(req),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},)

@router.get("/status/{session_id}")
async def status(session_id: str):
    session = await asyncio.get_event_loop().run_in_executor(None, get_session, session_id)
    if session:
        return {"status": session["final_status"]}
    else:
        return {"status": "not_found"}

@router.get("/export/{session_id}/sketch")
async def export_sketch(session_id: str):
    session = await asyncio.get_event_loop().run_in_executor(None, get_session, session_id)
    if not session or not session.get("spec_hash"):
        return {"error": "not_found"}
    cached = await asyncio.get_event_loop().run_in_executor(None, check_cache, session["spec_hash"])
    if not cached:
        return {"error": "not_found"}
    return Response(
        content=cached["sketch_ino"],
        media_type="text/plain",
        headers={"Content-Disposition": "attachment; filename=sketch.ino"})

@router.get("/export/{session_id}/circuit")
async def export_circuit(session_id: str):
    session = await asyncio.get_event_loop().run_in_executor(None, get_session, session_id)
    if not session or not session.get("spec_hash"):
        return {"error": "not_found"}
    cached = await asyncio.get_event_loop().run_in_executor(None, check_cache, session["spec_hash"])
    if not cached:
        return {"error": "not_found"}
    return Response(
        content=cached["diagram_json"],
        media_type="application/json",
        headers={"Content-Disposition": "attachment; filename=diagram.json"})

@router.get("/hex/{session_id}")
async def get_hex(session_id: str):
    session = await asyncio.get_event_loop().run_in_executor(None, get_session, session_id)
    if not session or not session.get("hex_path"):
        return {"error": "not_found"}
    try:
        with open(session["hex_path"], "r", encoding="utf-8") as f:
            hex_content = f.read()
    except FileNotFoundError:
        return {"error": "hex_file_missing"}
    return Response(
        content=hex_content,
        media_type="text/plain",
        headers={"Content-Disposition": "attachment; filename=firmware.hex"})

@router.get("/health")
async def health():
    return {"status": "ok"}
