"""
AWS Integration Module for Facade Inspection Software

Provides unified AWS/S3 functionality with support for:
- LocalStack (development)
- AWS Staging
- AWS Production
- Configuration management
- File upload/download
- Bucket management
"""

import os
import json
import boto3
from pathlib import Path
from typing import Dict, Optional, Any
from botocore.exceptions import ClientError, NoCredentialsError

class AWSManager:
    """Manages AWS S3 operations with environment-aware configuration"""
    
    def __init__(self, config_path: str = None):
        """
        Initialize AWS Manager with configuration
        
        Args:
            config_path: Path to AWS config file. If None, uses default location.
        """
        if config_path is None:
            workspace_root = Path(__file__).resolve().parents[2]
            config_path = os.path.join(workspace_root, "config", "aws_config.json")
        
        self.config_path = config_path
        self.config = self._load_config()
        self.current_env = self.config.get("current_environment", "development")
        self.s3_client = None
        self._initialize_s3_client()
    
    def _load_config(self) -> Dict:
        """Load AWS configuration from file"""
        try:
            with open(self.config_path, 'r') as f:
                config = json.load(f)
                print(f"[INFO] Loaded AWS config from {self.config_path}")
                return config
        except FileNotFoundError:
            print(f"[WARNING] AWS config file not found: {self.config_path}")
            return self._get_default_config()
        except json.JSONDecodeError as e:
            print(f"[ERROR] Invalid JSON in AWS config: {e}")
            return self._get_default_config()
    
    def _get_default_config(self) -> Dict:
        """Get default LocalStack configuration"""
        return {
            "current_environment": "development",
            "development": {
                "endpoint_url": "http://localhost:4566",
                "aws_access_key_id": "test",
                "aws_secret_access_key": "test",
                "region_name": "us-east-1",
                "bucket_name": "facade-inspection-dev"
            }
        }
    
    def _initialize_s3_client(self):
        """Initialize S3 client with current environment configuration"""
        env_config = self.config.get(self.current_env, {})
        
        try:
            # Build S3 client parameters
            client_params = {
                "aws_access_key_id": env_config.get("aws_access_key_id"),
                "aws_secret_access_key": env_config.get("aws_secret_access_key"),
                "region_name": env_config.get("region_name", "us-east-1")
            }
            
            # Add endpoint_url for LocalStack
            endpoint_url = env_config.get("endpoint_url")
            if endpoint_url:
                client_params["endpoint_url"] = endpoint_url
            
            self.s3_client = boto3.client("s3", **client_params)
            self.bucket_name = env_config.get("bucket_name", "facade-inspection")
            
            print(f"[INFO] Initialized S3 client for environment: {self.current_env}")
            if endpoint_url:
                print(f"[INFO] Using endpoint: {endpoint_url}")
            
            # Test connection and create bucket if needed
            self._ensure_bucket_exists()
            
        except Exception as e:
            print(f"[ERROR] Failed to initialize S3 client: {e}")
            self.s3_client = None
    
    def _ensure_bucket_exists(self):
        """Ensure the configured bucket exists"""
        if not self.s3_client:
            return False
        
        try:
            self.s3_client.head_bucket(Bucket=self.bucket_name)
            print(f"[INFO] Using existing bucket: {self.bucket_name}")
        except ClientError as e:
            error_code = e.response['Error']['Code']
            if error_code == '404':
                try:
                    self.s3_client.create_bucket(Bucket=self.bucket_name)
                    print(f"[INFO] Created bucket: {self.bucket_name}")
                except Exception as create_error:
                    print(f"[ERROR] Failed to create bucket {self.bucket_name}: {create_error}")
                    return False
            else:
                print(f"[ERROR] Bucket access error: {e}")
                return False
        return True
    
    def switch_environment(self, environment: str) -> bool:
        """
        Switch to a different environment (development/staging/production)
        
        Args:
            environment: Target environment name
            
        Returns:
            bool: True if switch was successful
        """
        if environment not in self.config:
            print(f"[ERROR] Environment '{environment}' not found in config")
            return False
        
        self.current_env = environment
        self.config["current_environment"] = environment
        
        # Save updated config
        try:
            with open(self.config_path, 'w') as f:
                json.dump(self.config, f, indent=2)
            print(f"[INFO] Switched to environment: {environment}")
        except Exception as e:
            print(f"[ERROR] Failed to save config: {e}")
            return False
        
        # Reinitialize S3 client
        self._initialize_s3_client()
        return True
    
    def upload_file(self, local_path: str, s3_key: str) -> bool:
        """
        Upload a file to S3
        
        Args:
            local_path: Path to local file
            s3_key: S3 object key (path in bucket)
            
        Returns:
            bool: True if upload was successful
        """
        if not self.s3_client:
            print("[ERROR] S3 client not initialized")
            return False
        
        try:
            self.s3_client.upload_file(local_path, self.bucket_name, s3_key)
            endpoint = self.config[self.current_env].get("endpoint_url", "AWS")
            print(f"[INFO] Uploaded {local_path} to {endpoint}/{self.bucket_name}/{s3_key}")
            return True
        except FileNotFoundError:
            print(f"[ERROR] Local file not found: {local_path}")
            return False
        except Exception as e:
            print(f"[ERROR] Failed to upload file: {e}")
            return False
    
    def download_file(self, s3_key: str, local_path: str) -> bool:
        """
        Download a file from S3
        
        Args:
            s3_key: S3 object key (path in bucket)
            local_path: Local path to save file
            
        Returns:
            bool: True if download was successful
        """
        if not self.s3_client:
            print("[ERROR] S3 client not initialized")
            return False
        
        try:
            # Ensure local directory exists
            os.makedirs(os.path.dirname(local_path), exist_ok=True)
            
            self.s3_client.download_file(self.bucket_name, s3_key, local_path)
            print(f"[INFO] Downloaded {s3_key} to {local_path}")
            return True
        except ClientError as e:
            if e.response['Error']['Code'] == 'NoSuchKey':
                print(f"[ERROR] File not found in S3: {s3_key}")
            else:
                print(f"[ERROR] Failed to download file: {e}")
            return False
        except Exception as e:
            print(f"[ERROR] Failed to download file: {e}")
            return False
    
    def upload_json(self, data: Any, s3_key: str) -> bool:
        """
        Upload JSON data directly to S3
        
        Args:
            data: Data to serialize as JSON
            s3_key: S3 object key
            
        Returns:
            bool: True if upload was successful
        """
        if not self.s3_client:
            print("[ERROR] S3 client not initialized")
            return False
        
        try:
            json_str = json.dumps(data, indent=2, default=str)
            self.s3_client.put_object(
                Bucket=self.bucket_name,
                Key=s3_key,
                Body=json_str,
                ContentType='application/json'
            )
            endpoint = self.config[self.current_env].get("endpoint_url", "AWS")
            print(f"[INFO] Uploaded JSON to {endpoint}/{self.bucket_name}/{s3_key}")
            return True
        except Exception as e:
            print(f"[ERROR] Failed to upload JSON: {e}")
            return False
    
    def download_json(self, s3_key: str) -> Optional[Any]:
        """
        Download and parse JSON data from S3
        
        Args:
            s3_key: S3 object key
            
        Returns:
            Parsed JSON data or None if failed
        """
        if not self.s3_client:
            print("[ERROR] S3 client not initialized")
            return None
        
        try:
            response = self.s3_client.get_object(Bucket=self.bucket_name, Key=s3_key)
            data = json.loads(response['Body'].read().decode('utf-8'))
            print(f"[INFO] Downloaded JSON from {s3_key}")
            return data
        except ClientError as e:
            if e.response['Error']['Code'] == 'NoSuchKey':
                print(f"[INFO] File not found in S3: {s3_key}")
            else:
                print(f"[ERROR] Failed to download JSON: {e}")
            return None
        except Exception as e:
            print(f"[ERROR] Failed to download JSON: {e}")
            return None
    
    def list_objects(self, prefix: str = "") -> list:
        """
        List objects in the bucket with optional prefix
        
        Args:
            prefix: Object key prefix to filter by
            
        Returns:
            List of object keys
        """
        if not self.s3_client:
            print("[ERROR] S3 client not initialized")
            return []
        
        try:
            response = self.s3_client.list_objects_v2(
                Bucket=self.bucket_name,
                Prefix=prefix
            )
            
            objects = []
            if 'Contents' in response:
                objects = [obj['Key'] for obj in response['Contents']]
            
            print(f"[INFO] Found {len(objects)} objects with prefix '{prefix}'")
            return objects
        except Exception as e:
            print(f"[ERROR] Failed to list objects: {e}")
            return []
    
    def delete_object(self, s3_key: str) -> bool:
        """
        Delete an object from S3
        
        Args:
            s3_key: S3 object key
            
        Returns:
            bool: True if deletion was successful
        """
        if not self.s3_client:
            print("[ERROR] S3 client not initialized")
            return False
        
        try:
            self.s3_client.delete_object(Bucket=self.bucket_name, Key=s3_key)
            print(f"[INFO] Deleted object: {s3_key}")
            return True
        except Exception as e:
            print(f"[ERROR] Failed to delete object: {e}")
            return False
    
    def get_status(self) -> Dict:
        """
        Get current AWS manager status
        
        Returns:
            Dict with status information
        """
        status = {
            "environment": self.current_env,
            "bucket_name": getattr(self, 'bucket_name', 'Unknown'),
            "s3_client_initialized": self.s3_client is not None,
            "endpoint_url": self.config.get(self.current_env, {}).get("endpoint_url", "AWS"),
        }
        
        if self.s3_client:
            try:
                # Test bucket access
                self.s3_client.head_bucket(Bucket=self.bucket_name)
                status["bucket_accessible"] = True
            except:
                status["bucket_accessible"] = False
        else:
            status["bucket_accessible"] = False
        
        return status

