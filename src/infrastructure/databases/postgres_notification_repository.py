from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Type
from itmentorsoft_persistence.repositories import NotificationRepository
from itmentorsoft_persistence.mappers import NotificationMapper
from itmentorsoft_persistence.dto import Notification, InsertNotificationRequest
from itmentorsoft_persistence.models import NotificationEntity


class PostgresNotificationRepository(NotificationRepository):
    def __init__(self, session_factory: AsyncSession, mapper: Type[NotificationMapper]):
        self.session_factory = session_factory
        self.mapper = mapper

    async def create_notification(self, notification: InsertNotificationRequest):
        entity = self.mapper.to_entity(notification)
        self.session_factory.add(entity)
        await self.session_factory.commit()

    async def get_notifications_for_user(
        self, user_id: str
    ) -> list[Notification] | None:
        stmt = (
            select(NotificationEntity)
            .where(NotificationEntity.user_id == user_id)
            .order_by(NotificationEntity.created_at.desc())
        )
        result = await self.session_factory.execute(stmt)
        entities = result.scalars().all()
        if not entities:
            return None
        return [self.mapper.to_dto(entity) for entity in entities]

    async def get_notifications_unread_for_user(
        self, user_id: str
    ) -> list[Notification] | None:
        stmt = (
            select(NotificationEntity)
            .where(
                NotificationEntity.user_id == user_id, NotificationEntity.read == False
            )
            .order_by(NotificationEntity.created_at.desc())
        )
        result = await self.session_factory.execute(stmt)
        entities = result.scalars().all()
        if not entities:
            return None
        return [self.mapper.to_dto(entity) for entity in entities]
