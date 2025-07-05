from fastapi import FastAPI
from fastapi import Query
from fastapi import HTTPException
from typing import List
from src.models import Ticket
from src.services.tickets import fetch_tickets
import redis.asyncio as redis

app = FastAPI()

redis_client: redis.Redis | None = None

REDIS_HOST = "redis" 
REDIS_PORT = 6379
REDIS_KEY_USERS = "dummyjson_users"

@app.on_event("startup")
async def startup_event():
    global redis_client
    redis_client = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, decode_responses=True)

@app.on_event("shutdown")
async def shutdown_event():
    if redis_client:
        await redis_client.close()

@app.get("/tickets", response_model=List[Ticket])
async def get_tickets(page: int = Query(1, ge=1), page_size: int = Query(10, ge=1, le=50)):
    return await fetch_tickets(redis_client, page, page_size)

@app.get("/tickets/{ticket_id}", response_model=Ticket)
async def get_ticket(ticket_id: int):
    from src.services.tickets import get_ticket_by_id  # lokalni import da izbjegneš cirkularni
    ticket = await get_ticket_by_id(ticket_id, redis_client)
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")
    return ticket


