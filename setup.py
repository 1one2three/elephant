from setuptools import setup, find_packages

setup(
    name="citation-mind",
    version="0.1.0",
    packages=find_packages(),
    include_package_data=True,
    install_requires=[
        'requests>=2.31.0',
        'click>=8.1.0',
        'rich>=13.0.0',
        'python-dotenv>=1.0.0',
        'pydantic>=2.0.0',
        'sqlalchemy>=2.0.0',
        'pandas>=2.0.0',
        'arxiv>=2.0.0',
        'scholarly>=1.7.0',
        'habanero>=1.2.0',
        'aiohttp>=3.9.0',
        'beautifulsoup4>=4.12.0',
        'lxml>=4.9.0',
        'plotext>=5.2.0',
        'tabulate>=0.9.0',
        'python-dateutil>=2.8.0',
    ],
    entry_points={
        'console_scripts': [
            'citation-mind=src.cli:main',
        ],
    },
    python_requires='>=3.8',
    author="Your Name",
    description="A CLI tool to track and boost your scientific citations",
    keywords="citations academic research orcid arxiv",
)
