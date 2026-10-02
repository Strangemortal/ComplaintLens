from fastapi import APIRouter, UploadFile, File, HTTPException
from app.services.ocr import extract_text_from_pdf
from app.services.langgraph import run_agent_workflow

router = APIRouter(prefix="/api/upload", tags=["upload"])

@router.post("")
async def upload_document(file: UploadFile = File(...)):
    if not (file.filename and file.filename.lower().endswith(".pdf")):
        raise HTTPException(status_code=400, detail="Only PDF files are supported.")
        
    try:
        content = await file.read()
        extracted_text = extract_text_from_pdf(content)
        
        if not extracted_text:
            raise HTTPException(status_code=422, detail="Could not extract text from the PDF. Ensure it contains selectable text.")
            
        # Run extraction agent on the PDF text as a new complaint
        result = run_agent_workflow(message=extracted_text)
        return {
            "text": extracted_text[:1000],  # Return preview of text
            "form": result["form"],
            "risk": result["risk"],
            "chat_response": "PDF uploaded and processed. Complaint fields have been pre-filled from document text."
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to process PDF: {str(e)}")

