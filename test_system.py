#!/usr/bin/env python3
"""
DevSecrin Test Script
Quick verification that the system is working correctly
"""

import sys
import os
import requests
import time
import json
from pathlib import Path

# Add the packages directory to the path
sys.path.insert(0, str(Path(__file__).parent / "packages"))

from packages.config import get_config

# Load configuration
config = get_config()

class TestRunner:
    def __init__(self):
        self.api_base = "http://localhost:8000"
        self.frontend_url = "http://localhost:3000"
        self.passed = 0
        self.failed = 0
        
    def test_api_health(self):
        """Test if API is healthy"""
        try:
            response = requests.get(f"{self.api_base}/health", timeout=5)
            if response.status_code == 200:
                data = response.json()
                if data.get("status") == "healthy":
                    print("✅ API Health Check: PASSED")
                    self.passed += 1
                    return True
                else:
                    print(f"❌ API Health Check: FAILED - Status: {data.get('status')}")
                    self.failed += 1
                    return False
            else:
                print(f"❌ API Health Check: FAILED - Status Code: {response.status_code}")
                self.failed += 1
                return False
        except Exception as e:
            print(f"❌ API Health Check: FAILED - {str(e)}")
            self.failed += 1
            return False
    
    def test_frontend_accessibility(self):
        """Test if frontend is accessible"""
        try:
            response = requests.get(self.frontend_url, timeout=5)
            if response.status_code == 200:
                print("✅ Frontend Accessibility: PASSED")
                self.passed += 1
                return True
            else:
                print(f"❌ Frontend Accessibility: FAILED - Status Code: {response.status_code}")
                self.failed += 1
                return False
        except Exception as e:
            print(f"❌ Frontend Accessibility: FAILED - {str(e)}")
            self.failed += 1
            return False
    
    def test_database_connection(self):
        """Test database connection"""
        try:
            from packages.db.db import engine
            from sqlalchemy import text
            
            with engine.connect() as conn:
                result = conn.execute(text("SELECT 1"))
                if result.fetchone()[0] == 1:
                    print("✅ Database Connection: PASSED")
                    self.passed += 1
                    return True
                else:
                    print("❌ Database Connection: FAILED - Query returned unexpected result")
                    self.failed += 1
                    return False
        except Exception as e:
            print(f"❌ Database Connection: FAILED - {str(e)}")
            self.failed += 1
            return False
    
    def test_ollama_connection(self):
        """Test Ollama connection"""
        try:
            response = requests.get(f"{config.ollama_host}/api/tags", timeout=10)
            if response.status_code == 200:
                models = response.json().get("models", [])
                model_names = [model["name"] for model in models]
                
                if any(config.ollama_model in name for name in model_names):
                    print("✅ Ollama Connection & Model: PASSED")
                    self.passed += 1
                    return True
                else:
                    print(f"❌ Ollama Model: FAILED - Required model '{config.ollama_model}' not found")
                    print(f"Available models: {model_names}")
                    self.failed += 1
                    return False
            else:
                print(f"❌ Ollama Connection: FAILED - Status Code: {response.status_code}")
                self.failed += 1
                return False
        except Exception as e:
            print(f"❌ Ollama Connection: FAILED - {str(e)}")
            self.failed += 1
            return False
    
    def test_vector_store(self):
        """Test vector store functionality"""
        try:
            from packages.ai.retriever.factory import get_vectorstore
            
            vectorstore = get_vectorstore("chroma", collection_name=f"{config.chroma_collection_name}_test")
            
            # Test adding a document
            test_embedding = [0.1] * 384  # Mock embedding
            vectorstore.add_document(
                doc_id="test_doc",
                embedding=test_embedding,
                document="This is a test document",
                metadata={"type": "test"}
            )
            
            # Test querying
            results = vectorstore.query(test_embedding, n_results=1)
            if results:
                print("✅ Vector Store: PASSED")
                self.passed += 1
                return True
            else:
                print("❌ Vector Store: FAILED - No results returned")
                self.failed += 1
                return False
        except Exception as e:
            print(f"❌ Vector Store: FAILED - {str(e)}")
            self.failed += 1
            return False
    
    def test_ai_generation(self):
        """Test AI text generation"""
        try:
            from packages.ai.newindex import run_graph_generator
            
            # Test with a simple question
            result = run_graph_generator("What is DevSecrin?")
            if result and len(result) > 0 and "Error" not in result:
                print("✅ AI Generation: PASSED")
                self.passed += 1
                return True
            else:
                print(f"❌ AI Generation: FAILED - {result}")
                self.failed += 1
                return False
        except Exception as e:
            print(f"❌ AI Generation: FAILED - {str(e)}")
            self.failed += 1
            return False
    
    def test_api_endpoints(self):
        """Test key API endpoints"""
        try:
            # Test status endpoint
            response = requests.get(f"{self.api_base}/api/status", timeout=5)
            if response.status_code != 200:
                print(f"❌ API Status Endpoint: FAILED - Status Code: {response.status_code}")
                self.failed += 1
                return False
            
            # Test chat endpoint
            chat_data = {"message": "Hello, this is a test"}
            response = requests.post(
                f"{self.api_base}/api/chat",
                json=chat_data,
                timeout=30
            )
            if response.status_code == 200:
                print("✅ API Endpoints: PASSED")
                self.passed += 1
                return True
            else:
                print(f"❌ API Chat Endpoint: FAILED - Status Code: {response.status_code}")
                self.failed += 1
                return False
        except Exception as e:
            print(f"❌ API Endpoints: FAILED - {str(e)}")
            self.failed += 1
            return False
    
    def test_configuration(self):
        """Test configuration loading"""
        try:
            config_dict = config.to_dict()
            
            if config_dict:
                print("✅ Configuration: PASSED")
                self.passed += 1
                return True
            else:
                print("❌ Configuration: FAILED - No configuration loaded")
                self.failed += 1
                return False
        except Exception as e:
            print(f"❌ Configuration: FAILED - {str(e)}")
            self.failed += 1
            return False
    
    def run_all_tests(self):
        """Run all tests"""
        print("🧪 Running DevSecrin System Tests...")
        print("=" * 50)
        
        # Load environment variables
        env_file = Path(".env")
        if env_file.exists():
            print("📁 Loading environment variables from .env")
            from dotenv import load_dotenv
            load_dotenv()
        else:
            print("⚠️  No .env file found, using defaults")
        
        print("\n🔍 Running Tests:")
        print("-" * 30)
        
        # Run tests
        self.test_configuration()
        self.test_database_connection()
        self.test_ollama_connection()
        self.test_vector_store()
        self.test_api_health()
        self.test_frontend_accessibility()
        self.test_api_endpoints()
        self.test_ai_generation()
        
        # Print summary
        print("\n" + "=" * 50)
        print(f"📊 Test Summary:")
        print(f"✅ Passed: {self.passed}")
        print(f"❌ Failed: {self.failed}")
        print(f"📈 Success Rate: {(self.passed / (self.passed + self.failed) * 100):.1f}%")
        
        if self.failed == 0:
            print("\n🎉 All tests passed! DevSecrin is ready to use.")
            return True
        else:
            print(f"\n⚠️  {self.failed} test(s) failed. Please check the issues above.")
            return False

def main():
    """Main function"""
    test_runner = TestRunner()
    success = test_runner.run_all_tests()
    
    if success:
        print("\n🚀 Next Steps:")
        print("1. Open http://localhost:3000 in your browser")
        print("2. Configure your GitHub/Confluence integrations")
        print("3. Start asking questions about your codebase!")
        sys.exit(0)
    else:
        print("\n🔧 Troubleshooting:")
        print("1. Check that all services are running: docker-compose ps")
        print("2. Check logs: docker-compose logs")
        print("3. Verify your .env configuration")
        print("4. Ensure Ollama is running and models are downloaded")
        sys.exit(1)

if __name__ == "__main__":
    main()
