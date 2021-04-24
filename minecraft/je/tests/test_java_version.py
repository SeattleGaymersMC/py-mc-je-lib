#!/usr/bin/env python3
"""Test the :module:`minecraft.je.version` module loading MC: JE version metadata."""

import json
import pytest
import os
from unittest.mock import AsyncMock
import py
from datetime import datetime
from minecraft.je.common import JEDevelopmentPhase, JEVersionType

from minecraft.je.version import JEVersionManifestV2

__dir = os.path.dirname(os.path.realpath(__file__))
TEST_VOLUME_MANIFEST_F = py.path.local(__dir) / "version_manifest_test_data.json"


@pytest.fixture
def mock_client_metadata(mocker):
    """Create a mock client metadata object."""
    mock_client = mocker.patch("minecraft.je.version.JEClientMetadata")
    mock_client.load = AsyncMock()
    mock_client.load.return_value = mock_client
    return mock_client


@pytest.mark.asyncio
async def test_volume_manifest(mock_client_metadata):
    """Test the volume manifest and version load from JSON correctly."""
    test_volume_manifest_json = json.loads(TEST_VOLUME_MANIFEST_F.read())
    manifest = JEVersionManifestV2(test_volume_manifest_json)
    assert len(manifest.versions()) == 4
    assert str(manifest.latest_release) == "some.official.release.123acdef"
    assert str(manifest.latest_snapshot) == "some-version.snap.shot"

    assert len(manifest.search_regex(".*")) == 4
    assert len(manifest.search_regex(".*123test")) == 2

    assert len(manifest.releases()) == 1
    assert len(manifest.snapshots()) == 1

    assert len(manifest.search_phase(JEDevelopmentPhase.INFDEV)) == 1
    assert len(manifest.search_phase(JEDevelopmentPhase.CLASSIC)) == 0
    assert len(manifest.search_phase(JEDevelopmentPhase.RELEASE)) == 2

    some_official_releases = manifest.search_regex("some.official")
    assert len(some_official_releases) == 1
    release = some_official_releases[0]
    assert str(release) == "some.official.release.123acdef"
    assert release.id == "some.official.release.123acdef"
    assert release.type == JEVersionType.RELEASE
    assert release.development_phase == JEDevelopmentPhase.RELEASE
    assert release.client_version_url == "https://test.data/geromino.json"
    assert release.last_updated == datetime.fromisoformat("1991-03-02T23:59:59+00:00")
    assert release.released == datetime.fromisoformat("1991-04-02T23:59:59+00:00")
    assert release.sha1 == "7341221e7d9b4b92b1ae5d1e890cfe77d4928922"
    assert str(manifest.latest_release) in repr(release)

    client_metadata = await release.get_metadata()
    client_metadata_2 = await release.get_metadata()
    mock_client_metadata.load.assert_called_once_with(url=release.client_version_url)
    assert client_metadata is client_metadata_2
    assert release._client_metadata is client_metadata

    assert release == release
    assert release >= release
    assert release <= release
    assert not release != release

    snapshot = manifest.get(str(manifest.latest_snapshot))
    assert snapshot.id == str(manifest.latest_snapshot)

    assert snapshot < release
    assert release > snapshot
    assert not release == snapshot
    assert release != snapshot
