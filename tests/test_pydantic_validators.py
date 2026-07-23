from validators.schemas import (
    SignupSchema,
    SigninSchema,
    FellowSchema,
    validate_with_pydantic,
)


def test_signup_pydantic_validation():
    # Valid payload
    valid_data = {
        "username": "  alice  ",
        "email": "ALICE@Example.com",
        "password": "securepassword"
    }
    is_valid, err, cleaned = validate_with_pydantic(SignupSchema, valid_data)
    assert is_valid is True
    assert cleaned["username"] == "alice"
    assert cleaned["email"].lower() == "alice@example.com"

    # Short password
    invalid_data = {
        "username": "bob",
        "email": "bob@example.com",
        "password": "123"
    }
    is_valid, err, cleaned = validate_with_pydantic(SignupSchema, invalid_data)
    assert is_valid is False
    assert "at least 6 characters" in err


def test_fellow_pydantic_validation():
    # Valid fellow
    is_valid, err, cleaned = validate_with_pydantic(FellowSchema, {"name": "  Charlie  ", "email": "charlie@dev.com"})
    assert is_valid is True
    assert cleaned["name"] == "Charlie"

    # Missing name
    is_valid, err, cleaned = validate_with_pydantic(FellowSchema, {"name": ""})
    assert is_valid is False
