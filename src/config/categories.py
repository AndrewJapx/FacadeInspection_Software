# Two-layer category options for findings/defects
# First layer: Material (e.g., stone, window, etc.)
# Second layer: Defect type within that material

CATEGORY_OPTIONS = {
    "Stone": [
        "Crack",
        "Spall",
        "Discoloration",
        "Efflorescence",
        "Other Stone Defect"
    ],
    "Window": [
        "Broken Glass",
        "Seal Failure",
        "Frame Corrosion",
        "Air/Water Leak",
        "Other Window Defect"
    ],
    "Metal Panel": [
        "Corrosion",
        "Loose Panel",
        "Denting",
        "Other Metal Defect"
    ],
    "Sealant": [
        "Cracking",
        "Loss of Adhesion",
        "Loss of Cohesion",
        "Other Sealant Defect"
    ],
    "Other": [
        "General Defect",
        "Observation",
        "Info",
        "Other"
    ]
}
