from pymongo import MongoClient
import os

client = MongoClient(os.getenv("MONGO_URI"))
database = client["ai_doctor"]
sessions = database["sessions"]
patients = database["patients"]
