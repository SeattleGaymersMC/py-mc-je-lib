#!/usr/bin/env python3
"""Async classes to help download files over HTTP."""

from collections.abc import Awaitable
from asyncio import create_task, Task, CancelledError
from httpx import AsyncClient as HttpAsyncClient
from tempfile import mkstemp
import hashlib
import os

from types import TracebackType
from typing import (
    Callable,
    Iterator,
    Optional,
    Union,
    Type,
)
from warnings import warn


class FileDownladException(Exception):
    """Base exception for file download errors."""

    pass


class FileDownloader:
    """HTTP based file download manager."""

    def __init__(
        self,
        url: str,
        expected_size: Optional[int] = None,
        file_hash: Optional[Union[bytes, str]] = None,
        file_hash_type: Callable[[], hashlib._hashlib.HASH] = hashlib.md5,
    ):
        """File download manager initialization method.

        :param url: HTTP/S URL to download a file from.
        :param expected_size: Expected size in bytes of the file.
        :param file_hash: Expected file hash of the file.
        :param file_hash_type: :class:`hashlib` method representing the hash type
            (eg. md5, sha1, etc).
        """
        self.url = url
        self.expected_size = expected_size
        self.file_hash_type = file_hash_type

        self.file_hash = None
        if file_hash:
            self.file_hash = (
                file_hash if isinstance(file_hash, bytes) else file_hash.encode()
            )

    def download(
        self,
        filename: str,
        overwrite: bool = False,
        no_warnings: bool = False,
    ) -> "FileDownloadContext":
        """Download the remote object to a local file.

        :param filename: Download location for the remote file.
        :param overwrite: Overwrite the file if it exists (default=False)
        :param no_warnings: Suppress all warnings (default=False)
        :return: :class:`FileDownloadContext`_ context manager for the file download.
        """
        return FileDownloadContext(
            self,
            filename,
            overwrite=overwrite,
            no_warnings=no_warnings,
        )


