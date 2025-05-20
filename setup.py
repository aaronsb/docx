"""Setup script for memory_graph_extract package."""
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
    "markitdown>=0.1.0",  # For multi-format support
]

# Optional dependencies
extras_require = {
    "dev": ["pytest>=7.0.0", "pytest-cov>=4.0.0"],
    "test": ["pytest>=7.0.0", "pytest-cov>=4.0.0", "pytest-mock>=3.0.0"],
}

setup(
    name="memory-graph-extract",
    version="0.1.0",
    packages=find_packages(),
    install_requires=install_requires,
    extras_require=extras_require,
    entry_points={
        "console_scripts": [
            "mge=pdf_manipulator.cli.main:main",        # Primary command (Memory Graph Extract)
            "pdfx=pdf_manipulator.cli.main:main",       # Legacy compatibility
            "docaitool=pdf_manipulator.cli.main:main",  # Original compatibility
        ],
    },
    scripts=[
        "scripts/mge-setup",  # Configuration wizard
    ],
    author="Aaron Bockelie",
    author_email="aaronsb@gmail.com",
    description="Semantic extraction framework for the memory-graph ecosystem",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    url="https://github.com/aaronsb/memory-graph-extract",
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Topic :: Text Processing :: Linguistic",
        "Topic :: Scientific/Engineering :: Artificial Intelligence",
    ],
    python_requires=">=3.8",
    keywords="semantic extraction, knowledge graph, memory graph, document processing, AI",
)