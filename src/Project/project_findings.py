"""
Project-specific findings management.
Each project has its own findings.json file, no more global master_findings.
"""

import os
import json
from datetime import date
from typing import List, Dict, Any, Optional
from config.status import STATUS_OPTIONS

def get_project_findings_path(project_name: str) -> str:
    """Get path to project-specific findings.json file"""
    if not project_name or not isinstance(project_name, str):
        raise ValueError("project_name must be a non-empty string.")
    
    base_dir = os.path.join("c:\\Users\\andre\\OneDrive\\Documents\\FacadeInspection_Software", "storage", project_name)
    os.makedirs(base_dir, exist_ok=True)
    return os.path.join(base_dir, "findings.json")

def load_project_findings(project_name: str) -> List[Dict[str, Any]]:
    """Load findings for a specific project"""
    findings_path = get_project_findings_path(project_name)
    
    if not os.path.exists(findings_path):
        # Create empty findings file
        save_project_findings(project_name, [])
        return []
    
    try:
        with open(findings_path, "r", encoding="utf-8") as fp:
            findings = json.load(fp)
            
        # Parse dates
        for finding in findings:
            if finding.get("start_date"):
                try:
                    finding["start_date"] = date.fromisoformat(finding["start_date"])
                except:
                    finding["start_date"] = None
            if finding.get("end_date"):
                try:
                    finding["end_date"] = date.fromisoformat(finding["end_date"])
                except:
                    finding["end_date"] = None
        
        return findings
        
    except (json.JSONDecodeError, Exception) as e:
        print(f"[ERROR] Failed to load findings for {project_name}: {e}")
        return []

def save_project_findings(project_name: str, findings: List[Dict[str, Any]]) -> bool:
    """Save findings for a specific project"""
    findings_path = get_project_findings_path(project_name)
    
    try:
        # Serialize dates
        findings_to_save = []
        for finding in findings:
            finding_copy = finding.copy()
            if isinstance(finding_copy.get("start_date"), date):
                finding_copy["start_date"] = finding_copy["start_date"].isoformat()
            if isinstance(finding_copy.get("end_date"), date):
                finding_copy["end_date"] = finding_copy["end_date"].isoformat() if finding_copy["end_date"] else None
            findings_to_save.append(finding_copy)
        
        with open(findings_path, "w", encoding="utf-8") as fp:
            json.dump(findings_to_save, fp, indent=2)
        
        print(f"[INFO] Saved {len(findings)} findings for project {project_name}")
        return True
        
    except Exception as e:
        print(f"[ERROR] Failed to save findings for {project_name}: {e}")
        return False

