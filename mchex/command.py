#!/usr/bin/env python3

from asyncio import iscoroutine, run
from argparse import ArgumentParser, Namespace
from abs import ABC, abstractmethod
from typing import Any, Dict


class MinecraftHexCommandError(Exception):
    def __init__(self, err_code: int, message: str):
        self.message = message
        self.err_code = err_code


class MinecraftHexCommand(ArgumentParser, ABC):
    @abstractmethod
    def run(self, args: Namespace) -> Dict[str, Any]:
        raise NotImplementedError()

    def __call__(self, args: Namespace) -> Dict[str, Any]:
        if iscoroutine(self.run):
            return await run(self.run(args))

        else:
            return run(self.run(args))
