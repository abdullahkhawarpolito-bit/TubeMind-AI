
from unittest.mock import patch

from google.genai.errors import ServerError, ClientError
from gemini_retry_service import call_gemini_with_retry


# -------------------------------------
# Test 1: Retry HTTP 503 errors
# -------------------------------------

attempts = 0


def simulate_server_error():
    global attempts

    attempts += 1

    if attempts < 3:
        raise ServerError(
            code=503,
            response_json={
                "error": {
                    "code": 503,
                    "message": "Service unavailable",
                    "status": "UNAVAILABLE"
                }
            }
        )

    return "Success"


with patch("gemini_retry_service.time.sleep"):
    result = call_gemini_with_retry(
        simulate_server_error,
        max_attempts=3,
        initial_delay=0.1
    )

assert result == "Success"
assert attempts == 3

print("TEST 1 PASSED: HTTP 503 retried successfully")


# -------------------------------------
# Test 2: Do not retry HTTP 429
# -------------------------------------

quota_attempts = 0


def simulate_quota_error():
    global quota_attempts

    quota_attempts += 1

    raise ClientError(
        code=429,
        response_json={
            "error": {
                "code": 429,
                "message": "Quota exceeded",
                "status": "RESOURCE_EXHAUSTED"
            }
        }
    )


try:
    with patch("gemini_retry_service.time.sleep"):
        call_gemini_with_retry(
            simulate_quota_error,
            max_attempts=3,
            initial_delay=0.1
        )

except ClientError as error:
    assert error.code == 429

assert quota_attempts == 1

print("TEST 2 PASSED: HTTP 429 was not retried")

print("\nALL RETRY TESTS PASSED!")