# Global AWS manager instance
aws_manager = AWSManager()

# Convenience functions
def upload_master_findings(master_findings_path: str) -> bool:
    """Upload master findings to S3"""
    return aws_manager.upload_file(master_findings_path, "master_findings.json")

def download_master_findings(local_path: str) -> bool:
    """Download master findings from S3"""
    return aws_manager.download_file("master_findings.json", local_path)

def switch_to_development():
    """Switch to development environment (LocalStack)"""
    return aws_manager.switch_environment("development")

def switch_to_staging():
    """Switch to staging environment"""
    return aws_manager.switch_environment("staging")

def switch_to_production():
    """Switch to production environment"""
    return aws_manager.switch_environment("production")

def get_aws_status() -> Dict:
    """Get current AWS status"""
    return aws_manager.get_status()

if __name__ == "__main__":
    # Test AWS manager
    print("Testing AWS Manager...")
    status = get_aws_status()
    for key, value in status.items():
        print(f"  {key}: {value}")
    
    # Test switching environments
    print("\nTesting environment switching...")
    print(f"Current: {aws_manager.current_env}")
    
    # Test LocalStack connection if available
    if status["bucket_accessible"]:
        print("\nTesting S3 operations...")
        test_data = {"test": "data", "timestamp": "2025-09-25"}
        if aws_manager.upload_json(test_data, "test/test.json"):
            downloaded = aws_manager.download_json("test/test.json")
            print(f"Upload/Download test: {'PASS' if downloaded == test_data else 'FAIL'}")
            aws_manager.delete_object("test/test.json")
    else:
        print("S3 not accessible - skipping operation tests")