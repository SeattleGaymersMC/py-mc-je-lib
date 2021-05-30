#!/usr/bin/env python3
"""Package definition for common Minecraft libraries."""

import setuptools

long_description = ""
# with open("README.md", "r", encoding="utf-8") as fh:
#    long_description = fh.read()

setuptools.setup(
    name="minecraft-je-lib",
    version="0.0.1",
    author="Seth Cook",
    author_email="cooker52@gmail.com",
    description="Minecraft server administration utility designed for DevOps and automation",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/SeattleGaymersMC/py-mc-je-lib",
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Framework :: AsyncIO",
        "Intended Audience :: Developers",
        "Intended Audience :: System Administrators",
        "License :: OSI Approved :: GNU General Public License v3 (GPLv3)",
        "Programming Language :: Python :: 3",
        "Operating System :: OS Independent",
    ],
    packages=setuptools.find_packages(),
    python_requires=">=3.7",
    install_requires=["httpx", "configargparse"],
    entry_point={"console_scripts": {"mchex = mchex.cli.__main__"}},
)
