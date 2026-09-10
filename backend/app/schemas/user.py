from pydantic import BaseModel, EmailStr, Field

from app.models.user import UserRole


class UserCreate(BaseModel):
    """Regjistrimi publik.

    Roli nuk është fushë e kësaj skeme me qëllim: po të ishte,
    kushdo do të mund të regjistrohej si ADMIN thjesht duke shtuar
    një fushë në trupin e kërkesës. Rolet i cakton administratori.
    """

    first_name: str = Field(min_length=2, max_length=100)
    last_name: str = Field(min_length=2, max_length=100)
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)

    model_config = {"extra": "forbid"}


class UserResponse(BaseModel):
    id: int
    first_name: str
    last_name: str
    email: EmailStr
    role: UserRole
    is_active: bool

    model_config = {
        "from_attributes": True
    }