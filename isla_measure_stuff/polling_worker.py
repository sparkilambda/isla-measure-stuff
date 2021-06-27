from concurrent.futures import ThreadPoolExecutor, Future
from dataclasses import dataclass
import time
from typing import Callable, Dict
import uuid


@dataclass
class TargetExecution:
    expires_at: float
    future: Future


class PollingWorker:
    """Worker for running a function asynchronously and acessing its result via polling."""

    def __init__(self, target: Callable):
        self._target = target

        self._executions: Dict[str, TargetExecution]
        self._executions = {}

    def process(self, result_ttl, *args, **kwargs) -> str:
        """Executes the target function asynchronously and returns the execution ID to retrieve the result."""

        executor = ThreadPoolExecutor()
        future = executor.submit(self._target, *args, **kwargs)

        self._clean_expired_executions()
        execution_id = uuid.uuid4().hex
        self._executions[execution_id] = TargetExecution(
            expires_at=time.time() + result_ttl,
            future=future
        )
        print('########## process', self._executions)

        return execution_id

    def is_done(self, execution_id: str) -> bool:
        """Returns if the execution for the given ID has already finished."""

        try:
            print('########## is_done', self._executions)
            execution = self._executions[execution_id]
            return execution.future.done()
        finally:
            print('########## is_done', self._executions)

    def get_result(self, execution_id: str):
        """Returns the result for the execution with the given ID."""

        try:
            print('########## get_result', self._executions)
            execution = self._executions[execution_id]
            return execution.future.result()
        finally:
            print('########## get_result', self._executions)

    def _clean_expired_executions(self):
        expired_ids = [
            execution_id
            for execution_id, execution in self._executions.items()
            if time.time() > execution.expires_at
        ]

        for expired_id in expired_ids:
            self._executions[expired_id].future.cancel()  # Ensure the future is not running
            del self._executions[expired_id]
