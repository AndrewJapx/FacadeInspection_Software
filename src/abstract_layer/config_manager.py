"""
Configuration manager for FacadeInspection storage backends.
Allows easy switching between local and S3 storage.
"""

import os
import json
from pathlib import Path

class ConfigManager:
    def __init__(self):
        self.config_file = Path(__file__).parent.parent.parent / "config" / "storage_config.json"
        self.config_file.parent.mkdir(exist_ok=True)
        self._load_config()
    
    def _load_config(self):
        """Load configuration from file or create default"""
        if self.config_file.exists():
            try:
                with open(self.config_file, 'r') as f:
                    self.config = json.load(f)
            except Exception as e:
                print(f"[WARN] Failed to load config: {e}, using defaults")
                self._create_default_config()
        else:
            self._create_default_config()
    
    def _create_default_config(self):
        """Create default configuration"""
        self.config = {
            "storage": {
                "backend": "local",  # Options: 'local', 's3', 'hybrid'
                "local": {
                    "base_path": None  # Uses default workspace/storage
                },
                "s3": {
                    "bucket_name": "facade-inspection",
                    "endpoint_url": "http://localhost:4566",  # LocalStack
                    "aws_access_key_id": "test",
                    "aws_secret_access_key": "test", 
                    "region_name": "us-east-1"
                },
                "aws_production": {
                    "bucket_name": "facade-inspection-prod",
                    "endpoint_url": None,  # Use real AWS
                    "aws_access_key_id": None,  # Will use AWS credentials
                    "aws_secret_access_key": None,
                    "region_name": "us-east-1"
                }
            },
            "features": {
                "auto_sync": False,
                "offline_mode": True,
                "backup_frequency": "daily"
            }
        }
        self.save_config()
    
    def save_config(self):
        """Save configuration to file"""
        try:
            with open(self.config_file, 'w') as f:
                json.dump(self.config, f, indent=2)
        except Exception as e:
            print(f"[ERROR] Failed to save config: {e}")
    
    def get_storage_backend(self) -> str:
        """Get current storage backend"""
        return self.config["storage"]["backend"]
    
    def set_storage_backend(self, backend: str):
        """Set storage backend"""
        valid_backends = ["local", "s3", "aws_production", "hybrid"]
        if backend not in valid_backends:
            raise ValueError(f"Invalid backend: {backend}. Options: {valid_backends}")
        
        self.config["storage"]["backend"] = backend
        self.save_config()
        print(f"✅ Storage backend set to: {backend}")
    
    def get_storage_config(self) -> dict:
        """Get configuration for current storage backend"""
        backend = self.get_storage_backend()
        return self.config["storage"][backend]
    
    def is_cloud_storage(self) -> bool:
        """Check if using cloud storage"""
        return self.get_storage_backend() in ["s3", "aws_production"]
    
    def switch_to_development(self):
        """Switch to development mode (LocalStack)"""
        self.set_storage_backend("s3")
        print("🔧 Switched to development mode (LocalStack)")
    
    def switch_to_production(self):
        """Switch to production mode (AWS)"""
        self.set_storage_backend("aws_production")
        print("🚀 Switched to production mode (AWS)")
    
    def switch_to_local(self):
        """Switch to local file storage"""
        self.set_storage_backend("local")
        print("💾 Switched to local file storage")

# Global config instance
config_manager = ConfigManager()

def get_current_backend():
    """Get current storage backend name"""
    return config_manager.get_storage_backend()

def switch_to_localstack():
    """Quick function to switch to LocalStack"""
    config_manager.switch_to_development()

def switch_to_aws():
    """Quick function to switch to AWS production"""
    config_manager.switch_to_production()

def switch_to_local():
    """Quick function to switch to local storage"""
    config_manager.switch_to_local()

if __name__ == "__main__":
    # CLI tool for switching backends
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python config_manager.py [local|localstack|aws|status]")
        print(f"Current backend: {get_current_backend()}")
        sys.exit(1)
    
    command = sys.argv[1].lower()
    
    if command == "local":
        switch_to_local()
    elif command == "localstack":
        switch_to_localstack()
    elif command == "aws":
        switch_to_aws()
    elif command == "status":
        backend = get_current_backend()
        cloud = "☁️" if config_manager.is_cloud_storage() else "💾"
        print(f"{cloud} Current storage backend: {backend}")
        if backend != "local":
            config = config_manager.get_storage_config()
            print(f"   Bucket: {config.get('bucket_name')}")
            print(f"   Endpoint: {config.get('endpoint_url', 'AWS Default')}")
    else:
        print(f"Unknown command: {command}")
        sys.exit(1)