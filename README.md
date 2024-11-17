# accsyn-python-api
Official accsyn fast film delivery Python API

Complete Python API reference can be found [here](https://support.accsyn.com/python-api).


Changelog:
----------

See doc/release_notes.rst


Documentation:
--------------

[https://accsyn-python-api.readthedocs.io/en/latest](https://accsyn-python-api.readthedocs.io/en/latest)


Building:
---------

To build the documentation locally, run:

```
    cd doc
    pip install -r requirements.txt
    python -m sphinx -T -E -b html -d _build/doctrees -D language=en . ../dist/doc
```

Deploying:
----------

```
python setup.py sdist bdist_wheel
twine upload --verbose --username accsyn dist/*
```

Henrik Norin, HDR AB, 2023
accsyn(r) - secure data delivery and workflow sync
https://accsyn.com 
https://support.accsyn.com

