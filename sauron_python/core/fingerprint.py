import hashlib


def is_user_frame(filename: str) -> bool:
    if "site-packages" in filename:
        return False
    if "lib/python" in filename:
        return False
    if filename.startswith("<"):
        return False
    return True


def normalize_stacktrace(frames: list[dict]) -> str:
    filtered = []
    for frame in frames:
        filename = frame.get("filename", "")
        if is_user_frame(filename):
            filtered.append(f"{filename}::{frame.get('function', '')}")

    if not filtered:
        filtered = [
            f"{f.get('filename', '')}::{f.get('function', '')}" for f in frames
        ]

    return "\n".join(filtered)


def compute_fingerprint(exception_type: str, frames: list[dict]) -> str:
    normalized = normalize_stacktrace(frames)
    raw = f"{exception_type}\n{normalized}"
    return hashlib.md5(raw.encode("utf-8")).hexdigest()


def compute_fingerprint_from_log(
    logger_name: str, level: str, message_template: str
) -> str:
    raw = f"{logger_name}\n{level}\n{message_template}"
    return hashlib.md5(raw.encode("utf-8")).hexdigest()
