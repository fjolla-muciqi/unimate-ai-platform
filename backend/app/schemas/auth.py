from pydantic import BaseModel, Field


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class PasswordChange(BaseModel):
    current_password: str = Field(min_length=1, max_length=128)

    # Të njëjtat kufij si te regjistrimi (`UserCreate`).
    new_password: str = Field(min_length=8, max_length=128)

    model_config = {"extra": "forbid"}
