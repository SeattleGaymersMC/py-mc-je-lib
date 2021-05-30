#!/usr/bin/env python3

from minecraft.server_fork import server_forks, ServerFork


def ServerForkType(fork_name: str) -> ServerFork:
    return server_forks().get(fork_name)
