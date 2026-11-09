from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from typing import Optional
from backend.app.services.resume_parser import ResumeParserService
from backend.app.schemas.resume import ResumeParseResult

router = APIRouter(prefix="/api/resume", tags=["Resume"])


@router.post("/parse", response_model=ResumeParseResult)
def parse_resume_endpoint(
    file: Optional[UploadFile] = File(None),
    raw_text: Optional[str] = Form(None),
    target_role: str = Form("AI/ML Engineer")
):
    """
    Parses an uploaded resume PDF or raw text, extracting candidate name, contact,
    categorized technical skills, domain exposure, and role alignment.
    """
    extracted_text = ""

    if isinstance(file, UploadFile) and file.filename:
        content = file.file.read()
        filename = file.filename.lower()
        if filename.endswith(".pdf"):
            try:
                extracted_text = ResumeParserService.extract_text_from_pdf_bytes(content)
            except Exception as e:
                raise HTTPException(status_code=400, detail=f"PDF parsing error: {str(e)}")
        else:
            try:
                extracted_text = content.decode("utf-8", errors="ignore")
            except Exception as e:
                raise HTTPException(status_code=400, detail=f"Text decoding error: {str(e)}")
    elif raw_text:
        extracted_text = raw_text
    else:
        raise HTTPException(status_code=400, detail="Must provide either a resume file or raw_text.")

    if len(extracted_text.strip()) < 20:
        raise HTTPException(status_code=400, detail="Resume text is too short or empty to extract meaningful profile.")

    parsed = ResumeParserService.parse_resume(extracted_text, target_role=target_role)
    return parsed
