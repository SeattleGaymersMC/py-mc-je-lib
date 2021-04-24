#!/usr/bin/env python3
"""Classes to retrieve and interact with the Version Manifest.

Implementation based on the Version Manifest described at
https://minecraft.gamepedia.com/Version_manifest.json.
"""

import re
from datetime import datetime
from typing import Any, Dict, List

from minecraft.common.json_retriever import HttpJsonRetriever

from .client_metadata import JEClientMetadata
from .common import ComplianceLevel, JEDevelopmentPhase, JEVersionType


class JEVersion:
    """Class representation of Minecraft: Java Edition versions.

    An object representin the Minecraft: Java Edition version metadata for
    a Minecraft: JE version available in the Minecraft launcher. This contains
    the client meatadata used to download a Minecraft client, server, assets,
    etc. This class represents the versions provided by the Minecraft: Java
    Edition Version Manifest v2. The class definition is based on the
    `version_manifest_v2.json` defined in the
    `Gamepedia Minecraft wiki<https://minecraft.gamepedia.com/Version_manifest.json>`_
    and provided by `Minecraft<
    https://launchermeta.mojang.com/mc/game/version_manifest_v2.json>`_.

    :param id: The Minecraft: Java Edition version ID for the deployment
        (eg. 1.16.4, 21w08b)
    :type id: int
    :param type: Enum representation of the version release type
    :type type: class:`JEVersionType`
    :param client_version_url: URL to the client version metadata
    :type client_version_url: str
    :param last_updated: Time when the version files were last updated
    :type last_updated: datetime
    :param released: :class:`datetime.datetime`_ when the version was first released
    :type released: :class:`datetime.datetime`_
    :param sha1: The SHA1 hash of the Minecraft: Java Edition version; acts as
        the client.json file name
    :type sha1: str
    :param compliance_level: Denotes if the version is up to date and includes
        the most recent player safety features
    :type compliance_level: class:`.compliance_level.ComplianceLevel`
    """

    def __init__(
        self,
        id: str,
        version_type: str,
        client_version_url: str,
        last_updated: str,
        released: str,
        sha1: str,
        compliance_level: int,
    ):
        """Initialize state and associations for :class:`JEVersion`_."""
        self.id: str = id
        self.type = JEVersionType(version_type)
        self.development_phase = JEDevelopmentPhase.from_id(self.id, self.type)
        self.client_version_url: str = client_version_url
        self.last_updated = datetime.fromisoformat(last_updated)
        self.released = datetime.fromisoformat(released)
        self.sha1: str = sha1
        self.compliance_level = ComplianceLevel(compliance_level)

        self._client_metadata = None

    async def get_metadata(self) -> JEClientMetadata:
        """Retrieve the MC: JE's client metadata."""
        if self._client_metadata:
            return self._client_metadata

        self._client_metadata = await JEClientMetadata.load(url=self.client_version_url)
        return self._client_metadata

    def __eq__(self, other: "JEVersion") -> bool:
        """Check if the MC: JE versions are the same."""
        return self.id == other.id

    def __ne__(self, other: "JEVersion") -> bool:
        """Check if the MC: JE versions are not the same."""
        return self.id != other.id

    def __lt__(self, other: "JEVersion") -> bool:
        """Check if the MC: JE is older than the compared version."""
        return self.released < other.released

    def __le__(self, other: "JEVersion") -> bool:
        """Check if the MC: JE version is older or the same as the compared version."""
        return self.released <= other.released

    def __gt__(self, other: "JEVersion") -> bool:
        """Check if the MC: JE version is newer than the given version."""
        return self.released > other.released

    def __ge__(self, other: "JEVersion") -> bool:
        """Check if the MC: JE version is newer or the same as the given version."""
        return self.released >= other.released

    def __str__(self) -> str:
        """Print ID for the MC: JE version."""
        return self.id

    def __repr__(self) -> str:
        """Print properties representing the MC: JE version."""
        compliance_str = "In" if self.compliance_level else "Not in"
        return (
            f"MC: JE Version {self.id} "
            f"({self.development_phase} - {self.type}):\n"
            f"\t{compliance_str} compliance\n"
            f"\tRelease: {self.released}\n"
            f"\tUpdated: {self.last_updated}\n"
            f"\tSHA1 Sum: {self.sha1}\n"
            f"\tLink: {self.client_version_url}"
        )


