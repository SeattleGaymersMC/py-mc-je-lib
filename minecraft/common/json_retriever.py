#!/usr/bin/env python3
"""Helper classes to retrieve and parse JSON from HTTP sources."""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Union
from httpx import AsyncClient as HttpAsyncClient
import json

T_JSON_RESULT = Union[Dict[str, Any], List[Any]]


class HttpJsonRetriever(ABC):
    """Abstract class for retrieving JSON over the HTTP/S protocol.

    :class:`abs.ABC` abstract class that implements class factory method to
    fetch JSON files over HTTP/S and use it to initialize the child class.

    :param URL: Default url to retrieve JSON result from.
    """

    URL: Optional[str] = None

    @abstractmethod
    def __init__(self, parsed_json: T_JSON_RESULT):
        """Override constrcutor to convert an JSON result into a class.

        :param parsed_json: Dictionary representation of the JSON result
            from :meth:`HttpJsonRetriever.load`.
        :type parsed_json: Dict[str, Any]
        """
        ...

    @classmethod
    async def load(klass, url: Optional[str] = None) -> "HttpJsonRetriever":
        """Fetch the JSON from the HTTP/S url and convert it into a class.

        :param url: Url to fetch JSON from.
        warning:: Passing a URL overrides the default class url and may
        retreive results that cannot be processed by the class constructor.
        Use this parameter at your own risk.
        :return: Child class that inherits the class :class:`HttpJsonRetriever`
        :rtype: :class:`HttpJsonRetriever`
        """
        actual_url = url if url else klass.URL
        if not actual_url:
            raise NotImplementedError(
                f"no default url has been defined for class {klass.__name__}"
            )

        async with HttpAsyncClient() as client:
            response = await client.get(actual_url)

            return klass(json.loads(response.text))

        raise RuntimeError("An unknown exception has occurred.")
