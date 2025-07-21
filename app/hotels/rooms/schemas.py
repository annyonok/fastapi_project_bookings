from typing import List

from pydantic import BaseModel


class SRoom(BaseModel):
    id: int
    hotel_id: int
    name: str
    description: str
    price: int
    services: List[str]
    quantity: int
    image_id: int

    class Config:
        from_attributes = True
        arbitrary_types_allowed = True  # Для поддержки JSON
