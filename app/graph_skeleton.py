import json
import datetime
from typing import TypedDict, List, Optional
import requests
from langgraph.graph import StateGraph, END
from langchain_google_genai import ChatGoogleGenerativeAI
from pydantic import BaseModel
import os
from dotenv import load_dotenv
from app.session_store import load_session, save_session_to_db
from prompts.rag_prompt import generate_rag_prompt
from prompts.lab_analyzer_prompt import generate_lab_analyzer_prompt
from IPython.display import Image, display
from app.utils import extract_text_from_pdf

load_dotenv()

class GraphState(TypedDict):
    session_id: str
    user_id: str
    input_event: str
    user_message: str
    file_url: str
    conversation_history: List[dict]
    lab_history: List[dict]
    patient_profile: dict
    llm_output: str
    ocr_text: str
    parsed_labs_json: str
    user_response_message: str


class LabTest(BaseModel):
    name: str
    value: float
    units: str
    ref_low: Optional[float] = None
    ref_high: Optional[float] = None
    flag: Optional[str] = None


class ParsedLabs(BaseModel):
    tests: List[LabTest]


os.environ["GOOGLE_API_KEY"] = os.getenv("GOOGLE_API_KEY")

class DoctorAgentWorkflow:
    def __init__(self):

        self.llm = ChatGoogleGenerativeAI(
            model="gemini-2.5-flash",
            temperature=0.3
        )

    def load_session_memory(self, state: GraphState):
        prev = load_session(state["session_id"], state["user_id"])
        if prev:
            history = prev.get("conversation_history", [])
            labs = prev.get("lab_history", [])
            patient = prev.get("patient_profile", {})
        else:
            history = []
            labs = []
            patient = {"name": "Patient", "age": 30, "gender": "Female"}

        return {
            "patient_profile": patient,
            "conversation_history": history,
            "lab_history": labs,
        }

    async def initial_rag(self, state: GraphState):
        if state["input_event"] == "file_uploaded":
            return {"llm_output": "PROCESS_FILE"}

        history = state.get("conversation_history", [])
        user_msg = state.get("user_message")

        if user_msg:
            if not history or history[-1].get("text") != user_msg:
                history.append({"role": "user", "text": user_msg})

        prompt = generate_rag_prompt(history, user_msg, state["patient_profile"])
        llm_response = await self.llm.ainvoke(prompt)

        return {
            "conversation_history": history,
            "llm_output": llm_response.content
        }

    async def call_ocr(self, state: GraphState):
        file_path = state.get("file_path")
        try:
            extracted_text = extract_text_from_pdf(file_path)
            return {"ocr_text": extracted_text}
        except Exception as e:
            text = f"OCR_ERROR: {str(e)}"

        return {"ocr_text": text}

    async def parse_lab_values(self, state: GraphState):
        if "OCR_ERROR" in state["ocr_text"]:
            return {"parsed_labs_json": "[]"}

        prompt = f"""
        Extract lab results from the OCR text.
        Return only JSON matching ParsedLabs.

        OCR:
        {state['ocr_text']}
        """
        res = await self.llm.with_structured_output(ParsedLabs).ainvoke(prompt)

        try:
            parsed_json = json.dumps(res.dict())
        except:
            parsed_json = "[]"

        return {"parsed_labs_json": parsed_json}

    def normalize_and_store_labs(self, state: GraphState):
        try:
            data = json.loads(state["parsed_labs_json"])
        except Exception:
            return {}

        if "tests" not in data:
            return {}

        entry = {
            "date": datetime.datetime.utcnow().isoformat(),
            "tests": data["tests"],
            "file_url": state["file_url"],
        }

        return {
            "lab_history": state.get("lab_history", []) + [entry]
        }

    async def analyze_labs(self, state: GraphState):
        prompt = generate_lab_analyzer_prompt(
            state["conversation_history"],
            state["patient_profile"],
            state["parsed_labs_json"]
        )
        res = await self.llm.ainvoke(prompt)
        return {"llm_output": res.content}

    def respond_to_user(self, state: GraphState):
        msg = state.get("llm_output", "")

        if msg.startswith("RESPOND:"):
            final = msg[8:].strip()
        elif msg.startswith("ASK_MORE:"):
            final = msg[9:].strip()
        elif msg.startswith("REQUEST_UPLOAD:"):
            final = msg.replace("REQUEST_UPLOAD:", "").strip()
        elif msg == "PROCESS_FILE":
            final = "I’m reviewing your uploaded report. One moment."
        else:
            final = msg.strip() or "Could you rephrase that?"

        history = state.get("conversation_history", [])
        history.append({"role": "assistant", "text": final})

        return {
            "user_response_message": final,
            "conversation_history": history,
        }

    def end_conversation(self, state: GraphState):
        final = state.get("llm_output", "").replace("END_CONSULTATION:", "").strip()

        history = state.get("conversation_history", [])
        history.append({"role": "assistant", "text": final})

        save_session_to_db(
            session_id=state["session_id"],
            user_id=state["user_id"],
            history=history,
            labs=state.get("lab_history", []),
            patient=state.get("patient_profile", {})
        )

        return {
            "user_response_message": final,
            "conversation_history": history,
        }

    def router(self, state: GraphState) -> str:
        msg = state.get("llm_output", "")

        if msg == "PROCESS_FILE":
            return "call_ocr"

        if msg.startswith("REQUEST_UPLOAD"):
            return "ask_for_upload"

        if msg.startswith("END_CONSULTATION"):
            return "end_conversation"

        return "respond"

    def build(self):
        workflow = StateGraph(GraphState)

        workflow.add_node("rag", self.initial_rag)
        workflow.add_node("call_ocr", self.call_ocr)
        workflow.add_node("parse", self.parse_lab_values)
        workflow.add_node("store", self.normalize_and_store_labs)
        workflow.add_node("analyze", self.analyze_labs)
        workflow.add_node("respond", self.respond_to_user)
        workflow.add_node("ask_for_upload", self.respond_to_user)
        workflow.add_node("end_conversation", self.end_conversation)

        workflow.set_entry_point("rag")

        # Router: DO NOT add it as a node
        workflow.add_conditional_edges(
            "rag",
            self.router,
            {
                "call_ocr": "call_ocr",
                "ask_for_upload": "ask_for_upload",
                "respond": "respond",
                "end_conversation": "end_conversation",
            },
        )

        workflow.add_edge("call_ocr", "parse")
        workflow.add_edge("parse", "store")
        workflow.add_edge("store", "analyze")
        workflow.add_edge("analyze", "respond")

        workflow.add_edge("respond", END)
        workflow.add_edge("ask_for_upload", END)
        workflow.add_edge("end_conversation", END)

        return workflow.compile()



# agent = DoctorAgentWorkflow()
# graph_executor = agent.build()
