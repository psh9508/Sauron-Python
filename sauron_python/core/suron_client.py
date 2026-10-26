from sauron_python.core.http_transport import HttpTransport
from sauron_python.models.envelope import Envelope


class SauronClient:
    def __init__(self, *, repository_key: str, endpoint: str, repository_url: str | None = None):
        self.repository_key = repository_key
        self.endpoint = endpoint
        self.repository_url = repository_url
        self._transport = HttpTransport()

    def send(self, data: dict):
        data["repository_key"] = self.repository_key
        if self.repository_url:
            data["repository_url"] = self.repository_url
        envelope = Envelope(
            id="",
            endpoint=self.endpoint,
            payload=data,
        )
        self._transport.send_envelope(envelope)

    def close(self, timeout: float = 2.0):
        self._transport.flush(timeout)
        self._transport.close()
