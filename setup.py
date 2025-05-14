"""Setup script for pdf_manipulator package."""
from setuptools import setup, find_packages

setup(
    name="pdf_manipulator",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        "pymupdf>=1.22.0",
        "pillow>=10.0.0",
        "pypdf>=3.15.0",
        "click>=8.1.3",
        "pydantic>=2.0.0",
        "tqdm>=4.65.0",
        "numpy>=1.24.0",
        "pandas>=2.0.0",
    ],
    entry_points={
        "console_scripts": [
            "pdf-manipulator=pdf_manipulator.cli.commands:cli",
        ],
    },
    author="PDF Manipulator Team",
    description="A modular toolkit for PDF manipulation",
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.8",
)