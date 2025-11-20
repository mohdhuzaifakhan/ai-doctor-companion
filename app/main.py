from fastapi import FastAPI, WebSocket, WebSocketDisconnect, UploadFile, File, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from app.utils import get_presigned_url , upload_file_on_presigned_url
import uuid
from app.graph_skeleton import DoctorAgentWorkflow
import os

app = FastAPI(title="AI Doctor Companion")
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

agent = DoctorAgentWorkflow()


@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})


@app.post("/upload")
async def upload_file(file: UploadFile):
    file_location = f"uploads/{file.filename}"
    with open(file_location, "wb") as f:
        f.write(await file.read())

    return {"file_path": file_location}


# @app.post("/upload")
# async def upload_file(file: UploadFile):
#     local_path = f"uploads/{file.filename}"
#     os.makedirs("uploads", exist_ok=True)

#     file_bytes = await file.read()

#     with open(local_path, "wb") as f:
#         f.write(file_bytes)

#     presigned_url = get_presigned_url(file_name=file.filename)
#     if not presigned_url:
#         return {
#             "success": False,
#             "message": "Failed to get presigned URL",
#             "file_path": local_path
#         }

#     try:
#         upload_res = upload_file_on_presigned_url(presigned_url, file_path=local_path)
#         if upload_res.status_code not in (200, 204):
#             return {
#                 "success": False,
#                 "message": f"Cloud upload failed: {upload_res.status_code} - {upload_res.text}",
#                 "file_path": local_path
#             }
#     except Exception as e:
#         return {
#             "success": False,
#             "message": str(e),
#             "file_path": local_path
#         }

#     cloud_url = presigned_url.split("?")[0]
#     return {
#         "success": True,
#         "file": file.filename,
#         "file_path": local_path,
#         "cloud_url": cloud_url
#     }

@app.websocket("/ws")
async def websocket_chat(websocket: WebSocket):
    await websocket.accept()

    graph_executor = agent.build()

    user_state = {
        "session_id": str(uuid.uuid4()),
        "user_id": f"user_{uuid.uuid4()}",
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

    try:
        while True:
            msg = await websocket.receive_text()

            if msg.startswith("upload:"):
                user_state["input_event"] = "file_uploaded"
                user_state["file_url"] = msg.replace("upload:", "").strip()
                user_state["user_message"] = ""
            else:
                user_state["input_event"] = "user_message"
                user_state["user_message"] = msg
                user_state["file_url"] = ""

            result_state = await graph_executor.ainvoke(user_state)
            user_state.update(result_state)

            bot_reply = user_state.get("user_response_message", "Sorry, I cannot reply.")
            await websocket.send_text(bot_reply)

    except WebSocketDisconnect:
        print("User disconnected:", user_state["session_id"])
        return

    except Exception as e:
        await websocket.send_text(f"ERROR: {str(e)}")
