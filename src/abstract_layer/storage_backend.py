"""
Storage abstraction layer for FacadeInspection app.
Supports both local file storage and S3 (LocalStack/AWS) storage.
"""

import os
import json
import boto3
from pathlib import Path
from typing import Dict, List, Any, Optional
from datetime import date

class StorageBackend:
    """Abstract base for storage backends"""
    
    def save_json(self, path: str, data: Any) -> bool:
        raise NotImplementedError
        
    def load_json(self, path: str) -> Any:
        raise NotImplementedError
        
    def exists(self, path: str) -> bool:
        raise NotImplementedError
        
    def delete(self, path: str) -> bool:
        raise NotImplementedError
        
    def list_projects(self) -> List[str]:
        raise NotImplementedError

class LocalFileStorage(StorageBackend):
    """Local file system storage backend"""
    
    def __init__(self, base_path: str = None):
        if base_path is None:
            workspace_root = Path(__file__).resolve().parents[3]
            base_path = os.path.join(workspace_root, "storage")
        self.base_path = base_path
        os.makedirs(base_path, exist_ok=True)
    
    def _get_full_path(self, path: str) -> str:
        return os.path.join(self.base_path, path)
    
    def save_json(self, path: str, data: Any) -> bool:
        try:
            full_path = self._get_full_path(path)
            os.makedirs(os.path.dirname(full_path), exist_ok=True)
            
            # Handle date serialization
            def serialize_dates(obj):
                if isinstance(obj, date):
                    return obj.isoformat()
                elif isinstance(obj, dict):
                    return {k: serialize_dates(v) for k, v in obj.items()}
                elif isinstance(obj, list):
                    return [serialize_dates(item) for item in obj]
                return obj
            
            with open(full_path, 'w', encoding='utf-8') as f:
                json.dump(serialize_dates(data), f, indent=2)
            return True
        except Exception as e:
            print(f"[ERROR] Failed to save {path}: {e}")
            return False
    
    def load_json(self, path: str) -> Any:
        try:
            full_path = self._get_full_path(path)
            if not os.path.exists(full_path):
                return None
            
            with open(full_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Handle date parsing
            def parse_dates(obj):
                if isinstance(obj, str) and obj.count('-') == 2:
                    try:
                        return date.fromisoformat(obj)
                    except:
                        return obj
                elif isinstance(obj, dict):
                    return {k: parse_dates(v) for k, v in obj.items()}
                elif isinstance(obj, list):
                    return [parse_dates(item) for item in obj]
                return obj
            
            return parse_dates(data)
        except Exception as e:
            print(f"[ERROR] Failed to load {path}: {e}")
            return None
    
    def exists(self, path: str) -> bool:
        return os.path.exists(self._get_full_path(path))
    
    def delete(self, path: str) -> bool:
        try:
            full_path = self._get_full_path(path)
            if os.path.isfile(full_path):
                os.remove(full_path)
            elif os.path.isdir(full_path):
                import shutil
                shutil.rmtree(full_path)
            return True
        except Exception as e:
            print(f"[ERROR] Failed to delete {path}: {e}")
            return False
    
    def list_projects(self) -> List[str]:
        try:
            return [d for d in os.listdir(self.base_path) 
                   if os.path.isdir(os.path.join(self.base_path, d)) and not d.startswith('.')]
        except:
            return []

class S3Storage(StorageBackend):
    """S3 storage backend (works with LocalStack and AWS)"""
    
    def __init__(self, bucket_name: str = "facade-inspection", 
                 endpoint_url: str = "http://localhost:4566",
                 aws_access_key_id: str = "test",
                 aws_secret_access_key: str = "test",
                 region_name: str = "us-east-1"):
        self.bucket_name = bucket_name
        self.s3 = boto3.client(
            "s3",
            endpoint_url=endpoint_url,
            aws_access_key_id=aws_access_key_id,
            aws_secret_access_key=aws_secret_access_key,
            region_name=region_name
        )
        self._ensure_bucket_exists()
    
    def _ensure_bucket_exists(self):
        try:
            self.s3.head_bucket(Bucket=self.bucket_name)
        except:
            try:
                self.s3.create_bucket(Bucket=self.bucket_name)
                print(f"[INFO] Created S3 bucket: {self.bucket_name}")
            except Exception as e:
                print(f"[ERROR] Failed to create bucket: {e}")
    
    def save_json(self, path: str, data: Any) -> bool:
        try:
            # Handle date serialization
            def serialize_dates(obj):
                if isinstance(obj, date):
                    return obj.isoformat()
                elif isinstance(obj, dict):
                    return {k: serialize_dates(v) for k, v in obj.items()}
                elif isinstance(obj, list):
                    return [serialize_dates(item) for item in obj]
                return obj
            
            json_data = json.dumps(serialize_dates(data), indent=2)
            self.s3.put_object(
                Bucket=self.bucket_name,
                Key=path,
                Body=json_data,
                ContentType='application/json'
            )
            print(f"[INFO] Saved to S3: s3://{self.bucket_name}/{path}")
            return True
        except Exception as e:
            print(f"[ERROR] Failed to save to S3 {path}: {e}")
            return False
    
    def load_json(self, path: str) -> Any:
        try:
            response = self.s3.get_object(Bucket=self.bucket_name, Key=path)
            data = json.loads(response['Body'].read())
            
            # Handle date parsing
            def parse_dates(obj):
                if isinstance(obj, str) and obj.count('-') == 2:
                    try:
                        return date.fromisoformat(obj)
                    except:
                        return obj
                elif isinstance(obj, dict):
                    return {k: parse_dates(v) for k, v in obj.items()}
                elif isinstance(obj, list):
                    return [parse_dates(item) for item in obj]
                return obj
            
            return parse_dates(data)
        except self.s3.exceptions.NoSuchKey:
            return None
        except Exception as e:
            print(f"[ERROR] Failed to load from S3 {path}: {e}")
            return None
    
    def exists(self, path: str) -> bool:
        try:
            self.s3.head_object(Bucket=self.bucket_name, Key=path)
            return True
        except:
            return False
    
    def delete(self, path: str) -> bool:
        try:
            # Delete single object or all objects with prefix
            if path.endswith('/'):
                # Delete all objects with prefix (folder-like deletion)
                objects = self.s3.list_objects_v2(Bucket=self.bucket_name, Prefix=path)
                if 'Contents' in objects:
                    delete_keys = [{'Key': obj['Key']} for obj in objects['Contents']]
                    self.s3.delete_objects(
                        Bucket=self.bucket_name,
                        Delete={'Objects': delete_keys}
                    )
            else:
                self.s3.delete_object(Bucket=self.bucket_name, Key=path)
            return True
        except Exception as e:
            print(f"[ERROR] Failed to delete from S3 {path}: {e}")
            return False
    
    def list_projects(self) -> List[str]:
        try:
            response = self.s3.list_objects_v2(Bucket=self.bucket_name, Delimiter='/')
            projects = []
            if 'CommonPrefixes' in response:
                for prefix in response['CommonPrefixes']:
                    project_name = prefix['Prefix'].rstrip('/')
                    projects.append(project_name)
            return projects
        except Exception as e:
            print(f"[ERROR] Failed to list projects: {e}")
            return []

# Configuration
STORAGE_CONFIG = {
    'backend': 'local',  # Options: 'local', 's3'
    'local': {
        'base_path': None  # Will use default workspace/storage
    },
    's3': {
        'bucket_name': 'facade-inspection',
        'endpoint_url': 'http://localhost:4566',  # LocalStack endpoint
        'aws_access_key_id': 'test',
        'aws_secret_access_key': 'test',
        'region_name': 'us-east-1'
    }
}

def get_storage_backend() -> StorageBackend:
    """Get the configured storage backend"""
    backend_type = STORAGE_CONFIG['backend']
    
    if backend_type == 'local':
        config = STORAGE_CONFIG['local']
        return LocalFileStorage(base_path=config['base_path'])
    elif backend_type == 's3':
        config = STORAGE_CONFIG['s3']
        return S3Storage(**config)
    else:
        raise ValueError(f"Unknown storage backend: {backend_type}")

# Global storage instance
storage = get_storage_backend()