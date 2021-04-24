#!/usr/bin/env python3
"""Unittests for :class:`minecraft.common.file_downloader.FileDownloader`_."""

import pytest
from httpx import Response
from hashlib import md5
import tempfile
import os
from unittest.mock import MagicMock

from minecraft.common import file_downloader


@pytest.fixture
def temp_file():
    """Create a tempfile to store download files to."""
    tmp_file_handler, tmp_filename = tempfile.mkstemp()

    os.close(tmp_file_handler)
    if os.path.exists(tmp_filename):
        os.remove(tmp_filename)

    yield tmp_filename

    if os.path.exists(tmp_filename):
        os.remove(tmp_filename)


@pytest.fixture
def mock_httpx_stream(mocker):
    """Create mock HTTPX stream."""
    test_bytes = b"123123123 what a test 123123"
    hasher = md5()
    hasher.update(test_bytes)
    test_hash = hasher.hexdigest()
    test_size = len(test_bytes)
    test_url = "some badly formed url"

    mock_http_streamer = MagicMock(spec=Response)
    mock_http_streamer.headers = {
        "Content-Length": test_size,
    }
    mock_http_streamer.aiter_bytes.return_value.__aiter__.return_value = test_bytes
    mock_http_streamer.num_bytes_downloaded = len(test_bytes)

    mock_stream_ctx_mngr = MagicMock()
    mock_http_client = mocker.patch("minecraft.common.file_downloader.HttpAsyncClient")
    mock_http_client.return_value.stream.return_value = mock_stream_ctx_mngr
    mock_stream_ctx_mngr.__aenter__.return_value = mock_http_streamer

    yield test_url, test_size, test_hash


@pytest.mark.asyncio
async def test_async_with_file_download(temp_file, mock_httpx_stream):
    """Test the file downloads when used as an Async Context Manager."""
    test_url, test_size, test_hash = mock_httpx_stream
    tmp_filename = temp_file

    async with file_downloader.FileDownloader(
        test_url, expected_size=test_size, file_hash=test_hash
    ).download(tmp_filename, no_warnings=True) as download:
        assert download.downloading()
        assert not download.failed()
        assert download.failure() is None
        assert 0.0 == download.download_progress()
        assert not download.exists()
        with pytest.raises(FileNotFoundError):
            download.filesize

        with pytest.raises(FileNotFoundError):
            download.filehash

        await download.download_task

    assert not download.failed()
    assert download.downloaded()
    assert download.exists()
    assert download.verify_hash()
    assert download.verify_size()
    assert download.verify()
    assert 1.0 == download.download_progress()


@pytest.mark.asyncio
async def test_async_file_download(temp_file, mock_httpx_stream):
    """Assert the file downloads when used as a coroutine."""
    test_url, test_size, test_hash = mock_httpx_stream
    tmp_filename = temp_file

    download = file_downloader.FileDownloader(
        test_url, expected_size=test_size, file_hash=test_hash
    ).download(tmp_filename, no_warnings=True)

    assert not download.downloading()
    assert not download.failed()
    assert download.failure() is None
    assert download.download_progress() is None
    assert not download.exists()
    with pytest.raises(FileNotFoundError):
        download.filesize

    with pytest.raises(FileNotFoundError):
        download.filehash

    assert await download

    assert not download.failed()
    assert download.downloaded()
    assert download.exists()
    assert download.verify_hash()
    assert download.verify_size()
    assert download.verify()
    assert 1.0 == download.download_progress()
