import pytest


def test_validate_title_trims_whitespace(service):
    assert service.validate_title("  Learn Copilot  ") == "Learn Copilot"


def test_validate_title_rejects_empty_title(service):
    with pytest.raises(ValueError, match="Task title cannot be empty"):
        service.validate_title("   ")


def test_create_task_assigns_id_and_stores_task(service):
    task = service.create_task("Finish demo")

    assert task.id == 3
    assert task.title == "Finish demo"
    assert service.get_task(3) == task
