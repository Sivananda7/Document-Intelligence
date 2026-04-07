import asyncio
import os
import json
from schemas import DRIVER_LICENSE_SCHEMA, PASSPORT_SCHEMA, STUDENT_ID_SCHEMA, TX_POA_SCHEMA, TEMPLATE_MAP, enforce_schema
from bson import ObjectId
from database import get_db
import tempfile
import io
import fitz
import numpy as np
from PIL import Image
from doctr.io import DocumentFile
from doctr.models import ocr_predictor
from google import genai
from google.genai import types
from tenacity import retry, stop_after_attempt, wait_exponential

gemini_key = os.getenv("GEMINI_API_KEY")
if not gemini_key:
    raise ValueError("GEMINI_API_KEY is not set in the environment variables.")
client = genai.Client(api_key=gemini_key)

# Initialize docTR model
# We use db_resnet50 for detection and crnn_vgg16_bn for recognition by default
# Setting pretrained=True downloads and uses the pretrained weights.
doctr_model = ocr_predictor(det_arch='db_resnet50', reco_arch='crnn_vgg16_bn', pretrained=True)

class DocumentProcessingService:
    @staticmethod
    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10), reraise=True)
    async def extract_text_ocr(file_path: str, file_name: str) -> str:
        print("Extracting text natively using docTR...")
        
        def run_doctr():
            try:
                full_text = ""
                is_pdf = file_name and file_name.lower().endswith('.pdf')
                
                if is_pdf:
                    try:
                        doc_fitz = fitz.open(file_path)
                        for page in doc_fitz:
                            page_text = page.get_text()
                            if page_text.strip():
                                full_text += page_text + "\\n"
                        if full_text.strip():
                            print("Native text found in PDF. Skipping OCR.")
                            return full_text
                    except Exception as e:
                        print(f"PyMuPDF native text extraction failed: {e}. Falling back to OCR.")
                        full_text = ""
                
                print("No native text found or it is an image. Running docTR OCR...")
                # Provide path to docTR
                if is_pdf:
                    doc = DocumentFile.from_pdf(file_path)
                else:
                    doc = DocumentFile.from_images(file_path)

                # Process document
                result = doctr_model(doc)
                
                # Extract text lines
                for page in result.pages:
                    for block in page.blocks:
                        for line in block.lines:
                            line_text = " ".join([word.value for word in line.words])
                            full_text += line_text + "\\n"
                
                return full_text
            except Exception as e:
                raise Exception(f"docTR parsing error: {e}")

        try:
            # Offload CPU-heavy OCR to a separate thread
            extracted_text = await asyncio.to_thread(run_doctr)
            
            if not extracted_text.strip():
                return "No legible text found in document."
            return extracted_text.strip()
        except Exception as e:
            print(f"docTR failed: {e}")
            raise Exception(f"docTR Extraction Failed: {e}")

    @staticmethod
    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10), reraise=True)
    async def extract_structured_data(ocr_text: str) -> dict:
        prompt = f"""
You are an expert document understanding and structured data extraction system.

TASK
1. Determine the document type from the OCR text.
2. Select the most appropriate schema from the schemas provided below.
3. Extract the data according to that schema.

STRICTLY DOCUMENT TYPES AVAILABLE
1. driver_license
2. passport
3. student_id
4. vehicle_power_of_attorney
5. unknown

RULES
• Choose the schema that best matches the document.
• If none match confidently, return "document_type": "unknown", but you MUST STILL dynamically extract all salient information into logical key-value pairs inside the "data" object (e.g., name, dates, amounts, etc.).
• Never mix predefined schemas.
• Extract values exactly as shown in the document.
• If a predefined field cannot be found, set it to null.
• Do not hallucinate values.

OUTPUT FORMAT
Return ONLY valid JSON with the following structure:

{{
  "document_type": "<chosen_document_type>",
  "confidence": "<low|medium|high>",
  "data": {{ extracted data using the selected schema }}
}}

SCHEMAS

DRIVER LICENSE SCHEMA
{DRIVER_LICENSE_SCHEMA}

PASSPORT SCHEMA
{PASSPORT_SCHEMA}

STUDENT ID SCHEMA
{STUDENT_ID_SCHEMA}

VEHICLE POWER OF ATTORNEY SCHEMA
{TX_POA_SCHEMA}

CRITICAL
Return only JSON.
Do not include explanations or markdown.

OCR Text:
{ocr_text[:5000]}
"""
        try:
            response = await asyncio.to_thread(
                client.models.generate_content,
                model='gemini-3-flash-preview',
                contents=prompt,
                config=types.GenerateContentConfig(
                    temperature=0.0,
                    response_mime_type="application/json",
                ),
            )
            raw_json_str = response.text
            
            if not raw_json_str:
                print(f"Response empty or blocked. Details: {response}")
                raise ValueError("Empty response from LLM")
                
            raw_json_str = raw_json_str.strip()
            
            # Robust JSON extraction: find the first '{' and last '}'
            start_idx = raw_json_str.find('{')
            end_idx = raw_json_str.rfind('}')
            
            if start_idx != -1 and end_idx != -1:
                clean_json_str = raw_json_str[start_idx:end_idx+1]
            else:
                clean_json_str = raw_json_str # Fallback in case it's not a dictionary
                
            return json.loads(clean_json_str)
        except Exception as e:
            print(f"Extraction parsing error: {e}")
            raise Exception(f"Failed to generate valid structured data: {str(e)}")

    @staticmethod
    async def process_document(document_id: str, file_path: str, file_name: str = "document.pdf"):
        """
        Coordinates the OCR, classification, and extraction AI layers.
        """
        db = get_db()
        try:
            print(f"[{document_id}] Starting processing pipeline.")
            
            # Step 1: Text Extraction 
            print(f"[{document_id}] Extracting text ...")
            ocr_text = await DocumentProcessingService.extract_text_ocr(file_path, file_name)
            
            # Step 2 & 3: Consolidated classification + Extraction AI Prompt
            print(f"[{document_id}] LLM Extracting structural data and validating schema...")
            final_assessment = await DocumentProcessingService.extract_structured_data(ocr_text)
            
            classification = final_assessment.get("document_type", "unknown")
            raw_extracted_data = final_assessment.get("data", {})
            confidence = final_assessment.get("confidence", "low")
            
            # If Llama returns empty for an unknown document fallback to returning raw OCR text
            if classification == "unknown" and not raw_extracted_data:
                raw_extracted_data = {"raw_text": ocr_text}
            
            # Enforce schema to guarantee all template fields exist in the UI
            template = TEMPLATE_MAP.get(classification, {})
            extracted_data = enforce_schema(raw_extracted_data, template) if template else raw_extracted_data
            
            # Calculate extraction completeness % dynamically based on non-empty values
            def count_fields(d: dict):
                total, filled = 0, 0
                for k, v in d.items():
                    if isinstance(v, dict):
                        sub_t, sub_f = count_fields(v)
                        total += sub_t
                        filled += sub_f
                    else:
                        total += 1
                        if v is not None and str(v).strip() != "":
                            filled += 1
                return total, filled
                
            total_fields, filled_fields = count_fields(extracted_data) if isinstance(extracted_data, dict) else (0, 0)
            completeness = round((filled_fields / total_fields * 100), 1) if total_fields > 0 else 0.0
            
            # Step 4: Finalize MongoDB
            print(f"[{document_id}] Updating MongoDB status to REVIEW_PENDING ({classification} - {confidence} confidence, {completeness}% complete)...")
            await db.documents.update_one(
                {"_id": ObjectId(document_id)},
                {"$set": {
                    "status": "REVIEW_PENDING",
                    "classification": classification,
                    "extracted_data": extracted_data,
                    "extraction_completeness": completeness,
                    "confidence": confidence
                }}
            )
            print(f"[{document_id}] Pipeline completed successfully.")
            
        except Exception as e:
            print(f"[{document_id}] Critical failure in processing: {str(e)}")
            await db.documents.update_one(
                {"_id": ObjectId(document_id)},
                {"$set": {"status": "FAILED"}}
            )
        finally:
            # Clean up the large temp file to free disk space
            if os.path.exists(file_path):
                try:
                    os.remove(file_path)
                    print(f"[{document_id}] Temporary file cleaned up.")
                except Exception as cleanup_err:
                    print(f"[{document_id}] Failed to clean up temp file: {cleanup_err}")

document_processing_service = DocumentProcessingService()
