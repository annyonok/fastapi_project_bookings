from typing import List, Optional

from sqlalchemy import delete, insert, select, update

from app.database import async_session_maker
from app.hotels.models import Hotels
from app.hotels.schemas import SHotel
from app.service.base import BaseService


class HotelService(BaseService):
    model = Hotels

    @classmethod
    async def find_all(cls, name: Optional[str] = None, location: Optional[str] = None) -> List[SHotel]:
        async with async_session_maker() as session:
            query = select(cls.model)
            if name:
                query = query.filter(cls.model.name.ilike(f"%{name}%"))
            if location:
                query = query.filter(cls.model.location.ilike(f"%{location}%"))
            result = await session.execute(query)
            return [SHotel.model_validate(hotel) for hotel in result.scalars().all()]

    @classmethod
    async def add(cls, name: str, location: str, services: str, rooms_quantity: int, image_id: int) -> SHotel:
        async with async_session_maker() as session:
            hotel_data = {
                "name": name,
                "location": location,
                "services": services,
                "rooms_quantity": rooms_quantity,
                "image_id": image_id,
            }
            query = insert(cls.model).values(**hotel_data).returning(cls.model)
            result = await session.execute(query)
            await session.commit()
            return SHotel.model_validate(result.scalar_one())

    @classmethod
    async def update(cls, hotel_id: int, **data) -> Optional[SHotel]:
        async with async_session_maker() as session:
            query = update(cls.model).where(cls.model.id == hotel_id).values(**data).returning(cls.model)
            result = await session.execute(query)
            await session.commit()
            hotel = result.scalar_one_or_none()
            return SHotel.model_validate(hotel) if hotel else None

    @classmethod
    async def delete(cls, hotel_id: int) -> bool:
        async with async_session_maker() as session:
            query = delete(cls.model).where(cls.model.id == hotel_id)
            result = await session.execute(query)
            await session.commit()
            return result.rowcount > 0
