from tasks.email_tasks import send_password_reset_email, send_verification_email


def test_celery_email_tasks():
    res1 = send_password_reset_email.delay("user@test.com", "reset-token-123")
    result_val = res1.get()
    assert result_val["status"] == "sent"
    assert result_val["email"] == "user@test.com"

    res2 = send_verification_email.delay("user@test.com", "verify-token-456")
    result_val2 = res2.get()
    assert result_val2["status"] == "sent"
    assert result_val2["email"] == "user@test.com"
