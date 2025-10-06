# Facade Inspection Software

Welcome to the **Facade Inspection Software** documentation! This comprehensive tool is designed to streamline the process of building facade inspections, findings management, and reporting.

## Overview

The Facade Inspection Software is a desktop application built with Python and PyQt that helps professionals:

- **Manage Projects**: Create and organize facade inspection projects
- **Document Elevations**: Record detailed information about building elevations
- **Track Findings**: Identify, categorize, and document facade issues
- **Photo Management**: Attach and organize photos related to findings
- **Generate Reports**: Create comprehensive inspection reports
- **Template System**: Use predefined templates for consistent inspections
- **Cloud Integration**: Sync data with AWS services

## Key Features

### 🏗️ Project Management
- Create and manage multiple inspection projects
- Project-specific data organization
- Progress tracking and status updates

### 📊 Elevation Overview
- Visual elevation mapping
- Interactive pin placement for findings
- Detailed elevation documentation

### 🔍 Findings Management
- Comprehensive finding categorization
- Status tracking (Open, In Progress, Resolved)
- Priority levels and tags
- Photo attachments

### 📸 Photo Integration
- Photo capture and management
- Linking photos to specific findings
- Image annotation capabilities

### 📋 Template System
- Pre-built inspection templates
- Customizable finding categories
- Standardized reporting formats

### ☁️ AWS Integration
- Cloud storage for projects and media
- Secure data synchronization
- Backup and recovery capabilities

## Getting Started

To get started with the Facade Inspection Software:

1. [Install the software](getting-started/installation.md)
2. [Configure your environment](getting-started/configuration.md)
3. [Follow the quick start guide](getting-started/quick-start.md)

## Architecture

The software is built with a modular architecture:

```
src/
├── abstract_layer/        # Configuration and abstractions
├── HomePageFolder/        # Main application interface
├── Project/              # Project management modules
│   ├── Elevations/       # Elevation handling
│   ├── Findings/         # Findings management
│   ├── Photos/           # Photo management
│   └── NavBar/           # Navigation components
├── Templates/            # Template system
├── login/               # Authentication
└── config/              # Configuration files
```

## Support

If you need help or have questions:

- Check the [User Guide](user-guide/overview.md) for detailed instructions
- Review the [API Reference](api/core.md) for technical details
- Visit the [GitHub repository](https://github.com/AndrewJapx/FacadeInspection_Software) for issues and discussions

---

*Last updated: October 2025*