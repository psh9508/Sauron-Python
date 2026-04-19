from collections import deque
from datetime import datetime, timezone
from typing import Any, Deque

DEFAULT_MAX_BREADCRUMBS = 100

class ExecutionContext:
    def __init__(self):
        self._breadcrumbs : Deque[dict[str, Any]] = deque()

    
    def add_breadcrumb(self, crumb: dict[str, Any]):
        if crumb.get("timestamp") is None:
            crumb["timestamp"] = datetime.now(timezone.utc).isoformat()
        if crumb.get("type") is None:
            crumb["type"] = "default"

        self._breadcrumbs.append(crumb)

        while len(self._breadcrumbs) > DEFAULT_MAX_BREADCRUMBS:
            self._breadcrumbs.popleft()
