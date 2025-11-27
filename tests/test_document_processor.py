import os
import sys
import unittest
from pathlib import Path

# Add project root to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.document_processor import DocumentProcessor

class TestDocumentProcessor(unittest.TestCase):
    def setUp(self):
        # Mock streamlit to avoid errors during init if it uses st.error
        import streamlit
        self.original_error = streamlit.error
        self.original_warning = streamlit.warning
        self.original_success = streamlit.success
        self.original_spinner = streamlit.spinner
        
        streamlit.error = lambda x: print(f"ST ERROR: {x}")
        streamlit.warning = lambda x: print(f"ST WARNING: {x}")
        streamlit.success = lambda x: print(f"ST SUCCESS: {x}")
        # Mock spinner context manager
        class MockSpinner:
            def __enter__(self): pass
            def __exit__(self, exc_type, exc_val, exc_tb): pass
        streamlit.spinner = lambda x: MockSpinner()

        self.processor = DocumentProcessor()
        self.test_dir = "tests/test_docs"
        os.makedirs(self.test_dir, exist_ok=True)

    def tearDown(self):
        import streamlit
        streamlit.error = self.original_error
        streamlit.warning = self.original_warning
        streamlit.success = self.original_success
        streamlit.spinner = self.original_spinner
        
        # Clean up test files
        if os.path.exists(self.test_dir):
            for f in os.listdir(self.test_dir):
                os.remove(os.path.join(self.test_dir, f))
            os.rmdir(self.test_dir)

    def test_load_empty_directory(self):
        docs = self.processor.load_documents(self.test_dir)
        self.assertEqual(len(docs), 0)

    def test_load_bad_pdf(self):
        # Create a dummy bad PDF
        bad_pdf_path = os.path.join(self.test_dir, "bad.pdf")
        with open(bad_pdf_path, "wb") as f:
            f.write(b"Not a PDF content")
        
        # Should not crash and return empty list (or list without that file)
        docs = self.processor.load_documents(self.test_dir)
        self.assertEqual(len(docs), 0)

    def test_load_valid_txt(self):
        txt_path = os.path.join(self.test_dir, "good.txt")
        with open(txt_path, "w") as f:
            f.write("Hello world")
        
        docs = self.processor.load_documents(self.test_dir)
        self.assertEqual(len(docs), 1)
        self.assertEqual(docs[0]['content'], "Hello world")

if __name__ == '__main__':
    unittest.main()
