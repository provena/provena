"""Public resolve endpoint - redirects to landing page."""
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session
from database import get_db
from services import handle_service
from config import get_settings

router = APIRouter()
settings = get_settings()


@router.get("/{handle_id}")
async def resolve(
    handle_id: str,
    db: Session = Depends(get_db),
):
    """
    Resolve a handle to its URL. Redirects to the resolved URL if found,
    otherwise to a configurable base URL + /item/{id} for registry landing.
    """
    url = handle_service.resolve_url(db, handle_id)
    if url:
        return RedirectResponse(url=url, status_code=302)
    if settings.resolve_base_url:
        return RedirectResponse(
            url=f"{settings.resolve_base_url.rstrip('/')}/{handle_id}",
            status_code=302,
        )
    raise HTTPException(status_code=404, detail="Handle not found")
