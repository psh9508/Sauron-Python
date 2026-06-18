from unittest.mock import MagicMock, call, patch

import sauron_python.sauron_sdk as sauron
from sauron_python.core.suron_client import SauronClient


class TestInitRegistersAtexit:
    def test_init_registers_close_handler(self):
        sauron._atexit_registered = False
        with patch.object(sauron, "SauronClient"), \
             patch.object(sauron, "_setup_integrations"), \
             patch.object(sauron.atexit, "register") as mock_register:
            sauron.init(repository_id=1, endpoint="http://example.test/ingest")

        mock_register.assert_called_once_with(sauron._close_at_exit)

    def test_init_registers_only_once(self):
        sauron._atexit_registered = False
        with patch.object(sauron, "SauronClient"), \
             patch.object(sauron, "_setup_integrations"), \
             patch.object(sauron.atexit, "register") as mock_register:
            sauron.init(repository_id=1, endpoint="http://example.test/ingest")
            sauron.init(repository_id=2, endpoint="http://example.test/ingest")

        assert mock_register.call_count == 1


class TestCloseAtExit:
    def test_closes_current_client(self):
        mock_client = MagicMock()
        sauron._client = mock_client

        sauron._close_at_exit()

        mock_client.close.assert_called_once()

    def test_no_client_is_noop(self):
        sauron._client = None
        # Should not raise.
        sauron._close_at_exit()


class TestClientClose:
    def test_flushes_then_closes_transport(self):
        client = SauronClient(repository_id=1, endpoint="http://example.test/ingest")
        mock_transport = MagicMock()
        client._transport = mock_transport

        client.close(timeout=1.5)

        mock_transport.flush.assert_called_once_with(1.5)
        mock_transport.close.assert_called_once()

    def test_flush_happens_before_close(self):
        client = SauronClient(repository_id=1, endpoint="http://example.test/ingest")
        manager = MagicMock()
        client._transport = manager

        client.close()

        # flush must be called before close so pending events drain first.
        assert manager.mock_calls.index(call.flush(2.0)) < \
            manager.mock_calls.index(call.close())
