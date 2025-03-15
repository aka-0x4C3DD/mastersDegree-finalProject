import requests
import sys
import json
import os
from datetime import datetime

class ClinicalBERTClient:
    """Client for interacting with the ClinicalBERT server API"""
    
    def __init__(self, server_url="http://localhost:5000"):
        self.server_url = server_url
    
    def test_connection(self):
        """Test the connection to the server"""
        try:
            response = requests.get(f"{self.server_url}/api/health", timeout=5)
            if response.status_code == 200:
                return True, "Successfully connected to the server!"
            else:
                return False, f"Server returned status code: {response.status_code}"
        except Exception as e:
            return False, str(e)
    
    def submit_query(self, query, search_web=True):
        """Submit a query to the server"""
        if not query:
            return {"error": "No query provided"}
        
        try:
            data = {
                "query": query,
                "search_web": search_web
            }
            
            response = requests.post(
                f"{self.server_url}/api/query", 
                json=data,
                timeout=30
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                error_msg = f"Server error: {response.status_code}"
                if response.text:
                    error_msg += f" - {response.text}"
                return {"error": error_msg}
        except Exception as e:
            return {"error": str(e)}
    
    def upload_file(self, file_path):
        """Upload a file for processing"""
        if not os.path.exists(file_path):
            return {"error": "File not found"}
        
        try:
            with open(file_path, "rb") as file:
                files = {"file": (os.path.basename(file_path), file)}
                response = requests.post(
                    f"{self.server_url}/api/process-file",
                    files=files,
                    timeout=60
                )
            
            if response.status_code == 200:
                result = response.json()
                result["filename"] = os.path.basename(file_path)
                return result
            else:
                error_msg = f"Server error: {response.status_code}"
                if response.text:
                    error_msg += f" - {response.text}"
                return {"error": error_msg}
        except Exception as e:
            return {"error": str(e)}

if __name__ == "__main__":
    # Example usage:
    server_url = "http://localhost:5000"
    if len(sys.argv) > 1:
        server_url = sys.argv[1]
    
    client = ClinicalBERTClient(server_url)
    
    # Test connection
    success, message = client.test_connection()
    print(f"Connection test: {message}")
    
    if success:
        # Example query
        result = client.submit_query("What are the symptoms of type 2 diabetes?")
        print("\nQuery result:")
        print(json.dumps(result, indent=2))