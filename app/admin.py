"""
Administrative API (admin sprint).

Every route requires the admin key, supplied in the X-Admin-Key header and
checked against the ADMIN_KEY environment variable, so the knowledge base cannot
be read or changed without it. This is the access gate that keeps the KB
write-protected alongside the database's RLS.

Mount in main.py:
    from app.admin import router as admin_router
    app.include_router(admin_router)
    # and store the pool so routes can reach it:
    app.state.pool = pool            # in the lifespan, after creating the pool

Routes:
    GET    /admin/documents              list documents + chunk counts
    GET    /admin/documents/{title}      one document's source text
    PUT    /admin/documents/{title}      create/update a document, re-index it
    DELETE /admin/documents/{title}      remove a document and its chunks
    POST   /admin/reindex                re-embed every document
    GET    /admin/metrics                monitoring aggregates
    GET    /admin/logs?limit=50          recent requests
    GET    /admin/bookings               bookings (read-only)
"""
from __future__ import annotations

import os
import secrets

from fastapi import APIRouter, Depends, Header, HTTPException, Request
from pydantic import BaseModel

from app import analytics, kb

def require_admin(x_admin_key: str | None = Header(default=None)) -> None:
    expected = os.environ.get("ADMIN_KEY")
    if not expected or not x_admin_key or not secrets.compare_digest(
        x_admin_key.encode(), expected.encode()
    ):
        raise HTTPException(status_code=401, detail="Invalid or missing admin key.")


# Router-level dependency: every route on this router requires the admin key,
# including any added later, so there is no per-route check to forget.
router = APIRouter(
    prefix="/admin",
    tags=["admin"],
    dependencies=[Depends(require_admin)],
)


class DocumentIn(BaseModel):
    content: str


def _pool(request: Request):
    return request.app.state.pool


@router.get("/documents")
async def get_documents(request: Request):
    return await kb.list_documents(_pool(request))


@router.get("/documents/{title}")
async def get_document(title: str, request: Request):
    doc = await kb.get_document(_pool(request), title)
    if doc is None:
        raise HTTPException(status_code=404, detail="Document not found.")
    return doc


@router.put("/documents/{title}")
async def put_document(title: str, body: DocumentIn, request: Request):
    if not body.content.strip():
        raise HTTPException(status_code=400, detail="Document content is empty.")
    chunks = await kb.upsert_document(_pool(request), title, body.content)
    return {"title": title, "chunks": chunks}


@router.delete("/documents/{title}")
async def remove_document(title: str, request: Request):
    removed = await kb.delete_document(_pool(request), title)
    if not removed:
        raise HTTPException(status_code=404, detail="Document not found.")
    return {"title": title, "deleted": True}


@router.post("/reindex")
async def reindex(request: Request):
    return await kb.reindex_all(_pool(request))


@router.get("/metrics")
async def get_metrics(request: Request):
    return await analytics.metrics(_pool(request))


@router.get("/logs")
async def get_logs(request: Request, limit: int = 50):
    return await analytics.recent(_pool(request), min(max(limit, 1), 200))


@router.get("/bookings")
async def get_bookings(request: Request):
    rows = await _pool(request).fetch(
        "select pnr, last_name, first_name, flight_number, origin, destination, "
        "departure_time, seat, status from public.bookings order by pnr")
    return [dict(r) for r in rows]


@router.get("/ping")
async def admin_ping():
    return {"ok": True}