class FileDownloadContext(Awaitable):
    """Download context to keep track of a single file being downloaded.

    :param downloader: :class:`FileDownloader`_ that triggered the download.
    :param filename: Path to save the downloaded file to
    :param overwrite: Overwrite the file if it exists
    :param no_warnings: Mute all warnings about missing verification sources
    :param download_task: :class:`asyncio.Task`_ coroutine of the actual
        download
    :param download_expected_size: # bytes to download reported by the
        download source
    :param download_size: # bytes downloaded
    """

    def __init__(
        self,
        downloader: FileDownloader,
        filename: str,
        overwrite: bool = False,
        no_warnings: bool = False,
    ):
        """:class:`FileDownloadContext`_ init method."""
        self.downloader = downloader
        self.filename = filename
        self.overwrite = overwrite
        self.no_warnings = no_warnings
        self.download_task: Optional[Task] = None
        self.download_expected_size = (
            self.downloader.expected_size if self.downloader.expected_size else -1.0
        )
        self.download_size = 0

    def exists(self) -> bool:
        """Check if the local file exists.

        :return: True if the local file exists
        """
        return os.path.isfile(self.filename)

    @property
    def filehash(self) -> bytes:
        """Hash of the file in bytes, using the downloader's hash method.

        :return: Hash digest of the file in bytes
        """
        if not self.exists():
            raise FileNotFoundError(f"The file {self.filename} does not exist")

        if not self.downloader.file_hash_type:
            raise AttributeError(
                f"hash method for file {self.filename} is not provided in the "
                "downloader"
            )

        hasher = self.downloader.file_hash_type()
        with open(self.filename, "r+b") as file_handle:
            hasher.update(file_handle.read())

        return hasher.hexdigest().encode()

    @property
    def filesize(self) -> int:
        """Size in bytes of the local file.

        :return: Size of file in bytes
        """
        if not self.exists():
            raise FileNotFoundError(f"file {self.filename} does not exist")

        return os.path.getsize(self.filename)

    def downloading(self) -> bool:
        """Check if the file is downloading.

        :return: True if downloading, False otherwise
        """
        if not self.download_task:
            return False

        return not self.download_task.done()

    def downloaded(self) -> bool:
        """Check if the file completed downloading.

        :return: True if the file is downloaded successfully, False otherwise
        """
        return (
            not self.downloading() and not self.failed() and self.download_task.result()
        )

    def failed(self) -> bool:
        """Check if the download failed.

        :return: True if the download failed, False otherwise
        """
        return (
            not self.downloading()
            and self.download_task
            and self.download_task.exception() is not None
        )

    def failure(self) -> Optional[Exception]:
        """Retreive the failure raised during the download.

        :return: The exception if one was raised during the download, else None
        """
        if not self.failed():
            return None

        return self.download_task.exception()

    def download_progress(
        self,
    ) -> Optional[float]:
        """Floating point percentage of the download progress.

        :return: % of file downloaded, None if no download
        """
        if not self.download_task:
            return None

        return self.download_size / self.download_expected_size

    def verify_hash(self) -> bool:
        """Verify the hash using the downloader's hash method and digest.

        :return: True if the file digest matches the downloader's expected hash,
            else False.
        """
        if not self.exists():
            return False

        if not self.downloader.file_hash or not self.downloader.file_hash_type:
            if not self.no_warnings:
                warn(
                    (
                        f"downloader does not specify a file hash or hash type, cannot"
                        f"verify integrity of file {self.filename}"
                    ),
                    RuntimeWarning,
                )
            return True

        return self.filehash == self.downloader.file_hash

    def verify_size(self) -> bool:
        """Verify the file size against the downloader's expected size.

        :return: True if file size matches the downloader's expected size, else False.
        """
        if not self.exists():
            return False

        if not self.downloader.expected_size:
            if not self.no_warnings:
                warn(
                    (
                        f"downloader has no expected file size, cannot verify size of "
                        f"file {self.filename}"
                    ),
                    RuntimeWarning,
                )

            return True

        return self.filesize == self.downloader.expected_size

    def verify(self) -> bool:
        """Run all verify methods.

        :return: True if all verificiation methods succeed, False otherwise
        """
        return self.exists() and self.verify_hash() and self.verify_size()

    async def __download(self) -> bool:
        if self.exists() and not self.overwrite:
            raise FileDownladException(
                f"File {self.file_path} exists and overwriting is not permitted"
            )

        try:
            # Create temporary file
            (
                tmp_file,
                tmp_filename,
            ) = mkstemp()

            # Start downloading the file from an HTTP stream
            client = HttpAsyncClient()
            async with client.stream("GET", self.downloader.url) as streamer:
                self.download_expected_size = int(streamer.headers["Content-Length"])
                self.download_size = 0

                async for chunk in streamer.aiter_bytes():
                    os.write(tmp_file, bytes([chunk]))
                    self.download_size = streamer.num_bytes_downloaded

            os.fsync(tmp_file)

            # Move file to final location
            os.makedirs(
                os.path.dirname(self.filename),
                exist_ok=True,
            )
            if self.overwrite:
                os.replace(tmp_filename, self.filename)
            else:
                os.rename(tmp_filename, self.filename)

            # Check file integrity
            if not self.verify_size():
                raise FileDownladException(
                    "wrong download file size, expected "
                    f"{self.downloader.expected_size} but got {self.filesize}"
                )

            if not self.verify_hash():
                raise FileDownladException(
                    "failed to verify file integrity, expected "
                    f"'{self.downloader.file_hash}' but got '{self.filehash}'"
                )

        finally:
            # Clean up the temporary file
            os.close(tmp_file)
            if os.path.exists(tmp_filename):
                os.remove(tmp_filename)

        return True

    async def __aenter__(
        self,
    ) -> "FileDownloadContext":
        """Start a background file download.

        Starts a download and returns itself as the download metadata for
        the code opening the context. Download progress will be tracked via
        properties and methods of this class. The calling code will have to
        wait for the download to complete, otherwise the download will be
        cancelled if the context is closed early. An example call from the
        :class:`FileDownloader`_:
        .. code-block: python
            async with file_downloader.download("some_path") as download:
                with tqdm(total=download.download_expected_size) as progress_bar:
                    last_size = 0
                    while download.downloading():
                        if progress_bar.total != download.download_expected_size:
                            progress_bar.total = download.download_expected_size

                        progress_bar.update(n=download.download_size - last_size)

                print("Downloaded the file")

        :return: Returns itself as the Async Context Manager
        :rtype: FileDownloadContext
        """
        if not self.download_task:
            self.download_task = create_task(self.__download())

        return self

    async def __aexit__(
        self,
        exc_type: Optional[Type[BaseException]],
        exc_value: Optional[BaseException],
        traceback: Optional[TracebackType],
    ) -> bool:
        """Magic method to stop a download if the context was left early."""
        if not self.download_task.done():
            self.download_task.cancel()
            try:
                await self.download_task
            except CancelledError:
                pass

        return True

    def __await__(self) -> Iterator[bool]:
        """Start a download and wait for it as an awaitable method.

        Starts and waits for download to complete. This provides a simple
        interface for downloading files if the calling source doesn't need to
        monitor the download progress. Instead of building an `async with`
        statement and manually following the download, the calling source can
        `await` the download instead:
        .. code-block:: python
           try:
               success = await file_downloader.download("some/path")
            except FileDownloadException as err:
                print("The download failed")

        :return: True if the download succeeded, False if it didn't
        :rtype: bool
        """
        if not self.download_task:
            self.download_task = create_task(self.__download())

        # Wait for download to complete
        # All verification happens in the download method, failures
        # & exceptions will be raised from here
        yield from self.download_task.__await__()

        return self.downloaded()


