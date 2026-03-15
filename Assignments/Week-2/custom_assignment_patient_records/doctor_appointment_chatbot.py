import gradio as gr
import ast
from pathlib import Path


# --------------------------------
# File paths
# --------------------------------
BASE_DIR = Path(__file__).parent
PATIENT_FILE = BASE_DIR / "patients.txt"


# --------------------------------
# Patient Database Manager
# --------------------------------
class PatientDatabase:

    def __init__(self, file_path):
        self.file_path = file_path
        self.patients = self.load_patients()

    def load_patients(self):
        with open(self.file_path, "r") as f:
            content = f.read()
        return ast.literal_eval(content.split("=", 1)[1].strip())

    def save_patients(self):
        with open(self.file_path, "w") as f:
            f.write("patients = ")
            f.write(repr(self.patients))

    def find_by_name(self, name):
        for pid, details in self.patients.items():
            if details.get("name", "").lower() == name.lower():
                return pid
        return None

    def generate_new_id(self):
        numbers = [int(pid[1:]) for pid in self.patients.keys()]
        return f"P{max(numbers)+1:03d}"

    def add_patient(self, name, phone, address):
        new_id = self.generate_new_id()

        self.patients[new_id] = {
            "name": name,
            "contact": phone,
            "address": address
        }

        self.save_patients()


# --------------------------------
# Chatbot Logic
# --------------------------------
class AppointmentChatbot:

    def __init__(self, db):
        self.db = db
        self.reset()

    def reset(self):
        self.step = "ask_name"
        self.name = None
        self.phone = None
        self.patient_id = None

    def respond(self, message, history):

        if not message.strip():
            return "Please enter a valid input."

        # Step 1: Ask name
        if self.step == "ask_name":

            self.name = message
            pid = self.db.find_by_name(message)

            if pid:
                self.patient_id = pid
                self.step = "verify_phone"
                return "Welcome back! Please enter your phone number."

            else:
                self.step = "new_phone"
                return "I couldn't find your record. Please enter your phone number."

        # Step 2: Verify phone
        elif self.step == "verify_phone":

            patient = self.db.patients[self.patient_id]

            if message == patient["contact"]:
                self.step = "verify_address"

                if "address" in patient:
                    return "Please confirm your address."
                else:
                    return "Please enter your address."

            else:
                return "Phone number does not match. Please try again."

        # Step 3: Verify address
        elif self.step == "verify_address":

            patient = self.db.patients[self.patient_id]

            if "address" in patient:

                if message.lower() == patient["address"].lower():
                    self.reset()
                    return "Thank you for the details. Doctor has been informed and will call you soon."

                else:
                    patient["address"] = message
                    self.db.save_patients()
                    self.reset()
                    return "Address updated. Doctor will contact you soon."

            else:
                patient["address"] = message
                self.db.save_patients()
                self.reset()
                return "Address saved. Doctor will contact you soon."

        # Step 4: New patient phone
        elif self.step == "new_phone":

            self.phone = message
            self.step = "new_address"
            return "Please enter your address."

        # Step 5: New patient address
        elif self.step == "new_address":

            self.db.add_patient(self.name, self.phone, message)
            self.reset()

            return "Thank you for the details. Doctor has been informed and will call you soon."


# --------------------------------
# Initialize system
# --------------------------------
db = PatientDatabase(PATIENT_FILE)
chatbot_logic = AppointmentChatbot(db)


# --------------------------------
# Initial greeting
# --------------------------------
initial_message = [
    {
        "role": "assistant",
        "content": "Hello 👋 Welcome to the Patient Appointment Chatbot.\n\nPlease enter your name to begin."
    }
]


# --------------------------------
# UI
# --------------------------------
demo = gr.ChatInterface(
    fn=chatbot_logic.respond,
    chatbot=gr.Chatbot(value=initial_message, height=400),
    title="Doctor Appointment Chatbot"
)

demo.launch()