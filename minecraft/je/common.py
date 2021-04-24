#!/usr/bin/env python3
"""Common classes representing Minecraft: Java Edition version metadata."""

from enum import Enum


class ComplianceLevel(Enum):
    """:class:`enum.Enum` representation of the compliance level for MC: JE versions.

    :param OUT_OF_DATE: The Minecraft: Java Edition version is out of
        compliance and does not have the latest player safety features; a newer
        version is available and should be used.
    :param IN_COMPLIANCE: The Minecraft: Java Edition version is in compliance
        and contians the latest player safety features; it is safe to use.
    """

    OUT_OF_DATE = 0
    IN_COMPLIANCE = 1

    def __bool__(self) -> True:
        """Boolean representation of whether the current level is compliant.

        :return: True if the level is in compliance, false otherwise
        """
        return self.value == ComplianceLevel.IN_COMPLIANCE

    def __str__(self) -> str:
        """Get the description of the compliance level.

        :return: Description of the compliance level.
        """
        return "in compliance" if self else "not in compliance, please update"


class JEVersionType(Enum):
    """:class:`enum.Enum`_ representation of the Minecraft: Java Edition version types.

    :param OLD_ALPHA: A Minecraft version from the alpha or pre-alpha phases
    :param OLD_BETA: Beta Minecraft version
    :param RELEASE: Official Minecraft: Java Edition version release
    :param SNAPSHOT: A test/pre-release Minecraft: Java Edition version
    """

    OLD_ALPHA = "old_alpha"
    OLD_BETA = "old_beta"
    RELEASE = "release"
    SNAPSHOT = "snapshot"

    def __str__(self) -> str:
        """Get the version type name."""
        if self.value == self.OLD_ALPHA:
            return "alpha"
        elif self.value == self.OLD_BETA:
            return "beta"
        else:
            return self.value


class JEDevelopmentPhase(Enum):
    """List of Minecraft: Java Edition development phases.

    :class:`enum.Enum`_ representation of the Minecraft: Java Edition
    development phases. See `Gamepedia Minecraft Wiki
        <https://minecraft.gamepedia.com/Java_Edition#Development>`_.

    :param PRE_CLASSIC: First phase of Minecraft development. See
        `Gamepedia Minecraft Wiki
        <https://minecraft.gamepedia.com/Java_Edition_pre-Classic>`_.
    :param CLASSIC: Second phase of Minecraft development. See
        `Gamepedia Minecraft Wiki
        <https://minecraft.gamepedia.com/Java_Edition_Classic>`_.
    :param INDEV: Third phase of Minecraft development, short for
        'in-development'. See
        `Gamepedia Minecraft Wiki<https://minecraft.gamepedia.com/Java_Edition_Indev>`_.
    :param INFDEV: Fourth phase of Minecraft development, refers to 'infinite
        development' and `in further development`. See
        `Gamepedia Minecraft Wiki
        <https://minecraft.gamepedia.com/Java_Edition_Infdev>`_.
    :param ALPHA: Fifth phase of Minecraft development. See
        `Gamepedia Minecraft Wiki<https://minecraft.gamepedia.com/Java_Edition_Alpha>`_.
    :param BETA: Sixth phase of Minecraft development. See
        `Gamepedia Minecraft Wiki<https://minecraft.gamepedia.com/Java_Edition_Beta>`_.
    :param RELEASE: Full release phase, covering Minecraft versions released
        after the official release of Minecraft: Java Edition. See the
        `Gamepedia Minecraft Wiki
        <https://minecraft.gamepedia.com/Java_Edition_version_history>`_
        for more information about full versions.
    """

    PRE_CLASSIC = "Pre-Classic"
    CLASSIC = "Classic"
    INDEV = "Indev"
    INFDEV = "Infdev"
    ALPHA = "Alpha"
    BETA = "Beta"
    RELEASE = "Release"

    def __str__(self) -> str:
        """Get the development phase name."""
        return self.value.lower()

    @classmethod
    def from_id(
        klass: "JEDevelopmentPhase", id: str, version_type: JEVersionType
    ) -> "JEDevelopmentPhase":
        """Get the MC: JE development phase from the version ID and version type."""
        if version_type == JEVersionType.OLD_ALPHA:
            if id.startswith("rd"):
                return JEDevelopmentPhase.PRE_CLASSIC
            elif id.startswith("c"):
                return JEDevelopmentPhase.CLASSIC
            elif id.startswith("inf"):
                return JEDevelopmentPhase.INFDEV
            else:
                return JEDevelopmentPhase.ALPHA

        elif version_type == JEVersionType.OLD_BETA:
            return JEDevelopmentPhase.BETA

        else:
            return JEDevelopmentPhase.RELEASE
