from pydantic import BaseModel

class Ticket(BaseModel):
    id: int
    title: str
    status: str
    priority: str
    description: str
    assignee: str
