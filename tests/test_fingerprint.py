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
        fp1 = compute_fingerprint("ValueError", "test", frames)
        fp2 = compute_fingerprint("ValueError", "test", frames)
        assert fp1 == fp2

    def test_different_type_different_fingerprint(self):
        frames = [
            {"filename": "/app/main.py", "function": "handle"},
        ]
        fp1 = compute_fingerprint("ValueError", "error", frames)
        fp2 = compute_fingerprint("TypeError", "error", frames)
        assert fp1 != fp2

    def test_different_location_different_fingerprint(self):
        fp1 = compute_fingerprint("ValueError", "error", [
            {"filename": "/app/main.py", "function": "handle"},
        ])
        fp2 = compute_fingerprint("ValueError", "error", [
            {"filename": "/app/routes.py", "function": "index"},
        ])
        assert fp1 != fp2

    def test_value_ignored_when_stacktrace_present(self):
        frames = [
            {"filename": "/app/main.py", "function": "handle"},
        ]
        fp1 = compute_fingerprint("ValueError", "invalid email", frames)
        fp2 = compute_fingerprint("ValueError", "missing field", frames)
        assert fp1 == fp2

    def test_value_contributes_when_no_stacktrace(self):
        fp1 = compute_fingerprint("ValueError", "invalid email", [])
        fp2 = compute_fingerprint("ValueError", "missing field", [])
        assert fp1 != fp2

    def test_parameterized_values_group_together(self):
        frames = []
        fp1 = compute_fingerprint("ValueError", "User 123 not found", frames)
        fp2 = compute_fingerprint("ValueError", "User 456 not found", frames)
        assert fp1 == fp2

    def test_returns_32_char_hex(self):
        fp = compute_fingerprint("ValueError", "test", [
            {"filename": "/app/main.py", "function": "handle"},
        ])
        assert len(fp) == 32
        assert all(c in "0123456789abcdef" for c in fp)

    def test_fallback_when_empty_frames_and_empty_value(self):
        fp = compute_fingerprint("ValueError", "", [])
        assert len(fp) == 32


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

    def test_parameterized_fstring_messages_group(self):
        fp1 = compute_fingerprint_from_log("myapp", "ERROR", "User 123 not found")
        fp2 = compute_fingerprint_from_log("myapp", "ERROR", "User 456 not found")
        assert fp1 == fp2

    def test_returns_32_char_hex(self):
        fp = compute_fingerprint_from_log("myapp", "ERROR", "test")
        assert len(fp) == 32
        assert all(c in "0123456789abcdef" for c in fp)
