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
        "faker",
        "pandas",
        "pymysql",
        "psycopg2",
        "python-dateutil",
        "pytz",
        "sentry-sdk",
    ],
    tests_require=["mypy", "pytest", "pytest-mock"],
    entry_points={
        "console_scripts": [
            "ssda = ssda.cli:main",
            "ssda_delete = ssda.ssda_delete:main",
            "ssda_sync = ssda.util.ssda_sync:main",
            "ssda_daily_cronjob = ssda.daily_cronjob:main"
        ]
    },
    version="0.1.0",
)
