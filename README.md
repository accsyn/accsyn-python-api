# accsyn-python-api
Official accsyn fast and secure file delivery Python API

Python API support can be found [here](https://support.accsyn.com/workflows/python-api).


Changelog:
----------

See doc/release_notes.rst


Documentation:
--------------

[https://accsyn-python-api.readthedocs.io/en/latest](https://accsyn-python-api.readthedocs.io/en/latest)


Development Setup:
------------------

This project uses Poetry for dependency management. To get started:

```bash
# Install Poetry (if not already installed)
curl -sSL https://install.python-poetry.org | python3 -

# Install dependencies
poetry install

# Install with documentation dependencies
poetry install --with docs

# Activate the virtual environment
poetry shell
```

Building Documentation:
----------------------

To build the documentation locally:

```bash
# Install with docs dependencies
poetry install --with docs

# Build docs
cd doc
poetry run sphinx-build -T -E -b html -d _build/doctrees -D language=en . ../dist/doc
```

Or use the shorter command:
```bash
poetry run sphinx-build -b html doc dist/doc
```

Development Tools:
-----------------

```bash
# Format code
poetry run black .

```

Building and Publishing:
-----------------------

```bash
# Build the package
poetry build

# Publish to PyPI (requires authentication)
poetry publish

# Or publish to test PyPI first
poetry config repositories.testpypi https://test.pypi.org/legacy/
poetry publish -r testpypi
```

accsyn(r) - secure high speed file delivery and workflow sync
https://accsyn.com 
https://support.accsyn.com

