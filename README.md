# Facade Inspection Software

A comprehensive PyQt6-based desktop application for managing facade inspection projects, elevations, and findings.

## Features

- **Project Management**: Create and manage inspection projects
- **Elevation Overview**: Visual management of building elevations
- **Findings Tracking**: Categorize and track inspection findings
- **AWS Integration**: Cloud storage capabilities for project data
- **User Authentication**: Secure login system
- **Data Export**: Export findings and reports

## Requirements

- Python 3.8+
- PyQt6
- AWS SDK (boto3)
- See `requirements.txt` for full dependencies

## Installation

1. Clone the repository:
```bash
git clone https://github.com/AndrewJapx/FacadeInspection_Software.git
cd FacadeInspection_Software
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Run the application:
```bash
python src/main.py
```

## Project Structure

- `src/` - Main application source code
  - `Project/` - Project management modules
  - `login/` - Authentication system
  - `config/` - Configuration files
  - `abstract_layer/` - Abstract data handling layer
- `storage/` - Local data storage
- `requirements.txt` - Python dependencies

## Usage

1. Launch the application
2. Log in with your credentials
3. Create a new project or open an existing one
4. Add elevations and manage findings
5. Export reports as needed

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## License

[Add your license information here]