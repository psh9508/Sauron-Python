from sauron_python.core.fingerprint import (
    compute_fingerprint,
    compute_fingerprint_from_log,
    is_user_frame,
    normalize_stacktrace,
)


class TestIsUserFrame:
    def test_filters_site_packages(self):
        assert not is_user_frame("/env/lib/python3.11/site-packages/requests/api.py")

    def test_filters_python_lib(self):
        assert not is_user_frame("/usr/lib/python3.11/logging/__init__.py")

    def test_filters_synthetic_frames(self):
        assert not is_user_frame("<frozen importlib._bootstrap>")

    def test_allows_user_code(self):
        assert is_user_frame("/app/services/payment.py")


class TestNormalizeStacktrace:
    def test_includes_only_user_frames(self):
        frames = [
            {"filename": "/usr/lib/python3.11/logging/__init__.py", "function": "emit"},
            {"filename": "/app/services/payment.py", "function": "process"},
            {"filename": "/app/main.py", "function": "handle"},
        ]
        result = normalize_stacktrace(frames)
        assert "/app/services/payment.py::process" in result
        assert "/app/main.py::handle" in result
        assert "logging" not in result

    def test_falls_back_to_all_frames_when_no_user_frames(self):
        frames = [
            {"filename": "/usr/lib/python3.11/logging/__init__.py", "function": "emit"},
        ]
        result = normalize_stacktrace(frames)
        assert "logging" in result


class TestExceptionFingerprint:
    def test_same_error_same_fingerprint(self):
        frames = [
            {"filename": "/app/main.py", "function": "handle"},
        ]
        fp1 = compute_fingerprint("ValueError", frames)
        fp2 = compute_fingerprint("ValueError", frames)
        assert fp1 == fp2

    def test_different_type_different_fingerprint(self):
        frames = [
            {"filename": "/app/main.py", "function": "handle"},
        ]
        fp1 = compute_fingerprint("ValueError", frames)
        fp2 = compute_fingerprint("TypeError", frames)
        assert fp1 != fp2

    def test_different_location_different_fingerprint(self):
        fp1 = compute_fingerprint("ValueError", [
            {"filename": "/app/main.py", "function": "handle"},
        ])
        fp2 = compute_fingerprint("ValueError", [
            {"filename": "/app/routes.py", "function": "index"},
        ])
        assert fp1 != fp2

    def test_error_value_does_not_affect_fingerprint(self):
        frames = [
            {"filename": "/app/main.py", "function": "handle"},
        ]
        fp1 = compute_fingerprint("ValueError", frames)
        fp2 = compute_fingerprint("ValueError", frames)
        assert fp1 == fp2


class TestLogFingerprint:
    def test_same_log_same_fingerprint(self):
        fp1 = compute_fingerprint_from_log("myapp", "ERROR", "connection failed: %s")
        fp2 = compute_fingerprint_from_log("myapp", "ERROR", "connection failed: %s")
        assert fp1 == fp2

    def test_different_template_different_fingerprint(self):
        fp1 = compute_fingerprint_from_log("myapp", "ERROR", "connection failed: %s")
        fp2 = compute_fingerprint_from_log("myapp", "ERROR", "timeout after %s seconds")
        assert fp1 != fp2

    def test_different_logger_different_fingerprint(self):
        fp1 = compute_fingerprint_from_log("myapp.payment", "ERROR", "failed")
        fp2 = compute_fingerprint_from_log("myapp.auth", "ERROR", "failed")
        assert fp1 != fp2

    def test_different_level_different_fingerprint(self):
        fp1 = compute_fingerprint_from_log("myapp", "ERROR", "something broke")
        fp2 = compute_fingerprint_from_log("myapp", "CRITICAL", "something broke")
        assert fp1 != fp2

    def test_formatted_args_do_not_affect_fingerprint(self):
        fp1 = compute_fingerprint_from_log("myapp", "ERROR", "user %s failed")
        fp2 = compute_fingerprint_from_log("myapp", "ERROR", "user %s failed")
        assert fp1 == fp2