class NamedFileDownloader(FileDownloader):
    """File downloader for files with a set relative path.

    The :class:`minecraft.common.file_downloader.NamedFileDownloader` class is
    used when the filename and file's relative location to the download directory
    are known and need to be set. For example, if we always want to download
    `fileA` to the path `test/files/` in the dowlnoad location, the following code
    will download the file to `/download/dir/test/files/fileA` when instructed to
    download into `/download/dir`:
    .. code-block: python
        downloader = NamedFileDownloader(
            "https://some.test/url",
            "fileA",
            relative_file_path="test/files",
        )
        await downloader.download("/download/dir")
    """

    def __init__(
        self,
        url: str,
        filename: str,
        relative_file_path: str = "./",
        expected_size: Optional[int] = None,
        file_hash: Optional[Union[bytes, str]] = None,
        file_hash_type: Callable[[], hashlib._hashlib.HASH] = hashlib.md5,
    ):
        """Initialize the file downloader with a relative file path.

        :param url: HTTP/S URL to download a file from.
        :param filename: Name of the file that will be downloaded.
        :param relative_file_path: Relative directory path to download a file to.
        :param expected_size: Expected size in bytes of the file.
        :param file_hash: Expected file hash of the file.
        :param file_hash_type: :class:`hashlib` method representing the hash type
            (eg. md5, sha1, etc).
        """
        super().__init__(
            url,
            expected_size=expected_size,
            file_hash=file_hash,
            file_hash_type=file_hash_type,
        )
        self.filename = filename
        self.relative_file_path = relative_file_path

    def download(
        self,
        download_dir: str,
        overwrite: bool = False,
        no_warnings: bool = False,
    ) -> "FileDownloadContext":
        """Download the remote object to a local file.

        :param download_dir: Download location for the remote file.
        :param overwrite: Overwrite the file if it exists (default=False)
        :param no_warnings: Suppress all warnings (default=False)
        :return: :class:`FileDownloadContext`_ context manager for the file download.
        """
        file_path = os.path.realpath(
            os.path.join(download_dir, self.relative_file_path, self.filename)
        )
        return FileDownloadContext(
            self,
            file_path,
            overwrite=overwrite,
            no_warnings=no_warnings,
        )
