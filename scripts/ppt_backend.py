"""Pinned PPT Master adapter. Keeps upstream attribution and quality gates intact."""
import argparse
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PYTHON = ROOT / '.runtime/Scripts/python.exe'
UPSTREAM = ROOT / 'vendor/ppt-master'
TOOLS = {'check': 'svg_quality_checker.py', 'export': 'svg_to_pptx.py',
         'init': 'project_manager.py', 'preview': 'svg_editor/server.py',
         'integrity': 'attribution_guard.py', 'notes': 'total_md_split.py',
         'import-pptx': 'pptx_to_svg.py', 'import-template': 'pptx_template_import.py',
         'apply-template': 'apply_template.py', 'register-template': 'register_template.py',
         'template-preview': 'template_preview_pptx.py', 'stamp-native': 'stamp_native_fallbacks.py',
         'image-search': 'image_search.py', 'images': 'analyze_images.py'}

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('tool', choices=TOOLS)
    parser.add_argument('args', nargs=argparse.REMAINDER)
    opts = parser.parse_args()
    if not PYTHON.exists():
        parser.error('Isolated runtime missing; see references/svg-pipeline.md')
    if not (UPSTREAM / 'scripts' / TOOLS[opts.tool]).is_file():
        parser.error('Optional ppt-master backend is not installed; see references/svg-pipeline.md')
    args = opts.args[1:] if opts.args[:1] == ['--'] else opts.args
    explicit = '--explicit-background' in args
    args = [a for a in args if a != '--explicit-background']
    if opts.tool == 'export' and not explicit and '--help' not in args and '-h' not in args:
        parser.error('Default authoring is visible, foreground WPS page-by-page. '
                     'Use --explicit-background only when the user explicitly selects background deck conversion for this task.')
    return subprocess.call([str(PYTHON), '-X', 'utf8', str(UPSTREAM/'scripts'/TOOLS[opts.tool]), *args])

if __name__ == '__main__':
    sys.exit(main())
