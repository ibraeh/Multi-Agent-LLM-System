"""
Shared Tools Module
Reusable tools that can be used by multiple agents
"""
import logging
from typing import Dict, Any, List, Optional
import requests
from bs4 import BeautifulSoup
import json
from pathlib import Path

logger = logging.getLogger(__name__)


# ============================================================================
# WEB TOOLS
# ============================================================================

class WebTools:
    """Web-related tools"""
    
    @staticmethod
    def fetch_url(url: str, timeout: int = 10) -> Dict[str, Any]:
        """
        Fetch content from URL
        
        Args:
            url: URL to fetch
            timeout: Request timeout in seconds
        
        Returns:
            Response data
        """
        try:
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
            }
            
            response = requests.get(url, headers=headers, timeout=timeout)
            response.raise_for_status()
            
            return {
                "success": True,
                "url": url,
                "status_code": response.status_code,
                "content": response.text,
                "headers": dict(response.headers)
            }
            
        except Exception as e:
            logger.error(f"Failed to fetch URL {url}: {e}")
            return {
                "success": False,
                "url": url,
                "error": str(e)
            }
    
    @staticmethod
    def extract_text(html: str) -> str:
        """
        Extract clean text from HTML
        
        Args:
            html: HTML content
        
        Returns:
            Clean text
        """
        try:
            soup = BeautifulSoup(html, 'html.parser')
            
            # Remove unwanted elements
            for element in soup(['script', 'style', 'nav', 'footer', 'header']):
                element.decompose()
            
            # Get text
            text = soup.get_text(separator='\n', strip=True)
            
            # Clean up whitespace
            lines = [line.strip() for line in text.split('\n') if line.strip()]
            return '\n'.join(lines)
            
        except Exception as e:
            logger.error(f"Failed to extract text: {e}")
            return ""
    
    @staticmethod
    def extract_links(html: str, base_url: str = "") -> List[str]:
        """
        Extract all links from HTML
        
        Args:
            html: HTML content
            base_url: Base URL for relative links
        
        Returns:
            List of URLs
        """
        try:
            soup = BeautifulSoup(html, 'html.parser')
            links = []
            
            for a_tag in soup.find_all('a', href=True):
                href = a_tag['href']
                
                # Handle relative URLs
                if base_url and not href.startswith('http'):
                    from urllib.parse import urljoin
                    href = urljoin(base_url, href)
                
                links.append(href)
            
            return list(set(links))  # Remove duplicates
            
        except Exception as e:
            logger.error(f"Failed to extract links: {e}")
            return []


# ============================================================================
# FILE TOOLS
# ============================================================================

