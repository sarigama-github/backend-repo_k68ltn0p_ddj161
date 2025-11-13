"""
Database Schemas for Ride+

Each Pydantic model represents a MongoDB collection. The collection name is
the lowercase of the class name.
"""
from typing import List, Optional
from pydantic import BaseModel, Field
from datetime import datetime


class User(BaseModel):
    mobile: str = Field(..., description="E.164 formatted mobile number")
    name: Optional[str] = Field(None, description="Display name")
    avatar_url: Optional[str] = Field(None, description="Profile avatar URL")
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class Otp(BaseModel):
    mobile: str
    code: str
    expires_at: datetime
    used: bool = False
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class Session(BaseModel):
    mobile: str
    token: str
    expires_at: datetime
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class Vehicle(BaseModel):
    owner_mobile: str
    title: str = Field(..., description="Short title e.g., Honda Activa or Tesla Model 3")
    type: str = Field(..., description="bike | car")
    make: Optional[str] = None
    model: Optional[str] = None
    year: Optional[int] = Field(None, ge=1950, le=2100)
    images: List[str] = Field(default_factory=list, description="List of image URLs or data URLs")
    insurance_active: bool = True
    price_per_day: float = Field(..., ge=0)
    location: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class Booking(BaseModel):
    user_mobile: str
    vehicle_id: str
    start_date: str  # ISO date string (yyyy-mm-dd)
    end_date: str    # ISO date string
    status: str = "pending"  # pending | confirmed | cancelled
    plan: Optional[str] = None  # subscription plan if any
    instant_delivery: bool = False
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class SupportMessage(BaseModel):
    mobile: str
    role: str = Field(..., description="user | bot")
    text: str
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
