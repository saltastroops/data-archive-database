from abc import ABC

from ssda.database import DatabaseService
from ssda.observation import ObservationProperties
from ssda.util.types import TaskName, TaskExecutionMode


def execute_task(
    task_name: TaskName, fits_path: str, task_mode: TaskExecutionMode
) -> None:
    print("TASK")
