#!/bin/bash

# run lint
echo "Running lint..."

# install pre-commit
pre-commit install

# run lint
pre-commit run --all-files --show-diff-on-failure

# exit with exit code of lint script
exit $?
