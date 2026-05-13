from pydantic import BaseModel, EmailStr


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class TokenPayload(BaseModel):
    sub: int        # user id
    role: str
    email: str


class RegisterRequest(BaseModel):
    name: str
    email: EmailStr
    password: str
    # role no se expone — siempre será "user" en el registro público
