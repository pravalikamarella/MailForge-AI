"""
Unit tests for the AI Email Assistant helper functions.
Covers stats calculations, PDF cleaning, TXT generation, and local storage.
"""

import unittest
import os
import json
import sqlite3
import utils
import prompts

class TestEmailAssistant(unittest.TestCase):
    
    def test_text_stats_empty(self):
        """Test text stats with empty input."""
        stats = utils.get_text_stats("")
        self.assertEqual(stats["words"], 0)
        self.assertEqual(stats["chars"], 0)
        self.assertEqual(stats["reading_time"], "0s")
        
    def test_text_stats_calculation(self):
        """Test text stats with mock input containing 10 words."""
        sample_text = "One two three four five six seven eight nine ten"
        stats = utils.get_text_stats(sample_text)
        self.assertEqual(stats["words"], 10)
        self.assertEqual(stats["chars"], 48)
        self.assertEqual(stats["reading_time"], "3s") # 10 / 200 * 60 = 3 seconds
        
    def test_clean_for_pdf_quotes(self):
        """Test that smart curly quotes are successfully normalized to flat ASCII ones."""
        smart_text = "We \u201cvalue\u201d your feedback and \u2018appreciate\u2019 your business."
        cleaned = utils.clean_for_pdf(smart_text)
        self.assertNotIn("\u201c", cleaned)
        self.assertNotIn("\u201d", cleaned)
        self.assertNotIn("\u2018", cleaned)
        self.assertNotIn("\u2019", cleaned)
        self.assertIn('"value"', cleaned)
        self.assertIn("'appreciate'", cleaned)

    def test_generate_txt(self):
        """Test plain text generator helper returns valid bytes and details."""
        txt_bytes = utils.generate_txt(
            subject="Test Subject",
            body="Hello Team, this is a test body.",
            sender="Alice",
            recipient="Bob",
            category="Formal",
            tone="Professional"
        )
        self.assertIsInstance(txt_bytes, bytes)
        decoded = txt_bytes.decode("utf-8")
        self.assertIn("Test Subject", decoded)
        self.assertIn("Hello Team", decoded)
        self.assertIn("Category: Formal", decoded)
        self.assertIn("Tone: Professional", decoded)
        self.assertIn("Sender: Alice", decoded)
        self.assertIn("Recipient: Bob", decoded)

    def test_database_autosave_draft(self):
        """Test that draft state is successfully written to and read from SQLite."""
        test_draft = {
            "recipient": "Tester",
            "sender": "Developer",
            "subject": "Test Draft",
            "details": "Checking if SQLite is active.",
            "tone": "Confident"
        }
        
        # Save draft
        utils.save_draft("test_unit_draft", test_draft)
        
        # Load draft
        retrieved = utils.get_draft("test_unit_draft")
        self.assertEqual(retrieved.get("recipient"), "Tester")
        self.assertEqual(retrieved.get("sender"), "Developer")
        self.assertEqual(retrieved.get("subject"), "Test Draft")
        self.assertEqual(retrieved.get("tone"), "Confident")
        
        # Clean test draft key
        conn = sqlite3.connect(utils.DB_NAME)
        c = conn.cursor()
        c.execute("DELETE FROM drafts WHERE key = ?", ("test_unit_draft",))
        conn.commit()
        conn.close()

    def test_mock_mode_compose(self):
        """Test mock mode for generating emails."""
        prompt = (
            "- Subject Line Idea/Topic: Quarterly business review\n"
            "- Details/Points to Include: Discuss Q2 performance and Q3 outlook\n"
            "- Category: Formal\n"
            "- Recipient Name: Sarah\n"
            "- Sender Name: David\n"
            "- Target Audience: Executives\n"
            "- Desired Length: Medium\n"
            "- Tone: Professional"
        )
        response = utils.call_gemini(
            api_key="",
            model_name="gemini-2.0-flash",
            system_instruction="",
            prompt=prompt,
            creativity=0.7,
            mock_mode=True
        )
        self.assertIn("Quarterly business review", response.get("subject"))
        self.assertIn("Sarah", response.get("body"))
        self.assertIn("David", response.get("body"))
        self.assertTrue(len(response.get("alternatives")) > 0)
        self.assertTrue(len(response.get("action_items")) > 0)
        self.assertTrue(len(response.get("writing_tips")) > 0)

    def test_mock_mode_rewrite(self):
        """Test mock mode for rewriting emails."""
        prompt = (
            "You are tasked with rewriting an existing email.\n"
            "\"\"\"\n"
            "Hey Sarah, can we meet?\n"
            "\"\"\"\n"
            "Rewrite Instructions:\n"
            "- Desired Tone: Polite\n"
            "- Desired Length: Short\n"
            "- Target Audience: Sarah"
        )
        response = utils.call_gemini(
            api_key="",
            model_name="gemini-2.0-flash",
            system_instruction="",
            prompt=prompt,
            creativity=0.7,
            mock_mode=True
        )
        self.assertIn("Polished", response.get("subject"))
        self.assertTrue(len(response.get("action_items")) > 0)
        self.assertTrue(len(response.get("writing_tips")) > 0)

if __name__ == "__main__":
    unittest.main()
