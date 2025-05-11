from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from utils import extract_text, extract_entities, check_interactions
import io
from PIL import Image
import logging
import os

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI()

# CORS Configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.post("/process")
async def process_prescription(file: UploadFile = File(...)):
    try:
        # Validate file type
        if not file.content_type.startswith('image/'):
            raise HTTPException(status_code=400, detail="File must be an image")

        logger.info(f"Processing file: {file.filename}")
        
        # Read and validate image
        image_data = await file.read()
        image = Image.open(io.BytesIO(image_data))
        
        # Save temporary file (optional)
        temp_path = "temp.jpg"
        image.save(temp_path)
        
        # OCR Processing
        text = extract_text(temp_path)
        if not text.strip():
            raise HTTPException(status_code=422, detail="No text could be extracted from the image")
            
        # NLP Processing
        entities = extract_entities(text)
        interactions = check_interactions(entities.get("DRUG", []))
        
        # Clean up
        if os.path.exists(temp_path):
            os.remove(temp_path)
            
        return {
            "status": "success",
            "text": text,
            "entities": entities,
            "interactions": interactions
        }
        
    except Exception as e:
        logger.error(f"Error processing prescription: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/process")
async def process_prescription(file: UploadFile = File(...)):
    try:
        # Validate file type
        if not file.content_type.startswith('image/'):
            raise HTTPException(status_code=400, detail="File must be an image (JPEG/PNG)")

        # Read and validate image
        contents = await file.read()
        if not contents:
            raise HTTPException(status_code=400, detail="Empty file uploaded")

        # Process image
        try:
            image = Image.open(io.BytesIO(contents))
            image.verify()  # Verify it's a valid image
            image = Image.open(io.BytesIO(contents))  # Reopen after verify
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Invalid image: {str(e)}")

        # OCR Processing
        text = extract_text(image)  # Modified to accept PIL Image directly
        if text == "OCR_FAILED":
            raise HTTPException(status_code=422, detail="OCR failed to process image")

        # NLP Processing
        entities = extract_entities(text)
        if "error" in entities:
            raise HTTPException(status_code=422, detail=f"NLP processing failed: {entities['error']}")

        interactions = check_interactions(entities.get("DRUG", []))
        
        return {
            "status": "success",
            "text": text,
            "medicines": entities.get("DRUG", []),
            "dosages": entities.get("DOSAGE", []),
            "frequencies": entities.get("FREQUENCY", []),
            "interactions": interactions
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal processing error")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
