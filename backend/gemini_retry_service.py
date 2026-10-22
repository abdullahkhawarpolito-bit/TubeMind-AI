
import logging
import random
import time

from google.genai.errors import ClientError, ServerError


logger = logging.getLogger(__name__)


def call_gemini_with_retry(
    operation,
    max_attempts: int = 3,
    initial_delay: float = 1.0,
):
    """
    Retry temporary Gemini server failures.

    - Retry only server errors such as HTTP 500/503.
    - Do not retry client errors, including HTTP 429.
    - Return the original API response on success.
    - Raise the final error if all attempts fail.
    """

    if max_attempts < 1:
        raise ValueError(
            "max_attempts must be at least 1"
        )

    for attempt in range(1, max_attempts + 1):
        try:
            return operation()

        except ClientError:
            # Includes 429 quota/rate-limit errors.
            # Let main.py handle these directly.
            raise

        except ServerError as error:
            status_code = getattr(
                error, "code", None
            )

            # Retry only temporary provider errors.
            if status_code not in (500, 502, 503, 504):
                raise

            if attempt == max_attempts:
                logger.error(
                    "Gemini request failed after %d attempts "
                    "(status=%s)",
                    attempt,
                    status_code
                )
                raise

            # Exponential backoff with small jitter.
            delay = (
                initial_delay * (2 ** (attempt - 1))
                + random.uniform(0, 0.5)
            )

            logger.warning(
                "Temporary Gemini error %s. "
                "Retrying in %.2f seconds "
                "(attempt %d/%d)",
                status_code,
                delay,
                attempt,
                max_attempts
            )

            time.sleep(delay)
