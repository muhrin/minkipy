# -*- coding: utf-8 -*-
"""Tests of the settings module"""

import shutil

from minkipy import settings


def test_saving_settings(tmp_path):
    settings_dict = settings.read_settings()

    # Now, make sure that even if the folder is not present saving settings will still work
    # (by creating the folder first)
    shutil.rmtree(str(tmp_path))

    # This should succeed
    settings.write_settings(settings_dict)

    assert settings_dict == settings.read_settings()


def test_settings_path(monkeypatch):
    """Test that settings fall back to reasonable value even if the environmental variable
    isn't set"""
    monkeypatch.delenv(settings.ENV_MINKIPY_SETTINGS)
    assert settings.settings_path()
