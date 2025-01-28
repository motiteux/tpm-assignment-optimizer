# setup.py
from setuptools import setup, find_packages

setup(
    name="tpm-optimizer",
    version="0.1.0",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    install_requires=[
        "numpy>=2.2.2",
        "pandas>=2.2.3",
        "PuLP>=2.9.0",
        "python-dateutil>=2.9.0",
        "pytz>=2024.2",
        "six>=1.17.0",
        "tzdata>=2025.1",
    ],
    extras_require={
        "dev": [
            "pytest>=7.4.4",
            "pytest-cov>=4.1.0",
        ],
    },
    entry_points={
        'console_scripts': [
            'tpm-optimizer=tpm_optimizer.cli.commands:main',
        ],
    },
    python_requires=">=3.8",
    author="Your Name",
    author_email="your.email@example.com",
    description="TPM Assignment Optimizer",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    url="https://github.com/yourusername/tpm-assignment-optimizer",
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
    ],
)