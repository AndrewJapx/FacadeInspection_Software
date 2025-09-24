

import os
from datetime import date
import json
from config.status import STATUS_OPTIONS
import boto3

# Recommended: store all finding photos in this directory for traceability
PHOTOS_DIR = os.path.join(os.path.dirname(__file__), "..", "photos")
os.makedirs(PHOTOS_DIR, exist_ok=True)

master_findings = [
    {
        "id": 1,
        "title": "Crack in wall",
        # description removed
        "status": STATUS_OPTIONS[0],
        "color": "#d32f2f",
        "category": "Defect",
        "assignee": "Inspector A",
        "drop": "Tag1",
        "start_date": date(2025, 9, 1),
        "end_date": None,
        "photos": [
            # Example: os.path.join(PHOTOS_DIR, "finding1_photo1.jpg")
        ],
        "material": "Stone",
        "defect": "Crack",
        "elevation": "Elevation 1",  # Example value
    },
    {
        "id": 2,
        "title": "Loose panel",
        # description removed
        "status": STATUS_OPTIONS[1] if len(STATUS_OPTIONS) > 1 else STATUS_OPTIONS[0],
        "color": "#1976d2",
        "category": "Defect",
        "assignee": "Inspector B",
        "drop": "Tag2",
        "start_date": date(2025, 9, 5),
        "end_date": None,
        "photos": [],
        "material": "Stone",
        "defect": "Crack",
        "elevation": "Elevation 2",  # Example value
    },
    {
        "id": 3,
        "title": "Water stain",
        # description removed
        "status": STATUS_OPTIONS[2] if len(STATUS_OPTIONS) > 2 else STATUS_OPTIONS[0],
        "color": "#ffe082",
        "category": "Observation",
        "assignee": "Inspector C",
        "drop": "Tag3",
        "start_date": date(2025, 8, 20),
        "end_date": date(2025, 9, 10),
        "photos": [],
        "material": "Stone",
        "defect": "Spall",
        "elevation": "Elevation 3",  # Example value
    },
    # Add more findings as needed
]

def add_finding_from_pin(pin):
    """
    Create a new finding from a pin dict and add it to master_findings.
    Fields not present in pin will default to empty or None.
    Status will be validated against STATUS_OPTIONS.
    Elevation will be traced from pin if present, else empty string.
    """
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

# Example usage:
# pin = {"name": "New Pin", "material": "Steel", "defect": "Rust"}
# add_finding_from_pin(pin)


import pathlib
# --- Persistent storage for master_findings ---
# Always resolve storage at workspace root (two levels up from this file)
WORKSPACE_ROOT = pathlib.Path(__file__).resolve().parents[2]
STORAGE_DIR = os.path.join(WORKSPACE_ROOT, "storage")
os.makedirs(STORAGE_DIR, exist_ok=True)
MASTER_FINDINGS_PATH = os.path.join(STORAGE_DIR, "master_findings.json")

def save_master_findings():
    """
    Save master_findings to storage/master_findings.json.
    Dates are converted to ISO format strings.
    Also uploads master_findings.json to S3 (LocalStack or AWS).
    """
    def serialize_finding(f):
        f = f.copy()
        if isinstance(f.get("start_date"), date):
            f["start_date"] = f["start_date"].isoformat()
        if isinstance(f.get("end_date"), date):
            f["end_date"] = f["end_date"].isoformat() if f["end_date"] else None
        return f
    with open(MASTER_FINDINGS_PATH, "w", encoding="utf-8") as fp:
        json.dump([serialize_finding(f) for f in master_findings], fp, indent=2)
    upload_master_findings_to_s3()

def upload_master_findings_to_s3(bucket_name="facade-inspection", object_name="master_findings.json"):
    """
    Uploads master_findings.json to S3 bucket (LocalStack or AWS).
    Assumes LocalStack is running at endpoint_url=http://localhost:4566.
    """
    s3 = boto3.client(
        "s3",
        endpoint_url="http://localhost:4566",  # Change to AWS endpoint for production
        aws_access_key_id="test",
        aws_secret_access_key="test",
        region_name="us-east-1"
    )
    # Ensure bucket exists
    try:
        s3.head_bucket(Bucket=bucket_name)
    except Exception:
        s3.create_bucket(Bucket=bucket_name)
    # Upload file
    s3.upload_file(MASTER_FINDINGS_PATH, bucket_name, object_name)

def load_master_findings():
    """
    Load master_findings from storage/master_findings.json.
    Dates are parsed from ISO format strings.
    """
    global master_findings
    if not os.path.exists(MASTER_FINDINGS_PATH):
        return
    def parse_date(d):
        if d:
            try:
                return date.fromisoformat(d)
            except Exception:
                return d
        return None
    with open(MASTER_FINDINGS_PATH, "r", encoding="utf-8") as fp:
        findings = json.load(fp)
        for f in findings:
            f["start_date"] = parse_date(f.get("start_date"))
            f["end_date"] = parse_date(f.get("end_date"))
        master_findings = findings
