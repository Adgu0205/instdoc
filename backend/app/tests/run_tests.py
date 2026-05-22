import unittest
import asyncio
import os
import sys

# Ensure backend root is on python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from app.middleware.security import validate_file_metadata, verify_file_signature, validate_text_size
from app.services.cache_service import get_cached_analysis, cache_analysis, get_contract_hash
from app.services.analytics_service import record_analysis, get_analytics
from app.services.task_manager import create_task, tasks
from fastapi import HTTPException

class TestSecurityMiddleware(unittest.TestCase):
    def test_validate_file_metadata_valid(self):
        # Should not raise exception
        validate_file_metadata("contract.pdf", "application/pdf")
        validate_file_metadata("NDA.docx", "application/vnd.openxmlformats-officedocument.wordprocessingml.document")
        validate_file_metadata("readme.txt", "text/plain")

    def test_validate_file_metadata_invalid_ext(self):
        with self.assertRaises(HTTPException) as ctx:
            validate_file_metadata("virus.exe", "application/pdf")
        self.assertEqual(ctx.exception.status_code, 400)
        self.assertIn("Unsupported file format", ctx.exception.detail)

    def test_validate_file_metadata_invalid_mime(self):
        with self.assertRaises(HTTPException) as ctx:
            validate_file_metadata("contract.pdf", "application/json")
        self.assertEqual(ctx.exception.status_code, 400)
        self.assertIn("Unsupported file content type", ctx.exception.detail)

    def test_verify_file_signature_valid(self):
        # Should not raise exception
        verify_file_signature("contract.pdf", b"%PDF-1.4 header")
        verify_file_signature("NDA.docx", b"PK\x03\x04ziparchive")
        verify_file_signature("readme.txt", b"plain text contract contents")

    def test_verify_file_signature_invalid_pdf(self):
        with self.assertRaises(HTTPException) as ctx:
            verify_file_signature("contract.pdf", b"NOTAPDF header")
        self.assertEqual(ctx.exception.status_code, 400)
        self.assertIn("MIME verification failed", ctx.exception.detail)

    def test_verify_file_signature_invalid_docx(self):
        with self.assertRaises(HTTPException) as ctx:
            verify_file_signature("contract.docx", b"NOTAZIP header")
        self.assertEqual(ctx.exception.status_code, 400)
        self.assertIn("MIME verification failed", ctx.exception.detail)

    def test_verify_file_signature_invalid_txt(self):
        with self.assertRaises(HTTPException) as ctx:
            verify_file_signature("contract.txt", b"text contents with \x00 null bytes")
        self.assertEqual(ctx.exception.status_code, 400)
        self.assertIn("contains binary/null character data", ctx.exception.detail)

    def test_validate_text_size_limits(self):
        validate_text_size("a" * 100) # Should pass
        with self.assertRaises(HTTPException) as ctx:
            validate_text_size("a" * 1000001)
        self.assertEqual(ctx.exception.status_code, 413)

class TestCacheService(unittest.TestCase):
    def test_cache_get_and_set(self):
        text = "This is a dummy contract to cache."
        result = {"overallRisk": 35, "riskLevel": "MEDIUM"}
        
        # Cache it
        cache_analysis(text, result)
        
        # Verify retrieved analysis matches
        self.assertEqual(get_cached_analysis(text), result)

class TestAnalyticsService(unittest.TestCase):
    def setUp(self):
        # Access the global dictionary inside the analytics module to reset it
        from app.services.analytics_service import _stats
        _stats.clear()
        _stats.update({
            "total_analyzed": 0,
            "total_risk_score": 0,
            "average_risk_score": 0.0,
            "contract_types": {}
        })

    def test_track_metrics(self):
        record_analysis("Non-Disclosure Agreement", 10)
        record_analysis("Service Contract", 20)
        record_analysis("Non-Disclosure Agreement", 30)

        metrics = get_analytics()
        self.assertEqual(metrics["total_analyzed"], 3)
        self.assertEqual(metrics["average_risk_score"], 20.0)
        self.assertEqual(metrics["contract_types"]["Non-Disclosure Agreement"], 2)
        self.assertEqual(metrics["contract_types"]["Service Contract"], 1)

class TestTaskManager(unittest.TestCase):
    def test_create_and_update_task(self):
        task_id = create_task()
        self.assertIsNotNone(task_id)
        self.assertIn(task_id, tasks)
        
        task_state = tasks[task_id]
        self.assertEqual(task_state.status, "pending")
        self.assertEqual(task_state.stage, "Uploading")
        self.assertEqual(task_state.progress, 0)

        # Update status
        task_state.update_stage("Parsing", 25)
        self.assertEqual(task_state.status, "processing")
        self.assertEqual(task_state.stage, "Parsing")
        self.assertEqual(task_state.progress, 25)

        # Complete task
        dummy_result = {"dummy": "data"}
        task_state.complete(dummy_result)
        self.assertEqual(task_state.status, "completed")
        self.assertEqual(task_state.result, dummy_result)

    def test_fail_task(self):
        task_id = create_task()
        task_state = tasks[task_id]
        task_state.fail("Gemini API rate limit exceeded")
        self.assertEqual(task_state.status, "failed")
        self.assertEqual(task_state.error, "Gemini API rate limit exceeded")

if __name__ == '__main__':
    unittest.main()
