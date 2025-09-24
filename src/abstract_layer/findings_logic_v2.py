"""
Updated findings_logic.py using the storage abstraction layer.
Can work with both local files and S3 (LocalStack/AWS).
"""

import os
import json
from typing import List, Dict, Any, Optional
from .storage_backend import storage

def get_project_storage_path(project_name: str) -> str:
    """Get the storage path for a project (works with both local and S3)"""
    if not project_name or not isinstance(project_name, str):
        raise ValueError("project_name must be a non-empty string.")
    return f"{project_name}/"

def get_pins_path(project_name: str) -> str:
    """Get path to pins file for the project"""
    return f"{project_name}/pins.json"

def get_project_config_path(project_name: str) -> str:
    """Get path to project config file"""
    return f"{project_name}/project.json"

def get_master_findings_path() -> str:
    """Get path to master findings file"""
    return "master_findings.json"

# --- Pin Storage Logic ---
def load_pins(project_name: str) -> List[Dict[str, Any]]:
    """Load pins from storage (local or S3)"""
    if not project_name or not isinstance(project_name, str):
        raise ValueError("project_name must be a non-empty string.")
    
    pins_path = get_pins_path(project_name)
    pins = storage.load_json(pins_path)
    
    if pins is None:
        # File doesn't exist, create empty pins file
        storage.save_json(pins_path, [])
        return []
    
    # Validate and convert pins
    if not isinstance(pins, list):
        print(f"[ERROR] Invalid pins data for {project_name}, resetting to empty list")
        storage.save_json(pins_path, [])
        return []
    
    # Convert pin positions to QPointF for UI use
    try:
        from PySide6.QtCore import QPointF
        for pin in pins:
            pos = pin.get('pos')
            if isinstance(pos, dict) and 'x' in pos and 'y' in pos:
                pin['pos'] = QPointF(pos['x'], pos['y'])
    except ImportError:
        pass
    
    return pins

def save_pins(pins: List[Dict[str, Any]], project_name: str) -> bool:
    """Save pins to storage (local or S3)"""
    if not project_name or not isinstance(project_name, str):
        raise ValueError("project_name must be a non-empty string.")
    
    # Convert QPointF to dict for all pins before saving
    pins_to_save = []
    for pin in pins:
        pin_copy = pin.copy()
        pos = pin_copy.get("pos")
        
        # Convert QPointF to dict if needed
        try:
            from PySide6.QtCore import QPointF
            if isinstance(pos, QPointF):
                pin_copy["pos"] = {"x": pos.x(), "y": pos.y()}
        except ImportError:
            pass
        
        pins_to_save.append(pin_copy)
    
    pins_path = get_pins_path(project_name)
    return storage.save_json(pins_path, pins_to_save)

def create_pin(pin_data: Dict[str, Any], elevation_name: str = None, project_name: str = None) -> Dict[str, Any]:
    """Create a new pin with unique ID"""
    if not project_name or not isinstance(project_name, str):
        raise ValueError("project_name must be a non-empty string.")
    
    required_fields = ["pos", "name", "defect", "material"]
    for field in required_fields:
        if field not in pin_data or pin_data[field] in (None, "", []):
            raise ValueError(f"Pin data missing required field: '{field}'")
    
    pins = load_pins(project_name)
    next_id = max([p.get("pin_id", 0) for p in pins], default=100) + 1
    
    pin = pin_data.copy()
    pin["pin_id"] = next_id
    if elevation_name:
        pin["elevation"] = elevation_name
    
    pins.append(pin)
    save_pins(pins, project_name)
    return pin

