import json
import os
import sys
import argparse
import urllib.request

def import_workflow(file_path, n8n_url, api_key):
    if not os.path.exists(file_path):
        print(f"Error: File {file_path} not found.")
        return

    with open(file_path, 'r', encoding='utf-8') as f:
        workflow_data = json.load(f)

    # n8n expects workflow in a specific format for API
    # Usually: { "name": "...", "nodes": [...], "connections": {...}, "settings": {...}, "staticData": {...} }
    
    headers = {
        'X-N8N-API-KEY': api_key,
        'Content-Type': 'application/json'
    }
    
    # Check if workflow already exists or create new
    req = urllib.request.Request(
        f"{n8n_url}/workflows",
        data=json.dumps(workflow_data).encode('utf-8'),
        headers=headers,
        method='POST'
    )
    
    try:
        with urllib.request.urlopen(req) as resp:
            result = json.loads(resp.read().decode('utf-8'))
            print(f"Success: Workflow imported/created. ID: {result.get('id')}")
    except Exception as e:
        print(f"Error during import: {e}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Import n8n workflow JSON via API.")
    parser.get_default("file")
    parser.add_argument("--file", required=True, help="Path to workflow JSON file")
    parser.add_argument("--url", default="http://localhost:5678/api/v1", help="n8n API URL")
    parser.add_argument("--key", required=True, help="n8n API Key")
    
    args = parser.parse_args()
    import_workflow(args.file, args.url, args.key)