class JEVersionManifestV2(HttpJsonRetriever):
    """Representation of the Minecraft: Java Edition version manifest V2.

    A :class:`.json_retriever.HttpJsonRetriever` implementation to retrieve and
    process the Minecraft: Java Edition version manifest v2 (see
    `Gamepedia Minecraft Wiki<https://minecraft.gamepedia.com/Version_manifest.json>`_).

    :param URL: Url to the Minecraft: Java Edition version manifest v2.
    :type URL: str
    :param versions: Map of version ID to :class:`JEVersion` representation of a
        Minecraft: Java Edition version.
    :type versions: Dict[str, :class:`JEVersion`]
    :param latest_release: Latest Minecraft: Java Edition release version.
    :type latest_release: class:`JEVersion`
    :param latest_snapshot: Latest Minecraft: Java Edition snapshot (test) version.
    :type latest_snapshot: class:`JEVersion`
    """

    URL = "https://launchermeta.mojang.com/mc/game/version_manifest_v2.json"

    def __init__(self, parsed_json: Dict[str, Any]):
        """Initialize class with the MC: JE Version Manifest.

        Constructor for :class:`JEVersionManifestV2`, meant to be called
        from the :class:`minecraft.common.json_retriever.HttpJsonRetriever`
        factory `load` method.

        :param parsed_json: The dictionary object representation of the
            `Minecraft: Java Edition version manifest
            v2<https://minecraft.gamepedia.com/Version_manifest.json>`_.
        """
        try:
            self._versions = {
                v["id"]: JEVersion(
                    v["id"],
                    v["type"],
                    v["url"],
                    v["time"],
                    v["releaseTime"],
                    v["sha1"],
                    v["complianceLevel"],
                )
                for v in parsed_json["versions"]
            }

            self.latest_release: str = self._versions[parsed_json["latest"]["release"]]
            self.latest_snapshot: str = self._versions[
                parsed_json["latest"]["snapshot"]
            ]
        except KeyError:
            raise Exception(
                "Failed to load the Minecraft Java Edition Version Manifest V2"
            )

    def versions(self) -> List[JEVersion]:
        """Get the list of versions sorted by release date (oldest -> newest).

        :return: Sorted list of Minecraft: Java Edition versions
        :rtype: List[class:`JEVersion`]
        """
        return list(sorted(self._versions.values()))

    def search_regex(self, regex: str) -> List[JEVersion]:
        """Regex search for MC: JE versions based on the version ID.

        :param regex: Regex string to compare against version ID's
        :type regex: str
        :return: Sorted list of Minecraft: Java Edition versions that match
            the provided regex
        :rtype: List[class:`JEVersion`]
        """
        r = re.compile(regex)
        return list(sorted(filter(lambda v: r.match(v.id), self._versions.values())))

    def releases(self) -> List[JEVersion]:
        """Get all Minecraft: Java Edition release versions.

        :return: A list of release versions
        :rtype: List[class:`JEVersion`]
        """
        return list(
            sorted(
                filter(
                    lambda v: v.type == JEVersionType.RELEASE,
                    self._versions.values(),
                )
            )
        )

    def snapshots(self) -> List[JEVersion]:
        """Get all Minecraft: Java Edition snapshot versions.

        :return: A list of snapshot versions
        :rtype: List[class:`JEVersion`]
        """
        return list(
            sorted(
                filter(
                    lambda v: v.type == JEVersionType.SNAPSHOT,
                    self._versions.values(),
                )
            )
        )

    def search_phase(self, phase: JEDevelopmentPhase) -> List[JEVersion]:
        """Get Minecraft: Java Edition versions released in the given phase.

        :param phase: Minecraft: Java Edition development phase
        :type phase: class:`JEDevelopmentPhase`
        :return: All versions released in the given development phase
        :rtype: List[class:`JEVersion`]
        """
        return list(
            sorted(
                filter(lambda v: v.development_phase == phase, self._versions.values())
            )
        )

    def get(self, id: str) -> JEVersion:
        """Get a specific MC: JE version from its ID."""
        return self._versions.get(id)
