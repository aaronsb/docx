"""Setup script for doc_ai_toolkit package."""
from setuptools import setup, find_packages

# Core requirements for basic functionality
install_requires = [
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
    "python-dotenv>=1.0.0",
    "pyyaml>=6.0",
]

# Optional dependencies
extras_require = {
    "llama": ["llama-cpp-python>=0.2.0"]
}

setup(
    name="doc_ai_toolkit",
    version="0.1.0",
    packages=find_packages(),
    install_requires=install_requires,
    extras_require=extras_require,
    entry_points={
        "console_scripts": [
            "pdfx=pdf_manipulator.cli.commands:cli",  # Primary command (PDF extractor)
            "docaitool=pdf_manipulator.cli.commands:cli",  # Original for compatibility
        ],
    },
    scripts=[
        "scripts/pdfx-setup",  # Configuration wizard
    ],
    author="Document AI Toolkit Team",
    description="A toolkit for document processing and analysis with AI",
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.8",
)