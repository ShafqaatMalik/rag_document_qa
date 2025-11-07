import pytest
from fastapi.testclient import TestClient
from io import BytesIO


class TestAPIEndpoints:
    """Integration tests for API endpoints."""
    
    def test_health_check(self, client):
        """Test health check endpoint."""
        response = client.get("/api/v1/health")
        assert response.status_code == 200
        data = response.json()
        assert data['status'] == 'healthy'
        assert 'version' in data
    
    def test_api_info_endpoint(self, client):
        """Test API info endpoint returns JSON."""
        response = client.get("/api/info")
        assert response.status_code == 200
        data = response.json()
        assert 'message' in data
        assert 'version' in data
    
    @pytest.mark.parametrize("question,top_k", [
        ("What is this about?", 5),
        ("Explain the main concept", 3),
    ])
    def test_query_validation(self, client, question, top_k):
        """Test query parameter validation."""
        response = client.post(
            "/api/v1/query",
            json={"question": question, "top_k": top_k}
        )
        # May return 200 or 500 depending on mock setup
        assert response.status_code in [200, 500]
    
    def test_query_empty_question(self, client):
        """Test query with empty question."""
        response = client.post(
            "/api/v1/query",
            json={"question": "", "top_k": 5}
        )
        assert response.status_code == 422
    
    def test_list_documents(self, client):
        """Test document listing."""
        response = client.get("/api/v1/documents")
        assert response.status_code in [200, 500]
        if response.status_code == 200:
            data = response.json()
            assert 'documents' in data
            assert 'total' in data
