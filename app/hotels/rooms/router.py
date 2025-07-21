from datetime import date
from typing import List

from fastapi import APIRouter, Query
from sqlalchemy import func, select

from app.bookings.models import Bookings
from app.database import async_session_maker
from app.exceptions import InvalidDateException
from app.hotels.rooms.models import Rooms
from app.hotels.rooms.schemas import SRoom

router = APIRouter(
    prefix="/hotels",
    tags=["Номера"],
)


@router.get("/{hotel_id}/rooms")
async def get_rooms(
    hotel_id: int,
    date_from: date = Query(..., description="Дата заезда (YYYY-MM-DD)"),
    date_to: date = Query(..., description="Дата выезда (YYYY-MM-DD)"),
) -> List[SRoom]:
    if (date_to - date_from).days <= 0:
        raise InvalidDateException

    async with async_session_maker() as session:
        booked_rooms = (
            select(Bookings.room_id, func.count(Bookings.id).label("booked_count"))
            .where(Bookings.date_from <= date_to, Bookings.date_to > date_from)
            .group_by(Bookings.room_id)
            .cte("booked_rooms")
        )

        query = (
            select(Rooms, (Rooms.quantity - func.coalesce(booked_rooms.c.booked_count, 0)).label("rooms_left"))
            .join(booked_rooms, booked_rooms.c.room_id == Rooms.id, isouter=True)
            .where(Rooms.hotel_id == hotel_id)
        )

        result = await session.execute(query)
        rooms = result.all()
        total_days = (date_to - date_from).days
        return [
            {
                **SRoom.model_validate(room.Rooms).model_dump(),
                "rooms_left": room.rooms_left,
                "total_cost": room.Rooms.price * total_days,
            }
            for room in rooms
        ]
