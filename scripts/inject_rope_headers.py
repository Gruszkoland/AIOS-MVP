#!/usr/bin/env python3
"""
ROPE 2.0 Section Header Injector for 33 Personas
Adds ROPE 2.0 section headers (## I. CONTEXT, etc.) to personas that have ROPE_VERSION: "2.0"
but missing the required section headers.
"""

import re
import sys
from pathlib import Path
from typing import List, Dict, Tuple


class RopeHeaderInjector:
    """Inject ROPE 2.0 section headers into personas."""
    
    REQUIRED_SECTIONS = [
        '## I. CONTEXT',
        '## II. REASONING',
        '## III. CONSTRAINTS',
        '## IV. OUTPUT_FORMAT',
        '## V. SAFETY_CHECKS',
        '## VI. EXAMPLES',
    ]
    
    SYSTEM_PAYLOAD_MARKER = '--- SYSTEM_PAYLOAD ---'
    
    def __init__(self, personas_dir: Path):
        self.personas_dir = personas_dir
        self.stats = {
            'total_files': 0,
            'files_with_rope_2_0': 0,
            'files_needing_injection': 0,
            'files_injected': 0,
            'files_failed': 0,
        }
    
    def has_rope_version_2_0(self, content: str) -> bool:
        """Check if file has ROPE_VERSION: 2.0."""
        patterns = [
            r'ROPE_VERSION:\s*2\.0',
            r'ROPE_VERSION:\s*"2\.0"',
            r'<!--\s*ROPE_VERSION:\s*2\.0\s*-->',
            r'Wersja:\s*2\.',
        ]
        for pattern in patterns:
            if re.search(pattern, content, re.IGNORECASE):
                return True
        return False
    
    def extract_sections(self, content: str) -> Dict[str, bool]:
        """Check which ROPE 2.0 sections exist."""
        sections = {
            'I_CONTEXT': bool(re.search(r'##\s*I\.\s*CONTEXT', content, re.IGNORECASE)),
            'II_REASONING': bool(re.search(r'##\s*II\.\s*REASONING', content, re.IGNORECASE)),
            'III_CONSTRAINTS': bool(re.search(r'##\s*III\.\s*CONSTRAINTS', content, re.IGNORECASE)),
            'IV_OUTPUT_FORMAT': bool(re.search(r'##\s*IV\.\s*OUTPUT_FORMAT', content, re.IGNORECASE)),
            'V_SAFETY_CHECKS': bool(re.search(r'##\s*V\.\s*SAFETY_CHECKS', content, re.IGNORECASE)),
            'VI_EXAMPLES': bool(re.search(r'##\s*VI\.\s*EXAMPLES', content, re.IGNORECASE)),
            'SYSTEM_PAYLOAD': bool(re.search(r'---\s*SYSTEM_PAYLOAD\s*---', content, re.MULTILINE)),
        }
        return sections
    
    def inject_rope_headers(self, content: str) -> str:
        """Inject missing ROPE 2.0 section headers by renaming existing sections."""
        # First, rename existing sections to ROPE 2.0 format (match full line to end)
        # Updated emoji list to cover all possible persona variations
        replacements = [
            (r'##\s*[🧠🎭🎯⚙️📊🔌📋]*\s*I\.\s*INTERNAL REASONING.*', '## I. CONTEXT'),
            (r'##\s*[🧠🎭🎯⚙️📊🔌📋]*\s*II\.\s*ROLE.*', '## II. REASONING'),
            (r'##\s*[🧠🎭🎯⚙️📊🔌📋]*\s*III\.\s*OBJECTIVE.*', '## III. CONSTRAINTS'),
            (r'##\s*[🧠🎭🎯⚙️📊🔌📋]*\s*IV\.\s*(FRAMEWORK|GUARDRAILS|PARAMETERS|INVOKE_WHEN).*', '## IV. OUTPUT_FORMAT'),
            (r'##\s*[🧠🎭🎯⚙️📊🔌📋]*\s*V\.\s*(EVALUATION|OCENA|SCORING).*', '## V. SAFETY_CHECKS'),
            (r'##\s*[🧠🎭🎯⚙️📊🔌📋]*\s*VI\.\s*SYSTEM_PAYLOAD.*', '## VI. EXAMPLES'),
        ]
        
        modified_content = content
        for pattern, replacement in replacements:
            modified_content = re.sub(pattern, replacement, modified_content, flags=re.IGNORECASE | re.MULTILINE)
        
        # Add missing section headers if they don't exist
        if '## I. CONTEXT' not in modified_content:
            # Find where to insert (after header/metadata, before first content section)
            lines = modified_content.split('\n')
            insert_idx = len(lines)
            for idx, line in enumerate(lines):
                if re.match(r'^##\s+', line):
                    insert_idx = idx
                    break
            
            lines.insert(insert_idx, '## I. CONTEXT')
            lines.insert(insert_idx + 1, '')
            modified_content = '\n'.join(lines)
        
        # Ensure SYSTEM_PAYLOAD exists
        if '--- SYSTEM_PAYLOAD ---' not in modified_content:
            modified_content += '\n\n--- SYSTEM_PAYLOAD ---\n'
        
        return modified_content
    
    def process_file(self, filepath: Path) -> Tuple[bool, str]:
        """Process single persona file."""
        try:
            content = filepath.read_text(encoding='utf-8', errors='replace')
            self.stats['total_files'] += 1
            
            if not self.has_rope_version_2_0(content):
                return False, "No ROPE_VERSION: 2.0 found"
            
            self.stats['files_with_rope_2_0'] += 1
            
            sections = self.extract_sections(content)
            missing_sections = [k for k, v in sections.items() if not v]
            
            if not missing_sections:
                return False, "All sections present"
            
            self.stats['files_needing_injection'] += 1
            
            # Inject headers
            injected_content = self.inject_rope_headers(content)
            
            # Write back
            filepath.write_text(injected_content, encoding='utf-8')
            self.stats['files_injected'] += 1
            
            return True, f"Injected {len(missing_sections)} missing sections"
        
        except Exception as e:
            self.stats['files_failed'] += 1
            return False, f"ERROR: {str(e)}"
    
    def process_directory(self) -> None:
        """Process all personas in directory."""
        if not self.personas_dir.exists():
            print(f"❌ Directory not found: {self.personas_dir}")
            sys.exit(1)
        
        persona_files = sorted(self.personas_dir.glob('*.md'))
        print(f"📂 Found {len(persona_files)} persona files\n")
        
        for filepath in persona_files:
            success, message = self.process_file(filepath)
            
            status = "✅" if success else "⏭️ "
            print(f"{status} {filepath.name}: {message}")
        
        print(f"\n{'='*70}")
        print(f"📊 INJECTION SUMMARY:")
        print(f"{'='*70}")
        print(f"Total files scanned:         {self.stats['total_files']}")
        print(f"Files with ROPE 2.0:        {self.stats['files_with_rope_2_0']}")
        print(f"Files needing injection:    {self.stats['files_needing_injection']}")
        print(f"Files successfully injected: {self.stats['files_injected']}")
        print(f"Files failed:               {self.stats['files_failed']}")
        print(f"{'='*70}\n")
        
        if self.stats['files_injected'] > 0:
            print(f"✅ SUCCESS: Injected ROPE 2.0 headers in {self.stats['files_injected']} files!")
            print(f"📍 Next step: Run validate_agents.py to verify compliance\n")


if __name__ == '__main__':
    # Personas directory
    personas_dir = Path(
        r"C:\Users\adiha\Desktop\Dokumentacja\03_OSOBOWOSCI_AI\Gemy Gemini\Gotowe i skoczone PERSONY\33 Persony AI"
    )
    
    injector = RopeHeaderInjector(personas_dir)
    injector.process_directory()
