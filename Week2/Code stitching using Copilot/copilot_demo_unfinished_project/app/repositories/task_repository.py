from app.models.task import Task


class TaskRepository:
    # Simple in-memory repository for the demo.

    def __init__(self) -> None:
        self._tasks: dict[int, Task] = {
            1: Task(id=1, title="Learn GitHub Copilot"),
            2: Task(id=2, title="Build a small demo"),
        }
        self._next_id = 3

    def list_tasks(self) -> list[Task]:
        return list(self._tasks.values())

    def get_task(self, task_id: int) -> Task | None:
        return self._tasks.get(task_id)

    def create_task(self, title: str) -> Task:
        task = Task(id=self._next_id, title=title)
        self._tasks[task.id] = task
        self._next_id += 1
        return task

    def delete_task(self, task_id: int) -> bool:
        if task_id not in self._tasks:
            return False
        del self._tasks[task_id]
        return True
