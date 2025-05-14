"""Setup script for doc_ai_toolkit package."""
from setuptools import setup, find_packages

setup(
    name="doc_ai_toolkit",
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
        "pytesseract>=0.3.10",
        "scikit-image>=0.20.0",
        "openai>=1.0.0",
        "httpx>=0.24.0",
        "langchain>=0.0.270",
        "llama-cpp-python>=0.2.0",
        "python-dotenv>=1.0.0",
    ],
    entry_points={
        "console_scripts": [
            "docaitool=pdf_manipulator.cli.commands:cli",
        ],
    },
    author="Document AI Toolkit Team",
    description="A toolkit for document processing and analysis with AI",
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.8",
)