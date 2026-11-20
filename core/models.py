"""Lead schema: 24 extraction-only columns."""
COLUMNS = [
    "Lead_ID", "Industry_Tag", "Full_Name", "Role_Title", "Department_Track",
    "Company_Size_Tier", "Outreach_Priority", "Company_Name", "Website_Domain",
    "Email", "Email_Source", "Email_Status", "Phone_Number", "LinkedIn_URL",
    "Location_Country", "Other_Extra_Info", "Source_Platform", "Signal_Category",
    "Exact_Evidence_Snippet", "Website_Audit_Fact", "Source_URL",
    "Person_Fingerprint", "Lead_Score", "QC_Passed_And_Status",
]
TABS = ["Raw_Leads", "Hot_Leads_Ready", "Needs_SMTP_Check", "Master_Dedup_Index", "Do_Not_Contact"]
DEDUP_COLS = ["Person_Fingerprint", "Normalized_Email", "LinkedIn_Slug", "Company_Domain", "Added_On"]
DNC_COLS = ["Value", "Type", "Added_On"]

def blank():
    return {c: "" for c in COLUMNS}

def row(lead):
    return [str(lead.get(c, "")) for c in COLUMNS]
