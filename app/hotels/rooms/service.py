from typing import List, Optional

from sqlalchemy import delete, insert, select, update

from app.database import async_session_maker
from app.hotels.rooms.models import Rooms
from app.hotels.rooms.schemas import SRoom
from app.service.base import BaseService


class RoomService(BaseService):
    model = Rooms

    @classmethod
    async def find_all(cls, hotel_id: Optional[int] = None, price: Optional[int] = None) -> List[SRoom]:
        async with async_session_maker() as session:
            query = select(cls.model)
            if hotel_id:
                query = query.filter(cls.model.hotel_id == hotel_id)
            if price:
                query = query.filter(cls.model.price <= price)
            result = await session.execute(query)
            return [SRoom.model_validate(room) for room in result.scalars().all()]

    @classmethod
    async def add(
        cls,
        hotel_id: int,
        name: str,
        description: str,
        price: int,
        services: dict,
        quantity: int,
        image_id: int,
    ) -> SRoom:
        async with async_session_maker() as session:
            room_data = {
                "hotel_id": hotel_id,
                "name": name,
                "description": description,
                "price": price,
                "services": services,
                "quantity": quantity,
                "image_id": image_id,
            }
            query = insert(cls.model).values(**room_data).returning(cls.model)
            result = await session.execute(query)
            await session.commit()
            return SRoom.model_validate(result.scalar_one())

    @classmethod
    async def update(cls, room_id: int, **data) -> Optional[SRoom]:
        async with async_session_maker() as session:
            query = update(cls.model).where(cls.model.id == room_id).values(**data).returning(cls.model)
            result = await session.execute(query)
            await session.commit()
            room = result.scalar_one_or_none()
            return SRoom.model_validate(room) if room else None

    @classmethod
    async def delete(cls, room_id: int) -> bool:
        async with async_session_maker() as session:
            query = delete(cls.model).where(cls.model.id == room_id)
            result = await session.execute(query)
            await session.commit()
            return result.rowcount > 0
