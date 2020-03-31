#!/bin/sh

python3 setup.py sdist bdist_wheel --universal && \
    ls -l dist/
    twine upload --repository-url https://test.pypi.org/legacy/ dist/* && \
    rm -rf build/ dist/ univention_config_registry.egg-info/

