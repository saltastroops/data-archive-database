from setuptools import setup, find_packages

setup(
    name='ssda',
    packages=find_packages(where='src'),
    package_dir={'': 'src'},
    python_requires=">=3.7",
    setup_requires=['pytest-runner'],
    install_requires=[],
    tests_require=['pytest', 'pytest-mock'],
    entry_points={"console_scripts": ["ssda = ssda.cli:main"]},
    version="0.1.0"
)
