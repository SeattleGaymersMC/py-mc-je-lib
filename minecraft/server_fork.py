#!/usr/bin/env python3

from abc import ABC, abstractmethod
from importlib import metadata
from typing import Dict, List, Optional, Union
from re import Pattern
from datetime import datetime
from functools import cache
from dataclasses import dataclass


@dataclass(eq=True)
class ServerVersion(ABC):
    created_at: datetime  # Listed first to enable sorting on creation dates
    id: str
    download_url: str
    server_fork: "ServerFork"
    expected_size: Optional[int] = None
    file_hash: Optional[Union[bytes, str]] = None
    file_hash_type: str = "md5"

    def filename(self) -> str:
        return f"{self.server_fork.short_name}-{self.id}.jar"

    def __str__(self) -> str:
        """Return the indexable version ID, used as input for maintenance operations."""
        return self.id

    def __lt__(self, other: "ServerVersion") -> bool:
        return self.created_at < other.created_at

    def __le__(self, other: "ServerVersion") -> bool:
        return self.created_at <= other.created_at

    def __gt__(self, other: "ServerVersion") -> bool:
        return self.created_at > other.created_at

    def __ge__(self, other: "ServerVersion") -> bool:
        return self.created_at >= other.created_at


@dataclass(eq=True)
class ServerFork:
    short_name: str
    long_name: str
    description: str
    project_url: Optional[str] = None

    @abstractmethod
    async def versions(self) -> List[ServerVersion]:
        ...

    async def latest(self) -> ServerVersion:
        return sorted(await self.versions(), reverse=True)[0]

    async def search(self, regex: Pattern) -> List[ServerVersion]:
        return list(sorted(filter(lambda v: regex.match(v.id), await self.versions())))

    async def get(self, id: str) -> ServerVersion:
        return filter(lambda v: v.id == id, await self.versions)


@cache
def server_forks() -> Dict[ServerFork]:
    forks = {}
    for entrypoint in metadata.entry_points()["mchex.server_forks"]:
        server_fork = entrypoint.load()
        if not isinstance(server_fork, ServerFork):
            raise TypeError(
                f"{entrypoint} does not inherit {ServerFork.__name__} and "
                "is not supported"
            )

        if server_fork.short_name in forks:
            raise TypeError(
                f"{entrypoint} is already loaded, {server_fork.__name__} "
                "may be a duplicate"
            )

        forks[server_fork.short_name] = server_fork

    return forks
