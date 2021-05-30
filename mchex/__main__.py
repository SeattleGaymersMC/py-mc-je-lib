#!/usr/bin/env python3

import json
import logging
import sys
from argparse import Namespace
from importlib import metadata
from typing import Dict, List, Optional
from mchex.arg_types import ServerForkType
from py import path

from configargparse import ArgParser, YAMLConfigFileParser

from .command import MinecraftHexCommand, MinecraftHexCommandError


def main(cli_flags: Optional[List[str]]) -> int:
    mchex_commands = load_command_plugins()

    mchex_parser = ArgParser(
        config_file_parser_class=YAMLConfigFileParser,
        default_config_files=["/etc/mchex.yaml", "~/.mchex.yaml", ".mchex.yaml"],
        description=(
            "Minecraft utility to help manage client and server environments for "
            "sysadmins."
        ),
        prog="mchex",
    )
    mchex_parser.add_argument(
        "log-level",
        "l",
        action="store",
        default="warning",
        type=str,
        choices={"critical", "error", "warning", "info", "debug"},
        help="Level of log messages to print",
    )
    mchex_parser.add_argument(
        "server-dir",
        "d",
        default="./",
        type=path.local,
        help="Server directory path",
    )
    mchex_parser.add_argument(
        "host", "h", default="localhost", type=str, help="Server hostname or IP address"
    )
    mchex_parser.add_argument(
        "port", "p", default=25565, type=int, help="Port the server is listening on"
    )
    mchex_parser.add_argument(
        "server-fork",
        "f",
        default="vanilla",
        type=ServerForkType,
        dest="server_fork",
        help="Type of server (eg. vanilla, bedrock, paper, etc)",
    )

    command_subparsers = mchex_parser.add_subparsers()
    command_subparsers.choices = mchex_commands.values()

    mchex_args: Namespace = mchex_parser.parse_args(args=cli_flags)
    mchex_cmd_name = mchex_args.get("mchex_cmd")
    mchex_cmd = mchex_commands[mchex_cmd_name]

    try:
        result = mchex_cmd(mchex_args)
    except Exception as err:
        msg = f"Encountered error running command {mchex_cmd_name}: {str(err)}"
        if mchex_args.log_level == logging.DEBUG:
            logging.error(msg, exc_info=err)
        else:
            logging.error(msg)

        return err.err_code if isinstance(err, MinecraftHexCommandError) else 255

    json.dump(result, sort_keys=True, indent=4)

    return result


def load_command_plugins() -> Dict[str, MinecraftHexCommand]:
    commands = {}
    for entrypoint in metadata.entry_points()["mchex.cmds"]:
        if entrypoint.name in commands:
            raise AttributeError(
                f"{entrypoint.name} conflicts with another plugin with the same name"
            )

        mchex_cmd_parser_cls = entrypoint.load()
        if not isinstance(mchex_cmd_parser_cls, MinecraftHexCommand):
            raise TypeError(
                f"{entrypoint} is not a Minecraft Hex Command, must be a "
                f"{MinecraftHexCommand.__name__} object"
            )

        mchex_cmd_parser: MinecraftHexCommand = mchex_cmd_parser_cls()
        mchex_cmd_parser.set_defaults(mchex_cmd=entrypoint.name)

        commands[entrypoint.name] = mchex_cmd_parser

    return commands


if __name__ == "__main__":
    sys.exit(main())
