"""
High School Management System API

A super simple FastAPI application that allows students to view and sign up
for extracurricular activities at Mergington High School.
"""

from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import RedirectResponse
import os
from pathlib import Path

app = FastAPI(title="Mergington High School API",
              description="API for viewing and signing up for extracurricular activities")

# Mount the static files directory
current_dir = Path(__file__).parent
app.mount("/static", StaticFiles(directory=os.path.join(Path(__file__).parent,
          "static")), name="static")

# In-memory activity database
activities = {
    "Chess Club": {
        "description": "Learn strategies and compete in chess tournaments",
        "schedule": "Fridays, 3:30 PM - 5:00 PM",
        "max_participants": 12,
    "participants": ["michael@mergington.edu", "daniel@mergington.edu"]
    },
    "Programming Class": {
        "description": "Learn programming fundamentals and build software projects",
        "schedule": "Tuesdays and Thursdays, 3:30 PM - 4:30 PM",
        "max_participants": 20,
        "participants": ["emma@mergington.edu", "sophia@mergington.edu"]
    },
    "Gym Class": {
        "description": "Physical education and sports activities",
        "schedule": "Mondays, Wednesdays, Fridays, 2:00 PM - 3:00 PM",
        "max_participants": 30,
        "participants": ["john@mergington.edu", "olivia@mergington.edu"]
    },
    "Soccer Team": {
        "description": "Join the school soccer team and compete in matches",
        "schedule": "Tuesdays and Thursdays, 4:00 PM - 5:30 PM",
        "max_participants": 22,
        "participants": ["liam@mergington.edu", "noah@mergington.edu"]
    },
    "Basketball Team": {
        "description": "Practice and play basketball with the school team",
        "schedule": "Wednesdays and Fridays, 3:30 PM - 5:00 PM",
        "max_participants": 15,
        "participants": ["ava@mergington.edu", "mia@mergington.edu"]
    },
    "Art Club": {
        "description": "Explore your creativity through painting and drawing",
        "schedule": "Thursdays, 3:30 PM - 5:00 PM",
        "max_participants": 15,
        "participants": ["amelia@mergington.edu", "harper@mergington.edu"]
    },
    "Drama Club": {
        "description": "Act, direct, and produce plays and performances",
        "schedule": "Mondays and Wednesdays, 4:00 PM - 5:30 PM",
        "max_participants": 20,
        "participants": ["ella@mergington.edu", "scarlett@mergington.edu"]
    },
    "Math Club": {
        "description": "Solve challenging problems and participate in math competitions",
        "schedule": "Tuesdays, 3:30 PM - 4:30 PM",
        "max_participants": 10,
        "participants": ["james@mergington.edu", "benjamin@mergington.edu"]
    },
    "Debate Team": {
        "description": "Develop public speaking and argumentation skills",
        "schedule": "Fridays, 4:00 PM - 5:30 PM",
        "max_participants": 12,
        "participants": ["charlotte@mergington.edu", "henry@mergington.edu"]
    }
}

# In-memory users store. Keys are user IDs (simple incremental ints as strings)
users = {}
_next_user_id = 1


def _create_user_if_missing(email: str, name: str | None = None, role: str | None = None, bio: str | None = None):
    """Ensure a user exists for the given email. If not, create a minimal user and return its id."""
    global _next_user_id
    # search for existing user by email
    for uid, u in users.items():
        if u.get("email") == email:
            return uid

    uid = str(_next_user_id)
    users[uid] = {"id": uid, "email": email, "name": name or email.split("@")[0], "role": role or "student", "bio": bio or ""}
    _next_user_id += 1
    return uid


# Migrate existing activity participants (emails) into user ids on startup
def _migrate_participants_to_user_ids():
    for activity in activities.values():
        migrated = []
        for p in activity.get("participants", []):
            # if participant already looks like a user id (digits), keep
            if isinstance(p, str) and p.isdigit() and p in users:
                migrated.append(p)
            else:
                migrated.append(_create_user_if_missing(p))
        activity["participants"] = migrated


# Run migration on import
_migrate_participants_to_user_ids()


@app.get("/")
def root():
    return RedirectResponse(url="/static/index.html")


@app.get("/activities")
def get_activities():
    return activities


@app.post("/users")
def create_user(email: str, name: str | None = None, role: str | None = None, bio: str | None = None):
    """Create a new user (minimal). Returns the created user's id and data."""
    # simple validation
    if not email or "@" not in email:
        raise HTTPException(status_code=400, detail="Invalid email")

    # Prevent duplicates
    for u in users.values():
        if u.get("email") == email:
            raise HTTPException(status_code=400, detail="User with this email already exists")

    uid = _create_user_if_missing(email=email, name=name, role=role, bio=bio)
    return users[uid]


@app.get("/users/{user_id}")
def get_user(user_id: str):
    u = users.get(user_id)
    if not u:
        raise HTTPException(status_code=404, detail="User not found")
    return u


@app.post("/activities/{activity_name}/signup")
def signup_for_activity(activity_name: str, email: str, user_id: str | None = None):
    """Sign up a student for an activity"""
    # Validate activity exists
    if activity_name not in activities:
        raise HTTPException(status_code=404, detail="Activity not found")

    # Get the specific activity
    activity = activities[activity_name]

    # Determine the user id for this signup (create user if needed)
    if user_id is None:
        user_id = _create_user_if_missing(email)

    # Validate student is not already signed up
    if user_id in activity["participants"]:
        raise HTTPException(
            status_code=400,
            detail="Student is already signed up"
        )

    # Add student by user id
    activity["participants"].append(user_id)
    return {"message": f"Signed up {email} (user id: {user_id}) for {activity_name}", "user_id": user_id}


@app.delete("/activities/{activity_name}/unregister")
def unregister_from_activity(activity_name: str, email: str = None, user_id: str = None):
    """Unregister a student from an activity"""
    # Validate activity exists
    if activity_name not in activities:
        raise HTTPException(status_code=404, detail="Activity not found")

    # Get the specific activity
    activity = activities[activity_name]

    # Resolve user id if email provided
    if user_id is None and email is not None:
        # find user id by email
        for uid, u in users.items():
            if u.get("email") == email:
                user_id = uid
                break

    # Validate student is signed up
    if user_id is None or user_id not in activity["participants"]:
        raise HTTPException(
            status_code=400,
            detail="Student is not signed up for this activity"
        )

    # Remove student
    activity["participants"].remove(user_id)
    return {"message": f"Unregistered user id {user_id} from {activity_name}"}
