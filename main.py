import os
from datetime import datetime, timedelta
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
from bson import ObjectId

from database import db, create_document, get_documents
from schemas import User, Otp, Session, Vehicle, Booking, SupportMessage

app = FastAPI(title="Ride+ API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Helpers
class OTPRequest(BaseModel):
    mobile: str


class OTPVerifyRequest(BaseModel):
    mobile: str
    code: str


class TokenResponse(BaseModel):
    token: str
    mobile: str


class VehicleCreate(Vehicle):
    pass


class BookingCreate(Booking):
    pass


class ChatMessage(BaseModel):
    mobile: str
    text: str


# Utility

def now_utc():
    return datetime.utcnow()


def to_object_id(id_str: str) -> ObjectId:
    try:
        return ObjectId(id_str)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid id")


@app.get("/")
async def root():
    return {"app": "Ride+ API", "status": "ok"}


@app.get("/test")
async def test_database():
    response = {
        "backend": "✅ Running",
        "database": "❌ Not Available",
        "database_url": None,
        "database_name": None,
        "connection_status": "Not Connected",
        "collections": []
    }
    try:
        if db is not None:
            response["database"] = "✅ Connected & Working"
            response["database_url"] = "✅ Set" if os.getenv("DATABASE_URL") else "❌ Not Set"
            response["database_name"] = db.name if hasattr(db, 'name') else "Unknown"
            response["connection_status"] = "Connected"
            try:
                collections = db.list_collection_names()
                response["collections"] = collections
            except Exception as e:
                response["database"] = f"⚠️ Connected but Error: {str(e)[:50]}"
        else:
            response["database"] = "⚠️ Available but not initialized"
    except Exception as e:
        response["database"] = f"❌ Error: {str(e)[:50]}"
    return response


# Auth: OTP flow (demo implementation)
@app.post("/auth/send-otp")
async def send_otp(payload: OTPRequest):
    code = "123456"  # demo code for simplicity
    otp = Otp(mobile=payload.mobile, code=code, expires_at=now_utc() + timedelta(minutes=5))
    create_document("otp", otp)
    return {"sent": True, "mobile": payload.mobile, "code": code}


@app.post("/auth/verify-otp", response_model=TokenResponse)
async def verify_otp(payload: OTPVerifyRequest):
    # For demo: accept 123456
    if payload.code != "123456":
        raise HTTPException(status_code=400, detail="Invalid OTP")
    token = os.urandom(16).hex()
    session = Session(mobile=payload.mobile, token=token, expires_at=now_utc() + timedelta(days=7))
    create_document("session", session)
    # Ensure user exists
    db["user"].update_one({"mobile": payload.mobile}, {"$setOnInsert": {"mobile": payload.mobile}}, upsert=True)
    return TokenResponse(token=token, mobile=payload.mobile)


# Vehicles
@app.post("/vehicles")
async def create_vehicle(vehicle: VehicleCreate):
    vid = create_document("vehicle", vehicle)
    return {"id": vid}


@app.get("/vehicles")
async def list_vehicles(owner_mobile: Optional[str] = None, limit: int = 50):
    filt = {"owner_mobile": owner_mobile} if owner_mobile else {}
    docs = get_documents("vehicle", filt, limit)
    # Convert ObjectId
    for d in docs:
        d["id"] = str(d.pop("_id"))
    return docs


@app.get("/vehicles/{vehicle_id}")
async def get_vehicle(vehicle_id: str):
    doc = db["vehicle"].find_one({"_id": to_object_id(vehicle_id)})
    if not doc:
        raise HTTPException(status_code=404, detail="Vehicle not found")
    doc["id"] = str(doc.pop("_id"))
    return doc


# Bookings
@app.post("/bookings")
async def create_booking(booking: BookingCreate):
    bid = create_document("booking", booking)
    return {"id": bid}


@app.get("/bookings")
async def list_bookings(mobile: Optional[str] = None, limit: int = 50):
    filt = {"user_mobile": mobile} if mobile else {}
    docs = get_documents("booking", filt, limit)
    for d in docs:
        d["id"] = str(d.pop("_id"))
    return docs


# Support chat (very simple echo-bot)
@app.post("/support/send")
async def support_send(msg: ChatMessage):
    create_document("supportmessage", SupportMessage(mobile=msg.mobile, role="user", text=msg.text))
    bot_reply = f"Got it! You said: '{msg.text}'. How can I help more with your booking?"
    create_document("supportmessage", SupportMessage(mobile=msg.mobile, role="bot", text=bot_reply))
    return {"ok": True, "reply": bot_reply}


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
