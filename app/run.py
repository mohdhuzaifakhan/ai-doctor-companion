import asyncio
from app.graph_skeleton import DoctorAgentWorkflow
import uuid


# This code is written only for testing purpose in CLI MODE 
agent = DoctorAgentWorkflow()
graph_executor = agent.build()

GLOBAL_STATE = {
    "session_id": str(uuid.uuid4()),
    "user_id": "demo_user",
    "conversation_history": [],
    "lab_history": [],

    "input_event": "user_message",
    "user_message": "",
    "file_url": "",
    "llm_output": "",
    "ocr_text": "",
    "parsed_labs_json": "",
    "user_response_message": "",
    "patient_profile": {}
}


async def run_cli():
    print("\n=== AI Doctor Companion (CLI Mode) ===")
    print("Type your message normally.")
    print("If you want to simulate a file upload, type:")
    print("upload <FILE_URL>\n")

    while True:
        user_input = input("\nYou: ").strip()

        if user_input.lower() in ["exit", "quit"]:
            print("Goodbye!")
            break

        if user_input.startswith("upload "):
            file_url = user_input.replace("upload ", "").strip()
            GLOBAL_STATE["input_event"] = "file_uploaded"
            GLOBAL_STATE["file_url"] = file_url
            GLOBAL_STATE["user_message"] = ""

        else:
            
            GLOBAL_STATE["input_event"] = "user_message"
            GLOBAL_STATE["user_message"] = user_input
            GLOBAL_STATE["file_url"] = ""

        try:
            result_state = await graph_executor.ainvoke(GLOBAL_STATE)
        except Exception as e:
            print(f"Error: {e}")
            continue

        GLOBAL_STATE.update(result_state)
        print(f"\nAI Doctor: {GLOBAL_STATE.get('user_response_message')}")


if __name__ == "__main__":
    asyncio.run(run_cli())
