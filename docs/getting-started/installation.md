# Installation

## System Requirements

### Operating System
- Windows 10 or later
- macOS 10.14 or later
- Linux (Ubuntu 18.04+ or equivalent)

### Hardware Requirements
- **RAM**: Minimum 4GB, recommended 8GB+
- **Storage**: 2GB free space
- **Display**: 1280x720 minimum resolution
- **Network**: Internet connection for cloud features

### Python Requirements
- Python 3.8 or later
- pip package manager

## Installation Steps

### 1. Clone the Repository

```bash
git clone https://github.com/AndrewJapx/FacadeInspection_Software.git
cd FacadeInspection_Software
```

### 2. Create Virtual Environment

```bash
# Create virtual environment
python -m venv venv

# Activate virtual environment
# On Windows:
venv\Scripts\activate

# On macOS/Linux:
source venv/bin/activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure AWS (Optional)

If you plan to use cloud features:

1. Copy the AWS configuration template:
   ```bash
   cp config/aws_config.json.example config/aws_config.json
   ```

2. Edit `config/aws_config.json` with your AWS credentials:
   ```json
   {
     "aws_access_key_id": "your_access_key",
     "aws_secret_access_key": "your_secret_key",
     "region": "your_region",
     "bucket_name": "your_bucket_name"
   }
   ```

### 5. Run the Application

```bash
python src/main.py
```

## Troubleshooting

### Common Issues

#### Import Errors
If you encounter import errors:
```bash
pip install --upgrade pip
pip install -r requirements.txt --force-reinstall
```

#### PyQt5 Installation Issues
On some systems, PyQt5 may require additional setup:

**Windows:**
```bash
pip install PyQt5
```

**macOS:**
```bash
brew install pyqt5
pip install PyQt5
```

**Linux (Ubuntu/Debian):**
```bash
sudo apt-get install python3-pyqt5
pip install PyQt5
```

#### Permission Issues
If you encounter permission issues on Windows:
1. Run command prompt as Administrator
2. Or use `--user` flag: `pip install --user -r requirements.txt`

### Support

If you continue to experience issues:
1. Check the [GitHub Issues](https://github.com/AndrewJapx/FacadeInspection_Software/issues)
2. Create a new issue with your system details and error messages
3. Include your Python version: `python --version`