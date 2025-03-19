#################################################################################
# Eclipse Tractus-X - Software Development KIT
#
# Copyright (c) 2025 Contributors to the Eclipse Foundation
#
# See the NOTICE file(s) distributed with this work for additional
# information regarding copyright ownership.
#
# This program and the accompanying materials are made available under the
# terms of the Apache License, Version 2.0 which is available at
# https://www.apache.org/licenses/LICENSE-2.0.
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND,
# either express or implied. See the
# License for the specific language govern in permissions and limitations
# under the License.
#
# SPDX-License-Identifier: Apache-2.0
#################################################################################


FROM python:3.12.6-slim-bookworm

# Python ENV
ENV PYTHONFAULTHANDLER=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONHASHSEED=random \
    PIP_NO_CACHE_DIR=off \
    PIP_DISABLE_PIP_VERSION_CHECK=on \
    PIP_DEFAULT_TIMEOUT=100

# Poetry ENV
ENV POETRY_NO_INTERACTION=1 \
    POETRY_VIRTUALENVS_CREATE=false \
    POETRY_CACHE_DIR='/var/cache/pypoetry' \
    POETRY_HOME='/usr/local' \
    POETRY_VERSION=2.1.0

# Install curl and Poetry via a script
RUN apt-get update && apt-get install -y --no-install-recommends curl=7.88.1-10+deb12u12 && rm -rf /var/lib/apt/lists/* \
	&& curl --proto "=https" -sSL https://install.python-poetry.org | python3 -

USER root

WORKDIR /tractusx-sdk/src/tractusx_sdk

# Add the project directory to the Python path
ENV PYTHONPATH=/tractusx-sdk/src:$PYTHONPATH

# Copy necessary Poetry configuration files to the container
# These files are required to install the correct dependencies
COPY pyproject.toml poetry.lock README.md /tractusx-sdk/

# Lock dependencies using Poetry and install them
RUN poetry lock \
	&& poetry install --no-root

# Copy the source code from the local machine into the container
COPY src/* /tractusx-sdk/src/tractusx_sdk/

## Create the directories logs and data
RUN mkdir -p ./logs \
	&& mkdir -p ./data

## Expose default port
EXPOSE 8000

# Create a non-root user
RUN addgroup --system appgroup && adduser --system --ingroup appgroup appuser \
	&& chown -R appuser:appgroup /tractusx-sdk

# Set the user for running the application
USER appuser

# Define the health check command to verify if the application is responsive
HEALTHCHECK CMD ["curl", "--fail", "-H", "Edc-Bpn: HEALTHCHECK", "http://localhost:8000/example"]

## Execute the application
CMD ["poetry", "run", "python3","dataspace/main.py", "--host", "0.0.0.0", "--port", "8000"]
