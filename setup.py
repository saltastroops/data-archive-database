"""The setup script."""

from setuptools import setup, find_packages

with open('README.md') as readme_file:
    readme = readme_file.read()

requirements = ['astropy', 'click', 'pandas', 'pillow', 'PyMySQL', 'python-dateutil']

setup_requirements = ['pytest-runner']

test_requirements = ['pytest']

setup(
    author="SAAO/SALT",
    author_email='salt-software@saao.ac.za',
    classifiers=[
        'Development Status :: 2 - Pre-Alpha',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Natural Language :: English',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.7',
    ],
    description="Update the SAAO/SALT Data Archive database",
    entry_points={
        'console_scripts': ['ssda=ssda.command_line:cli']
    },
    install_requires=requirements,
    license="MIT license",
    long_description=readme,
    long_description_content_type='text/markdown',
    include_package_data=True,
    keywords='',
    name='ssda',
    packages=find_packages('src'),
    package_dir={'': 'src'},
    setup_requires=setup_requirements,
    test_suite='tests',
    tests_require=test_requirements,
    url='https://github.com/saltastroops/salt_finder_charts',
    version='0.1.0',
    zip_safe=False,
)
