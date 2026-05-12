#!/usr/bin/env python3
"""
Agent Validation Suite for ADRION 369 33-Personas System
Validates ROPE 2.0 compliance, ROPE template structure, and agent readiness.
Fixes: CRLF/LF normalization, ROPE_VERSION in HTML comments, placeholder detection.
"""

import os
import re
import json
import sys
from pathlib import Path
from typing import Dict, List, Tuple, Optional


class RopeValidator:
    """Validates ROPE 2.0 agents with fixed parser for edge cases."""
    
    def __init__(self, agents_dir: Path):
        self.agents_dir = agents_dir
        self.results = {}
        self.issues = []
        
    def normalize_line_endings(self, content: str) -> str:
        """Normalize CRLF/LF to consistent LF."""
        return content.replace('\r\n', '\n')
    
    def extract_rope_version(self, content: str) -> Optional[str]:
        """Extract ROPE_VERSION from HTML comments or plain text."""
        patterns = [
            r'ROPE_VERSION:\s*([0-9.]+)',  # Plain text
            r'<!--\s*ROPE_VERSION:\s*([0-9.]+)\s*-->',  # HTML comment
            r'<!-- ROPE_VERSION: ([0-9.]+) -->',  # HTML comment variant
        ]
        for pattern in patterns:
            match = re.search(pattern, content)
            if match:
                return match.group(1)
        return None
    
    def extract_sections(self, content: str) -> Dict[str, bool]:
        """Extract ROPE 2.0 sections (I-VI + SYSTEM_PAYLOAD)."""
        sections = {
            'I_CONTEXT': bool(re.search(r'##\s*I\.\s*CONTEXT', content)),
            'II_REASONING': bool(re.search(r'##\s*II\.\s*REASONING', content)),
            'III_CONSTRAINTS': bool(re.search(r'##\s*III\.\s*CONSTRAINTS', content)),
            'IV_OUTPUT_FORMAT': bool(re.search(r'##\s*IV\.\s*OUTPUT_FORMAT', content)),
            'V_SAFETY_CHECKS': bool(re.search(r'##\s*V\.\s*SAFETY_CHECKS', content)),
            'VI_EXAMPLES': bool(re.search(r'##\s*VI\.\s*EXAMPLES', content)),
            'SYSTEM_PAYLOAD': bool(re.search(r'---\s*SYSTEM_PAYLOAD\s*---', content, re.MULTILINE)),
        }
        return sections
    
    def check_placeholder_substitution(self, content: str, filename: str) -> Dict[str, bool]:
        """Check if placeholders are properly substituted (e.g., [AKRONIM]-[NR])."""
        # Extract agent identifier from filename (e.g., MPG-01 from MPG-01_filename.md)
        match = re.match(r'([A-Z0-9]+-\d+)', filename)
        agent_id = match.group(1) if match else None
        
        checks = {
            'has_agent_id': agent_id is not None,
            'agent_id_in_content': agent_id in content if agent_id else False,
            'has_unsubstituted_placeholders': bool(re.search(r'\[AKRONIM\]|\[NR\]', content)),
        }
        return checks
    
    def validate_agent(self, agent_file: Path) -> Dict:
        """Validate a single agent file."""
        try:
            content = agent_file.read_text(encoding='utf-8')
            content = self.normalize_line_endings(content)
        except Exception as e:
            return {
                'status': 'ERROR',
                'score': 0,
                'error': str(e)
            }
        
        rope_version = self.extract_rope_version(content)
        sections = self.extract_sections(content)
        placeholders = self.check_placeholder_substitution(content, agent_file.name)
        
        # Scoring
        score = 0
        issues = []
        
        # ROPE version check
        if rope_version == '2.0':
            score += 20
        elif rope_version:
            score += 10
            issues.append(f"ROPE version {rope_version}, expected 2.0")
        else:
            issues.append("ROPE version not found")
        
        # Sections check
        section_score = sum(1 for v in sections.values() if v) * (60 // 7)
        score += section_score
        missing_sections = [k for k, v in sections.items() if not v]
        if missing_sections:
            issues.append(f"Missing sections: {', '.join(missing_sections)}")
        
        # Placeholder check
        if placeholders['has_unsubstituted_placeholders']:
            score -= 10
            issues.append("Unsubstituted placeholders detected: [AKRONIM] or [NR]")
        
        status = 'PASS' if score >= 75 else 'WARN' if score >= 50 else 'FAIL'
        
        return {
            'status': status,
            'score': score,
            'rope_version': rope_version,
            'sections': sections,
            'placeholders': placeholders,
            'issues': issues
        }
    
    def validate_all(self) -> Tuple[Dict, List[Dict]]:
        """Validate all agents in directory."""
        if not self.agents_dir.exists():
            return {}, [{'file': 'N/A', 'status': 'ERROR', 'error': f'Directory not found: {self.agents_dir}'}]
        
        results = {}
        failed_agents = []
        
        for agent_file in sorted(self.agents_dir.glob('*.md')):
            result = self.validate_agent(agent_file)
            results[agent_file.name] = result
            
            if result['status'] != 'PASS':
                failed_agents.append({
                    'file': agent_file.name,
                    'status': result['status'],
                    'score': result.get('score', 0),
                    'issues': result.get('issues', [])
                })
        
        return results, failed_agents


def generate_ci_workflow(output_path: Path) -> str:
    """Generate GitHub Actions CI workflow for agent validation."""
    workflow = """name: Agent Validation CI

on:
  push:
    branches: [main, master, develop]
    paths:
      - '**.md'
      - 'scripts/validate_agents.py'
  pull_request:
    branches: [main, master, develop]
    paths:
      - '**.md'

jobs:
  validate-agents:
    runs-on: ubuntu-latest
    
    steps:
      - uses: actions/checkout@v3
      
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      
      - name: Run Agent Validation
        run: |
          python scripts/validate_agents.py --agents-dir . --strict
      
      - name: Generate Report
        if: always()
        run: |
          python scripts/validate_agents.py --agents-dir . --report report.json
      
      - name: Upload Report
        if: always()
        uses: actions/upload-artifact@v3
        with:
          name: validation-report
          path: report.json
      
      - name: Comment PR
        if: github.event_name == 'pull_request'
        uses: actions/github-script@v6
        with:
          script: |
            const fs = require('fs');
            const report = JSON.parse(fs.readFileSync('report.json', 'utf8'));
            const passed = Object.values(report.results).filter(r => r.status === 'PASS').length;
            const failed = report.failed_agents.length;
            const message = `
            ### Agent Validation Results
            - ✅ Passed: ${passed}
            - ⚠️ Issues: ${failed}
            `;
            github.rest.issues.createComment({
              issue_number: context.issue.number,
              owner: context.repo.owner,
              repo: context.repo.repo,
              body: message
            });
"""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(workflow)
    return workflow


def main():
    import argparse
    
    parser = argparse.ArgumentParser(description='Validate ROPE 2.0 agents')
    parser.add_argument('--agents-dir', type=Path, default=Path('.'), help='Agents directory')
    parser.add_argument('--strict', action='store_true', help='Fail on warnings')
    parser.add_argument('--report', type=Path, help='Output JSON report')
    parser.add_argument('--generate-workflow', action='store_true', help='Generate CI workflow')
    
    args = parser.parse_args()
    
    validator = RopeValidator(args.agents_dir)
    results, failed_agents = validator.validate_all()
    
    # Print summary
    total = len(results)
    passed = sum(1 for r in results.values() if r['status'] == 'PASS')
    warned = sum(1 for r in results.values() if r['status'] == 'WARN')
    failed = sum(1 for r in results.values() if r['status'] == 'FAIL')
    
    print(f"\n{'='*60}")
    print(f"Agent Validation Report")
    print(f"{'='*60}")
    print(f"Total:  {total} | ✅ Pass: {passed} | ⚠️  Warn: {warned} | ❌ Fail: {failed}")
    print(f"{'='*60}\n")
    
    if failed_agents:
        print("Issues detected:")
        for agent in failed_agents:
            print(f"\n  {agent['file']} [{agent['status']}] - Score: {agent.get('score', 'N/A')}")
            for issue in agent.get('issues', []):
                print(f"    - {issue}")
    
    # Save report if requested
    if args.report:
        report_data = {
            'summary': {
                'total': total,
                'passed': passed,
                'warned': warned,
                'failed': failed
            },
            'results': results,
            'failed_agents': failed_agents
        }
        args.report.write_text(json.dumps(report_data, indent=2))
        print(f"\nReport saved to: {args.report}")
    
    # Generate workflow if requested
    if args.generate_workflow:
        workflow_path = Path('.github/workflows/validate-agents.yml')
        generate_ci_workflow(workflow_path)
        print(f"Workflow generated: {workflow_path}")
    
    # Exit with error if strict mode and failures
    if args.strict and (failed > 0 or warned > 0):
        sys.exit(1)
    
    sys.exit(0 if failed == 0 else 1)


if __name__ == '__main__':
    main()
