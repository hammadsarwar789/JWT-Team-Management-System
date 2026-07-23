from typing import Optional, List, Dict, Any
from pydantic import BaseModel, EmailStr, Field, ValidationError, field_validator


class SignupSchema(BaseModel):
    username: str = Field(..., min_length=1, description="Username is required")
    email: EmailStr = Field(..., description="Valid email address is required")
    password: str = Field(..., min_length=6, description="Password must be at least 6 characters")
    full_name: Optional[str] = ""
    bio: Optional[str] = ""
    role: Optional[str] = "User"

    @field_validator("username", "full_name", "bio", mode="before")
    @classmethod
    def strip_strings(cls, v):
        if isinstance(v, str):
            return v.strip()
        return v or ""


class SigninSchema(BaseModel):
    email: str = Field(..., min_length=1, description="Email is required")
    password: str = Field(..., min_length=1, description="Password is required")

    @field_validator("email", mode="before")
    @classmethod
    def lower_email(cls, v):
        if isinstance(v, str):
            return v.strip().lower()
        return v or ""


class ProfileUpdateSchema(BaseModel):
    username: Optional[str] = None
    full_name: Optional[str] = None
    bio: Optional[str] = None

    @field_validator("username", mode="before")
    @classmethod
    def validate_username(cls, v):
        if v is not None and not str(v).strip():
            raise ValueError("Username cannot be empty")
        return str(v).strip() if v is not None else None


class FellowSchema(BaseModel):
    name: str = Field(..., min_length=1, description="Name is required")
    email: Optional[str] = ""
    relation: Optional[str] = ""
    notes: Optional[str] = ""
    attachments: Optional[List[Any]] = []

    @field_validator("name", "email", "relation", "notes", mode="before")
    @classmethod
    def strip_text(cls, v):
        if isinstance(v, str):
            return v.strip()
        return v or ""


class PasswordResetRequestSchema(BaseModel):
    email: EmailStr = Field(..., description="Valid email address is required")


class PasswordResetConfirmSchema(BaseModel):
    reset_token: str = Field(..., min_length=1, description="Reset token is required")
    new_password: str = Field(..., min_length=6, description="New password must be at least 6 characters")


def validate_with_pydantic(model_cls, data: dict):
    """
    Validate dictionary data against a Pydantic model.
    Returns: (is_valid: bool, error_message: str | None, cleaned_dict: dict | None)
    """
    if not isinstance(data, dict):
        return False, "Invalid payload format; JSON object expected", None
    try:
        instance = model_cls(**data)
        return True, None, instance.model_dump()
    except ValidationError as err:
        errors = err.errors()
        first_err = errors[0]
        field_name = ".".join(str(loc) for loc in first_err.get("loc", []))
        msg = first_err.get("msg", "Validation error")
        error_str = f"{msg}" if not field_name else f"{field_name}: {msg}"
        return False, error_str, None
