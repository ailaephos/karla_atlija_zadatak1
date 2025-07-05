import json
from httpx import AsyncClient
from typing import List
from src.models import Ticket
import redis.asyncio as redis


REDIS_KEY_USERS = "dummyjson_users"
REDIS_TTL = 3600  # cache vrijedi 1h

USERS_API_URL = "https://dummyjson.com/users"
TODOS_API_URL = "https://dummyjson.com/todos"

async def fetch_users(redis_client: redis.Redis) -> dict[int, str]:
    cached = await redis_client.get(REDIS_KEY_USERS)
    if cached:
        cached_dict = json.loads(cached)
        return {int(k): v for k, v in cached_dict.items()}

    async with AsyncClient() as client:
        all_users = {}
        limit = 100
        skip = 0

        while True:
            url = f"{USERS_API_URL}?limit={limit}&skip={skip}"
            response = await client.get(url)
            data = response.json()

            users = data.get("users", [])
            if not users:
                break

            for user in users:
                all_users[user["id"]] = user["username"]

            skip += limit
            if skip >= data.get("total", 0):
                break

        # Spremi u Redis
        await redis_client.set(REDIS_KEY_USERS, json.dumps(all_users), ex=REDIS_TTL)
        return all_users

async def fetch_tickets(redis_client: redis.Redis, page: int = 1, page_size: int = 10) -> List[Ticket]:
    user_map = await fetch_users(redis_client)
    skip = (page - 1) * page_size
    limit = page_size

    async with AsyncClient() as client:
        response = await client.get(f"{TODOS_API_URL}?limit={limit}&skip={skip}")
        data = response.json()
        todos = data.get("todos", [])

        tickets = []
        for todo in todos:
            assignee = user_map.get(todo["userId"], "unknown")
            ticket = Ticket(
                id=todo["id"],
                title=todo["todo"],
                status="closed" if todo["completed"] else "open",
                priority=["low", "medium", "high"][todo["id"] % 3],
                description=todo["todo"][:100],
                assignee=assignee
            )
            tickets.append(ticket)

        return tickets

async def get_ticket_by_id(ticket_id: int, redis_client: redis.Redis) -> Ticket | None:
    async with AsyncClient() as client:
        response = await client.get(f"{TODOS_API_URL}/{ticket_id}")
        if response.status_code != 200:
            return None

        todo = response.json()
        user_map = await fetch_users(redis_client)

        assignee = user_map.get(todo["userId"], "unknown")
        return Ticket(
            id=todo["id"],
            title=todo["todo"],
            status="closed" if todo["completed"] else "open",
            priority=["low", "medium", "high"][todo["id"] % 3],
            description=todo["todo"][:100],
            assignee=assignee
        )
    