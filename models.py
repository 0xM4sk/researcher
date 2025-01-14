# research_agent/models.py
from pydantic import BaseModel, Field, HttpUrl, validator, EmailStr
from typing import List, Dict, Optional, Union, Any
from enum import Enum
from datetime import datetime
import uuid

class SourceType(str, Enum):
    """Available research source types."""
    WEB = "web"
    WIKI = "wikipedia"
    ACADEMIC = "academic"
    NEWS = "news"
    SCHOLARLY = "scholarly"

class SearchProvider(str, Enum):
    """Supported search providers."""
    GOOGLE = "google"
    DUCKDUCKGO = "duckduckgo"
    SERPER = "serper"

class TaskStatus(str, Enum):
    """Status of research tasks."""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"

class SearchParameters(BaseModel):
    """Search configuration parameters."""
    provider: Optional[SearchProvider] = None
    max_depth: int = Field(default=2, ge=1, le=5)
    min_relevance_score: float = Field(default=0.5, ge=0.0, le=1.0)
    exclude_domains: List[str] = Field(default_factory=list)
    include_domains: List[str] = Field(default_factory=list)
    date_range: Optional[Dict[str, datetime]] = None

    @validator('date_range')
    def validate_date_range(cls, v):
        if v is not None:
            if 'start' not in v or 'end' not in v:
                raise ValueError("Date range must include 'start' and 'end' dates")
            if v['start'] > v['end']:
                raise ValueError("Start date must be before end date")
        return v

class ResearchQuery(BaseModel):
    """Research query model with validation."""
    query_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    query: str = Field(
        ...,
        min_length=3,
        max_length=500,
        description="The research query string"
    )
    sources: List[SourceType] = Field(
        ...,
        min_items=1,
        description="List of sources to search"
    )
    max_results: int = Field(
        default=5,
        ge=1,
        le=50,
        description="Maximum number of results to return"
    )
    search_params: Optional[SearchParameters] = Field(
        default_factory=SearchParameters,
        description="Search configuration parameters"
    )
    user_context: Optional[Dict[str, Any]] = Field(
        default_factory=dict,
        description="Additional context for the research"
    )

    class Config:
        schema_extra = {
            "example": {
                "query": "What are the latest developments in quantum computing?",
                "sources": ["ACADEMIC", "NEWS"],
                "max_results": 5,
                "search_params": {
                    "provider": "GOOGLE",
                    "max_depth": 2,
                    "min_relevance_score": 0.7
                }
            }
        }

class ContentMetadata(BaseModel):
    """Metadata for research content."""
    url: Optional[HttpUrl] = None
    title: Optional[str] = None
    author: Optional[str] = None
    published_date: Optional[datetime] = None
    language: str = Field(default="en")
    word_count: Optional[int] = None
    citation_count: Optional[int] = None
    domain: Optional[str] = None
    content_type: Optional[str] = None

class AnalysisResult(BaseModel):
    """Results of content analysis."""
    summary: str
    key_points: List[str]
    sentiment_score: float = Field(ge=-1.0, le=1.0)
    credibility_score: float = Field(ge=0.0, le=1.0)
    topics: List[str]
    entities: List[Dict[str, str]]
    citations: List[Dict[str, str]]
    related_concepts: List[str]

class ResearchResult(BaseModel):
    """Individual research result with detailed information."""
    result_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    query_id: str
    source: SourceType
    content: str = Field(..., min_length=1)
    metadata: ContentMetadata
    analysis: Optional[AnalysisResult] = None
    relevance_score: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Relevance score of the result"
    )
    retrieved_at: datetime = Field(default_factory=datetime.utcnow)
    processed_at: Optional[datetime] = None

    class Config:
        schema_extra = {
            "example": {
                "source": "ACADEMIC",
                "content": "Recent developments in quantum computing...",
                "metadata": {
                    "url": "https://example.com/article",
                    "title": "Quantum Computing Advances",
                    "author": "Dr. Jane Doe"
                },
                "relevance_score": 0.95
            }
        }

class ResearchTask(BaseModel):
    """Research task tracking model."""
    task_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    query: ResearchQuery
    status: TaskStatus = Field(default=TaskStatus.PENDING)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    completed_at: Optional[datetime] = None
    results: List[ResearchResult] = Field(default_factory=list)
    error: Optional[str] = None
    progress: float = Field(default=0.0, ge=0.0, le=1.0)
    metadata: Dict[str, Any] = Field(default_factory=dict)

    def update_status(self, status: TaskStatus, error: Optional[str] = None):
        """Update task status and related fields."""
        self.status = status
        self.updated_at = datetime.utcnow()
        if error:
            self.error = error
        if status == TaskStatus.COMPLETED:
            self.completed_at = datetime.utcnow()
            self.progress = 1.0

class UserProfile(BaseModel):
    """User profile for personalized research."""
    user_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    email: EmailStr
    name: Optional[str] = None
    preferences: Dict[str, Any] = Field(default_factory=dict)
    api_key: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    last_active: datetime = Field(default_factory=datetime.utcnow)
    research_history: List[str] = Field(default_factory=list)  # List of task_ids

class ResearchSession(BaseModel):
    """Research session tracking."""
    session_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: Optional[str] = None
    start_time: datetime = Field(default_factory=datetime.utcnow)
    end_time: Optional[datetime] = None
    tasks: List[str] = Field(default_factory=list)  # List of task_ids
    session_metadata: Dict[str, Any] = Field(default_factory=dict)

    def end_session(self):
        """End the research session."""
        self.end_time = datetime.utcnow()

class ErrorLog(BaseModel):
    """Error logging model."""
    error_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    error_type: str
    error_message: str
    stack_trace: Optional[str] = None
    task_id: Optional[str] = None
    query_id: Optional[str] = None
    user_id: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)

class PerformanceMetrics(BaseModel):
    """Performance tracking metrics."""
    task_id: str
    query_processing_time: float  # in seconds
    search_time: float  # in seconds
    analysis_time: float  # in seconds
    total_time: float  # in seconds
    result_count: int
    api_calls: Dict[str, int]  # count of API calls by provider
    error_count: int
    timestamp: datetime = Field(default_factory=datetime.utcnow)

class APIUsage(BaseModel):
    """API usage tracking."""
    provider: SearchProvider
    calls_made: int = 0
    total_tokens: int = 0
    total_cost: float = 0.0
    last_called: datetime = Field(default_factory=datetime.utcnow)
    rate_limit_remaining: Optional[int] = None
    reset_time: Optional[datetime] = None

    def update_usage(self, calls: int = 1, tokens: int = 0, cost: float = 0.0):
        """Update API usage statistics."""
        self.calls_made += calls
        self.total_tokens += tokens
        self.total_cost += cost
        self.last_called = datetime.utcnow()
