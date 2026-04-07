import pytest
from httpx import AsyncClient, ASGITransport
from main import app
from database import get_db
from mongomock_motor import AsyncMongoMockClient

# Setup a global mock client for the tests
mock_client = AsyncMongoMockClient()
mock_db = mock_client['test_db']

@pytest.fixture(autouse=True)
def override_db(monkeypatch):
    monkeypatch.setattr("main.get_db", lambda: mock_db)

@pytest.fixture(autouse=True)
def override_storage(monkeypatch):
    class MockStorage:
        def upload_file(self, file_path, original_filename):
            return f"s3://mock_bucket/{original_filename}"
    monkeypatch.setattr("main.storage_repo", MockStorage())

@pytest.fixture(autouse=True)
def override_processing(monkeypatch):
    class MockService:
        async def process_document(self, document_id, file_path, file_name):
            pass
    monkeypatch.setattr("main.DocumentProcessingService", MockService())

# Clear out any stale records before each test starts
@pytest.fixture(autouse=True)
async def clear_db():
    await mock_db.documents.delete_many({})

async def test_upload_document():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        file_content = b"fake image content"
        files = {'file': ('test.jpg', file_content, 'image/jpeg')}
        response = await ac.post("/api/v1/documents/upload", files=files)
        
    assert response.status_code == 200
    data = response.json()
    assert "document_id" in data
    assert data["status"] == "PROCESSING"
    assert "started in background" in data["message"]
    
async def test_upload_invalid_file_type():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        file_content = b"fake text content"
        files = {'file': ('test.txt', file_content, 'text/plain')}
        response = await ac.post("/api/v1/documents/upload", files=files)
        
    assert response.status_code == 400
    assert "Invalid file type" in response.json()["detail"]

async def test_get_document():
    result = await mock_db.documents.insert_one({
        "status": "COMPLETED",
        "classification": "passport",
        "extracted_data": {"name": "John Doe"},
        "extraction_completeness": 100.0,
        "confidence": "high"
    })
    doc_id = str(result.inserted_id)

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        response = await ac.get(f"/api/v1/documents/{doc_id}")
        
    assert response.status_code == 200
    data = response.json()
    assert data["document_id"] == doc_id
    assert data["status"] == "COMPLETED"
    assert data["classification"] == "passport"
    assert data["extracted_data"]["name"] == "John Doe"

async def test_get_document_not_found():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        # Use a random object_id
        response = await ac.get("/api/v1/documents/5f8b8be88b8b8b8b8b8b8b8b")
        
    assert response.status_code == 404
    assert response.json()["detail"] == "Document not found."

async def test_confirm_document():
    result = await mock_db.documents.insert_one({
        "status": "REVIEW_PENDING",
        "classification": "driver_license",
        "extracted_data": {"name": "Jane Doe"}
    })
    doc_id = str(result.inserted_id)

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        payload = {
            "status": "ACCEPTED",
            "classification": "driver_license",
            "extracted_data": {"name": "Jane Doe", "updated": True}
        }
        response = await ac.put(f"/api/v1/documents/{doc_id}/confirm", json=payload)
        
    assert response.status_code == 200
    
    # Verify the database updated
    updated_doc = await mock_db.documents.find_one({"_id": result.inserted_id})
    assert updated_doc["status"] == "ACCEPTED"
    assert updated_doc["extracted_data"].get("updated") is True
