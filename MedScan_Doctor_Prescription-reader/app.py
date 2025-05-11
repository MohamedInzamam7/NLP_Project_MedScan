import streamlit as st
import requests
from utils import send_reminder, validate_dosage
from PIL import Image
import io

st.title("📄 Doctor Prescription Reader")

# Sidebar for email alerts
with st.sidebar:
    st.header("Reminder Settings")
    email = st.text_input("Patient Email")
    enable_reminders = st.checkbox("Enable Email Reminders")

# Main interface
uploaded_file = st.file_uploader("Upload Prescription Image", type=["jpg", "png"])

if uploaded_file:
    # Display image
    image = Image.open(uploaded_file)
    st.image(image, caption="Uploaded Prescription", width=300)
    
    # Send to backend
    files = {"file": uploaded_file.getvalue()}
    response = requests.post("http://localhost:8000/process", files=files)
    
    if response.status_code == 200:
        data = response.json()
        
        # Show extracted data
        st.subheader("Extracted Information")
        st.json(data["entities"])
        
        # Show interactions
        st.subheader("Drug Interactions Check")
        st.write(data["interactions"])
        
        # Dosage validation
        if data["entities"]["DRUG"] and data["entities"]["DOSAGE"]:
            validation = validate_dosage(
                data["entities"]["DRUG"][0],
                data["entities"]["DOSAGE"][0]
            )
            st.warning(validation)
        
        # Reminder scheduling
        if enable_reminders and email:
            time = st.time_input("Reminder Time")
            if st.button("Schedule Reminder"):
                send_reminder(
                    email,
                    data["entities"]["DRUG"][0],
                    data["entities"]["DOSAGE"][0],
                    str(time)
                )
                st.success("Reminder scheduled!")
    else:
        st.error("Processing failed")