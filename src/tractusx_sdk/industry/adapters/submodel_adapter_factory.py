#################################################################################
# Eclipse Tractus-X - Software Development KIT
#
# Copyright (c) 2026 LKS Next
# Copyright (c) 2026 DRÄXLMAIER Group
# (represented by Lisa Dräxlmaier GmbH)
# Copyright (c) 2025,2026 Contributors to the Eclipse Foundation
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

from enum import StrEnum
import inspect
import logging
from importlib import import_module
from typing import Any, Callable, Mapping, Union, get_args, get_origin
import types

from tractusx_sdk._logging_fields import log_extra

# Security: the configuration of an adapter holds credentials (S3 keys, API tokens). Its values are never logged,
# only the names of its settings.
logger = logging.getLogger(__name__)
class SubmodelAdapterType(StrEnum):
    """
    Enum for different adapter types. Each adapter type corresponds to a specific implementation,
    and must correspond exactly to the prefix of the adapter class it is associated with.
    """
    FILE_SYSTEM = "FileSystem"
    HTTP_SUBMODEL = "HttpSubmodel"
    S3 = "S3"

class SubmodelAdapterFactory:
    """
    Factory for creating and extending submodel adapters.

    The factory supports two creation paths:
    - Built-in adapters discovered from the SDK adapter module.
    - External adapters registered at runtime via ``register_adapter``.

    Adapters are instantiated through their builder interface and can be
    configured from key-value mappings via ``from_config``.

    Example:
        Create a built-in adapter from configuration::

            adapter = SubmodelAdapterFactory.from_config(
                adapter_type="file_system",
                config={"root_path": "./submodels"},
            )
    """
    _registered_builders: dict[str, Callable[[], Any]] = {}

    @staticmethod
    def _normalize_type_key(adapter_type: str | SubmodelAdapterType) -> str:
        """
        Normalize an adapter type identifier into a registry-safe key.

        Examples:
            >>> SubmodelAdapterFactory._normalize_type_key("file_system")
            'file_system'
            >>> SubmodelAdapterFactory._normalize_type_key(SubmodelAdapterType.FILE_SYSTEM)
            'file_system'
            >>> SubmodelAdapterFactory._normalize_type_key(" File-System ")
            'file_system'
            >>> SubmodelAdapterFactory._normalize_type_key("Custom Adapter")
            'custom_adapter'
            >>> SubmodelAdapterFactory._normalize_type_key("")
            ValueError: adapter_type must be a non-empty string or SubmodelAdapterType

        :param adapter_type: Adapter type as enum or string.
        :return: Lowercase normalized key using underscores.
        :raises ValueError: If the input is empty or invalid.
        """
        if isinstance(adapter_type, SubmodelAdapterType):
            return adapter_type.name.lower()

        if not isinstance(adapter_type, str) or not adapter_type.strip():
            logger.warning("An adapter type must be a non-empty string or a SubmodelAdapterType", extra=log_extra(operation="adapter_factory"))
            raise ValueError("adapter_type must be a non-empty string or SubmodelAdapterType")

        return adapter_type.strip().replace("-", "_").replace(" ", "_").lower()

    @staticmethod
    def _to_adapter_type(adapter_type: str | SubmodelAdapterType) -> SubmodelAdapterType | None:
        """
        Resolve a built-in adapter type from enum or string input.

        :param adapter_type: Adapter type as enum name/value or string.
        :return: Matching built-in enum value, or ``None`` if no built-in type matches.
        """
        if isinstance(adapter_type, SubmodelAdapterType):
            return adapter_type

        normalized = SubmodelAdapterFactory._normalize_type_key(adapter_type).upper()

        try:
            return SubmodelAdapterType[normalized]
        except KeyError:
            for value in SubmodelAdapterType:
                if value.value.lower() == adapter_type.strip().lower():
                    return value
            return None

    @staticmethod
    def register_adapter(
            adapter_type: str,
            builder_factory: Callable[[], Any] | None = None,
            adapter_class: Any = None,
            overwrite: bool = False,
    ) -> None:
        """
        Register an external adapter type.

        Provide either ``builder_factory`` (returns a builder) or ``adapter_class``
        exposing a callable ``builder`` classmethod.

        :param adapter_type: External adapter type key.
        :param builder_factory: Callable returning a builder instance.
        :param adapter_class: Adapter class exposing ``builder()``.
        :param overwrite: Whether to overwrite an existing external registration.
        :raises ValueError: If registration parameters are invalid.
        :raises TypeError: If callable requirements are not met.

        Example:
            Register a custom adapter class and use it with ``from_config``::

                class ExternalAdapter:
                    @classmethod
                    def builder(cls):
                        return cls._Builder()

                SubmodelAdapterFactory.register_adapter(
                    adapter_type="external",
                    adapter_class=ExternalAdapter,
                )
        """
        if not builder_factory and adapter_class is None:
            logger.warning("Registering the adapter type '%s' needs a builder_factory or an adapter_class", adapter_type,
                           extra=log_extra(adapter_type=str(adapter_type), operation="adapter_factory.register"))
            raise ValueError("Either builder_factory or adapter_class must be provided")

        if builder_factory and adapter_class is not None:
            logger.warning("Registering the adapter type '%s': give a builder_factory or an adapter_class, not both", adapter_type,
                           extra=log_extra(adapter_type=str(adapter_type), operation="adapter_factory.register"))
            raise ValueError("Provide only one of builder_factory or adapter_class")

        adapter_key = SubmodelAdapterFactory._normalize_type_key(adapter_type)
        if adapter_key in SubmodelAdapterFactory._registered_builders and not overwrite:
            logger.warning("The adapter type '%s' is already registered and overwrite is off", adapter_key,
                           extra=log_extra(adapter_type=adapter_key, operation="adapter_factory.register"))
            raise ValueError(f"Adapter type '{adapter_type}' is already registered")

        if adapter_key in SubmodelAdapterFactory._registered_builders:
            logger.info("Overwriting the registered adapter type '%s'", adapter_key,
                        extra=log_extra(adapter_type=adapter_key, operation="adapter_factory.register"))

        if builder_factory is not None:
            if not callable(builder_factory):
                logger.warning("The builder_factory of the adapter type '%s' is not callable", adapter_key,
                               extra=log_extra(adapter_type=adapter_key, operation="adapter_factory.register"))
                raise TypeError("builder_factory must be callable")
            SubmodelAdapterFactory._registered_builders[adapter_key] = builder_factory
            logger.info("Registered the adapter type '%s' through a builder factory", adapter_key,
                        extra=log_extra(adapter_type=adapter_key, operation="adapter_factory.register"))
            return

        class_builder = getattr(adapter_class, "builder", None)
        if not callable(class_builder):
            logger.warning("The adapter class of the adapter type '%s' has no callable builder", adapter_key,
                           extra=log_extra(adapter_type=adapter_key, operation="adapter_factory.register"))
            raise TypeError("adapter_class must expose a callable builder classmethod")
        SubmodelAdapterFactory._registered_builders[adapter_key] = class_builder
        logger.info("Registered the adapter type '%s' through the class %s", adapter_key, getattr(adapter_class, "__name__", "?"),
                    extra=log_extra(adapter_type=adapter_key, operation="adapter_factory.register"))

    @staticmethod
    def unregister_adapter(adapter_type: str) -> None:
        """
        Unregister a previously registered external adapter type.

        :param adapter_type: External adapter type key.

        Example:
            Remove a runtime registration::

                SubmodelAdapterFactory.unregister_adapter("external")
        """
        adapter_key = SubmodelAdapterFactory._normalize_type_key(adapter_type)
        if SubmodelAdapterFactory._registered_builders.pop(adapter_key, None) is not None:
            logger.info("Unregistered the adapter type '%s'", adapter_key,
                        extra=log_extra(adapter_type=adapter_key, operation="adapter_factory.unregister"))
        else:
            logger.debug("The adapter type '%s' was not registered, nothing to unregister", adapter_key,
                         extra=log_extra(adapter_type=adapter_key, operation="adapter_factory.unregister"))

    @staticmethod
    def get_registered_adapter_types() -> list[str]:
        """
        Return all currently registered external adapter type keys.

        This method only reports adapters registered at runtime through
        ``register_adapter``. Built-in adapters declared in
        ``SubmodelAdapterType`` are intentionally excluded.

        :return: Sorted list of registered adapter keys.

        Example:
            Inspect current registrations::

                types = SubmodelAdapterFactory.get_registered_adapter_types()
        """
        return sorted(SubmodelAdapterFactory._registered_builders.keys())

    @staticmethod
    def get_available_adapter_types() -> list[str]:
        """
        Return all available adapter type keys.

        This method combines:
        - Built-in adapter types from ``SubmodelAdapterType``.
        - External adapter types registered via ``register_adapter``.

        Built-in and external values are normalized to the same lowercase
        underscore style.

        :return: Sorted list of all available adapter keys.

        Example:
            Inspect all available adapters::

                types = SubmodelAdapterFactory.get_available_adapter_types()
        """
        builtins = [item.name.lower() for item in SubmodelAdapterType]
        externals = SubmodelAdapterFactory.get_registered_adapter_types()
        return sorted(set(builtins + externals))

    @staticmethod
    def _get_adapter_builder(
            adapter_type: str | SubmodelAdapterType,
    ):
        """
        Resolve and return a builder for a built-in or registered adapter type.

        :param adapter_type: Adapter type identifier.
        :return: Builder instance for the resolved adapter.
        :raises ValueError: If the type is unknown.
        :raises AttributeError: If the built-in adapter class cannot be resolved.
        :raises ImportError: If the built-in adapter module cannot be imported.
        """
        adapter_type_enum = SubmodelAdapterFactory._to_adapter_type(adapter_type)

        if adapter_type_enum is None:
            adapter_key = SubmodelAdapterFactory._normalize_type_key(adapter_type)
            if adapter_key in SubmodelAdapterFactory._registered_builders:
                logger.debug("The adapter type '%s' is not a built-in one, using its registered builder", adapter_key,
                             extra=log_extra(adapter_type=adapter_key, operation="adapter_factory.get_builder"))
                return SubmodelAdapterFactory._registered_builders[adapter_key]()

            allowed = SubmodelAdapterFactory.get_available_adapter_types()
            logger.error("Unsupported adapter type '%s'. Allowed values: %s", adapter_type, ", ".join(sorted(set(allowed))),
                         extra=log_extra(adapter_type=str(adapter_type), operation="adapter_factory.get_builder"))
            raise ValueError(
                f"Unsupported adapter type '{adapter_type}'. Allowed values: {', '.join(sorted(set(allowed)))}"
            )

        adapter_module = ".".join(__name__.split(".")[0:-1])
        module_name = f"{adapter_module}.submodel_adapters"
        adapter_class_name = f"{adapter_type_enum.value}Adapter"

        try:
            module = import_module(module_name)
            adapter_class = getattr(module, adapter_class_name)
            logger.debug("Resolved %s from %s", adapter_class_name, module_name,
                         extra=log_extra(adapter_type=adapter_class_name, operation="adapter_factory.get_builder"))
            return adapter_class.builder()
        except AttributeError as attr_exception:
            logger.exception("The adapter class %s was not found in %s", adapter_class_name, module_name,
                             extra=log_extra(adapter_type=adapter_class_name, operation="adapter_factory.get_builder"))
            raise AttributeError(
                f"Failed to import adapter class {adapter_class_name} for module {module_name}"
            ) from attr_exception
        except ImportError as import_exception:
            logger.exception("The adapter module %s could not be imported", module_name,
                             extra=log_extra(adapter_type=adapter_class_name, operation="adapter_factory.get_builder"))
            raise ImportError(
                f"Failed to import module {module_name}. Ensure that the required packages are installed and the PYTHONPATH is set correctly."
            ) from import_exception

    @staticmethod
    def _is_value_compatible_with_annotation(annotation: Any, value: Any) -> bool:
        """
        Check whether a value matches a type annotation when runtime checking is possible.

        Non-runtime-checkable annotations are treated as compatible.
        """
        if annotation is inspect.Signature.empty or annotation is Any:
            return True

        if annotation is None or annotation is type(None):
            return value is None

        origin = get_origin(annotation)
        if origin is None:
            if isinstance(annotation, type):
                return isinstance(value, annotation)
            return True

        if origin in (Union, types.UnionType):
            return any(
                SubmodelAdapterFactory._is_value_compatible_with_annotation(item, value)
                for item in get_args(annotation)
            )

        if origin in (list, dict, tuple, set, frozenset):
            return isinstance(value, origin)

        try:
            return isinstance(value, origin)
        except TypeError:
            return True

    @staticmethod
    def _annotation_to_display_name(annotation: Any) -> str:
        """
        Return a compact human-readable annotation name for error messages.
        """
        if annotation is inspect.Signature.empty:
            return "Any"

        try:
            return annotation.__name__
        except AttributeError:
            return str(annotation)

    @staticmethod
    def from_config(adapter_type: str | SubmodelAdapterType, config: Mapping[str, Any]):
        """
        Create a submodel adapter from key-value configuration.

        The adapter type is provided explicitly and all config keys are passed
        to builder methods with the same name.

        :param adapter_type: Adapter type identifier.
        :param config: Configuration map used to construct the adapter.
        :return: Constructed adapter instance.
        :raises TypeError: If ``config`` is not a mapping.
        :raises ValueError: If builder key resolution fails.

        Examples:
            Create with explicit adapter type::

                adapter = SubmodelAdapterFactory.from_config(
                    adapter_type="file_system",
                    config={"root_path": "./submodels"},
                )
        """
        if not isinstance(config, Mapping):
            logger.warning("The configuration of a '%s' adapter must be a mapping, got a %s", adapter_type, type(config).__name__,
                           extra=log_extra(adapter_type=str(adapter_type), operation="adapter_factory.from_config"))
            raise TypeError("config must be a mapping")

        builder = SubmodelAdapterFactory._get_adapter_builder(adapter_type=adapter_type)
        # Only the names of the settings are logged: their values may be credentials
        logger.debug("Creating a '%s' adapter with the settings %s", adapter_type, sorted(config),
                     extra=log_extra(adapter_type=str(adapter_type), operation="adapter_factory.from_config"))

        for key, value in config.items():
            builder_method = getattr(builder, key, None)
            if not callable(builder_method):
                logger.warning("Unsupported setting '%s' for the adapter type '%s'", key, adapter_type,
                               extra=log_extra(adapter_type=str(adapter_type), operation="adapter_factory.from_config"))
                raise ValueError(f"Unsupported config key '{key}' for adapter type '{adapter_type}'")

            # Perform runtime type checking against the builder method's first parameter annotation, if available
            parameters = list(inspect.signature(builder_method).parameters.values())
            if parameters:
                expected_annotation = parameters[0].annotation
                if not SubmodelAdapterFactory._is_value_compatible_with_annotation(expected_annotation, value):
                    expected = SubmodelAdapterFactory._annotation_to_display_name(expected_annotation)
                    actual = type(value).__name__
                    logger.warning("The setting '%s' of the adapter type '%s' should be a %s, got a %s", key, adapter_type, expected, actual,
                                   extra=log_extra(adapter_type=str(adapter_type), operation="adapter_factory.from_config"))
                    raise TypeError(
                        f"Invalid type for config key '{key}' for adapter type '{adapter_type}': "
                        f"expected '{expected}', got '{actual}'"
                    )

            builder_method(value)

        adapter = builder.build()
        logger.info("Created a '%s' adapter (%s)", adapter_type, type(adapter).__name__,
                    extra=log_extra(adapter_type=type(adapter).__name__, operation="adapter_factory.from_config"))
        return adapter
    
    @staticmethod
    def get_file_system(root_path: str = "./submodel", path_pattern: str = "{asset_path}") -> Any:
        """
        Create a file system submodel adapter.

        :param root_path: Root directory for submodel storage.
        :param path_pattern: Pattern for submodel paths.
        :return: Built file system adapter instance.

        Example:
            Create the default file system adapter::

                adapter = SubmodelAdapterFactory.get_file_system("./submodels")
        """
        return SubmodelAdapterFactory.from_config(
            adapter_type=SubmodelAdapterType.FILE_SYSTEM,
            config={
                "root_path": root_path,
                "path_pattern": path_pattern,
            },
        )

    @staticmethod
    def get_s3(
            bucket_name: str,
            region_name: str,
            key_pattern: str = "{path}",
            endpoint_url: str | None = None,
            aws_access_key_id: str | None = None,
            aws_secret_access_key: str | None = None
    ) -> Any:
        """
        Create an S3 submodel adapter.

        Requires the ``boto3`` package (``pip install tractusx_sdk[s3]``).

        :param bucket_name: Target S3 bucket name (required).
        :param region_name: AWS region (required, e.g. ``"eu-central-1"``).
        :param key_pattern: Pattern for S3 object keys, resolved from submodel metadata.
            Uses the same ``{field}`` substitution convention as ``FileSystemAdapter``.
            Defaults to ``"{path}"``.
        :param endpoint_url: Override endpoint URL for S3-compatible stores such as MinIO.
            If not provided, uses AWS S3 endpoint.
        :param aws_access_key_id: AWS access key ID. Must be provided together with
            ``aws_secret_access_key``. If neither is provided, boto3 will use environment
            variables, IAM roles, or AWS config files.
        :param aws_secret_access_key: AWS secret access key. Must be provided together with
            ``aws_access_key_id``. If neither is provided, boto3 will use environment
            variables, IAM roles, or AWS config files.
        :return: Configured S3 adapter instance (SubmodelAdapter).

        Example:
            Create an S3 adapter with explicit credentials:

                adapter = SubmodelAdapterFactory.get_s3(
                    bucket_name="my-submodels",
                    region_name="eu-central-1",
                    key_pattern="{semantic_id}/{submodel_id}.json",
                    aws_access_key_id="YOUR_ACCESS_KEY",
                    aws_secret_access_key="YOUR_SECRET_KEY",
                )
        """
        config = {"bucket_name": bucket_name, "region_name": region_name, "key_pattern": key_pattern}
        if endpoint_url is not None:
            config["endpoint_url"] = endpoint_url
        if aws_access_key_id is not None:
            config["aws_access_key_id"] = aws_access_key_id
        if aws_secret_access_key is not None:
            config["aws_secret_access_key"] = aws_secret_access_key
        return SubmodelAdapterFactory.from_config(
            adapter_type=SubmodelAdapterType.S3,
            config=config,
        )
