from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
import uvicorn

from agents.paper_search_agent import PaperSearchAgent, Paper

app = FastAPI(
    title="Academic Paper Search API",
    description="An API for searching academic papers using AI",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods
    allow_headers=["*"],  # Allows all headers
)

# Mount static files
app.mount("/static", StaticFiles(directory="src/static"), name="static")

# Initialize the agent
paper_agent = PaperSearchAgent()

class SearchRequest(BaseModel):
    topic: str
    max_results: Optional[int] = 10

class SearchResponse(BaseModel):
    papers: List[Paper]
    total_results: int

@app.get("/")
async def read_root():
    return {"message": "Welcome to the Academic Paper Search API"}

@app.post("/search", response_model=SearchResponse)
async def search_papers(request: SearchRequest):
    """
    Search for academic papers based on a topic
    """
    try:
        papers = paper_agent.search_papers(request.topic)
        return SearchResponse(
            papers=papers[:request.max_results],
            total_results=len(papers)
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/paper/{paper_id}", response_model=Paper)
async def get_paper_details(paper_id: str):
    """
    Get detailed information about a specific paper
    """
    paper = paper_agent.get_paper_details(paper_id)
    if not paper:
        raise HTTPException(status_code=404, detail="Paper not found")
    return paper

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True) 