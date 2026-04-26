from sauron_python.core.parameterizer import Parameterizer, default_parameterizer


class TestParameterizer:
    def setup_method(self):
        self.p = default_parameterizer

    def test_no_dynamic_values(self):
        assert self.p.parameterize("no dynamic values here") == "no dynamic values here"

    def test_empty_string(self):
        assert self.p.parameterize("") == ""

    def test_int_replacement(self):
        assert self.p.parameterize("User 123 not found") == "User <int> not found"

    def test_multiple_ints(self):
        assert self.p.parameterize("Error on line 42, column 7") == "Error on line <int>, column <int>"

    def test_float_replacement(self):
        assert self.p.parameterize("took 3.14 seconds") == "took <float> seconds"

    def test_negative_float(self):
        assert self.p.parameterize("offset -2.5 detected") == "offset <float> detected"

    def test_uuid_replacement(self):
        result = self.p.parameterize(
            "Request a1b2c3d4-e5f6-7890-abcd-ef1234567890 failed"
        )
        assert result == "Request <uuid> failed"

    def test_uuid_not_caught_by_int(self):
        result = self.p.parameterize("id=550e8400-e29b-41d4-a716-446655440000")
        assert "<int>" not in result
        assert "<uuid>" in result

    def test_email_replacement(self):
        result = self.p.parameterize("Email user@example.com is invalid")
        assert result == "Email <email> is invalid"

    def test_url_replacement(self):
        result = self.p.parameterize("Failed to fetch https://api.example.com/v2/users")
        assert result == "Failed to fetch <url>"

    def test_ip_replacement(self):
        assert self.p.parameterize("Connection from 192.168.1.100 refused") == (
            "Connection from <ip> refused"
        )

    def test_date_iso_replacement(self):
        result = self.p.parameterize("Error at 2024-01-15T10:30:00Z")
        assert result == "Error at <date>"

    def test_date_simple_replacement(self):
        result = self.p.parameterize("Since 2024-01-15 data is missing")
        assert result == "Since <date> data is missing"

    def test_hex_replacement(self):
        assert self.p.parameterize("Address 0xdeadbeef invalid") == (
            "Address <hex> invalid"
        )

    def test_mixed_types(self):
        result = self.p.parameterize(
            "User 42 at 192.168.0.1 sent email to admin@test.com"
        )
        assert "<int>" in result
        assert "<ip>" in result
        assert "<email>" in result

    def test_custom_patterns(self):
        from sauron_python.core.parameterizer import ParameterizationPattern

        custom = Parameterizer(
            patterns=[ParameterizationPattern(name="word", pattern=r"\b[a-z]+\b")]
        )
        assert custom.parameterize("hello world 123") == "<word> <word> 123"
