import os
import shutil
import tempfile
from typing import Optional, Dict, Any
from contextlib import asynccontextmanager
from bson import ObjectId

from dotenv import load_dotenv
load_dotenv()

from fastapi import FastAPI, UploadFile, File, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from database import connect_to_mongo, close_mongo_connection, get_db
from storage import storage_repo
from models import DocumentModel
from services import DocumentProcessingService
@asynccontextmanager
async def lifespan(app: FastAPI):
    await connect_to_mongo()
    yield
    await close_mongo_connection()

app = FastAPI(
    title="Document Intelligence API",
    description="API for document ingestion, processing, and validation.",
    version="1.0.0",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class DocumentUploadResponse(BaseModel):
    document_id: str
    status: str
    message: str

class DocumentDetailsResponse(BaseModel):
    document_id: str
    status: str
    classification: Optional[str]
    extracted_data: Optional[Dict[str, Any]]
    extraction_completeness: Optional[float]
    confidence: Optional[str]

class CorrectDocumentRequest(BaseModel):
    extracted_data: Dict[str, Any]
    classification: Optional[str]
    status: Optional[str] = "COMPLETED"

class ConfirmDocumentResponse(BaseModel):
    document_id: str
    status: str
    message: str

@app.post("/api/v1/documents/upload", response_model=DocumentUploadResponse, summary="Upload a document image")
async def upload_document(background_tasks: BackgroundTasks, file: UploadFile = File(...)):
    """
    Accepts a scanned document image or photo of a physical document.
    """
    if file.content_type not in ["image/jpeg", "image/png", "image/webp", "application/pdf"]:
        raise HTTPException(status_code=400, detail="Invalid file type. Only JPEG, PNG, WEBP, or PDF are supported.")
    ext = os.path.splitext(file.filename)[1] if file.filename else ".pdf"
    fd, temp_file_path = tempfile.mkstemp(suffix=ext)
    
    with os.fdopen(fd, "wb") as f_out:
        while chunk := await file.read(1024 * 1024):
            f_out.write(chunk)
    
    try:
        s3_uri = storage_repo.upload_file(file_path=temp_file_path, original_filename=file.filename)
    except Exception as e:
        if os.path.exists(temp_file_path):
            os.remove(temp_file_path)
        raise HTTPException(status_code=500, detail=f"Storage upload failed: {str(e)}")

    db = get_db()
    new_doc = DocumentModel(object_storage_uri=s3_uri, status="PROCESSING")
    result = await db.documents.insert_one(new_doc.model_dump(by_alias=True))
    document_id = str(result.inserted_id)
    
    background_tasks.add_task(DocumentProcessingService.process_document, document_id, temp_file_path, file.filename)
    
    return DocumentUploadResponse(
        document_id=document_id,
        status="PROCESSING",
        message="Document uploaded successfully. AI processing pipeline started in background."
    )

@app.get("/api/v1/documents/{id}", response_model=DocumentDetailsResponse, summary="Get document details")
async def get_document(id: str):
    """
    Retrieves the processing status, classification result, and extracted data for a specific document.
    """
    if not ObjectId.is_valid(id):
        raise HTTPException(status_code=400, detail="Invalid document ID format.")

    db = get_db()
    document = await db.documents.find_one({"_id": ObjectId(id)})
    
    if not document:
        raise HTTPException(status_code=404, detail="Document not found.")
        
    return DocumentDetailsResponse(
        document_id=str(document["_id"]),
        status=document.get("status", "UNKNOWN"),
        classification=document.get("classification"),
        extracted_data=document.get("extracted_data"),
        extraction_completeness=document.get("extraction_completeness"),
        confidence=document.get("confidence")
    )

@app.put("/api/v1/documents/{id}/confirm", response_model=ConfirmDocumentResponse, summary="Confirm or Reject document data")
async def confirm_document(id: str, request: CorrectDocumentRequest):
    """
    Accepts the final corrected data from the user and marks the document processing as ACCEPTED or REJECTED.
    """
    if not ObjectId.is_valid(id):
        raise HTTPException(status_code=400, detail="Invalid document ID format.")
        
    db = get_db()
    
    update_data = {
        "status": request.status,
        "extracted_data": request.extracted_data
    }
    
    if request.classification is not None:
        update_data["classification"] = request.classification
        
    result = await db.documents.update_one(
        {"_id": ObjectId(id)},
        {"$set": update_data}
    )
    
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Document not found.")
    
    return ConfirmDocumentResponse(
        document_id=id,
        status=request.status,
        message=f"Document explicitly marked as {request.status}."
    )