def add_pin_to_master_findings(pin: Dict[str, Any], elevation_name: str = None, project_name: str = None) -> Any:
    """Add pin to master findings with duplicate prevention"""
    if not project_name or not isinstance(project_name, str):
        raise ValueError("project_name must be a non-empty string.")
    
    # Check for existing pin at same position and elevation
    pins = load_pins(project_name)
    pin_pos = pin.get("pos")
    current_elevation = elevation_name or pin.get("elevation")
    
    # Convert QPointF to comparable values
    try:
        from PySide6.QtCore import QPointF
        if isinstance(pin_pos, QPointF):
            pos_x, pos_y = pin_pos.x(), pin_pos.y()
        else:
            pos_x, pos_y = pin_pos.get("x", 0), pin_pos.get("y", 0)
    except ImportError:
        pos_x, pos_y = pin_pos.get("x", 0), pin_pos.get("y", 0)
    
    # Check for duplicates
    for existing_pin in pins:
        existing_pos = existing_pin.get("pos")
        existing_elevation = existing_pin.get("elevation")
        
        try:
            if isinstance(existing_pos, dict):
                ex_x, ex_y = existing_pos.get("x", 0), existing_pos.get("y", 0)
            else:
                ex_x, ex_y = existing_pos.x(), existing_pos.y()
                
            if (abs(ex_x - pos_x) < 1e-6 and abs(ex_y - pos_y) < 1e-6 and 
                existing_elevation == current_elevation):
                # Update existing pin
                existing_pin.update({
                    'name': pin.get('name', existing_pin.get('name')),
                    'status': pin.get('status', existing_pin.get('status')),
                    'material': pin.get('material', existing_pin.get('material')),
                    'defect': pin.get('defect', existing_pin.get('defect')),
                    'chat': pin.get('chat', existing_pin.get('chat', []))
                })
                save_pins(pins, project_name)
                return existing_pin.get("finding_id")
        except (AttributeError, TypeError):
            continue
    
    # Create new pin and add to master findings
    if "pin_id" not in pin:
        pin = create_pin(pin, elevation_name, project_name)
    
    pin_data = pin.copy()
    if elevation_name:
        pin_data['elevation'] = elevation_name
    
    # Add to master findings
    finding = add_finding_from_pin(pin_data)
    finding_id = finding.get("id")
    pin["finding_id"] = finding_id
    
    # Update pin with finding_id
    pins = load_pins(project_name)
    for p in pins:
        if p.get("pin_id") == pin["pin_id"]:
            p["finding_id"] = finding_id
    save_pins(pins, project_name)
    save_master_findings()
    return finding

# --- Master Findings Integration ---
def add_finding_from_pin(pin: Dict[str, Any]) -> Dict[str, Any]:
    """Create a finding from pin data"""
    # Import here to avoid circular imports
    import sys
    sys.path.append(os.path.dirname(os.path.dirname(__file__)))
    from config.status import STATUS_OPTIONS
    
    master_findings = load_master_findings()
    
    status = pin.get("status", STATUS_OPTIONS[0])
    if status not in STATUS_OPTIONS:
        status = STATUS_OPTIONS[0]
    
    new_finding = {
        "id": max([f["id"] for f in master_findings], default=0) + 1,
        "title": pin.get("name", "Untitled Finding"),
        "status": status,
        "color": pin.get("color", "#d32f2f"),
        "category": pin.get("category", "Defect"),
        "assignee": pin.get("assignee", ""),
        "drop": pin.get("drop", ""),
        "start_date": pin.get("start_date", None),
        "end_date": pin.get("end_date", None),
        "photos": pin.get("photos", []),
        "material": pin.get("material", ""),
        "defect": pin.get("defect", ""),
        "elevation": pin.get("elevation", ""),
    }
    
    master_findings.append(new_finding)
    return new_finding

def load_master_findings() -> List[Dict[str, Any]]:
    """Load master findings from storage"""
    findings = storage.load_json(get_master_findings_path())
    return findings if findings is not None else []

def save_master_findings(findings: List[Dict[str, Any]] = None):
    """Save master findings to storage"""
    if findings is None:
        # If no findings provided, we need to get them from the global list
        # This maintains compatibility with existing code
        try:
            import sys
            sys.path.append(os.path.dirname(os.path.dirname(__file__)))
            from Project.master_findings import master_findings as global_findings
            findings = global_findings
        except ImportError:
            findings = []
    
    return storage.save_json(get_master_findings_path(), findings)

# --- Project Management ---
def load_project_config(project_name: str) -> Optional[Dict[str, Any]]:
    """Load project configuration"""
    config_path = get_project_config_path(project_name)
    return storage.load_json(config_path)

def save_project_config(project_name: str, config: Dict[str, Any]) -> bool:
    """Save project configuration"""
    config_path = get_project_config_path(project_name)
    return storage.save_json(config_path, config)

def list_all_projects() -> List[str]:
    """List all available projects"""
    return storage.list_projects()

def delete_project(project_name: str) -> bool:
    """Delete entire project"""
    project_path = get_project_storage_path(project_name)
    return storage.delete(project_path)

# --- Migration helpers ---
def migrate_to_s3():
    """Migrate from local storage to S3"""
    print("Migration functionality would go here...")
    # Implementation would copy all local files to S3

def switch_storage_backend(backend: str):
    """Switch storage backend"""
    global storage
    from .storage_backend import STORAGE_CONFIG, get_storage_backend
    
    STORAGE_CONFIG['backend'] = backend
    storage = get_storage_backend()
    print(f"Switched to {backend} storage backend")

# Example usage:
if __name__ == "__main__":
    # Test the abstraction layer
    print("Testing storage abstraction...")
    
    # Test with local storage
    switch_storage_backend('local')
    projects = list_all_projects()
    print(f"Local projects: {projects}")
    
    # Test with S3 storage
    try:
        switch_storage_backend('s3')
        projects = list_all_projects()
        print(f"S3 projects: {projects}")
    except Exception as e:
        print(f"S3 not available: {e}")
        switch_storage_backend('local')