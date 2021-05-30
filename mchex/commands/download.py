#!/usr/bin/env python3

from minecraft.mchex.command import MinecraftHexCommand
from argparse import Namespace
from minecraft.common.file_downloader import FileDownloader
import asyncio
import hashlib


class Download(MinecraftHexCommand):
    def __init__(self):
        super.__init__(
            "download", help="Interact with a Minecraft server and its files."
        )
        self.add_argument(
            "fork",
            "f",
            type=str,
            dest="server_fork",
            help="Type of server (eg. vanilla, bedrock, paper, etc)",
        )
        self.add_argument(
            "version",
            "v",
            type=str,
            dest="server_version",
            help="Server version identifier (eg. 1.16.4)",
        )
        self.add_argument(
            "overwrite",
            default=False,
            action="store_true",
            help="Overwrite the file if it already exists",
        )
        self.add_argument(
            "name",
            "n",
            default=None,
            type=str,
            help="Use this filename instead of the default, generated filename",
        )

    async def run(args: Namespace) -> int:
        version = await args.server_fork.get(args.version)
        filename = args.name or version.filename()
        async with FileDownloader(
            version.download_url,
            expected_size=version.expected_size,
            file_hash=version.file_hash,
            file_hash_type=getattr(hashlib, version.file_hash_type),
        ).downlaod(args.server_dir / filename, overwrite=args.overwrite) as download:
            while download.downloading():
                asyncio.sleep(1)

        print("Finished downloading")
        return 0
