from common_py_aws import ConsumerHandler, SqsMessageReceived


class SqsNotificatorConsumer(ConsumerHandler):

    async def process_message(self, message: SqsMessageReceived) -> bool:
        # Recibir mensaje, enviarlo a servicio de validación
        # Si es valido, enviar correo
        print(f"Processing message: {message.body}")
        return True
