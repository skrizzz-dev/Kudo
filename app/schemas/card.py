from pydantic import BaseModel

class CardMove(BaseModel):
    board_id: int
    position: int