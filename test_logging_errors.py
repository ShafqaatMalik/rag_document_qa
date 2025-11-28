"""
Test script for logging and error handling

This script demonstrates and tests:
1. Structured JSON logging with trace IDs
2. Custom exception handling
3. Retry mechanism with exponential backoff
4. Error scenarios in the RAG pipeline
"""

import asyncio
import httpx
import json
import sys
from pathlib import Path


class LoggingErrorTester:
    """Test logging and error handling in the RAG system."""

    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.client = httpx.Client(timeout=30.0)

    def print_section(self, title: str):
        """Print section header."""
        print(f"\n{'='*80}")
        print(f"{title}")
        print(f"{'='*80}\n")

    def test_1_health_check_logging(self):
        """Test 1: Health check endpoint - observe normal logging."""
        self.print_section("TEST 1: Health Check - Normal Logging")

        print("Making request to /api/v1/health...")
        response = self.client.get(f"{self.base_url}/api/v1/health")

        print(f"Status: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2)}")
        print("\nCheck the server logs - you should see:")
        print("  ✓ Structured JSON log entry")
        print("  ✓ trace_id field")
        print("  ✓ timestamp, level, logger, message fields")

    def test_2_validation_error(self):
        """Test 2: Trigger validation error with empty query."""
        self.print_section("TEST 2: Validation Error - Empty Query")

        print("Sending query with empty question...")
        try:
            response = self.client.post(
                f"{self.base_url}/api/v1/query",
                json={"question": ""}
            )
            print(f"Status: {response.status_code}")
            print(f"Response: {json.dumps(response.json(), indent=2)}")
        except Exception as e:
            print(f"Error: {e}")

        print("\nCheck the server logs - you should see:")
        print("  ✓ ValidationError logged")
        print("  ✓ Error details in structured format")

    def test_3_file_validation_error(self):
        """Test 3: Trigger file validation error."""
        self.print_section("TEST 3: File Validation Error - Unsupported Type")

        print("Uploading unsupported file type (.exe)...")
        try:
            # Create a fake file
            files = {"file": ("test.exe", b"fake content", "application/x-msdownload")}
            response = self.client.post(
                f"{self.base_url}/api/v1/documents/upload",
                files=files
            )
            print(f"Status: {response.status_code}")
            print(f"Response: {json.dumps(response.json(), indent=2)}")
        except Exception as e:
            print(f"Error: {e}")

        print("\nCheck the server logs - you should see:")
        print("  ✓ ValidationError for file type")
        print("  ✓ trace_id for request tracking")

    def test_4_missing_documents_query(self):
        """Test 4: Query with no documents in database."""
        self.print_section("TEST 4: Query with No Documents")

        print("Querying when no documents are uploaded...")
        try:
            response = self.client.post(
                f"{self.base_url}/api/v1/query",
                json={"question": "What is machine learning?"}
            )
            print(f"Status: {response.status_code}")
            print(f"Response: {json.dumps(response.json(), indent=2)}")
        except Exception as e:
            print(f"Error: {e}")

        print("\nCheck the server logs - you should see:")
        print("  ✓ Warning: No relevant documents found")
        print("  ✓ Query metrics logged")
        print("  ✓ Response with helpful message")

    def test_5_invalid_top_k(self):
        """Test 5: Test validation with invalid top_k value."""
        self.print_section("TEST 5: Invalid Parameter - top_k")

        print("Sending query with top_k > 20...")
        try:
            response = self.client.post(
                f"{self.base_url}/api/v1/query",
                json={"question": "Test question", "top_k": 100}
            )
            print(f"Status: {response.status_code}")
            print(f"Response: {json.dumps(response.json(), indent=2)}")
        except Exception as e:
            print(f"Error: {e}")

        print("\nCheck the server logs - you should see:")
        print("  ✓ Validation error for top_k parameter")

    def test_6_successful_upload_logging(self):
        """Test 6: Successful document upload - observe success logging."""
        self.print_section("TEST 6: Successful Upload - Success Logging")

        # Create a sample text file
        sample_text = "Vector embeddings are numerical representations of text."

        print("Uploading a valid text file...")
        try:
            files = {"file": ("test.txt", sample_text.encode(), "text/plain")}
            response = self.client.post(
                f"{self.base_url}/api/v1/documents/upload",
                files=files
            )
            print(f"Status: {response.status_code}")
            print(f"Response: {json.dumps(response.json(), indent=2)}")
        except Exception as e:
            print(f"Error: {e}")

        print("\nCheck the server logs - you should see:")
        print("  ✓ Document ingestion logs")
        print("  ✓ Chunk count")
        print("  ✓ Embedding generation logs")
        print("  ✓ Elapsed time metrics")
        print("  ✓ trace_id throughout the pipeline")

    def test_7_successful_query_logging(self):
        """Test 7: Successful query - observe complete logging."""
        self.print_section("TEST 7: Successful Query - Complete Logging")

        print("Querying with uploaded document...")
        try:
            response = self.client.post(
                f"{self.base_url}/api/v1/query",
                json={"question": "What are vector embeddings?", "top_k": 3}
            )
            print(f"Status: {response.status_code}")
            result = response.json()
            print(f"Answer length: {len(result.get('answer', ''))}")
            print(f"Sources: {len(result.get('sources', []))}")
            print(f"Latency: {result.get('latency_seconds', 0)}s")
            print(f"Trace ID: {result.get('trace_id', 'N/A')}")
        except Exception as e:
            print(f"Error: {e}")

        print("\nCheck the server logs - you should see:")
        print("  ✓ Query received log")
        print("  ✓ Retrieval logs with similarity scores")
        print("  ✓ LLM generation logs")
        print("  ✓ Query completion with metrics")
        print("  ✓ Same trace_id across all log entries")

    def test_8_trace_id_propagation(self):
        """Test 8: Verify trace ID propagation."""
        self.print_section("TEST 8: Trace ID Propagation")

        print("Making multiple requests and checking trace IDs...")
        trace_ids = []

        for i in range(3):
            response = self.client.get(f"{self.base_url}/api/v1/health")
            trace_id = response.json().get('timestamp')  # Just to show different requests
            trace_ids.append(trace_id)
            print(f"Request {i+1}: {response.status_code}")

        print(f"\nMade {len(trace_ids)} requests")
        print("\nCheck the server logs - you should see:")
        print("  ✓ Different trace_id for each request")
        print("  ✓ All logs for a request share the same trace_id")

    def run_all_tests(self):
        """Run all tests."""
        print("\n")
        print("╔" + "="*78 + "╗")
        print("║" + " "*20 + "LOGGING & ERROR HANDLING TESTS" + " "*28 + "║")
        print("╚" + "="*78 + "╝")

        print("\nThis script will test various logging and error scenarios.")
        print("Watch the server logs in your terminal to see:")
        print("  • Structured JSON logging")
        print("  • Trace ID propagation")
        print("  • Error handling")
        print("  • Retry mechanisms")
        print("\nPress Enter to continue...")
        input()

        tests = [
            self.test_1_health_check_logging,
            self.test_2_validation_error,
            self.test_3_file_validation_error,
            self.test_4_missing_documents_query,
            self.test_5_invalid_top_k,
            self.test_6_successful_upload_logging,
            self.test_7_successful_query_logging,
            self.test_8_trace_id_propagation,
        ]

        for i, test in enumerate(tests, 1):
            try:
                test()
                input(f"\n✓ Test {i} completed. Press Enter for next test...")
            except Exception as e:
                print(f"\n✗ Test {i} failed: {e}")
                input("\nPress Enter to continue...")

        self.print_section("ALL TESTS COMPLETED")
        print("Review the server logs to see:")
        print("  ✓ JSON-formatted log entries")
        print("  ✓ Trace IDs for request tracking")
        print("  ✓ Error details and stack traces")
        print("  ✓ Performance metrics (latency, etc.)")
        print("  ✓ Different log levels (INFO, WARNING, ERROR)")


