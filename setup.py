from setuptools import setup, find_packages

setup(
    name="ssda",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    python_requires=">=3.7",
    setup_requires=["pytest-runner"],
    install_requires=[
        "astropy",
        "click",
        "dsnparse",
        "python-dateutil",
        "faker",
        "psycopg2",
        "sentry-sdk",
    ],
    tests_require=["mypy", "pytest", "pytest-mock"],
    entry_points={
        "console_scripts": [
            "ssda = ssda.cli:main",
            "ssda_delete = ssda.ssda_delete:main",
        ]
    },
    version="0.1.0",
)