def add_finding_to_project(project_name: str, pin_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Add a finding to a specific project's findings.json based on pin data.
    Returns the created finding.
    """
    findings = load_project_findings(project_name)
    
    # Check if finding already exists for this pin_id
    pin_id = pin_data.get("pin_id")
    if pin_id:
        for finding in findings:
            if finding.get("pin_id") == pin_id:
                # Update existing finding
                finding.update({
                    "title": pin_data.get("name", finding.get("title", "Untitled Finding")),
                    "status": pin_data.get("status", finding.get("status")),
                    "material": pin_data.get("material", finding.get("material", "")),
                    "defect": pin_data.get("defect", finding.get("defect", "")),
                    "elevation": pin_data.get("elevation", finding.get("elevation", "")),
                })
                save_project_findings(project_name, findings)
                print(f"[INFO] Updated finding {finding['id']} for pin {pin_id} in project {project_name}")
                return finding
    
    # Create new finding
    next_id = max([f.get("id", 0) for f in findings], default=0) + 1
    
    # Validate status
    status = pin_data.get("status", STATUS_OPTIONS[0])
    if status not in STATUS_OPTIONS:
        status = STATUS_OPTIONS[0]
    
    new_finding = {
        "id": next_id,
        "title": pin_data.get("name", "Untitled Finding"),
        "status": status,
        "color": pin_data.get("color", "#d32f2f"),
        "category": pin_data.get("category", "Defect"),
        "assignee": pin_data.get("assignee", ""),
        "drop": pin_data.get("drop", ""),
        "start_date": pin_data.get("start_date", None),
        "end_date": pin_data.get("end_date", None),
        "photos": pin_data.get("photos", []),
        "material": pin_data.get("material", ""),
        "defect": pin_data.get("defect", ""),
        "elevation": pin_data.get("elevation", ""),
        "pin_id": pin_id,
    }
    
    findings.append(new_finding)
    save_project_findings(project_name, findings)
    
    print(f"[INFO] Created finding {new_finding['id']} for pin {pin_id} in project {project_name}")
    return new_finding

def get_findings_by_status(project_name: str) -> Dict[str, List[Dict[str, Any]]]:
    """
    Group project findings by status for the kanban board.
    Returns dict with status as keys and list of findings as values.
    """
    findings = load_project_findings(project_name)
    
    # Group by status
    findings_by_status = {status: [] for status in STATUS_OPTIONS}
    findings_by_status['Other'] = []
    
    for finding in findings:
        status = finding.get('status', STATUS_OPTIONS[0]) or STATUS_OPTIONS[0]
        if status in findings_by_status:
            findings_by_status[status].append(finding)
        else:
            findings_by_status['Other'].append(finding)
    
    return findings_by_status

def get_material_defect_summary(project_name: str) -> Dict[tuple, int]:
    """
    Get summary of material/defect pairs for sidebar display.
    Returns dict with (material, defect) tuples as keys and counts as values.
    Now uses pins directly since that's where all the findings data is stored.
    """
    from collections import Counter
    pair_counts = Counter()
    
    try:
        # Load pins directly since they contain the material/defect information
        from Project.Elevations.findings_logic import load_pins
        pins = load_pins(project_name)
        
        for pin in pins:
            material = pin.get('material', '').strip()
            defect = pin.get('defect', '').strip()
            if material and defect:
                pair_counts[(material, defect)] += 1
        
        print(f"[DEBUG] get_material_defect_summary for {project_name}: {dict(pair_counts)}")
        
    except Exception as e:
        print(f"[ERROR] Failed to load pins for material/defect summary: {e}")
        # Fallback to findings if pins fail
        findings = load_project_findings(project_name)
        for finding in findings:
            material = finding.get('material', '').strip()
            defect = finding.get('defect', '').strip()
            if material and defect:
                pair_counts[(material, defect)] += 1
    
    return dict(pair_counts)

def delete_finding_from_project(project_name: str, finding_id: int) -> bool:
    """Delete a finding from project"""
    findings = load_project_findings(project_name)
    
    # Find and remove the finding
    for i, finding in enumerate(findings):
        if finding.get("id") == finding_id:
            findings.pop(i)
            save_project_findings(project_name, findings)
            print(f"[INFO] Deleted finding {finding_id} from project {project_name}")
            return True
    
    print(f"[WARNING] Finding {finding_id} not found in project {project_name}")
    return False

def migrate_master_findings_to_project(project_name: str):
    """
    One-time migration: Move relevant findings from master_findings to project-specific findings.
    Only migrates findings that have pin_id matching pins in the project.
    """
    from Project.Elevations.findings_logic import load_pins
    
    # Load project pins to see which findings belong to this project
    pins = load_pins(project_name)
    project_pin_ids = {pin.get("pin_id") for pin in pins if pin.get("pin_id")}
    
    if not project_pin_ids:
        print(f"[INFO] No pins found for project {project_name}, skipping migration")
        return
    
    # Load global master findings
    try:
        master_findings_path = os.path.join("c:\\Users\\andre\\OneDrive\\Documents\\FacadeInspection_Software", "storage", "master_findings.json")
        if os.path.exists(master_findings_path):
            with open(master_findings_path, "r", encoding="utf-8") as fp:
                master_findings = json.load(fp)
        else:
            print("[INFO] No master_findings.json found, skipping migration")
            return
    except Exception as e:
        print(f"[ERROR] Failed to load master findings: {e}")
        return
    
    # Find findings that belong to this project
    project_findings = []
    for finding in master_findings:
        finding_pin_id = finding.get("pin_id")
        if finding_pin_id in project_pin_ids:
            project_findings.append(finding)
    
    if project_findings:
        # Save to project-specific findings
        save_project_findings(project_name, project_findings)
        print(f"[INFO] Migrated {len(project_findings)} findings to project {project_name}")
    else:
        print(f"[INFO] No findings to migrate for project {project_name}")

# Example usage and testing
if __name__ == "__main__":
    test_project = "test0124092025_PRJ3105"
    
    print(f"Testing project-specific findings for: {test_project}")
    
    # Test loading
    findings = load_project_findings(test_project)
    print(f"Current findings: {len(findings)}")
    
    # Test grouping by status
    by_status = get_findings_by_status(test_project)
    for status, status_findings in by_status.items():
        if status_findings:
            print(f"  {status}: {len(status_findings)} findings")
    
    # Test material/defect summary
    summary = get_material_defect_summary(test_project)
    print(f"Material/Defect pairs: {len(summary)}")
    for (material, defect), count in summary.items():
        print(f"  {material} - {defect}: {count}")