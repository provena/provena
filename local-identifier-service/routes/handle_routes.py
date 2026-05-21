"""Handle API routes - compatible with ProvenaInterfaces.HandleAPI."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import List
from database import get_db
from services import handle_service

router = APIRouter()


class ValueType:
    DESC = "DESC"
    URL = "URL"


class MintRequest(BaseModel):
    value_type: str = "URL"
    value: str


class ModifyRequest(BaseModel):
    id: str
    index: int
    value: str


class HandleProperty(BaseModel):
    type: str
    value: str
    index: int


class Handle(BaseModel):
    id: str
    properties: List[HandleProperty]


@router.post("/mint", response_model=Handle)
async def mint(
    mint_request: MintRequest,
    db: Session = Depends(get_db),
):
    """Mint a new handle. Accepts Bearer token for compatibility with registry-api."""
    handle_id = handle_service.mint_handle(
        db, mint_request.value, mint_request.value_type
    )
    handle = handle_service.get_handle(db, handle_id)
    return Handle(
        id=handle["id"],
        properties=[
            HandleProperty(type=p["type"], value=p["value"], index=p["index"])
            for p in handle["properties"]
        ],
    )


@router.put("/modify_by_index", response_model=Handle)
async def modify_by_index(
    modify_request: ModifyRequest,
    db: Session = Depends(get_db),
):
    """Modify value at index. Accepts Bearer token for compatibility."""
    ok = handle_service.modify_by_index(
        db, modify_request.id, modify_request.index, modify_request.value
    )
    if not ok:
        raise HTTPException(status_code=404, detail="Handle or index not found")
    handle = handle_service.get_handle(db, modify_request.id)
    return Handle(
        id=handle["id"],
        properties=[
            HandleProperty(type=p["type"], value=p["value"], index=p["index"])
            for p in handle["properties"]
        ],
    )


@router.get("/get", response_model=Handle)
async def get_handle(id: str, db: Session = Depends(get_db)):
    """Get handle by ID."""
    handle = handle_service.get_handle(db, id)
    if not handle:
        raise HTTPException(status_code=404, detail="Handle not found")
    return Handle(
        id=handle["id"],
        properties=[
            HandleProperty(type=p["type"], value=p["value"], index=p["index"])
            for p in handle["properties"]
        ],
    )


@router.get("/list")
async def list_handles(db: Session = Depends(get_db)):
    """List all handle IDs."""
    return {"ids": handle_service.list_handles(db)}
