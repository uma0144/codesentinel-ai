import difflib
from typing import Dict, Any, List

class PatchEngine:
    '''Calculates diffs, generates unified git diffs, and computes code change metrics.'''
    
    @staticmethod
    def generate_unified_diff(original: str, modified: str, filename: str = "source.py") -> str:
        orig_lines = original.splitlines(keepends=True)
        mod_lines = modified.splitlines(keepends=True)
        
        diff = difflib.unified_diff(
            orig_lines,
            mod_lines,
            fromfile=f"a/{filename}",
            tofile=f"b/{filename}",
            lineterm=""
        )
        return "".join(diff)

    @staticmethod
    def compute_stats(original: str, modified: str) -> Dict[str, int]:
        orig_lines = original.splitlines()
        mod_lines = modified.splitlines()
        matcher = difflib.SequenceMatcher(None, orig_lines, mod_lines)
        
        additions = 0
        deletions = 0
        modifications = 0
        
        for tag, i1, i2, j1, j2 in matcher.get_opcodes():
            if tag == 'replace':
                modifications += max(i2 - i1, j2 - j1)
            elif tag == 'insert':
                additions += (j2 - j1)
            elif tag == 'delete':
                deletions += (i2 - i1)
                
        return {
            'additions': additions,
            'deletions': deletions,
            'modifications': modifications,
            'total_changes': additions + deletions + modifications
        }

    @staticmethod
    def generate_html_diff_table(original: str, modified: str) -> str:
        '''Generates a clean HTML side-by-side diff table.'''
        orig_lines = original.splitlines()
        mod_lines = modified.splitlines()
        
        differ = difflib.HtmlDiff(tabsize=4, wrapcolumn=80)
        return differ.make_table(orig_lines, mod_lines, fromdesc="Original Code (Vulnerable/Buggy)", todesc="AI Refactored & Fixed Code", context=True, numlines=3)
