"""Tests for src.utils.http_client — HTTP fetch with retry logic."""

import json
from unittest.mock import MagicMock, patch

import httpx
import pytest
from src.utils.http_client import create_client, fetch_json_with_retry


class TestCreateClient:

    def test_returns_httpx_client(self) -> None:
        client = create_client()
        try:
            assert isinstance(client, httpx.Client)
        finally:
            client.close()

    def test_custom_timeout(self) -> None:
        client = create_client(timeout_s=60)
        try:
            assert client.timeout.connect == 60
        finally:
            client.close()

    def test_has_json_accept_header(self) -> None:
        client = create_client()
        try:
            assert client.headers["accept"] == "application/json"
        finally:
            client.close()


class TestFetchJsonWithRetry:

    def _mock_client_with_response(
        self,
        status_code: int = 200,
        json_data: object = None,
        text: str = "",
    ) -> httpx.Client:
        """Create a mock httpx.Client that returns a controlled response."""
        mock_response = MagicMock(spec=httpx.Response)
        mock_response.status_code = status_code
        mock_response.json.return_value = json_data
        mock_response.text = text

        if status_code >= 400:
            mock_response.raise_for_status.side_effect = httpx.HTTPStatusError(
                message=f"HTTP {status_code}",
                request=MagicMock(),
                response=mock_response,
            )
        else:
            mock_response.raise_for_status.return_value = None

        mock_client = MagicMock(spec=httpx.Client)
        mock_client.get.return_value = mock_response
        return mock_client

    def test_successful_fetch_returns_data(self) -> None:
        data = [{"id": 1}, {"id": 2}]
        client = self._mock_client_with_response(json_data=data)

        result = fetch_json_with_retry(client, "https://example.com/api", max_retries=1)

        assert result == data
        client.get.assert_called_once()

    def test_successful_fetch_dict_response(self) -> None:
        data = {"key": "value"}
        client = self._mock_client_with_response(json_data=data)

        result = fetch_json_with_retry(client, "https://example.com/api", max_retries=1)
        assert result == data

    @patch("src.utils.http_client.time.sleep")
    def test_retries_on_http_error(self, mock_sleep: MagicMock) -> None:
        """Should retry on HTTP errors and eventually raise after max retries."""
        client = self._mock_client_with_response(status_code=500)

        with pytest.raises(httpx.HTTPStatusError):
            fetch_json_with_retry(
                client, "https://example.com/api", max_retries=3, base_delay_s=1,
            )

        assert client.get.call_count == 3
        assert mock_sleep.call_count == 2  # no sleep after last attempt

    @patch("src.utils.http_client.time.sleep")
    def test_exponential_backoff_delays(self, mock_sleep: MagicMock) -> None:
        """Verify that retry delays follow exponential backoff."""
        client = self._mock_client_with_response(status_code=503)

        with pytest.raises(httpx.HTTPStatusError):
            fetch_json_with_retry(
                client, "https://example.com/api", max_retries=4, base_delay_s=2,
            )

        delays = [call.args[0] for call in mock_sleep.call_args_list]
        assert delays == [2, 4, 8]  # 2*2^0, 2*2^1, 2*2^2 (no delay after last)

    @patch("src.utils.http_client.time.sleep")
    def test_retries_on_request_error(self, mock_sleep: MagicMock) -> None:
        """Should retry on network-level errors (connection refused, timeout, etc.)."""
        mock_client = MagicMock(spec=httpx.Client)
        mock_client.get.side_effect = httpx.RequestError("Connection refused")

        with pytest.raises(httpx.RequestError):
            fetch_json_with_retry(
                mock_client, "https://example.com/api", max_retries=2, base_delay_s=1,
            )

        assert mock_client.get.call_count == 2

    @patch("src.utils.http_client.time.sleep")
    def test_retries_on_invalid_json(self, mock_sleep: MagicMock) -> None:
        """Should retry when response body is not valid JSON."""
        mock_response = MagicMock(spec=httpx.Response)
        mock_response.status_code = 200
        mock_response.raise_for_status.return_value = None
        mock_response.json.side_effect = json.JSONDecodeError("Expecting value", "", 0)
        mock_response.text = "<html>not json</html>"

        mock_client = MagicMock(spec=httpx.Client)
        mock_client.get.return_value = mock_response

        with pytest.raises(json.JSONDecodeError):
            fetch_json_with_retry(
                mock_client, "https://example.com/api", max_retries=2, base_delay_s=1,
            )

        assert mock_client.get.call_count == 2

    @patch("src.utils.http_client.time.sleep")
    def test_succeeds_after_transient_failure(self, mock_sleep: MagicMock) -> None:
        """Should return data if a retry succeeds after initial failure."""
        fail_response = MagicMock(spec=httpx.Response)
        fail_response.status_code = 500
        fail_response.raise_for_status.side_effect = httpx.HTTPStatusError(
            message="HTTP 500", request=MagicMock(), response=fail_response,
        )

        ok_response = MagicMock(spec=httpx.Response)
        ok_response.status_code = 200
        ok_response.raise_for_status.return_value = None
        ok_response.json.return_value = [{"id": 1}]

        mock_client = MagicMock(spec=httpx.Client)
        mock_client.get.side_effect = [fail_response, ok_response]

        result = fetch_json_with_retry(
            mock_client, "https://example.com/api", max_retries=3, base_delay_s=1,
        )

        assert result == [{"id": 1}]
        assert mock_client.get.call_count == 2
