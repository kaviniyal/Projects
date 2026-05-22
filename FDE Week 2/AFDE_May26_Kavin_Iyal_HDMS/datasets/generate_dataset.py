"""
Dataset Generator for Helpdesk Historical Tickets
Generates 270 rows (250 base + 20 intentional duplicates) with realistic
dirty data to demonstrate ETL cleaning capabilities.
"""
import csv
import random
from datetime import datetime, timedelta
import os

random.seed(42)

employees = [
    ("Alice Johnson", "Engineering"), ("Bob Smith", "Marketing"),
    ("Carol Davis", "Sales"), ("David Wilson", "HR"),
    ("Emma Brown", "Finance"), ("Frank Miller", "Operations"),
    ("Grace Lee", "Legal"), ("Henry Taylor", "Customer Support"),
    ("Isabella Anderson", "Engineering"), ("James Thomas", "Marketing"),
    ("Karen Jackson", "Sales"), ("Liam White", "HR"),
    ("Mia Harris", "Finance"), ("Noah Martin", "Operations"),
    ("Olivia Garcia", "Legal"), ("Peter Martinez", "Customer Support"),
    ("Quinn Robinson", "Engineering"), ("Rachel Clark", "Marketing"),
    ("Samuel Rodriguez", "Sales"), ("Tina Lewis", "HR"),
    ("Uma Walker", "Finance"), ("Victor Hall", "Engineering"),
    ("Wendy Allen", "Operations"), ("Xavier Young", "Customer Support"),
    ("Yolanda Hernandez", "Marketing"), ("Zach King", "Sales"),
    ("Aaron Wright", "Engineering"), ("Bella Scott", "HR"),
    ("Carlos Green", "Finance"), ("Diana Baker", "Legal"),
    ("Ethan Adams", "Customer Support"), ("Fiona Nelson", "Engineering"),
    ("George Carter", "Marketing"), ("Hannah Mitchell", "Sales"),
    ("Ian Perez", "HR"), ("Julia Roberts", "Finance"),
    ("Kevin Turner", "Operations"), ("Laura Phillips", "Engineering"),
    ("Michael Campbell", "Customer Support"), ("Nancy Parker", "Marketing"),
]

clean_categories = [
    "VPN Issue", "Password Reset", "Software Installation",
    "Laptop Issue", "Email Access", "Network Connectivity", "Hardware Request"
]

dirty_categories = {
    "VPN Issue": ["VPN", "vpn issue", "VPN Problem", "VPN Issue"],
    "Password Reset": ["pwd reset", "Password reset", "password_reset", "Password Reset"],
    "Software Installation": ["Software Install", "SW Installation", "Software Installation"],
    "Laptop Issue": ["Laptop Problem", "laptop issue", "Laptop Issue"],
    "Email Access": ["Email Problem", "email access", "Email Access"],
    "Network Connectivity": ["Network Issue", "Network Connectivity", "network problem"],
    "Hardware Request": ["HW Request", "Hardware Req", "Hardware Request"],
}

priorities = ["Low", "Medium", "High", "Critical"]
priority_weights = [0.25, 0.40, 0.25, 0.10]

statuses = ["Open", "In Progress", "Resolved", "Closed"]
status_weights = [0.20, 0.15, 0.40, 0.25]

