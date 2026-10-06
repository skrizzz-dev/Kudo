from pydantic import BaseModel, EmailStr

class UserRegister(BaseModel):
    email: EmailStr
    password: str
    
class UserLogin(BaseModel):
    email:EmailStr
    password: str
    
class UserRead(BaseModel):
    id: int
    emal: EmailStr
    
    model_config = {"from_attributes": True}