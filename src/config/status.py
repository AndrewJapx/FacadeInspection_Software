# Status options and their associated colors for findings/defects
#
# This uses a dictionary to map each status to its color code.
# Usage: color = STATUS_COLORS.get(status, "#cccccc")

STATUS_COLORS = {
    "Unsafe": "#d32f2f",                  # Red
    "Pre-con": "#1976d2",                 # Blue
    "Require Repair": "#ffe082",           # Yellow
    "Completed Before Last Week": "#ef5350", # Light Red
    "For Verification": "#ff9800",         # Orange
    "Completed Last Week": "#43a047",      # Green
    "Verified": "#81d4fa"                 # Light Blue
}

# To get a list of all statuses:
STATUS_OPTIONS = list(STATUS_COLORS.keys())
