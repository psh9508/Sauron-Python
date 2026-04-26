import hashlib

from sauron_python.core.grouping.component import GroupingComponent
from sauron_python.core.parameterizer import default_parameterizer


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


def _build_frame_component(frame: dict) -> GroupingComponent:
    filename = frame.get("filename", "")
    function = frame.get("function", "")

    contributes = is_user_frame(filename)
    hint = None if contributes else "ignored because frame is not user code"

    return GroupingComponent(
        id="frame",
        values=[
            GroupingComponent(id="filename", values=[filename]),
            GroupingComponent(id="function", values=[function]),
        ],
        contributes=contributes,
        hint=hint,
    )


def _build_stacktrace_component(frames: list[dict]) -> GroupingComponent:
    if not frames:
        return GroupingComponent(
            id="stacktrace", values=[], contributes=False, hint="no frames available"
        )

    frame_components = [_build_frame_component(f) for f in frames]

    if not any(fc.contributes for fc in frame_components):
        for fc in frame_components:
            fc.contributes = True
            fc.hint = "included because no user frames were found"

    return GroupingComponent(id="stacktrace", values=frame_components)


def _build_exception_component(
    exception_type: str,
    exception_value: str,
    frames: list[dict],
) -> GroupingComponent:
    type_component = GroupingComponent(id="type", values=[exception_type])

    parameterized_value = default_parameterizer.parameterize(exception_value)
    value_component = GroupingComponent(id="value", values=[parameterized_value])

    stacktrace_component = _build_stacktrace_component(frames)

    if stacktrace_component.contributes:
        value_component.contributes = False
        value_component.hint = "ignored because stacktrace takes precedence"

    return GroupingComponent(
        id="exception",
        values=[type_component, value_component, stacktrace_component],
    )


def _fallback_hash(seed: str) -> str:
    return hashlib.md5(seed.encode("utf-8")).hexdigest()


def compute_fingerprint(
    exception_type: str,
    exception_value: str,
    frames: list[dict],
) -> str:
    component = _build_exception_component(exception_type, exception_value, frames)
    return component.get_hash() or _fallback_hash(exception_type)


def compute_fingerprint_from_log(
    logger_name: str, level: str, message_template: str
) -> str:
    parameterized = default_parameterizer.parameterize(message_template)

    component = GroupingComponent(
        id="log_message",
        values=[
            GroupingComponent(id="logger", values=[logger_name]),
            GroupingComponent(id="level", values=[level]),
            GroupingComponent(id="message", values=[parameterized]),
        ],
    )
    return component.get_hash() or _fallback_hash(f"{logger_name}:{level}")
