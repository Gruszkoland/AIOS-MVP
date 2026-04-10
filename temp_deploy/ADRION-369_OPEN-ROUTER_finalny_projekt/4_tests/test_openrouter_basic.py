import unittest
import sys
import os
import json
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

class TestOpenRouterBasic(unittest.TestCase):
    """Basic connectivity and configuration tests"""
    
    def test_env_file_exists(self):
        """Verify .env file is present"""
        env_path = Path('..') / '.env'
        self.assertTrue(env_path.exists(), ".env file not found")
    
    def test_env_has_openrouter_key(self):
        """Verify OPENROUTER_API_KEY is in .env"""
        with open('../.env', 'r') as f:
            content = f.read()
            self.assertIn('OPENROUTER_API_KEY', content, "OPENROUTER_API_KEY not found in .env")
    
    def test_config_files_exist(self):
        """Verify all config files are present"""
        configs = [
            '../3_config/openrouter/models.json',
            '../3_config/openrouter/settings.json',
            '../1_env_templates/.env.openrouter-production'
        ]
        for config in configs:
            config_path = Path(config)
            self.assertTrue(config_path.exists(), f"Config not found: {config}")
    
    def test_docker_compose_files(self):
        """Verify docker-compose files exist"""
        docker_files = [
            '../6_docker/docker-compose.cloud.yml',
            '../6_docker/docker-compose.yml'
        ]
        for docker_file in docker_files:
            docker_path = Path(docker_file)
            self.assertTrue(docker_path.exists(), f"Docker file not found: {docker_file}")
    
    def test_documentation_completeness(self):
        """Verify all doc files are present"""
        docs = [
            '../5_docs/INDEX_READ_ME_FIRST.md',
            '../5_docs/QUICKSTART_OPENROUTER.md',
            '../5_docs/OPENROUTER_CONFIG.md',
            '../5_docs/DEPLOYMENT_CHECKLIST.md'
        ]
        for doc in docs:
            doc_path = Path(doc)
            self.assertTrue(doc_path.exists(), f"Documentation not found: {doc}")

    def test_scripts_exist(self):
        """Verify deployment scripts are present"""
        scripts = [
            '../2_scripts/deployment/validate-openrouter-key.sh',
            '../2_scripts/deployment/deploy-openrouter-full.sh',
            '../2_scripts/deployment/verify-openrouter-setup.sh'
        ]
        for script in scripts:
            script_path = Path(script)
            self.assertTrue(script_path.exists(), f"Script not found: {script}")

    def test_models_config_valid_json(self):
        """Verify models.json is valid JSON"""
        with open('../3_config/openrouter/models.json', 'r') as f:
            try:
                data = json.load(f)
                self.assertIsInstance(data, dict, "models.json should contain JSON object")
                self.assertIn('models', data, "models.json missing 'models' key")
                self.assertIsInstance(data['models'], list, "models should be a list")
            except json.JSONDecodeError as e:
                self.fail(f"models.json invalid JSON: {e}")

if __name__ == '__main__':
    unittest.main(verbosity=2)
