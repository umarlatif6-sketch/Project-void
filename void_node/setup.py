from setuptools import setup, find_packages

setup(
    name="void-engine-node",
    version="1.0.0",
    description="PROJECT VOID — Sovereign Node for the Ghost Internet Mesh",
    author="PROJECT VOID",
    packages=find_packages(),
    python_requires=">=3.11",
    install_requires=[
        "numpy",
        "cryptography",
        "Pillow",
        "requests",
        "psycopg2-binary",
    ],
    entry_points={
        "console_scripts": [
            "void-engine=void_launcher:main",
        ],
    },
    classifiers=[
        "Programming Language :: Python :: 3.11",
        "Operating System :: OS Independent",
    ],
)
