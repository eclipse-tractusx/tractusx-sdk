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

# Python
ENV PYTHONFAULTHANDLER=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONHASHSEED=random \
    PIP_NO_CACHE_DIR=off \
    PIP_DISABLE_PIP_VERSION_CHECK=on \
    PIP_DEFAULT_TIMEOUT=100

# Poetry
ENV POETRY_NO_INTERACTION=1 \
    POETRY_VIRTUALENVS_CREATE=false \
    POETRY_CACHE_DIR='/var/cache/pypoetry' \
    POETRY_HOME='/usr/local' \
    POETRY_VERSION=1.8.3


RUN apt-get update && apt-get install -y curl && rm -rf /var/lib/apt/lists/* \
	&& curl -sSL https://install.python-poetry.org | python3 -

USER root

WORKDIR /tractusx-sdk/src/tractusx_sdk

ENV PYTHONPATH=/tractusx-sdk/src:$PYTHONPATH

COPY pyproject.toml poetry.lock /tractusx-sdk/

RUN poetry lock

RUN poetry install --no-ansi

## Move all the files from the project to the sdk directory
COPY . /tractusx-sdk

## Create the directories
RUN mkdir -p ./logs
RUN mkdir -p ./data

## Expose default port
EXPOSE 8000

## Execute the application
CMD ["poetry", "run", "python3","dataspace/main.py", "--host", "0.0.0.0", "--port", "8000"]
