# MkDocs Documentation Setup

This README provides instructions for setting up MkDocs documentation for your Facade Inspection Software project.

## 📚 What's Been Set Up

I've configured a complete MkDocs documentation system for your project:

### ✅ **Files Created:**
- `mkdocs.yml` - Main MkDocs configuration
- `docs/` directory with initial documentation pages
- `.github/workflows/docs.yml` - GitHub Actions for automated deployment
- `docs-requirements.txt` - Python dependencies for documentation

### ✅ **Current Structure:**
```
docs/
├── index.md                    # Homepage
├── about.md                   # About page
├── getting-started/
│   ├── installation.md       # Installation guide
│   ├── quick-start.md        # Quick start guide
│   └── configuration.md      # Configuration guide
└── user-guide/
    └── overview.md           # User guide overview
```

## 🚀 **Setting up GitHub Pages**

To deploy your documentation to `https://AndrewJapx.github.io/FacadeInspection_Software/`:

### Step 1: Enable GitHub Pages
1. Go to your GitHub repository: `https://github.com/AndrewJapx/FacadeInspection_Software`
2. Click **Settings** tab
3. Scroll down to **Pages** section (left sidebar)
4. Under **Source**, select **GitHub Actions**

### Step 2: Commit and Push Files
```bash
git add .
git commit -m "Add MkDocs documentation setup"
git push origin main
```

### Step 3: GitHub Actions Will Deploy Automatically
- The workflow in `.github/workflows/docs.yml` will trigger
- Documentation will be built and deployed automatically
- Available at: `https://AndrewJapx.github.io/FacadeInspection_Software/`

## 🛠️ **Local Development**

### Prerequisites
```bash
pip install mkdocs mkdocs-material mkdocstrings[python] pymdown-extensions
```

### Serve Locally
```bash
mkdocs serve
```
- Opens at: `http://127.0.0.1:8000`
- Auto-reloads when you edit files

### Build Documentation
```bash
mkdocs build
```

## 📝 **Adding Content**

### Create New Pages
1. Add `.md` files in the `docs/` directory
2. Update the `nav` section in `mkdocs.yml`

### Example - Adding API Documentation:
```bash
# Create directory
mkdir docs/api

# Create file
echo "# API Reference" > docs/api/core.md
```

### Update Navigation in `mkdocs.yml`:
```yaml
nav:
  - Home: index.md
  - API Reference:
    - Core: api/core.md
```

## 🎨 **Customization**

### Theme Options
The Material theme is configured in `mkdocs.yml` with:
- Light/dark mode toggle
- Navigation tabs
- Search functionality
- Code highlighting

### Available Extensions
- Admonitions (callout boxes)
- Code highlighting
- Tables
- Math expressions (KaTeX)
- Mermaid diagrams

## 📚 **Documentation Structure Recommendations**

```
docs/
├── index.md                    # Project overview
├── getting-started/           
│   ├── installation.md       
│   ├── quick-start.md        
│   └── configuration.md      
├── user-guide/               
│   ├── overview.md           
│   ├── project-management.md 
│   ├── elevations.md         
│   ├── findings.md           
│   ├── photos.md             
│   └── templates.md          
├── api/                      
│   ├── core.md               
│   ├── project.md            
│   ├── elevations.md         
│   ├── findings.md           
│   └── aws.md                
├── development/              
│   ├── architecture.md       
│   ├── contributing.md       
│   └── testing.md            
└── about.md                  
```

## 🔧 **Troubleshooting**

### Common Issues:

1. **GitHub Pages not working:**
   - Check repository settings → Pages → Source = "GitHub Actions"
   - Verify workflow file is in `.github/workflows/docs.yml`

2. **Build failures:**
   - Check missing files referenced in `mkdocs.yml` nav
   - Validate YAML syntax in `mkdocs.yml`

3. **Local serving issues:**
   - Ensure all dependencies are installed
   - Check for port conflicts (default: 8000)

### Build Warnings:
Currently, there are warnings about missing pages referenced in navigation. These are normal for initial setup - create the pages as needed.

## 📈 **Next Steps**

1. **Enable GitHub Pages** (see Step 1 above)
2. **Push changes** to trigger first deployment
3. **Add content** to fill out the documentation structure
4. **Customize** theme and styling as needed

## 🆘 **Need Help?**

- [MkDocs Documentation](https://www.mkdocs.org/)
- [Material Theme Docs](https://squidfunk.github.io/mkdocs-material/)
- [GitHub Pages Setup](https://docs.github.com/en/pages/getting-started-with-github-pages)

---

**Your documentation will be live at:** `https://AndrewJapx.github.io/FacadeInspection_Software/`

*Documentation built with ❤️ using MkDocs and Material theme*