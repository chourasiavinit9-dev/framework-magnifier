import unittest
import sys
import os

# Add parent directory to path so we can import magnifier
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import magnifier
import psutil

class TestMagnifier(unittest.TestCase):
    
    def test_get_gemini_model_missing_key(self):
        # Temporarily remove key if exists
        original_key = os.environ.get("GEMINI_API_KEY")
        if original_key:
            del os.environ["GEMINI_API_KEY"]
            
        with self.assertRaises(SystemExit):
            magnifier.get_gemini_model()
            
        # Restore key
        if original_key:
            os.environ["GEMINI_API_KEY"] = original_key

    def test_psutil_can_fetch_processes(self):
        # Just ensure psutil is working on the runner system
        procs = list(psutil.process_iter(['pid', 'name']))
        self.assertGreater(len(procs), 0, "Should find running processes")
        
    def test_dependency_manager_config(self):
        self.assertIn('requirements.txt', magnifier.DEPENDENCY_MANAGERS)
        self.assertIn('package.json', magnifier.DEPENDENCY_MANAGERS)

if __name__ == '__main__':
    unittest.main()
