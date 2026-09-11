from dotenv import load_dotenv
import os

load_dotenv()  # Load environment variables from .env file


class EnvironmentVariablesConstants:

    _mandatory_env_vars = [
        "BREVO_API_KEY",
        "BREVO_BASE_API_URL",
        "REVIEW_URL_BASE",
        "EMAIL_DEFAULT_SENDER",
        "DEFAULT_USER_PASSWORD",
        "RECOVERY_URL_BASE",
        "LOGIN_URL_BASE",
        "AWS_ACCESS_KEY_ID",
        "AWS_SECRET_ACCESS_KEY",
        "AWS_REGION",
        "AWS_ENDPOINT_URL",
        "AWS_SQS_NOTIFICATION_QUEUE_URL",
        "AWS_SQS_NOTIFY_DLQ_URL",
    ]

    REVIEW_URL_BASE = os.getenv("REVIEW_URL_BASE", "")
    RECOVERY_URL_BASE = os.getenv("RECOVERY_URL_BASE", "")
    LOGIN_URL_BASE = os.getenv("LOGIN_URL_BASE", "")
    EMAIL_DEFAULT_SENDER = os.getenv("EMAIL_DEFAULT_SENDER", "")

    BREVO_API_KEY = os.getenv("BREVO_API_KEY", "")
    BREVO_BASE_API_URL = os.getenv("BREVO_BASE_API_URL", "")

    AWS_ACCESS_KEY_ID = os.getenv("AWS_ACCESS_KEY_ID", "")
    AWS_SECRET_ACCESS_KEY = os.getenv("AWS_SECRET_ACCESS_KEY", "")
    AWS_REGION = os.getenv("AWS_REGION", "")
    AWS_ENDPOINT_URL = os.getenv("AWS_ENDPOINT_URL", "")
    AWS_SQS_NOTIFICATION_QUEUE_URL = os.getenv("AWS_SQS_NOTIFICATION_QUEUE_URL", "")
    AWS_SQS_NOTIFY_DLQ_URL = os.getenv("AWS_SQS_NOTIFY_DLQ_URL", "")

    @staticmethod
    def validate_mandatory_env_vars():
        for var in EnvironmentVariablesConstants._mandatory_env_vars:
            if not os.getenv(var):
                raise EnvironmentError(
                    f"Mandatory environment variable '{var}' is not set."
                )
