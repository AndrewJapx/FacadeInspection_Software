"""
Abstract Layer Package - Universal Storage Interface

This package provides a unified interface for storing facade inspection data
across different backends (local files, AWS S3, LocalStack).

Components:
- storage_backend: Core storage abstraction classes
- config_manager: Configuration management for switching backends
- findings_logic_v2: Updated findings logic using the abstraction layer

Usage:
    from abstract_layer import storage_backend, config_manager
    from abstract_layer.findings_logic_v2 import load_pins, save_pins
    
Example:
    # Switch to LocalStack for development
    config_manager.switch_to_localstack()
    
    # Load pins (now from S3/LocalStack)
    pins = load_pins("my_project")
"""

# Import main components for easy access
from .storage_backend import (
    StorageBackend, 
    LocalFileStorage, 
    S3Storage,
    storage,
    get_storage_backend
)

from .config_manager import (
    get_current_backend,
    switch_to_local,
    switch_to_localstack, 
    switch_to_aws
)

__all__ = [
    'StorageBackend',
    'LocalFileStorage', 
    'S3Storage',
    'storage',
    'get_storage_backend',
    'get_current_backend',
    'switch_to_local',
    'switch_to_localstack',
    'switch_to_aws'
]

__version__ = "1.0.0"