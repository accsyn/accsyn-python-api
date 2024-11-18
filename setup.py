import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name='accsyn-python-api',
    version='3.0.2',
    package_dir={'': 'source'},
    packages=['accsyn_api'],
    setup_requires=[
        'sphinx >= 1.2.2',
        'sphinx_rtd_theme >= 0.1.6, < 1',
        'lowdown >= 0.1.0, < 2',
        'setuptools>=30.3.0',
        'setuptools_scm',
    ],
    install_requires=['requests'],
    author="Henrik Norin",
    author_email="henrik.norin@accsyn.com",
    license='Apache License (2.0)',
    description="A Python API for accsyn programmable fast and secure data delivery software",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/accsyn/accsyn-python-api.git",
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=2.7.9, <4.0",
)
