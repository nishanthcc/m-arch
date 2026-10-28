import json
import uuid
from typing import Dict, Any, List, Optional
from a2a.types import Task, TaskStatus, TaskState, Artifact, Part, Message, Role

def create_a2a_task(
    task_id: str,
    context_id: str,
    instruction: str,
    metadata: Optional[Dict[str, str]] = None
) -> Task:
    """
    Creates an official A2A Task with initial WORKING state and context ID.
    """
    msg = Message(
        role=Role.ROLE_USER,
        parts=[Part(text=instruction)]
    )
    status = TaskStatus(
        state=TaskState.TASK_STATE_WORKING,
        message=msg
    )
    task = Task(
        id=task_id,
        context_id=context_id,
        status=status,
        history=[msg],
    )
    if metadata:
        for k, v in metadata.items():
            task.metadata[k] = str(v)
    return task

def complete_a2a_task(
    task: Task,
    artifact_id: str,
    name: str,
    payload: Dict[str, Any]
) -> Task:
    """
    Transitions an A2A Task to COMPLETED and attaches a structured Artifact.
    """
    payload_str = json.dumps(payload)
    artifact = Artifact(
        artifact_id=artifact_id,
        name=name,
        description=f"Structured result artifact for {name}",
        parts=[Part(text=payload_str)]
    )
    completion_msg = Message(
        role=Role.ROLE_AGENT,
        parts=[Part(text="Task completed successfully.")]
    )
    task.status.state = TaskState.TASK_STATE_COMPLETED
    task.status.message.CopyFrom(completion_msg)
    task.artifacts.append(artifact)
    return task

def fail_a2a_task(task: Task, error_message: str) -> Task:
    """
    Transitions an A2A Task to FAILED.
    """
    err_msg = Message(
        role=Role.ROLE_AGENT,
        parts=[Part(text=error_message)]
    )
    task.status.state = TaskState.TASK_STATE_FAILED
    task.status.message.CopyFrom(err_msg)
    return task
