#!/usr/bin/env python3
"""Unittests for :class:`minecraft.common.json_retriever.HttpJsonRetriever`_."""

import pytest
from unittest.mock import AsyncMock, MagicMock
from httpx import AsyncClient, Response

from minecraft.common import json_retriever


@pytest.fixture
def mock_httpx_client(mocker):
    """Provide a mock HTTPX object for :py:mod:`minecraft.common.json_retriever`_.

    This mock handles the async context management so that the test only has to
    implement the client's method calls.
    """
    mock_http_client = AsyncMock(spec=AsyncClient)
    mock_http_client.__aenter__.return_value = mock_http_client

    mock_http_client_func = mocker.patch(
        "minecraft.common.json_retriever.HttpAsyncClient",
    )
    mock_http_client_func.return_value = mock_http_client

    yield mock_http_client

    mock_http_client_func.assert_called_once()
    mock_http_client.__aenter__.assert_called_once()


@pytest.mark.asyncio
async def test_load(mock_httpx_client):
    """Test the retriever fetches HTTP content and returns its class."""

    class TestJsonRetrieverClass(json_retriever.HttpJsonRetriever):
        """Test class implementation of the abstract HttpJsonRetriever class."""

        def __init__(self, parsed_json: json_retriever.T_JSON_RESULT):
            """Parse test JSON results."""
            self.test_val = parsed_json["test"]
            self.hello = parsed_json["hello"]
            self.thoughts = parsed_json["thoughts?"]

    http_response = MagicMock(Response)
    http_response.text = (
        '{"test": 123, "hello": "world", "thoughts?": ["no", "6969", "2121"]}'
    )
    mock_httpx_client.get.return_value = http_response

    test_url = "http://some.test.website.local/a/random/extension"
    test_result = await TestJsonRetrieverClass.load(url=test_url)

    mock_httpx_client.get.assert_called_once_with(test_url)
    assert test_result.test_val == 123
    assert test_result.hello == "world"
    assert test_result.thoughts == ["no", "6969", "2121"]


@pytest.mark.asyncio
async def test_load_with_default_url(mock_httpx_client):
    """Test the retriever fetches HTTP content and returns its class."""

    class TestJsonRetrieverClass(json_retriever.HttpJsonRetriever):
        """Test class implementation of the abstract HttpJsonRetriever class."""

        URL = "http://some.test.website.local/a/random/extension"

        def __init__(self, parsed_json: json_retriever.T_JSON_RESULT):
            """Parse test JSON results."""
            self.test_val = parsed_json["test"]
            self.hello = parsed_json["hello"]
            self.thoughts = parsed_json["thoughts?"]

    http_response = MagicMock(Response)
    http_response.text = (
        '{"test": 123, "hello": "world", "thoughts?": ["no", "6969", "2121"]}'
    )
    mock_httpx_client.get.return_value = http_response

    test_result = await TestJsonRetrieverClass.load()

    mock_httpx_client.get.assert_called_once_with(TestJsonRetrieverClass.URL)
    assert test_result.test_val == 123
    assert test_result.hello == "world"
    assert test_result.thoughts == ["no", "6969", "2121"]


@pytest.mark.asyncio
async def test_load_bad_url():
    """Test an exception is raised when no URL is provided."""
    with pytest.raises(
        NotImplementedError,
        match=r"no default url has been defined for class HttpJsonRetriever"
    ):
        await json_retriever.HttpJsonRetriever.load()