class FileTools:
    """File operation tools"""
    
    @staticmethod
    def read_file(filepath: str) -> Dict[str, Any]:
        """
        Read file content
        
        Args:
            filepath: Path to file
        
        Returns:
            File content and metadata
        """
        try:
            path = Path(filepath)
            
            if not path.exists():
                return {
                    "success": False,
                    "error": f"File not found: {filepath}"
                }
            
            content = path.read_text(encoding='utf-8')
            
            return {
                "success": True,
                "filepath": str(path),
                "content": content,
                "size": path.stat().st_size,
                "extension": path.suffix
            }
            
        except Exception as e:
            logger.error(f"Failed to read file {filepath}: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    @staticmethod
    def write_file(filepath: str, content: str) -> Dict[str, Any]:
        """
        Write content to file
        
        Args:
            filepath: Path to file
            content: Content to write
        
        Returns:
            Operation result
        """
        try:
            path = Path(filepath)
            path.parent.mkdir(parents=True, exist_ok=True)
            
            path.write_text(content, encoding='utf-8')
            
            return {
                "success": True,
                "filepath": str(path),
                "size": len(content)
            }
            
        except Exception as e:
            logger.error(f"Failed to write file {filepath}: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    @staticmethod
    def list_files(directory: str, pattern: str = "*") -> List[str]:
        """
        List files in directory
        
        Args:
            directory: Directory path
            pattern: File pattern (e.g., "*.txt")
        
        Returns:
            List of file paths
        """
        try:
            path = Path(directory)
            
            if not path.exists():
                return []
            
            files = [str(f) for f in path.glob(pattern) if f.is_file()]
            return sorted(files)
            
        except Exception as e:
            logger.error(f"Failed to list files in {directory}: {e}")
            return []


# ============================================================================
# TEXT TOOLS
# ============================================================================

class TextTools:
    """Text processing tools"""
    
    @staticmethod
    def chunk_text(text: str, chunk_size: int = 1000, overlap: int = 100) -> List[str]:
        """
        Split text into chunks with overlap
        
        Args:
            text: Text to chunk
            chunk_size: Size of each chunk
            overlap: Overlap between chunks
        
        Returns:
            List of text chunks
        """
        if len(text) <= chunk_size:
            return [text]
        
        chunks = []
        start = 0
        
        while start < len(text):
            end = start + chunk_size
            chunk = text[start:end]
            chunks.append(chunk)
            start = end - overlap
        
        return chunks
    
    @staticmethod
    def count_tokens(text: str) -> int:
        """
        Estimate token count (rough approximation)
        
        Args:
            text: Text to count
        
        Returns:
            Estimated token count
        """
        # Rough approximation: 1 token ≈ 4 characters
        return len(text) // 4
    
    @staticmethod
    def truncate_text(text: str, max_tokens: int = 1000) -> str:
        """
        Truncate text to token limit
        
        Args:
            text: Text to truncate
            max_tokens: Maximum tokens
        
        Returns:
            Truncated text
        """
        max_chars = max_tokens * 4
        if len(text) <= max_chars:
            return text
        
        return text[:max_chars] + "..."
    
    @staticmethod
    def extract_keywords(text: str, top_n: int = 10) -> List[str]:
        """
        Extract key words from text (simple frequency-based)
        
        Args:
            text: Text to analyze
            top_n: Number of keywords to return
        
        Returns:
            List of keywords
        """
        # Simple word frequency approach
        import re
        from collections import Counter
        
        # Remove special characters and convert to lowercase
        words = re.findall(r'\b[a-z]{3,}\b', text.lower())
        
        # Common stop words to exclude
        stop_words = {
            'the', 'and', 'for', 'are', 'but', 'not', 'you', 'all', 
            'can', 'her', 'was', 'one', 'our', 'out', 'day', 'get', 
            'has', 'him', 'his', 'how', 'man', 'new', 'now', 'old',
            'see', 'two', 'way', 'who', 'boy', 'did', 'its', 'let',
            'put', 'say', 'she', 'too', 'use', 'with', 'this', 'that',
            'from', 'have', 'they', 'been', 'were', 'said', 'there'
        }
        
        words = [w for w in words if w not in stop_words]
        
        # Count and return top N
        counter = Counter(words)
        return [word for word, _ in counter.most_common(top_n)]


# ============================================================================
# DATA TOOLS
# ============================================================================

class DataTools:
    """Data processing tools"""
    
    @staticmethod
    def parse_json(text: str) -> Dict[str, Any]:
        """
        Parse JSON from text
        
        Args:
            text: JSON text
        
        Returns:
            Parsed data
        """
        try:
            return json.loads(text)
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON: {e}")
            return {}
    
    @staticmethod
    def format_json(data: Any, indent: int = 2) -> str:
        """
        Format data as JSON
        
        Args:
            data: Data to format
            indent: Indentation spaces
        
        Returns:
            Formatted JSON string
        """
        try:
            return json.dumps(data, indent=indent, default=str)
        except Exception as e:
            logger.error(f"Failed to format JSON: {e}")
            return str(data)
    
    @staticmethod
    def csv_to_dict(csv_text: str) -> List[Dict[str, Any]]:
        """
        Convert CSV text to list of dictionaries
        
        Args:
            csv_text: CSV content
        
        Returns:
            List of row dictionaries
        """
        import csv
        from io import StringIO
        
        try:
            reader = csv.DictReader(StringIO(csv_text))
            return list(reader)
        except Exception as e:
            logger.error(f"Failed to parse CSV: {e}")
            return []


# ============================================================================
# VALIDATION TOOLS
# ============================================================================

class ValidationTools:
    """Validation and checking tools"""
    
    @staticmethod
    def is_valid_url(url: str) -> bool:
        """Check if string is valid URL"""
        import re
        url_pattern = re.compile(
            r'^https?://'  # http:// or https://
            r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+[A-Z]{2,6}\.?|'  # domain
            r'localhost|'  # localhost
            r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'  # or ip
            r'(?::\d+)?'  # optional port
            r'(?:/?|[/?]\S+)$', re.IGNORECASE)
        return url_pattern.match(url) is not None
    
    @staticmethod
    def is_valid_email(email: str) -> bool:
        """Check if string is valid email"""
        import re
        email_pattern = re.compile(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$')
        return email_pattern.match(email) is not None
    
    @staticmethod
    def sanitize_filename(filename: str) -> str:
        """Sanitize filename for safe filesystem use"""
        import re
        # Remove invalid characters
        filename = re.sub(r'[<>:"/\\|?*]', '', filename)
        # Limit length
        if len(filename) > 255:
            filename = filename[:255]
        return filename


# ============================================================================
# EXPORT ALL TOOLS
# ============================================================================

# Create tool registry
TOOL_REGISTRY = {
    "web": WebTools,
    "file": FileTools,
    "text": TextTools,
    "data": DataTools,
    "validation": ValidationTools
}


def get_tool(category: str):
    """Get tool class by category"""
    return TOOL_REGISTRY.get(category)


def list_tools() -> Dict[str, List[str]]:
    """List all available tools"""
    return {
        category: [
            method for method in dir(tool_class)
            if not method.startswith('_') and callable(getattr(tool_class, method))
        ]
        for category, tool_class in TOOL_REGISTRY.items()
    }
