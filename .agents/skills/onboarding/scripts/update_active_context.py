import json
import pathlib
from datetime import datetime

ROOT = pathlib.Path(__file__).resolve().parent.parent.parent
ACTIVE_CONTEXT_PATH = ROOT / "memory-bank" / "activeContext.md"

def update_active_context(profile_initialized=True):
    try:
        with open(ACTIVE_CONTEXT_PATH, "r", encoding="utf-8") as f:
            content = f.read()
    except FileNotFoundError:
        content = ""

    timestamp = datetime.utcnow().isoformat() + "Z"

    # Update profile_initialized flag
    if "profile_initialized: true" not in content and profile_initialized:
        if "## Profile Status" in content:
            content = content.replace("## Profile Status", "## Profile Status\n- profile_initialized: true")
        else:
            content += "\n## Profile Status\n- profile_initialized: true\n"
    elif "profile_initialized: false" in content and profile_initialized:
        content = content.replace("profile_initialized: false", "profile_initialized: true")
    
    # Update onboarding_completed_at timestamp
    if "onboarding_completed_at:" in content:
        content = content.replace(re.search(r"onboarding_completed_at: .*", content).group(0), f"onboarding_completed_at: {timestamp}")
    else:
        if "## Profile Status" in content:
            content += f"- onboarding_completed_at: {timestamp}\n"
        else:
            content += f"\n## Profile Status\n- onboarding_completed_at: {timestamp}\n"

    with open(ACTIVE_CONTEXT_PATH, "w", encoding="utf-8") as f:
        f.write(content)

    print(f"Updated {ACTIVE_CONTEXT_PATH} with profile_initialized: {profile_initialized} and onboarding_completed_at: {timestamp}")

if __name__ == "__main__":
    update_active_context(profile_initialized=True)
