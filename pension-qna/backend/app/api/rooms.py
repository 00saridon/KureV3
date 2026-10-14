from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models import Room
from app.db.session import get_db

router = APIRouter(prefix="/rooms", tags=["rooms"])


def serialize_room(room: Room) -> dict:
    return {"id": room.id, "name": room.name, "description": room.description, "capacity": room.capacity,
            "base_price": room.base_price, "image_url": room.image_url, "is_active": room.is_active}


@router.get("")
def list_rooms(session: Session = Depends(get_db)) -> list[dict]:
    return [serialize_room(room) for room in session.scalars(select(Room).where(Room.is_active.is_(True))).all()]


@router.get("/{room_id}")
def get_room(room_id: int, session: Session = Depends(get_db)) -> dict:
    room = session.get(Room, room_id)
    if room is None or not room.is_active:
        raise HTTPException(status_code=404, detail="객실을 찾을 수 없습니다.")
    return serialize_room(room)
