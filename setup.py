from setuptools import setup, find_packages

setup(
    name="report-module",
    version="0.1.0",
    description="report module",
    author="Fritz Lindner",
    author_email="fritzl.lindner@outlook.com",
    packages=find_packages(),
    include_package_data=True,
    install_requires=[
        "bs4",
        "IPython",
        "quantstats",
        "pandas",
        "pydantic",
        "typing",
    ],
    entry_points={
        "console_scripts": [
            "run-report=report.__main__:main",
        ],
    },
    package_data={
        "": ["*.yaml", "*.csv"],
    },
    python_requires=">=3.9",
)
