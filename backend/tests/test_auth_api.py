def make_forgot_password_payload(email: str) -> dict[str, str]:
    return {
        "email": email,
        "turnstile_token": "test-turnstile-token",
    }
