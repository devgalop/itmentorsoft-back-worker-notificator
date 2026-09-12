from dotenv import load_dotenv
import os

load_dotenv()  # Load environment variables from .env file


class EnvironmentVariablesConstants:

    _mandatory_env_vars = [
        "ENVIRONMENT",
        "BREVO_API_KEY",
        "BREVO_BASE_API_URL",
        "EMAIL_DEFAULT_SENDER",
        "AWS_ACCESS_KEY_ID",
        "AWS_SECRET_ACCESS_KEY",
        "AWS_REGION",
        "AWS_ENDPOINT_URL",
        "AWS_SQS_NOTIFY_QUEUE_NAME",
        "AWS_SQS_NOTIFY_DLQ_NAME",
        "AWS_SQS_NOTIFY_QUEUE_URL",
        "AWS_SQS_NOTIFY_DLQ_URL",
        "CONSUMER_MAX_MESSAGES_PER_REQUEST",
        "CONSUMER_MAX_POOL_TIMEOUT",
        "CONSUMER_MAX_RETRIES",
    ]

    ENVIRONMENT = os.getenv("ENVIRONMENT", "")
    EMAIL_DEFAULT_SENDER = os.getenv("EMAIL_DEFAULT_SENDER", "")

    BREVO_API_KEY = os.getenv("BREVO_API_KEY", "")
    BREVO_BASE_API_URL = os.getenv("BREVO_BASE_API_URL", "")

    AWS_ACCESS_KEY_ID = os.getenv("AWS_ACCESS_KEY_ID", "")
    AWS_SECRET_ACCESS_KEY = os.getenv("AWS_SECRET_ACCESS_KEY", "")
    AWS_REGION = os.getenv("AWS_REGION", "")
    AWS_ENDPOINT_URL = os.getenv("AWS_ENDPOINT_URL", "")
    AWS_SQS_NOTIFY_QUEUE_NAME = os.getenv("AWS_SQS_NOTIFY_QUEUE_NAME", "")
    AWS_SQS_NOTIFY_DLQ_NAME = os.getenv("AWS_SQS_NOTIFY_DLQ_NAME", "")
    AWS_SQS_NOTIFY_QUEUE_URL = os.getenv("AWS_SQS_NOTIFY_QUEUE_URL", "")
    AWS_SQS_NOTIFY_DLQ_URL = os.getenv("AWS_SQS_NOTIFY_DLQ_URL", "")
    CONSUMER_MAX_MESSAGES_PER_REQUEST = os.getenv(
        "CONSUMER_MAX_MESSAGES_PER_REQUEST", ""
    )
    CONSUMER_MAX_POOL_TIMEOUT = os.getenv("CONSUMER_MAX_POOL_TIMEOUT", "")
    CONSUMER_MAX_RETRIES = os.getenv("CONSUMER_MAX_RETRIES", "")

    @staticmethod
    def validate_mandatory_env_vars():
        for var in EnvironmentVariablesConstants._mandatory_env_vars:
            if not os.getenv(var):
                raise EnvironmentError(
                    f"Mandatory environment variable '{var}' is not set."
                )
