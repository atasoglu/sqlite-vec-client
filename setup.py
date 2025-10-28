from pathlib import Path

from setuptools import find_packages, setup

here = Path(__file__).parent.resolve()

setup(
    name="sqlite-vec-client",
    version="0.1.0",
    author="Ahmet Atasoglu",
    author_email="ahmetatasoglu98@gmail.com",
    description=(
        "A tiny Python client around sqlite-vec for CRUD and similarity search."
    ),
    long_description=(here / "README.md").read_text(encoding="utf-8"),
    long_description_content_type="text/markdown",
    url="https://github.com/atasoglu/sqlite-vec-client",
    license="MIT",
    packages=find_packages(),
    install_requires=[
        "sqlite-vec>=0.1.6",
    ],
    python_requires=">=3.9",
    classifiers=[
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Programming Language :: Python :: 3.13",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    include_package_data=True,
)
