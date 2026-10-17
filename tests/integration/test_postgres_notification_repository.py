"""Integration tests for PostgresNotificationRepository using SQLite async in-memory.

Tests the repository's real SQL logic (inserts, queries, ordering, filtering)
without requiring a running PostgreSQL instance.
"""

import pytest
from datetime import datetime

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

from itmentorsoft_persistence.models import NotificationEntity
from itmentorsoft_persistence.models.postgresql_notification_model import Base
from itmentorsoft_persistence.mappers import NotificationMapper
from itmentorsoft_persistence.dto import InsertNotificationRequest

from src.infrastructure.databases.postgres_notification_repository import (
    PostgresNotificationRepository,
)


@pytest.fixture
async def async_session():
    """Create an async SQLite in-memory session with the notifications table."""
    engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False)

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    session_factory = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with session_factory() as session:
        yield session

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()


@pytest.fixture
def repository(async_session):
    """PostgresNotificationRepository wired to the SQLite async session."""
    return PostgresNotificationRepository(async_session, NotificationMapper)


def _make_insert_request(
    user_id="user-123",
    subject="Test Subject",
    message="Test message body",
    url="https://example.com",
) -> InsertNotificationRequest:
    return InsertNotificationRequest(
        user_id=user_id, subject=subject, message=message, url=url
    )


@pytest.mark.asyncio
async def test_constructor_sets_session_and_mapper(async_session):
    """PostgresNotificationRepository stores the session_factory and mapper."""
    repo = PostgresNotificationRepository(async_session, NotificationMapper)
    assert repo.session_factory is async_session
    assert repo.mapper is NotificationMapper


@pytest.mark.asyncio
async def test_create_notification_persists_entity(repository, async_session):
    """create_notification inserts a row that can be queried back."""
    request = _make_insert_request()

    await repository.create_notification(request)

    from sqlalchemy import select, text

    result = await async_session.execute(text("SELECT COUNT(*) FROM notifications"))
    count = result.scalar()
    assert count == 1


@pytest.mark.asyncio
async def test_create_notification_maps_fields_correctly(repository, async_session):
    """create_notification maps InsertNotificationRequest fields to entity columns."""
    request = _make_insert_request(
        user_id="user-abc",
        subject="Welcome",
        message="Hello world",
        url="https://test.com/review",
    )

    await repository.create_notification(request)

    from sqlalchemy import select

    result = await async_session.execute(select(NotificationEntity))
    entity = result.scalar_one()
    assert entity.user_id == "user-abc"
    assert entity.subject == "Welcome"
    assert entity.message == "Hello world"
    assert entity.url == "https://test.com/review"
    assert entity.read is False


@pytest.mark.asyncio
async def test_get_notifications_for_user_returns_ordered_list(
    repository, async_session
):
    """get_notifications_for_user returns notifications ordered by created_at desc."""
    await repository.create_notification(
        _make_insert_request(user_id="user-1", subject="First", message="msg1")
    )
    await repository.create_notification(
        _make_insert_request(user_id="user-1", subject="Second", message="msg2")
    )
    await repository.create_notification(
        _make_insert_request(user_id="user-2", subject="Other user", message="msg3")
    )

    result = await repository.get_notifications_for_user("user-1")

    assert result is not None
    assert len(result) == 2
    assert result[0].subject == "Second"
    assert result[1].subject == "First"
    assert result[0].user_id == "user-1"


@pytest.mark.asyncio
async def test_get_notifications_for_user_returns_none_when_empty(repository):
    """get_notifications_for_user returns None when no notifications exist for the user."""
    result = await repository.get_notifications_for_user("nonexistent-user")
    assert result is None


@pytest.mark.asyncio
async def test_get_notifications_for_user_maps_to_dto(repository):
    """get_notifications_for_user returns Notification DTOs with correct fields."""
    await repository.create_notification(
        _make_insert_request(
            user_id="user-dto",
            subject="DTO Test",
            message="DTO message",
            url="https://example.com/link",
        )
    )

    result = await repository.get_notifications_for_user("user-dto")

    assert result is not None
    assert len(result) == 1
    dto = result[0]
    assert dto.user_id == "user-dto"
    assert dto.subject == "DTO Test"
    assert dto.message == "DTO message"
    assert dto.url == "https://example.com/link"
    assert dto.read is False
    assert dto.id is not None
    assert dto.created_at is not None


@pytest.mark.asyncio
async def test_get_notifications_unread_for_user_returns_only_unread(
    repository, async_session
):
    """get_notifications_unread_for_user returns only notifications where read=False."""
    await repository.create_notification(
        _make_insert_request(user_id="user-unread", subject="Unread 1", message="m1")
    )
    await repository.create_notification(
        _make_insert_request(user_id="user-unread", subject="Unread 2", message="m2")
    )
    # Mark one as read directly via SQL
    from sqlalchemy import update

    await async_session.execute(
        update(NotificationEntity)
        .where(NotificationEntity.subject == "Unread 1")
        .values(read=True)
    )
    await async_session.commit()

    result = await repository.get_notifications_unread_for_user("user-unread")

    assert result is not None
    assert len(result) == 1
    assert result[0].subject == "Unread 2"
    assert result[0].read is False


@pytest.mark.asyncio
async def test_get_notifications_unread_for_user_returns_none_when_all_read(
    repository, async_session
):
    """get_notifications_unread_for_user returns None when all notifications are read."""
    await repository.create_notification(
        _make_insert_request(user_id="user-allread", subject="Read", message="m")
    )
    from sqlalchemy import update

    await async_session.execute(
        update(NotificationEntity)
        .where(NotificationEntity.user_id == "user-allread")
        .values(read=True)
    )
    await async_session.commit()

    result = await repository.get_notifications_unread_for_user("user-allread")
    assert result is None


@pytest.mark.asyncio
async def test_get_notifications_unread_for_user_excludes_other_users(
    repository,
):
    """get_notifications_unread_for_user only returns unread notifications for the specified user."""
    await repository.create_notification(
        _make_insert_request(user_id="user-a", subject="A msg", message="m")
    )
    await repository.create_notification(
        _make_insert_request(user_id="user-b", subject="B msg", message="m")
    )

    result = await repository.get_notifications_unread_for_user("user-a")

    assert result is not None
    assert len(result) == 1
    assert result[0].user_id == "user-a"


@pytest.mark.asyncio
async def test_create_multiple_notifications_and_query_separately(repository):
    """Creating notifications for different users and querying returns correct subsets."""
    await repository.create_notification(
        _make_insert_request(user_id="alice", subject="Alice 1", message="m1")
    )
    await repository.create_notification(
        _make_insert_request(user_id="bob", subject="Bob 1", message="m2")
    )
    await repository.create_notification(
        _make_insert_request(user_id="alice", subject="Alice 2", message="m3")
    )

    alice_notifications = await repository.get_notifications_for_user("alice")
    bob_notifications = await repository.get_notifications_for_user("bob")

    assert len(alice_notifications) == 2
    assert len(bob_notifications) == 1
    assert bob_notifications[0].subject == "Bob 1"
