# accsyn-python-api
Official accsyn fast and secure file delivery Python API

Python API support can be found [here](https://support.accsyn.com/developer/python-api).


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

Testing:
--------

The test suite requires role-specific credential files to test different user permissions,
Tests will be skipped if the required .env files are not present.
The tests also requires active accsyn clients running on behalf of the users, to be able to fully
test file transfers and compute. This requires all tests to run interactively, to be able to action
prompts that may appear during execution.

**Prepare test credentials:**

Create three `.env` files in the project root directory, one for each role:

1. `.env.admin` - Admin role credentials
2. `.env.employee` - Employee role credentials
3. `.env.standard` - Standard (restricted end user) role credentials

Each `.env` file should contain:

```bash
ACCSYN_WORKSPACE=your_workspace
ACCSYN_API_USER=user@example.com
ACCSYN_API_KEY=your_api_key
```

**Run tests:**

```bash
# Run all tests
poetry run pytest -x -s

# Run with coverage report
poetry run pytest -x -s --cov=accsyn_api --cov-report=term-missing

# Run a specific test file
poetry run pytest -x -s tests/test_find_entitytypes.py

# Some tests have dependencies in form of running clients, run interactively:
poetry run pytest -x -s tests/test_find_entitytypes.py

```

**Categories:** Use `@pytest.mark.base` for tests that create entities; use `@pytest.mark.extended` and `@pytest.mark.order(2)` (or higher) for tests that depend on those entities. Run `pytest -m "base or extended"` to run both in order in one session.

**Note:** Tests that require a specific role will be skipped if the corresponding `.env` file is missing.


Building and publishing to PyPi:
--------------------------------

```bash
# Build the package
poetry build

# Publish to PyPI (requires authentication)
poetry publish

# Or publish to test PyPI first
poetry config repositories.testpypi https://test.pypi.org/legacy/
poetry publish -r testpypi
```

Poetry can use saved credentials (`poetry config pypi-token.pypi <token>`) or username/password flags such as `poetry publish --username <user> --password <pass>`.

accsyn(r) - secure high speed file delivery and workflow sync
https://accsyn.com 
https://support.accsyn.com

