import pytest

from app.repositories.task_repository import TaskRepository
from app.services.task_service import TaskService


@pytest.fixture
def service() -> TaskService:
    return TaskService(TaskRepository())
