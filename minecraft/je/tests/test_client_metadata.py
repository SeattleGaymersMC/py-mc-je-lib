#!/usr/bin/env python3
"""Test the :module:`minecraft.je.version` module loading MC: JE version metadata."""

import json
import pytest
import os
import hashlib
import py
from datetime import datetime, timezone
from unittest.mock import call
from minecraft.je.common import JEDevelopmentPhase, JEVersionType, ComplianceLevel

from minecraft.je.client_metadata import JEClientMetadata

__dir = os.path.dirname(os.path.realpath(__file__))
TEST_CLIENT_METADATA_F = py.path.local(__dir) / "client_metadata_test_data.json"


@pytest.fixture
def mock_named_downloader(mocker):
    """Create a mock client metadata object."""
    mock_file_downloader = mocker.patch(
        "minecraft.je.client_metadata.NamedFileDownloader"
    )
    mock_file_downloader.return_value = mock_file_downloader
    return mock_file_downloader


@pytest.mark.asyncio
async def test_client_metadata(mock_named_downloader):
    """Test the volume manifest and version load from JSON correctly."""
    test_volume_manifest_json = json.loads(TEST_CLIENT_METADATA_F.read())
    metadata = JEClientMetadata(test_volume_manifest_json)
    assert metadata.compliance_level == ComplianceLevel.IN_COMPLIANCE
    assert metadata.id == "21w15a"
    assert metadata.type == JEVersionType.SNAPSHOT
    assert metadata.development_phase == JEDevelopmentPhase.RELEASE
    assert metadata.assets_version == "1.17"
    assert metadata.main_class == "net.minecraft.client.main.Main"
    assert metadata.released == datetime(2021, 4, 14, tzinfo=timezone.utc)
    assert metadata._time == datetime(2021, 4, 14, tzinfo=timezone.utc)
    assert metadata.min_launcher_version == 21

    assert mock_named_downloader.call_count == 2
    mock_named_downloader.assert_has_calls(
        [
            call(
                (
                    "https://launcher.mojang.com/v1/objects/"
                    "749805abb797f201a76e2c6ad2e7ff6f790bb53c/client.jar"
                ),
                "client.jar",
                expected_size=19341384,
                file_hash="749805abb797f201a76e2c6ad2e7ff6f790bb53c",
                file_hash_type=hashlib.sha1,
            ),
            call(
                (
                    "https://launcher.mojang.com/v1/objects/"
                    "0a39422009a7aa01dd185043746c50dc909dc345/server.jar"
                ),
                "server.jar",
                expected_size=39159385,
                file_hash="0a39422009a7aa01dd185043746c50dc909dc345",
                file_hash_type=hashlib.sha1,
            ),
        ]
    )
