#!/bin/bash

set -ex

PROJ_ROOT=$(cd "$(dirname "$0")/../.." && pwd)
cd ${PROJ_ROOT}

echo ">>> UT of dsl"
pytest ./octopus/dsl/ut/
