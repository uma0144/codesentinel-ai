import re
import requests
from typing import Dict, Any, Optional

class GitHubLoader:
    '''Fetches code files from public GitHub repositories and PRs.'''
    
    @staticmethod
    def parse_github_url(url: str) -> Optional[Dict[str, str]]:
        '''Parses GitHub file URL into owner, repo, branch/commit, and filepath.'''
        # Pattern: https://github.com/{owner}/{repo}/blob/{branch}/{path}
        blob_pattern = r"https?://github\.com/([^/]+)/([^/]+)/blob/([^/]+)/(.+)"
        match = re.match(blob_pattern, url)
        if match:
            owner, repo, branch, path = match.groups()
            return {"type": "file", "owner": owner, "repo": repo, "branch": branch, "path": path}
            
        # Raw URL: https://raw.githubusercontent.com/{owner}/{repo}/{branch}/{path}
        raw_pattern = r"https?://raw\.githubusercontent\.com/([^/]+)/([^/]+)/([^/]+)/(.+)"
        match = re.match(raw_pattern, url)
        if match:
            owner, repo, branch, path = match.groups()
            return {"type": "raw", "owner": owner, "repo": repo, "branch": branch, "path": path}
            
        return None

    @staticmethod
    def fetch_file(url: str, token: Optional[str] = None) -> Dict[str, Any]:
        '''Fetches raw file content from GitHub.'''
        parsed = GitHubLoader.parse_github_url(url)
        if not parsed:
            return {"error": "Invalid GitHub file URL format. Expected: https://github.com/owner/repo/blob/branch/path"}
            
        raw_url = f"https://raw.githubusercontent.com/{parsed['owner']}/{parsed['repo']}/{parsed['branch']}/{parsed['path']}"
        headers = {}
        if token:
            headers["Authorization"] = f"token {token}"
            
        try:
            resp = requests.get(raw_url, headers=headers, timeout=10)
            if resp.status_code == 200:
                filename = parsed['path'].split('/')[-1]
                ext = filename.split('.')[-1] if '.' in filename else ''
                lang = "python" if ext in ('py', 'pyw') else ("javascript" if ext in ('js', 'mjs', 'jsx') else ("typescript" if ext in ('ts', 'tsx') else ext))
                return {
                    "filename": filename,
                    "language": lang,
                    "content": resp.text,
                    "url": raw_url
                }
            elif resp.status_code == 404:
                return {"error": "File not found on GitHub. Check repository, branch, and file path."}
            else:
                return {"error": f"GitHub API returned status code {resp.status_code}"}
        except Exception as e:
            return {"error": f"Failed to connect to GitHub: {str(e)}"}
