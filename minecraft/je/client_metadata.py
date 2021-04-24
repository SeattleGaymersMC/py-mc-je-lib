#!/usr/bin/env python3
"""Retrieve and interact with Minecraft: Java Edition Client Metadata.

MC: JE Client Metadata defines download details (location, size, checksums) for clients,
servers, assets, de-obfuscation files, etc in a MC: JE version. This module provides
functionality to interact with this metadata and download these files. This
implementation is based on the Version Manifest provided by Mojang. See `Gamepedia
Minecraft Wiki<https://minecraft.gamepedia.com/Client.json>`_.
"""
# Implementation based on Version Manifest described in
# https://minecraft.gamepedia.com/Client.json

import hashlib
from datetime import datetime
from typing import Any, Dict

from minecraft.common.file_downloader import NamedFileDownloader
from minecraft.common.json_retriever import HttpJsonRetriever

from .common import ComplianceLevel, JEDevelopmentPhase, JEVersionType


class JEClientMetadata(HttpJsonRetriever):
    """Class representation of the Minecraft: Java Edition client metadata.

    :class:`HttpJsonRetriever`_ child class to fetch and represent the Minecraft: Java
    Edition client metadata. This metadata sits next to the `client.jar` file and
    provides links to the client & server jars, various game assets, decompiler
    references, and launcher flags. See `Gamepedia Minecraft Wiki
    <https://minecraft.gamepedia.com/Client.json>`_.

    :param id: The Minecraft: Java Edition version ID for the deployment
        (eg. 1.16.4, 21w08b).
    :param compliance_level: Denotes if the version is up to date and includes
        the most recent player safety features.
    :param released: :class:`datetime.datetime`_ when the version was first released
    :param type: :class:`minecraft.je.JEVersionType` representation of the
        version release type.
    :param development_phase: :class:`minecraft.je.JEDevelopmentPhase`
        representation for the development phase the version was released in.
    :param assets_version: Version ID of the MC: JE version's assets.
    :param main_class: Java class `main` method.
    :param min_launcher_version: Minimum Minecraft launcher version that can run
        this version of MC: JE.
    :param client_downloader:
        :class:`minecraft.common.file_downloader.NamedFileDownloader` file downloader
        for the MC: JE version's client JAR file.
    :param server_downloader:
        :class:`minecraft.common.file_downloader.NamedFileDownloader` file downloader
        for the MC: JE versions server JAR file if available.
    """

    def __init__(self, parsed_json: Dict[str, Any]):
        """Initialize the MC: JE client metadata from the remote JSON data.

        The class is meant to be loaded with the JSON decoded objects from the
        official Minecraft hosted source for Minecraft: Java Edition client metadata.
        The ideal method for invoking this method is through
        :func:`~minecraft.je.client_metadata.JEClientMetadata.load('some-url')`.

        :param parsed_json: Dictionary decoded representation of the client metadata
            from the Minecraft hosted location.
        """
        self.compliance_level = ComplianceLevel(parsed_json["complianceLevel"])
        self.id: str = parsed_json["id"]
        self.type = JEVersionType(parsed_json["type"])
        self.development_phase = JEDevelopmentPhase.from_id(self.id, self.type)
        self.assets_version: str = parsed_json["assets"]
        self.main_class: str = parsed_json["mainClass"]
        self.min_launcher_version: int = parsed_json["minimumLauncherVersion"]

        self.released = datetime.fromisoformat(parsed_json["releaseTime"])
        self._time = datetime.fromisoformat(
            parsed_json["time"]
        )  # Same as "releaseTime"

        self.client_downloader = NamedFileDownloader(
            parsed_json["downloads"]["client"]["url"],
            "client.jar",
            expected_size=parsed_json["downloads"]["client"]["size"],
            file_hash=parsed_json["downloads"]["client"]["sha1"],
            file_hash_type=hashlib.sha1,
        )
        self.server_downlaoder = None
        if parsed_json["downloads"]["server"]:
            self.server_downloader = NamedFileDownloader(
                parsed_json["downloads"]["server"]["url"],
                "server.jar",
                expected_size=parsed_json["downloads"]["server"]["size"],
                file_hash=parsed_json["downloads"]["server"]["sha1"],
                file_hash_type=hashlib.sha1,
            )
