import asyncio
from datetime import date
from typing import List

from fastapi import APIRouter, Query
from fastapi_cache.decorator import cache
from sqlalchemy import func, select

from app.bookings.models import Bookings
from app.database import async_session_maker
from app.exceptions import HotelNotFoundException, InvalidDateException
from app.hotels.models import Hotels
from app.hotels.rooms.models import Rooms
from app.hotels.schemas import SHotel
from app.hotels.service import HotelService

router = APIRouter(
    prefix="/hotels",
    tags=["Отели"],
)


@router.get("/{location}")
@cache(expire=30)
async def get_hotels(
    location: str,
    date_from: date = Query(..., description="Дата заезда (YYYY-MM-DD)"),
    date_to: date = Query(..., description="Дата выезда (YYYY-MM-DD)"),
) -> List[SHotel]:
    await asyncio.sleep(3)
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
            select(
                Hotels,
                (func.sum(Rooms.quantity) - func.coalesce(func.sum(booked_rooms.c.booked_count), 0)).label(
                    "rooms_left"
                ),
            )
            .join(Rooms, Rooms.hotel_id == Hotels.id)
            .join(booked_rooms, booked_rooms.c.room_id == Rooms.id, isouter=True)
            .where(Hotels.location.ilike(f"%{location}%"))
            .group_by(Hotels.id)
            .having(func.sum(Rooms.quantity) - func.coalesce(func.sum(booked_rooms.c.booked_count), 0) > 0)
        )

        result = await session.execute(query)
        hotels = result.all()
        return [
            {
                **SHotel.model_validate(hotel.Hotels).model_dump(),
                "rooms_left": hotel.rooms_left,
            }
            for hotel in hotels
        ]


@router.get("/id/{hotel_id}")
async def get_hotel(hotel_id: int) -> SHotel:
    hotel = await HotelService.find_by_id(hotel_id)
    if not hotel:
        raise HotelNotFoundException
    return SHotel.model_validate(hotel)
