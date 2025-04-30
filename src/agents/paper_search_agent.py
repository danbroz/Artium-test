from typing import List, Dict, Optional
from langchain.agents import Tool, AgentExecutor, create_openai_functions_agent
from langchain_openai import ChatOpenAI
from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain.tools import tool
from langchain.memory import ConversationBufferMemory
import requests
from pydantic import BaseModel
import os
from dotenv import load_dotenv
import json
import re

load_dotenv()

class Paper(BaseModel):
    title: str
    authors: List[str]
    abstract: str
    url: str
    year: Optional[int] = None
    citations: Optional[int] = None
    doi: Optional[str] = None
    open_access: Optional[bool] = None

class PaperSearchAgent:
    def __init__(self):
        self.llm = ChatOpenAI(
            model="gpt-4-turbo-preview",
            temperature=0.7
        )
        self.memory = ConversationBufferMemory(
            memory_key="chat_history",
            return_messages=True
        )
        self.tools = self._create_tools()
        self.agent = self._create_agent()

    def _create_tools(self) -> List[Tool]:
        @tool
        def search_openalex(query: str) -> List[Dict]:
            """Search for papers using OpenAlex API"""
            base_url = "https://api.openalex.org/works"
            params = {
                "search": query,
                "per_page": 10,
                "select": "id,title,abstract,publication_date,authorships,doi,open_access,cited_by_count"
            }
            response = requests.get(base_url, params=params)
            if response.status_code == 200:
                data = response.json()
                return self._process_openalex_results(data.get("results", []))
            return []

        @tool
        def search_arxiv(query: str) -> List[Dict]:
            """Search for papers using arXiv API"""
            base_url = "http://export.arxiv.org/api/query"
            params = {
                "search_query": f"all:{query}",
                "start": 0,
                "max_results": 10,
                "sortBy": "relevance",
                "sortOrder": "descending"
            }
            response = requests.get(base_url, params=params)
            if response.status_code == 200:
                from utils.xml_parser import parse_arxiv_response
                return parse_arxiv_response(response.text)
            return []

        @tool
        def reverse_inverted_index(abstract: str) -> str:
            """Convert an inverted index abstract back to a complete text"""
            # Check if the abstract is in inverted index format
            if not abstract or not isinstance(abstract, str):
                return abstract
                
            # Pattern to detect inverted index format (words with positions)
            pattern = r'(\w+)\s*\(\d+(?:,\s*\d+)*\)'
            
            if not re.search(pattern, abstract):
                return abstract
                
            # Extract words and their positions
            words_with_positions = re.findall(pattern, abstract)
            
            # Create a mapping of positions to words
            position_word_map = {}
            for match in re.finditer(pattern, abstract):
                word = match.group(1)
                positions = [int(pos) for pos in re.findall(r'\d+', match.group(0))]
                for pos in positions:
                    position_word_map[pos] = word
            
            # Reconstruct the original text
            if position_word_map:
                max_pos = max(position_word_map.keys())
                reconstructed = [''] * (max_pos + 1)
                for pos, word in position_word_map.items():
                    reconstructed[pos] = word
                return ' '.join(word for word in reconstructed if word)
            
            return abstract

        return [
            Tool(
                name="openalex_search",
                func=search_openalex,
                description="Search for academic papers using OpenAlex API"
            ),
            Tool(
                name="arxiv_search",
                func=search_arxiv,
                description="Search for papers using arXiv API"
            ),
            Tool(
                name="reverse_inverted_index",
                func=reverse_inverted_index,
                description="Convert an inverted index abstract back to a complete text"
            )
        ]

    def _process_openalex_results(self, results: List[Dict]) -> List[Dict]:
        """Process OpenAlex API results into a standardized format"""
        processed_results = []
        for result in results:
            # Extract authors
            authors = []
            for authorship in result.get("authorships", []):
                author = authorship.get("author", {})
                if author:
                    authors.append(author.get("display_name", ""))
            
            # Extract year from publication date
            year = None
            pub_date = result.get("publication_date", "")
            if pub_date and len(pub_date) >= 4:
                try:
                    year = int(pub_date[:4])
                except ValueError:
                    pass
            
            # Process abstract if it's in inverted index format
            abstract = ""
            abstract_inverted = result.get("abstract_inverted_index", {})
            if abstract_inverted:
                # Convert inverted index to regular text
                words = []
                for word, positions in abstract_inverted.items():
                    for pos in positions:
                        words.append((pos, word))
                
                # Sort by position and join
                words.sort(key=lambda x: x[0])
                abstract = " ".join(word for _, word in words)
            
            processed_results.append({
                "title": result.get("title", ""),
                "authors": authors,
                "abstract": abstract,
                "url": f"https://openalex.org/{result.get('id', '')}",
                "year": year,
                "citations": result.get("cited_by_count", 0),
                "doi": result.get("doi", ""),
                "open_access": result.get("open_access", {}).get("is_oa", False)
            })
        
        return processed_results

    def _create_agent(self) -> AgentExecutor:
        prompt = ChatPromptTemplate.from_messages([
            ("system", """You are an AI research assistant specialized in finding academic papers.
            Your task is to help users find relevant research papers based on their topics.
            Use the available tools to search across multiple academic sources.
            Always provide detailed information about the papers you find, including:
            - Title
            - Authors
            - Abstract (complete text, not inverted index)
            - URL
            - Year (if available)
            - Citation count (if available)
            - DOI (if available)
            - Open Access status (if available)
            
            If the user's query is ambiguous, ask clarifying questions.
            
            If you encounter abstracts in inverted index format, use the reverse_inverted_index tool to convert them to complete text."""),
            MessagesPlaceholder(variable_name="chat_history"),
            ("human", "{input}"),
            MessagesPlaceholder(variable_name="agent_scratchpad"),
        ])

        agent = create_openai_functions_agent(
            llm=self.llm,
            prompt=prompt,
            tools=self.tools
        )

        return AgentExecutor(
            agent=agent,
            tools=self.tools,
            memory=self.memory,
            verbose=True
        )

    def search_papers(self, topic: str) -> List[Paper]:
        """
        Search for papers related to the given topic
        """
        # Direct API call to OpenAlex
        base_url = "https://api.openalex.org/works"
        params = {
            "search": topic,
            "per_page": 50,
            "select": "id,title,abstract_inverted_index,publication_date,authorships,doi,open_access,cited_by_count",
            "email": "dbroz@captechu.edu"  # Required by OpenAlex API
        }
        
        print(f"Searching OpenAlex with query: {topic}")
        print(f"API URL: {base_url}")
        print(f"Parameters: {params}")
        
        try:
            response = requests.get(base_url, params=params)
            print(f"Response status code: {response.status_code}")
            print(f"Response headers: {response.headers}")
            
            if response.status_code == 200:
                data = response.json()
                print(f"Response data keys: {data.keys() if isinstance(data, dict) else 'Not a dict'}")
                results = data.get("results", [])
                print(f"Number of results: {len(results)}")
                
                if not results:
                    print("No results found in the response")
                    # Try a different search approach
                    params["search"] = f'"{topic}"'  # Try with exact phrase
                    print(f"Trying exact phrase search with: {params['search']}")
                    response = requests.get(base_url, params=params)
                    if response.status_code == 200:
                        data = response.json()
                        results = data.get("results", [])
                        print(f"Number of results with exact phrase: {len(results)}")
                
                processed_results = self._process_openalex_results(results)
                return [Paper(**paper) for paper in processed_results]
            else:
                print(f"Error from OpenAlex API: {response.status_code}")
                print(f"Response: {response.text}")
                return []
        except Exception as e:
            print(f"Error searching papers: {str(e)}")
            import traceback
            traceback.print_exc()
            return []

    def get_paper_details(self, paper_id: str) -> Optional[Paper]:
        """
        Get detailed information about a specific paper
        """
        response = self.agent.invoke({
            "input": f"Get detailed information about paper with ID: {paper_id}"
        })
        
        # Process the response and convert to Paper object
        try:
            if isinstance(response, dict) and "output" in response:
                # Try to parse the output as JSON
                try:
                    output_text = response["output"]
                    json_matches = re.findall(r'\{.*?\}', output_text, re.DOTALL)
                    for json_str in json_matches:
                        try:
                            data = json.loads(json_str)
                            return Paper(**data)
                        except json.JSONDecodeError:
                            pass
                except Exception:
                    pass
                
                # If no paper was found through JSON parsing, try to extract from text
                paper_blocks = re.split(r'\n\s*\n', response["output"])
                for block in paper_blocks:
                    if "title" in block.lower() and "abstract" in block.lower():
                        title_match = re.search(r'title:?\s*([^\n]+)', block, re.IGNORECASE)
                        abstract_match = re.search(r'abstract:?\s*([^\n]+(?:\n(?!\w+:)[^\n]+)*)', block, re.IGNORECASE | re.DOTALL)
                        url_match = re.search(r'url:?\s*([^\n]+)', block, re.IGNORECASE)
                        
                        if title_match and abstract_match:
                            title = title_match.group(1).strip()
                            abstract = abstract_match.group(1).strip()
                            url = url_match.group(1).strip() if url_match else ""
                            
                            # Extract authors if available
                            authors = []
                            author_match = re.search(r'author[s]?:?\s*([^\n]+)', block, re.IGNORECASE)
                            if author_match:
                                authors_text = author_match.group(1).strip()
                                authors = [a.strip() for a in re.split(r',|\band\b', authors_text) if a.strip()]
                            
                            # Extract year if available
                            year = None
                            year_match = re.search(r'year:?\s*(\d{4})', block, re.IGNORECASE)
                            if year_match:
                                year = int(year_match.group(1))
                            
                            # Extract citations if available
                            citations = None
                            citations_match = re.search(r'citation[s]?:?\s*(\d+)', block, re.IGNORECASE)
                            if citations_match:
                                citations = int(citations_match.group(1))
                            
                            return Paper(
                                title=title,
                                authors=authors,
                                abstract=abstract,
                                url=url,
                                year=year,
                                citations=citations
                            )
        except Exception as e:
            print(f"Error processing paper details: {e}")
        
        return None 