# Configuration

This guide covers how to configure the Facade Inspection Software for optimal performance.

## Configuration Files

The application uses several configuration files located in the `config/` directory:

```
config/
├── aws_config.json      # AWS integration settings
├── categories.py        # Finding categories
├── status.py           # Status definitions
└── tags.py             # Available tags
```

## AWS Configuration

### Setting up AWS Integration

1. **Create AWS Account**: If you don't have one, create an AWS account
2. **Create S3 Bucket**: Set up an S3 bucket for file storage
3. **Get Access Keys**: Create IAM user with S3 permissions

### Configure AWS Settings

Edit `config/aws_config.json`:

```json
{
  "aws_access_key_id": "AKIAIOSFODNN7EXAMPLE",
  "aws_secret_access_key": "wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY",
  "region": "us-west-2",
  "bucket_name": "my-facade-inspection-bucket",
  "enable_sync": true,
  "auto_backup": true,
  "backup_interval": 300
}
```

## Application Settings

### Performance Settings

Create `config/app_settings.json` for performance tuning:

```json
{
  "image_quality": 85,
  "max_image_size": 1920,
  "auto_save_interval": 60,
  "cache_size_mb": 500,
  "concurrent_uploads": 3,
  "thumbnail_size": 150
}
```

## Environment Variables

Set these environment variables for enhanced security:

```bash
# Windows
set FACADE_AWS_ACCESS_KEY=your_access_key
set FACADE_AWS_SECRET_KEY=your_secret_key

# macOS/Linux
export FACADE_AWS_ACCESS_KEY=your_access_key
export FACADE_AWS_SECRET_KEY=your_secret_key
```

---

*For advanced configuration options, see the Development Guide.*