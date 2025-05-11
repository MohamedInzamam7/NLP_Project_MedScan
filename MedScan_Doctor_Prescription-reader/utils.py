import pytesseract
from PIL import Image
from transformers import pipeline
import smtplib
from email.mime.text import MIMEText
import requests
import re

# Initialize NLP pipeline
ner_pipeline = pipeline("ner", model="emilyalsentzer/Bio_ClinicalBERT", aggregation_strategy="simple")

def extract_text(image):
    """OCR extraction using Tesseract"""
    return pytesseract.image_to_string(image)


def extract_entities(text):
    """Extract medicines, dosage, frequency using BioClinicalBERT"""
    entities = ner_pipeline(text)
    result = {"DRUG": [], "DOSAGE": [], "FREQUENCY": []}
    
    for entity in entities:
        if entity["entity_group"] == "DRUG":
            result["DRUG"].append(entity["word"])
        elif "DOSAGE" in entity["entity_group"]:
            result["DOSAGE"].append(entity["word"])
        elif "FREQUENCY" in entity["entity_group"]:
            result["FREQUENCY"].append(entity["word"])
    
    return result

def send_reminder(email, medicine, dosage, time):
    """Send email reminder"""
    msg = MIMEText(f"Reminder: Take {dosage} of {medicine} at {time}")
    msg["Subject"] = "Prescription Reminder"
    msg["From"] = "mohamedinzamam2004@gmail.com"  # Fixed typo in email
    msg["To"] = email
    
    with smtplib.SMTP("smtp.gmail.com", 587) as server:
        server.starttls()
        server.login("mohamedinzamam2004@gmail.com", "#*Mohamed*#")
        server.send_message(msg)

def validate_dosage(drug, dosage):
    """Context-aware dosage validation"""
    safe_limits = {
        "ibuprofen": "800mg", 
        "metformin": "2000mg",
        "paracetamol": "4000mg"
    }
    
    # Extract numerical value
    try:
        num = int(re.search(r'\d+', dosage).group())
        max_num = int(re.search(r'\d+', safe_limits.get(drug.lower(), "0mg")).group())
        return "Warning: High dosage" if num > max_num else "Dosage OK"
    except:
        return "Invalid dosage format"

def check_interactions(drugs):
    """Check drug interactions using OpenFDA API"""
    if len(drugs) < 2:
        return "No interactions (single drug)"
    
    drug_pair = "+".join(drugs[:2])
    try:
        response = requests.get(f"https://api.fda.gov/drug/label.json?search=interactions:{drug_pair}&limit=1")
        return response.json().get("results", [{}])[0].get("warnings", ["No known interactions"])[0]
    except:
        return "API limit reached"