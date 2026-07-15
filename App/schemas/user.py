from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class UserBase(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    email: str = Field(description="Unique user email address")


class UserCreate(UserBase):
    password: str = Field(min_length=6, description="Plain-text password (hashed before storage)")


class UserRead(UserBase):
    user_id: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
