# Sauron-Python

Lightweight error tracking SDK for Python applications.

Automatically captures exceptions and error-level logs, computes fingerprints for grouping, and sends events to your backend asynchronously.

## Installation

```bash
pip install sauron-python
```

## Quick Start

```python
from sauron_python import sauron_sdk

sauron_sdk.init(
    repository_id=1,
    endpoint="https://your-sauron-backend.com/analyze",
)
```

Once initialized, the SDK automatically captures:

- **Uncaught exceptions** via `sys.excepthook`
- **Error-level logs** via `logging` integration

No additional code changes needed.

## Manual Capture

```python
from sauron_python import capture_exception, add_breadcrumb

add_breadcrumb({"type": "http", "message": "GET /api/users"})

try:
    do_something()
except Exception:
    capture_exception()
```

## Features

- Async event delivery (non-blocking)
- Automatic fingerprinting and event grouping
- Breadcrumb context tracking
- Safe by design -- SDK errors never crash your application
