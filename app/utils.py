import pdfplumber
from dotenv import load_dotenv
import requests
import os
import re

load_dotenv()
def extract_text_from_pdf(file_path: str) -> str:
    text = ""
    with pdfplumber.open(file_path) as pdf:
        for page in pdf.pages:
            text += page.extract_text() or ""
    return text.strip()

def clean_file_name(name: str):
    # Replace any character that’s not alphanumeric, dot, or hyphen
    name = name.replace(" ", "_")     # first replace spaces
    name = re.sub(r"[^A-Za-z0-9._-]", "", name)
    return name

def get_presigned_url(file_name: str):
    file_name = clean_file_name(file_name)
    token = os.getenv('BEARER_TOKEN')
    api_end_point = os.getenv('HURAD_AI_END_POINT')

    headers = {
        "Authorization": f"Bearer {token}"
    }

    params = {
        "file_name": file_name,
        "expiry_minutes": 5
    }

    try:
        res = requests.get(
            f"{api_end_point}/generate-upload-url",
            headers=headers,
            params=params
        )
        res.raise_for_status()
        data = res.json()
        return data.get("upload_url")

    except Exception as e:
        raise Exception(f"Failed to fetch presigned URL: {e}")



def upload_file_on_presigned_url(url: str, file_path: str):
    try:
        with open(file_path, "rb") as f:
            file_bytes = f.read()

        res = requests.put(url, data=file_bytes)

        if res.status_code in (200, 204):
            return {"success": True, "message": "File uploaded successfully"}
        else:
            return {"success": False, "message": f"Upload failed: {res.status_code} - {res.text}"}

    except Exception as e:
        return {"success": False, "message": str(e)}

