from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
from datetime import datetime
from bson import ObjectId

class PyObjectId(ObjectId):
    @classmethod
    def __get_validators__(cls):
        yield cls.validate

    @classmethod
    def validate(cls, v):
        if not ObjectId.is_valid(v):
            raise ValueError("Invalid objectid")
        return ObjectId(v)

    @classmethod
    def __get_pydantic_json_schema__(cls, field_schema):
        field_schema.update(type="string")

class DocumentModel(BaseModel):
    id: Optional[PyObjectId] = Field(default_factory=PyObjectId, alias="_id")
    object_storage_uri: str
    status: str = Field(default="PROCESSING")
    classification: Optional[str] = None
    
    # We store the structured JSON output from the LLM here.
    # We do NOT explicitly define what fields are inside it (e.g. first_name, last_name).
    # It maps roughly to per-page JSON output: { "page_1": {...}, "page_2": {...} }
    extracted_data: Optional[Dict[str, Any]] = None
    extraction_completeness: Optional[float] = None
    confidence: Optional[str] = None
    
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}
