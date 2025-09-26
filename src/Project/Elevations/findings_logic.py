# findings_logic.py
# Abstracts pin info and adds it to the master findings list

import os
import json
from Project.master_findings import add_finding_from_pin, save_master_findings

import pathlib
def get_project_storage_dir(project_name):
    """
    Returns the absolute path to the storage subfolder for the given project name.
    Creates the folder if it does not exist.
    Raises ValueError if project_name is None.
    """
    if not project_name or not isinstance(project_name, str):
        raise ValueError("project_name must be a non-empty string.")
    # Always resolve storage at FacadeInspection_Software/storage/<project_name>
    # This is absolute, not relative to workspace root
    base_dir = os.path.join("c:\\Users\\andre\\OneDrive\\Documents\\FacadeInspection_Software", "storage", project_name)
    os.makedirs(base_dir, exist_ok=True)
    return base_dir

def get_pins_path(project_name):
    """Get path to the shared pins.json file."""
    return os.path.join(get_project_storage_dir(project_name), "pins.json")

    # ...existing code...


# --- Pin Storage Logic ---
def load_pins(project_name):
    """Load pins from the shared pins.json file."""
    if not project_name or not isinstance(project_name, str):
        raise ValueError("project_name must be a non-empty string.")
    pins_path = get_pins_path(project_name)
    # Validate pins.json contents before loading
    if not os.path.exists(pins_path):
        with open(pins_path, "w", encoding="utf-8") as fp:
            json.dump([], fp)
        return []
    with open(pins_path, "r", encoding="utf-8") as fp:
        try:
            pins = json.load(fp)
            # Validate pins: must be a list of dicts with 'pos' as dict with x/y
            if not isinstance(pins, list):
                raise ValueError("pins.json must be a list")
            for pin in pins:
                if not isinstance(pin, dict):
                    raise ValueError("Each pin must be a dict")
                pos = pin.get("pos")
                if not isinstance(pos, dict) or "x" not in pos or "y" not in pos:
                    raise ValueError("Pin 'pos' must be a dict with 'x' and 'y'")
            # Convert pin['pos'] dicts to QPointF for UI use
            try:
                from PySide6.QtCore import QPointF
                for pin in pins:
                    pos = pin.get('pos')
                    if isinstance(pos, dict) and 'x' in pos and 'y' in pos:
                        pin['pos'] = QPointF(pos['x'], pos['y'])
            except ImportError:
                pass
            return pins
        except (json.JSONDecodeError, ValueError) as e:
            print(f"[ERROR] Invalid pins.json: {e}. Resetting to empty array.")
            with open(pins_path, "w", encoding="utf-8") as fpw:
                json.dump([], fpw)
            return []

def save_pins(pins, project_name):
    """Save pins to the shared pins.json file."""
    if not project_name or not isinstance(project_name, str):
        raise ValueError("project_name must be a non-empty string.")
    pins_path = get_pins_path(project_name)
    # Convert QPointF to dict for all pins before saving
    for pin in pins:
        pos = pin.get("pos")
        # Only convert if it's a QPointF (avoid double conversion)
        try:
            from PySide6.QtCore import QPointF
            if isinstance(pos, QPointF):
                pin["pos"] = {"x": pos.x(), "y": pos.y()}
        except ImportError:
            # If PySide6 not available, skip conversion
            pass
    with open(pins_path, "w", encoding="utf-8") as fp:
        json.dump(pins, fp, indent=2)

# --- Pin Creation and Linking ---
def create_pin(pin_data, elevation_name=None, project_name=None):
    """
    Create a new pin, assign a unique pin_id, and store it in the project's pins.json.
    Optionally set elevation_name.
    Returns the pin dict with pin_id.
    Raises ValueError if project_name is None.
    """
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

# --- Pin to Finding Linking ---
def add_pin_to_project_findings(pin, elevation_name=None, project_name=None):
    """
    Abstracts all info from a pin and adds it to the project-specific findings.json.
    Optionally sets the elevation name.
    Also links the finding to the pin by storing pin_id in the finding and finding_id in the pin.
    Requires project_name to store pins in the correct folder.
    Raises ValueError if project_name is None.
    Prevents duplicate pins by checking position and elevation.
    """
    if not project_name or not isinstance(project_name, str):
        raise ValueError("project_name must be a non-empty string.")
    
    # Check for existing pin at same position and elevation to prevent duplicates
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
    
    # Check for existing pin at same location and elevation
    for existing_pin in pins:
        existing_pos = existing_pin.get("pos")
        existing_elevation = existing_pin.get("elevation")
        
        # Compare positions (with small tolerance for floating point)
        try:
            if isinstance(existing_pos, dict):
                ex_x, ex_y = existing_pos.get("x", 0), existing_pos.get("y", 0)
            else:
                ex_x, ex_y = existing_pos.x(), existing_pos.y()
                
            if (abs(ex_x - pos_x) < 1e-6 and abs(ex_y - pos_y) < 1e-6 and 
                existing_elevation == current_elevation):
                # Pin already exists, update it instead of creating duplicate
                existing_pin.update({
                    'name': pin.get('name', existing_pin.get('name')),
                    'status': pin.get('status', existing_pin.get('status')),
                    'material': pin.get('material', existing_pin.get('material')),
                    'defect': pin.get('defect', existing_pin.get('defect')),
                    'chat': pin.get('chat', existing_pin.get('chat', []))
                })
                save_pins(pins, project_name)
                print(f"[INFO] Updated existing pin at ({pos_x:.3f}, {pos_y:.3f}) in {current_elevation}")
                return existing_pin.get("finding_id")
        except (AttributeError, TypeError):
            continue
    
    # No duplicate found, create new pin if it doesn't have pin_id
    if "pin_id" not in pin:
        pin = create_pin(pin, elevation_name, project_name)
        print(f"[INFO] Created new pin with ID {pin['pin_id']}")
    
    # Prepare pin data for finding creation
    pin_data = pin.copy()
    if elevation_name:
        pin_data['elevation'] = elevation_name
        pin['elevation'] = elevation_name  # Also set it in the original pin
    
    # Add to project-specific findings
    from Project.project_findings import add_finding_to_project
    finding = add_finding_to_project(project_name, pin_data)
    finding_id = finding.get("id")
    
    # Update the pin with the finding_id
    pin["finding_id"] = finding_id
    
    # Reload pins and update the specific pin with finding_id
    pins = load_pins(project_name)
    pin_updated = False
    for p in pins:
        if p.get("pin_id") == pin["pin_id"]:
            p["finding_id"] = finding_id
            pin_updated = True
            break
    
    if not pin_updated:
        # Pin not found in list, add it
        pins.append(pin)
        print(f"[INFO] Added pin {pin['pin_id']} to pins list")
    
    # Save the updated pins
    save_pins(pins, project_name)
    
    print(f"[INFO] Linked pin {pin['pin_id']} to finding {finding_id} in project {project_name}")
    return finding

# Keep the old function name for backward compatibility, but redirect to new function
def add_pin_to_master_findings(pin, elevation_name=None, project_name=None):
    """Legacy function name - redirects to add_pin_to_project_findings"""
    return add_pin_to_project_findings(pin, elevation_name, project_name)

# --- Explanation ---
# This module:
# - Stores all pins in pins.json, each with a unique pin_id
# - When a finding is created from a pin, links them by storing pin_id in the finding and finding_id in the pin
# - Provides functions to load/save pins and findings
# - Keeps business logic separate from UI, making the codebase easier to maintain and extend