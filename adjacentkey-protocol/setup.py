from setuptools import setup, find_packages

setup(
    name="adjacentkey-protocol",
    version="0.1.0",
    description="Keyboard adjacency protocol for AI/human communication",
    author="Project VOID",
    license="MIT",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    entry_points={
        "console_scripts": [
            "adjacentkey=adjacentkey_protocol.cli:main"
        ]
    },
    python_requires=">=3.7",
    install_requires=[],
)
