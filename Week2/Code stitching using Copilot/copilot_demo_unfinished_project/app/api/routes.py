from fastapi import APIRouter, HTTPException, status

from app.repositories.task_repository import TaskRepository
from app.schemas.task import TaskCreate, TaskResponse
from app.services.task_service import TaskService

router = APIRouter(prefix="/tasks", tags=["tasks"])

repository = TaskRepository()
service = TaskService(repository)


@router.get("", response_model=list[TaskResponse])
def list_tasks() -> list[TaskResponse]:
    return [TaskResponse(**task.__dict__) for task in service.list_tasks()]


@router.get("/{task_id}", response_model=TaskResponse)
def get_task(task_id: int) -> TaskResponse:
    task = service.get_task(task_id)

    if task is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found",
        )

    return TaskResponse(**task.__dict__)


@router.post("", response_model=TaskResponse, status_code=status.HTTP_201_CREATED)
def create_task(payload: TaskCreate) -> TaskResponse:
    try:
        task = service.create_task(payload.title)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc

    return TaskResponse(**task.__dict__)


@router.delete("/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_task(task_id: int) -> None:
    deleted = service.delete_task(task_id)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found",
        )