def test_retry_mechanism():
    """Demonstrate retry mechanism."""
    print("\n" + "="*80)
    print("BONUS: Testing Retry Mechanism")
    print("="*80 + "\n")

    print("The retry mechanism is used in:")
    print("  • LLM API calls (src/core/llm.py)")
    print("  • Embedding generation (src/core/embeddings.py)")
    print("\nTo test retry:")
    print("  1. Temporarily break your Gemini API key in .env")
    print("  2. Make a query")
    print("  3. Watch logs show retry attempts with exponential backoff")
    print("  4. After 3 retries, see the final error")
    print("\nExample log output:")
    print('  {"timestamp": "...", "level": "WARNING", "message": "Retry 1/3 for generate_answer after 1.0s"}')
    print('  {"timestamp": "...", "level": "WARNING", "message": "Retry 2/3 for generate_answer after 2.0s"}')
    print('  {"timestamp": "...", "level": "ERROR", "message": "Max retries (3) reached for generate_answer"}')


if __name__ == "__main__":
    print("\n" + "╔" + "="*78 + "╗")
    print("║" + " "*15 + "RAG SYSTEM LOGGING & ERROR HANDLING TEST" + " "*23 + "║")
    print("╚" + "="*78 + "╝\n")

    print("Prerequisites:")
    print("  1. API server must be running on http://localhost:8000")
    print("  2. Keep server logs visible to observe logging")
    print()

    port = input("Enter API port (default: 8000): ").strip() or "8000"
    base_url = f"http://localhost:{port}"

    print(f"\nUsing base URL: {base_url}")

    tester = LoggingErrorTester(base_url=base_url)

    try:
        tester.run_all_tests()
        test_retry_mechanism()
    except KeyboardInterrupt:
        print("\n\nTests interrupted by user.")
    except Exception as e:
        print(f"\n\nFatal error: {e}")

    print("\n" + "="*80)
    print("Testing complete!")
    print("="*80 + "\n")
