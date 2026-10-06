from pydantic import BaseModel

class ProjectCreate(BaseModel):
    title: str
    
class ProjecyRead(BaseModel):
    id: int
    title: str
    
    model_config = {"from_attributes": True}