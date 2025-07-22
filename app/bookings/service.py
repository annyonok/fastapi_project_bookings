from datetime import date
from typing import List, Optional

from sqlalchemy import and_, delete, func, insert, or_, select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from app.bookings.models import Bookings
from app.bookings.schemas import SBooking
from app.database import async_session_maker
from app.hotels.rooms.models import Rooms
from app.service.base import BaseService
from app.logger import logger


class BookingService(BaseService):
    model = Bookings

    @classmethod
    async def add(
        cls,
        session: AsyncSession,
        user_id: int,
        room_id: int,
        date_from: date,
        date_to: date,
    ) -> Optional[SBooking]:
        """
        WITH booked_rooms AS (
            SELECT * FROM bookings
            WHERE room_id = 1 AND
            (date_from >= '2023-05-15' AND date_from <= '2023-06-20') OR
            (date_from <= '2023-05-15' AND date_to > '2023-05-15')
        )
        SELECT rooms.quantity - COUNT (booked_rooms.room_id) FROM rooms
        LEFT JOIN booked_rooms ON booked_rooms.room_id = rooms.id
        WHERE rooms.id = 1
        GROUP BY rooms.quantity, booked_rooms.room_id
        """

        try:
            async with async_session_maker() as session:
                booked_rooms = (
                    select(Bookings)
                    .where(
                        and_(
                            Bookings.room_id == room_id,
                            or_(
                                and_(
                                    Bookings.date_from >= date_from,
                                    Bookings.date_from <= date_to,
                                ),
                                and_(
                                    Bookings.date_from <= date_from,
                                    Bookings.date_to > date_from,
                                ),
                            ),
                        )
                    )
                    .cte("booked_rooms")
                )

                """
                SELECT rooms.quantity - COUNT (booked_rooms.room_id) FROM rooms
                LEFT JOIN booked_rooms ON booked_rooms.room_id = rooms.id
                WHERE rooms.id = 1
                GROUP BY rooms.quantity, booked_rooms.room_id
                """

                get_rooms_left = (
                    select((Rooms.quantity - func.count(booked_rooms.c.room_id)).label("rooms_left"))
                    .select_from(Rooms)
                    .join(booked_rooms, booked_rooms.c.room_id == Rooms.id, isouter=True)
                    .where(Rooms.id == room_id)
                    .group_by(Rooms.quantity, booked_rooms.c.room_id)
                )

                # print(get_rooms_left.compile(engine, compile_kwargs={"literal_binds": True}))

                rooms_left = await session.execute(get_rooms_left)  # type: ignore
                rooms_left: int = rooms_left.scalar()  # type: ignore

                if rooms_left > 0:
                    get_price = select(Rooms.price).filter_by(id=room_id)
                    price = await session.execute(get_price)  # type: ignore
                    price: int = price.scalar()  # type: ignore
                    add_booking = (
                        insert(Bookings)
                        .values(
                            room_id=room_id,
                            user_id=user_id,
                            date_from=date_from,
                            date_to=date_to,
                            price=price,
                        )
                        .returning(Bookings)
                    )

                    new_booking = await session.execute(add_booking)
                    await session.commit()
                    return new_booking.scalar()  # type: ignore
                else:
                    return None
        except (SQLAlchemyError, Exception) as e:
            msg = ""
            if isinstance(e, SQLAlchemyError):
                msg = "Database Exc"
            elif isinstance(e, Exception):
                msg = "Unknown Exc"
            msg += ": Cannot add booking"
            extra = {
                "user_id": user_id,
                "room_id": room_id,
                "date_from": date_from,
                "date_to": date_to,
            }
            logger.error(msg, extra=extra, exc_info=True)

    @classmethod
    async def find_all(
        cls,
        session: AsyncSession,
        user_id: Optional[int] = None,
        room_id: Optional[int] = None,
        date_from: Optional[date] = None,
        date_to: Optional[date] = None,
    ) -> List[SBooking]:
        async with async_session_maker() as session:
            query = select(cls.model)
            if user_id:
                query = query.filter(cls.model.user_id == user_id)
            if room_id:
                query = query.filter(cls.model.room_id == room_id)
            if date_from:
                query = query.filter(cls.model.date_from >= date_from)
            if date_to:
                query = query.filter(cls.model.date_to <= date_to)
            result = await session.execute(query)
            return [SBooking.model_validate(booking) for booking in result.scalars().all()]

    @classmethod
    async def delete(cls, booking_id: int) -> bool:
        async with async_session_maker() as session:
            query = delete(cls.model).where(cls.model.id == booking_id)
            result = await session.execute(query)
            await session.commit()
            return result.rowcount > 0
