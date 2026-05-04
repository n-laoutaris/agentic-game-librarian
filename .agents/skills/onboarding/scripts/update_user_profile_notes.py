import json
import pathlib
from datetime import datetime

ROOT = pathlib.Path(__file__).resolve().parent.parent.parent
PROFILE_PATH = ROOT / "database" / "user_profile.json"

def load_json(path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def save_json(path, data):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

def update_user_profile_notes(summary, details):
    profile = load_json(PROFILE_PATH)
    profile.setdefault("experience_notes", []).append(
        {
            "note_id": f"onboarding-completion-{datetime.utcnow().strftime("%Y%m%d-%H%M%S")}",
            "created_at": datetime.utcnow().isoformat() + "Z",
            "summary": summary,
            "details": details,
        }
    )
    profile["last_updated_at"] = datetime.utcnow().isoformat() + "Z"
    save_json(PROFILE_PATH, profile)
    print(f"Updated {PROFILE_PATH} with onboarding completion note.")

if __name__ == "__main__":
    # Example usage (can be called from the agent with specific summary and details)
    update_user_profile_notes(
        summary="User completed first-run onboarding.",
        details="User prefers time-bounded sessions, structured play, and games that feel wondrous and creative. They enjoy sandbox exploration, sci-fi/fantasy RPG worlds, collecting, and cooperative play. Sports games and competitive MOBAs are disliked."
    )
