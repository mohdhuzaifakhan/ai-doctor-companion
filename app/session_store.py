from db.connection import sessions
import datetime

def load_session(session_id: str, user_id: str):
    doc = sessions.find_one({"session_id": session_id, "user_id": user_id})
    return doc["state"] if doc else None

def save_session(session_id: str, user_id: str, state: dict):
    sessions.update_one(
        {"session_id": session_id, "user_id": user_id},
        {"$set": {"state": state}},
        upsert=True
    )

def save_session_to_db(session_id: str, user_id: str, history: list, labs: list, patient: dict):
    state = {
        "conversation_history": history,
        "lab_history": labs,
        "patient_profile": patient,
        "ended_at": datetime.datetime.utcnow().isoformat()
    }

    sessions.update_one(
        {"session_id": session_id, "user_id": user_id},
        {
            "$set": {
                "session_id": session_id,
                "user_id": user_id,
                "state": state,
                "updated_at": datetime.datetime.utcnow(),
            },
            "$setOnInsert": {
                "created_at": datetime.datetime.utcnow()
            }
        },
        upsert=True
    )
