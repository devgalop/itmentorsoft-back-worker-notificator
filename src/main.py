
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from common_py_aws import (
    SqsConnectionFactoryService,
    SqsConnectionRequest,
    SqsConsumerConfig,
    SqsConsumerService,
)
from src.infrastructure.env_manager.env_manager import EnvironmentVariablesConstants
from src.infrastructure.broker.aws.aws_sqs_notificator_consumer import SqsNotificatorConsumer
from src.endpoints.init import router as endpoints_router

@asynccontextmanager
async def lifespan(app: FastAPI):
    print("Starting up the application...")
    sqs_connection_factory = SqsConnectionFactoryService(
        SqsConnectionRequest(
            EnvironmentVariablesConstants.AWS_ENDPOINT_URL,
            EnvironmentVariablesConstants.AWS_ACCESS_KEY_ID,
            EnvironmentVariablesConstants.AWS_SECRET_ACCESS_KEY,
            EnvironmentVariablesConstants.AWS_REGION
        )
    )
    sqs_connection = sqs_connection_factory.create_connection()
    sqs_consumer = SqsConsumerService(
        sqs_client= sqs_connection,
        sqs_config= SqsConsumerConfig(
            queue_url= EnvironmentVariablesConstants.AWS_SQS_NOTIFICATION_QUEUE_URL,
            max_messages= 10,
            wait_time_seconds= 20,
            is_enabled = False,
            max_retries = 3,
            dlq_url= EnvironmentVariablesConstants.AWS_SQS_NOTIFY_DLQ_URL
        ),
        sqs_handler = SqsNotificatorConsumer()
    )
    app.state.sqs_consumer = sqs_consumer
    sqs_consumer.start_consumer()
    yield
    print("Shutting down the application...")
    await sqs_consumer.stop_consumer()


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
