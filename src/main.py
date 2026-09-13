from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from common_py_aws import (
    SqsConnectionFactoryService,
    SqsConnectionRequest,
    SqsConsumerConfig,
    SqsConsumerService,
)
from src.dependencies import (
    get_message_sanitizer,
    get_notification_manager_service,
    get_notification_service,
    get_template_loader,
)
from src.infrastructure.broker.aws.aws_sqs_create_queues import SqsCreator
from src.infrastructure.broker.aws.aws_sqs_publisher import SqsPublisher
from src.infrastructure.env_manager.env_manager import EnvironmentVariablesConstants
from src.infrastructure.broker.aws.aws_sqs_notificator_consumer import (
    SqsNotificatorConsumer,
)
from src.endpoints.init import router as endpoints_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    print("Starting up the application...")
    print("Validating environment variables...")
    EnvironmentVariablesConstants.validate_mandatory_env_vars()
    print("Creating SQS connection...")
    sqs_connection_factory = SqsConnectionFactoryService(
        SqsConnectionRequest(
            EnvironmentVariablesConstants.AWS_ENDPOINT_URL,
            EnvironmentVariablesConstants.AWS_ACCESS_KEY_ID,
            EnvironmentVariablesConstants.AWS_SECRET_ACCESS_KEY,
            EnvironmentVariablesConstants.AWS_REGION,
        )
    )
    sqs_connection = sqs_connection_factory.create_connection()
    if EnvironmentVariablesConstants.ENVIRONMENT == "dev":
        sqs_creator = SqsCreator(sqs_connection)
        sqs_creator.create_queues()
        sqs_publisher = SqsPublisher(sqs_connection)
        await sqs_publisher.publish_sample_messages()
    print("SQS connection established.")

    sqs_consumer = SqsConsumerService(
        sqs_client=sqs_connection,
        sqs_config=SqsConsumerConfig(
            queue_url=EnvironmentVariablesConstants.AWS_SQS_NOTIFY_QUEUE_URL,
            max_messages=int(
                EnvironmentVariablesConstants.CONSUMER_MAX_MESSAGES_PER_REQUEST
            ),
            wait_time_seconds=int(
                EnvironmentVariablesConstants.CONSUMER_MAX_POOL_TIMEOUT
            ),
            is_enabled=True,
            max_retries=int(EnvironmentVariablesConstants.CONSUMER_MAX_RETRIES),
            dlq_url=EnvironmentVariablesConstants.AWS_SQS_NOTIFY_DLQ_URL,
        ),
        sqs_handler=SqsNotificatorConsumer(
            message_sanitizer=get_message_sanitizer(),
            notification_manager_service=get_notification_manager_service(
                get_notification_service(), get_template_loader()
            ),
        ),
    )
    app.state.sqs_consumer = sqs_consumer
    sqs_consumer.start_consumer()
    print("SQS consumer started.")
    yield
    print("Shutting down the application...")
    await sqs_consumer.stop_consumer()
    print("SQS consumer stopped.")
    print("Application shutdown complete.")


app = FastAPI(lifespan=lifespan)

app.include_router(endpoints_router, prefix="/api")


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    return JSONResponse(
        status_code=500,
        content={
            "status": 500,
            "message": "An unexpected error occurred",
            "path": request.url.path,
        },
    )
