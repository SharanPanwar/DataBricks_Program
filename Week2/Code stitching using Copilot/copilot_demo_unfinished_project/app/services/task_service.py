from app.models.task import Task
from app.repositories.task_repository import TaskRepository


class TaskService:
    def __init__(self, repository: TaskRepository) -> None:
        self.repository = repository

    def validate_title(self, title: str) -> str:
        cleaned = title.strip()
        if not cleaned:
            raise ValueError("Task title cannot be empty")
        return cleaned

    def list_tasks(self) -> list[Task]:
        return self.repository.list_tasks()

    def create_task(self, title: str) -> Task:
        cleaned_title = self.validate_title(title)
        return self.repository.create_task(cleaned_title)

    def get_task(self, task_id: int) -> Task | None:
        return self.repository.get_task(task_id)

    def delete_task(self, task_id: int) -> bool:
        return self.repository.delete_task(task_id)
