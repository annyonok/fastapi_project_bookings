from datetime import date
from typing import Any, Dict, List

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, status
from sqlalchemy import select
from fastapi_versioning import version

from app.bookings.models import Bookings
from app.bookings.schemas import SBooking
from app.bookings.service import BookingService
from app.database import async_session_maker
from app.exceptions import BookingNotFoundException, RoomCannotBeBookedException
from app.hotels.rooms.models import Rooms
from app.tasks.tasks import send_booking_confirmation_email
from app.users.dependencies import get_current_user
from app.users.models import Users

router = APIRouter(
    prefix="/bookings",
    tags=["Бронирование"],
)


# @router.get("")
# async def get_bookings(user: Users = Depends(get_current_user)) -> list[SBooking]:
#     return await BookingService.find_all(user_id=user.id)


@router.get("")
@version(1)
async def get_bookings(user: Users = Depends(get_current_user)) -> List[Dict[str, Any]]:
    async with async_session_maker() as session:
        query = (
            select(Bookings, Rooms.image_id, Rooms.name, Rooms.description, Rooms.services)
            .join(Rooms, Rooms.id == Bookings.room_id)
            .where(Bookings.user_id == user.id)
        )
        result = await session.execute(query)
        bookings = result.all()
        return [
            {
                **SBooking.model_validate(booking.Bookings).model_dump(),
                "image_id": booking.image_id,
                "name": booking.name,
                "description": booking.description,
                "services": booking.services,
            }
            for booking in bookings
        ]


@router.post("")
@version(1)
async def add_booking(
    background_tasks: BackgroundTasks,
    room_id: int,
    date_from: date,
    date_to: date,
    user: Users = Depends(get_current_user),
):
    booking = await BookingService.add(user.id, room_id, date_from, date_to)
    if not booking:
        raise RoomCannotBeBookedException
    booking_model = SBooking(**booking.__dict__)  # Преобразование в модель Pydantic
    booking_dict = booking_model.model_dump()  # Используем model_dump вместо dict
    # вариант с celery
    send_booking_confirmation_email.delay(booking_dict, user.email)
    # вариант встроенный background tasks
    # background_tasks.add_task(send_booking_confirmation_email, booking_dict, user.email)
    return booking_dict


@router.delete("/{booking_id}", status_code=status.HTTP_204_NO_CONTENT)
@version(1)
async def delete_booking(booking_id: int, user: Users = Depends(get_current_user)):
    booking = await BookingService.find_one_or_none(id=booking_id, user_id=user.id)
    if not booking:
        raise BookingNotFoundException

    success = await BookingService.delete(booking_id)
    if not success:
        raise BookingNotFoundException
