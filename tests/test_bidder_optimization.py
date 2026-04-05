import unittest
from unittest.mock import patch, MagicMock

# Import modules from arbitrage
from arbitrage.bidder import _generate_cover_letter
from arbitrage.config import COVER_LETTER_SYSTEM

class TestBidderPrompts(unittest.TestCase):

    def setUp(self):
        self.sample_job = {
            "id": "test_123",
            "title": "Python Developer",
            "platform": "Upwork",
            "description": "Need a dev to build a scraper."
        }

    @patch('arbitrage.bidder.get_active_llm_backend')
    @patch('openai.OpenAI')
    def test_openrouter_prompt_integration(self, mock_openai, mock_get_backend):
        # Setup
        mock_get_backend.return_value = "openrouter"
        mock_client = MagicMock()
        mock_openai.return_value = mock_client

        mock_response = MagicMock()
        mock_response.choices = [MagicMock(message=MagicMock(content="Mocked Cover Letter"))]
        mock_client.chat.completions.create.return_value = mock_response

        # Execute
        result = _generate_cover_letter(self.sample_job, 50.0, 5.0)

        # Assert
        self.assertEqual(result, "Mocked Cover Letter")

        # Verify if correct system prompt was used (from config)
        args, kwargs = mock_client.chat.completions.create.call_args
        messages = kwargs.get('messages')

        system_msg = next(m for m in messages if m['role'] == 'system')
        self.assertEqual(system_msg['content'], COVER_LETTER_SYSTEM)

        user_msg = next(m for m in messages if m['role'] == 'user')
        self.assertIn("Python Developer", user_msg['content'])
        self.assertIn("Upwork", user_msg['content'])

    def test_mock_backend_format(self):
        with patch('arbitrage.bidder.get_active_llm_backend', return_value="mock"):
            result = _generate_cover_letter(self.sample_job, 100.0, 10.0)
            self.assertIn("Python Developer", result)
            self.assertIn("$100.0", result)

if __name__ == '__main__':
    unittest.main()
