import xml.etree.ElementTree as ET
from typing import List, Dict
from datetime import datetime

def parse_arxiv_response(xml_content: str) -> List[Dict]:
    """
    Parse the XML response from arXiv API and convert it to a list of paper dictionaries
    """
    root = ET.fromstring(xml_content)
    
    # Define the XML namespace
    ns = {
        'atom': 'http://www.w3.org/2005/Atom',
        'arxiv': 'http://arxiv.org/schemas/atom'
    }
    
    papers = []
    for entry in root.findall('.//atom:entry', ns):
        paper = {
            'title': entry.find('atom:title', ns).text.strip(),
            'authors': [author.find('atom:name', ns).text 
                       for author in entry.findall('atom:author', ns)],
            'abstract': entry.find('atom:summary', ns).text.strip(),
            'url': entry.find('atom:id', ns).text,
            'year': datetime.strptime(
                entry.find('atom:published', ns).text,
                '%Y-%m-%dT%H:%M:%SZ'
            ).year,
            'citations': None  # arXiv doesn't provide citation count
        }
        papers.append(paper)
    
    return papers 