descriptions = {
    "VPN Issue": [
        "Cannot connect to VPN from home office",
        "VPN disconnects frequently during video calls",
        "VPN client throws authentication error on startup",
        "Unable to access internal resources via VPN",
        "VPN connection extremely slow, affecting productivity",
        "Split tunneling not working after recent update",
        "VPN certificate expired, cannot authenticate",
    ],
    "Password Reset": [
        "Account locked after multiple failed login attempts",
        "Forgot password and need urgent reset",
        "Password expired, cannot login to work systems",
        "Two-factor authentication code not working",
        "Need password reset for CRM system access",
        "SSO not working, redirecting to error page",
        "Admin portal login credentials not recognized",
    ],
    "Software Installation": [
        "Need Microsoft Office 365 installed on new laptop",
        "Requesting installation of Adobe Creative Suite",
        "Cannot install required development tools, admin rights needed",
        "Zoom client not working properly, needs reinstall",
        "Requesting installation of project management software",
        "Python and pip environment setup required",
        "Antivirus software outdated, requesting update",
    ],
    "Laptop Issue": [
        "Laptop screen flickering and sometimes goes black",
        "Battery draining within 2 hours, needs replacement",
        "Keyboard keys sticking and unresponsive",
        "Laptop overheating during normal usage",
        "Laptop wont boot, stuck on startup screen",
        "Touchpad not responding intermittently",
        "USB ports not recognizing connected devices",
    ],
    "Email Access": [
        "Cannot receive emails since this morning",
        "Outlook not syncing with Exchange server",
        "Email signature not displaying correctly",
        "Unable to access shared team mailbox",
        "Emails going to spam folder from internal senders",
        "Calendar invites not appearing in inbox",
        "Auto-reply not triggering despite being configured",
    ],
    "Network Connectivity": [
        "No internet connection at workstation",
        "WiFi signal extremely weak in conference room B",
        "Network printer not accessible from laptop",
        "Intermittent connection drops throughout the day",
        "Cannot access shared network drives",
        "Ethernet port not detecting cable connection",
        "DNS resolution failing for internal hostnames",
    ],
    "Hardware Request": [
        "Requesting second monitor for better productivity",
        "Need ergonomic keyboard and mouse for workspace",
        "Requesting docking station for new laptop",
        "Need replacement headset for customer calls",
        "Requesting USB hub for multiple device connections",
        "Need webcam for remote meetings",
        "Requesting standing desk converter",
    ],
}

resolution_notes_map = {
    "VPN Issue": "Reconfigured VPN client settings and updated credentials. Issue resolved.",
    "Password Reset": "Password reset completed via Active Directory. User notified with new credentials.",
    "Software Installation": "Software installed successfully with admin credentials. License activated.",
    "Laptop Issue": "Hardware inspected and repaired/replaced. Unit tested and confirmed working.",
    "Email Access": "Email configuration corrected in Exchange admin console. Access restored.",
    "Network Connectivity": "Network switch port reset and DHCP lease renewed. Connectivity restored.",
    "Hardware Request": "Hardware ordered and delivered. Setup completed by IT technician.",
}

start_date = datetime(2024, 5, 1)
end_date = datetime(2025, 5, 1)
date_range = (end_date - start_date).days

rows = []
ticket_counter = 1

for i in range(250):
    emp_name, dept = random.choice(employees)
    clean_cat = random.choices(clean_categories, weights=[15, 18, 14, 12, 16, 13, 12])[0]

    # 30% chance of using a dirty/variant category name
    if random.random() < 0.30:
        cat = random.choice(dirty_categories[clean_cat])
    else:
        cat = clean_cat

    priority = random.choices(priorities, weights=priority_weights)[0]
    status = random.choices(statuses, weights=status_weights)[0]

    created_at = start_date + timedelta(days=random.randint(0, date_range))

    if status in ["Resolved", "Closed"]:
        resolution_days = random.randint(1, 14)
        resolved_at = created_at + timedelta(days=resolution_days)
        res_notes = resolution_notes_map[clean_cat]
    else:
        resolved_at = None
        res_notes = ""

    desc = random.choice(descriptions[clean_cat])

    rows.append({
        "ticket_id": f"TKT-{ticket_counter:04d}",
        "employee_name": emp_name,
        "department": dept,
        "issue_category": cat,
        "description": desc,
        "priority": priority,
        "status": status,
        "resolution_notes": res_notes,
        "created_at": created_at.strftime("%Y-%m-%d %H:%M:%S"),
        "resolved_at": resolved_at.strftime("%Y-%m-%d %H:%M:%S") if resolved_at else "",
    })
    ticket_counter += 1

# Add ~20 duplicate rows (same data, different ticket_id) for ETL dedup demo
dup_indices = random.sample(range(len(rows)), 20)
for idx in dup_indices:
    dup = dict(rows[idx])
    dup["ticket_id"] = f"TKT-{ticket_counter:04d}"
    rows.append(dup)
    ticket_counter += 1

random.shuffle(rows)

fieldnames = [
    "ticket_id", "employee_name", "department", "issue_category",
    "description", "priority", "status", "resolution_notes",
    "created_at", "resolved_at"
]

os.makedirs("datasets", exist_ok=True)
with open("datasets/tickets_historical.csv", "w", newline="", encoding="utf-8") as f:
    writer = csv.DictWriter(f, fieldnames=fieldnames)
    writer.writeheader()
    writer.writerows(rows)

print(f"Generated {len(rows)} rows ({len(rows) - 20} base records + 20 intentional duplicates)")
print("Dirty data includes: variant category names, mixed-case priorities")
print("Saved to datasets/tickets_historical.csv")
