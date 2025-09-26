"""
Template loader utility to integrate templates with the pin/finding system
"""
import os
import json
from typing import Dict, List, Any, Optional

class TemplateLoader:
    """Loads and manages templates for categories, materials, defects, and statuses"""
    
    def __init__(self):
        self.templates_dir = os.path.abspath(os.path.join(
            os.path.dirname(__file__), '..', '..', 'templates'
        ))
        self.current_template = None
        self.template_data = None
    
    def get_available_templates(self) -> List[str]:
        """Get list of available template names"""
        templates = []
        if os.path.exists(self.templates_dir):
            for filename in os.listdir(self.templates_dir):
                if filename.endswith('.json'):
                    templates.append(filename[:-5])  # Remove .json extension
        return templates
    
    def load_template(self, template_name: str) -> bool:
        """Load a specific template"""
        template_file = os.path.join(self.templates_dir, f"{template_name}.json")
        if not os.path.exists(template_file):
            return False
        
        try:
            with open(template_file, 'r', encoding='utf-8') as f:
                self.template_data = json.load(f)
            self.current_template = template_name
            return True
        except Exception as e:
            print(f"[ERROR] Failed to load template {template_name}: {e}")
            return False
    
    def get_statuses(self) -> Dict[str, Dict[str, Any]]:
        """Get status options from current template"""
        if not self.template_data:
            return {}
        return self.template_data.get('statuses', {})
    
    def get_materials(self) -> Dict[str, Dict[str, Any]]:
        """Get material options from current template"""
        if not self.template_data:
            return {}
        return self.template_data.get('materials', {})
    
    def get_defects(self) -> Dict[str, Dict[str, Any]]:
        """Get defect options from current template"""
        if not self.template_data:
            return {}
        return self.template_data.get('defects', {})
    
    def get_material_defects(self, material_name: str) -> List[str]:
        """Get defects associated with a specific material"""
        materials = self.get_materials()
        material_data = materials.get(material_name, {})
        return material_data.get('defects', [])
    
    def get_status_color(self, status_name: str) -> str:
        """Get color for a specific status"""
        statuses = self.get_statuses()
        status_data = statuses.get(status_name, {})
        return status_data.get('color', '#cccccc')
    
    def get_category_options_for_pin_dialog(self) -> Dict[str, List[str]]:
        """
        Get category options in the format expected by pin dialogs.
        Returns a dictionary with materials as keys and their defects as values.
        """
        materials = self.get_materials()
        category_options = {}
        
        for material_name, material_data in materials.items():
            defects = material_data.get('defects', [])
            category_options[material_name] = defects
        
        # If no template is loaded, fall back to master list
        if not category_options:
            category_options = self.get_master_list_categories()
        
        return category_options
    
    def get_status_options_for_pin_dialog(self) -> List[str]:
        """Get status options as a list for pin dialogs"""
        statuses = self.get_statuses()
        status_list = list(statuses.keys())
        
        # If no template is loaded, fall back to master list
        if not status_list:
            master_data = self.load_master_list()
            status_list = list(master_data.get('statuses', {}).keys())
        
        return status_list
    
    def get_status_colors_dict(self) -> Dict[str, str]:
        """Get status colors in the format expected by the existing system"""
        statuses = self.get_statuses()
        colors = {}
        for status_name, status_data in statuses.items():
            colors[status_name] = status_data.get('color', '#cccccc')
        
        # If no template is loaded, fall back to master list
        if not colors:
            colors = self.get_master_list_statuses()
        
        return colors
    
    def create_default_template(self, template_name: str) -> bool:
        """Create a default template with some basic categories"""
        default_template = {
            "statuses": {
                "Unsafe": {
                    "color": "#d32f2f",
                    "description": "Immediate safety concern requiring urgent attention"
                },
                "Pre-con": {
                    "color": "#1976d2",
                    "description": "Pre-construction phase item"
                },
                "Require Repair": {
                    "color": "#ffe082",
                    "description": "Needs repair but not urgent"
                },
                "Completed Before Last Week": {
                    "color": "#ef5350",
                    "description": "Work completed before last week"
                },
                "For Verification": {
                    "color": "#ff9800",
                    "description": "Requires verification of completion"
                },
                "Completed Last Week": {
                    "color": "#43a047",
                    "description": "Work completed within the last week"
                },
                "Verified": {
                    "color": "#81d4fa",
                    "description": "Work completed and verified"
                }
            },
            "materials": {
                "Stone": {
                    "defects": ["Crack", "Spall", "Discoloration", "Efflorescence", "Other Stone Defect"],
                    "description": "Natural stone materials including granite, limestone, marble, etc."
                },
                "Window": {
                    "defects": ["Broken Glass", "Seal Failure", "Frame Corrosion", "Air/Water Leak", "Other Window Defect"],
                    "description": "Window systems including frames, glass, and sealing components"
                },
                "Metal Panel": {
                    "defects": ["Corrosion", "Loose Panel", "Denting", "Other Metal Defect"],
                    "description": "Metal cladding panels and related components"
                },
                "Sealant": {
                    "defects": ["Cracking", "Loss of Adhesion", "Loss of Cohesion", "Other Sealant Defect"],
                    "description": "Sealant materials used for weatherproofing"
                },
                "Other": {
                    "defects": ["General Defect", "Observation", "Info", "Other"],
                    "description": "Other materials or general observations"
                }
            },
            "defects": {
                "Crack": {
                    "severity": "High",
                    "description": "Structural or surface cracking"
                },
                "Spall": {
                    "severity": "High",
                    "description": "Material spalling or breaking away"
                },
                "Discoloration": {
                    "severity": "Low",
                    "description": "Color changes in material"
                },
                "Efflorescence": {
                    "severity": "Medium",
                    "description": "White salt deposits on surface"
                },
                "Broken Glass": {
                    "severity": "High",
                    "description": "Cracked or broken glass panels"
                },
                "Seal Failure": {
                    "severity": "Medium",
                    "description": "Failure of sealing materials"
                },
                "Frame Corrosion": {
                    "severity": "High",
                    "description": "Corrosion of window or door frames"
                },
                "Air/Water Leak": {
                    "severity": "High",
                    "description": "Leakage of air or water through openings"
                },
                "Corrosion": {
                    "severity": "High",
                    "description": "Metal oxidation and deterioration"
                },
                "Loose Panel": {
                    "severity": "High",
                    "description": "Panel not properly secured"
                },
                "Denting": {
                    "severity": "Medium",
                    "description": "Physical damage causing indentations"
                },
                "Cracking": {
                    "severity": "Medium",
                    "description": "Cracks in sealant material"
                },
                "Loss of Adhesion": {
                    "severity": "High",
                    "description": "Sealant separating from substrate"
                },
                "Loss of Cohesion": {
                    "severity": "High",
                    "description": "Sealant material breaking down internally"
                },
                "General Defect": {
                    "severity": "Medium",
                    "description": "General deficiency or issue"
                },
                "Observation": {
                    "severity": "Low",
                    "description": "General observation or note"
                },
                "Info": {
                    "severity": "Low",
                    "description": "Informational item"
                },
                "Other": {
                    "severity": "Medium",
                    "description": "Other unspecified defect or issue"
                }
            }
        }
        
        os.makedirs(self.templates_dir, exist_ok=True)
        template_file = os.path.join(self.templates_dir, f"{template_name}.json")
        
        try:
            with open(template_file, 'w', encoding='utf-8') as f:
                json.dump(default_template, f, indent=2)
            
            self.template_data = default_template
            self.current_template = template_name
            return True
        except Exception as e:
            print(f"[ERROR] Failed to create default template: {e}")
            return False
    
    def load_master_list(self) -> Dict[str, Any]:
        """Load the master list data"""
        master_file = os.path.join(self.templates_dir, 'master_list.json')
        if os.path.exists(master_file):
            try:
                with open(master_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                print(f"[ERROR] Failed to load master list: {e}")
        return {'statuses': {}, 'materials': {}, 'defects': {}}
    
    def get_master_list_categories(self) -> Dict[str, List[str]]:
        """Get category options from master list"""
        master_data = self.load_master_list()
        materials = master_data.get('materials', {})
        category_options = {}
        
        for material_name, material_data in materials.items():
            defects = material_data.get('defects', [])
            category_options[material_name] = defects
        
        return category_options
    
    def get_master_list_statuses(self) -> Dict[str, str]:
        """Get status colors from master list"""
        master_data = self.load_master_list()
        statuses = master_data.get('statuses', {})
        colors = {}
        
        for status_name, status_data in statuses.items():
            colors[status_name] = status_data.get('color', '#cccccc')
        
        return colors

# Global template loader instance
template_loader = TemplateLoader()

def get_template_loader() -> TemplateLoader:
    """Get the global template loader instance"""
    return template_loader

def load_default_template_if_needed():
    """Load a default template if no templates exist"""
    available_templates = template_loader.get_available_templates()
    if not available_templates:
        # Check if master list exists and has data
        master_data = template_loader.load_master_list()
        if (master_data.get('statuses') or master_data.get('materials') or master_data.get('defects')):
            # Master list has data, create a default template from it
            template_loader.template_data = master_data
            template_loader.current_template = "Default (from Master List)"
        else:
            # Create and load default template
            template_loader.create_default_template("Default")
    else:
        # Load the first available template
        template_loader.load_template(available_templates[0])