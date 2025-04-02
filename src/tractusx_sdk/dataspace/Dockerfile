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

# Build stage
FROM python:3.12-alpine AS builder

WORKDIR /build

# Copy source code and build configuration
COPY pyproject.toml README.md ./
COPY src/ ./src/

# Install build tool and build the wheel
RUN pip install --no-cache-dir build==1.2.2 \
    && python -m build --wheel

# Production stage
FROM python:3.12-alpine AS production

# Set environment variables for runtime
ENV PYTHONFAULTHANDLER=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# Install runtime dependencies
RUN apk add --no-cache curl

# Copy only the built wheel
COPY --from=builder /build/dist/*.whl ./

# Install the package wheel
RUN pip install --no-cache-dir ./*.whl && rm -f ./*.whl \
# Create required directories
    && mkdir -p ./logs ./data \
# Create a non-root user
    && addgroup -S appgroup && adduser -S -G appgroup appuser \
    && chown -R appuser:appgroup /app ./logs ./data

# Set the user for running the application
USER appuser

# Expose the port
EXPOSE 8000

# Define the health check command to verify if the application is responsive
HEALTHCHECK CMD ["curl", "--fail", "http://localhost:8000/api/check/health"]

# Run the industry module from the installed package
CMD ["python", "-m", "tractusx_sdk.dataspace.main", "--host", "0.0.0.0", "--port", "8000"]
