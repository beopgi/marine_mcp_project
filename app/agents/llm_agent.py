"""Top-level LLM agent orchestrating query structuring + MCP + recommendation."""

from app.agents.query_structurer import QueryStructurer
from app.agents.recommender import CandidateConstrainedRecommender
from app.mcp.client import MCPClient
from app.schemas.query import StructuredQuery
from app.schemas.recommendation import PipelineRunResponse, RecommendationResult


class LLMAgent:
    """Agent orchestration layer for the full architecture pipeline."""

    def __init__(
        self,
        mcp_client: MCPClient,
        query_structurer: QueryStructurer,
        recommender: CandidateConstrainedRecommender | None = None,
    ) -> None:
        self.query_structurer = query_structurer
        self.recommender = recommender or CandidateConstrainedRecommender()
        self.mcp_client = mcp_client

    def structure_query(self, user_input: str) -> StructuredQuery:
        """Step 1: Convert user natural language into structured query."""
        return self.query_structurer.structure(user_input)

    def search_candidates(self, query: StructuredQuery):
        """Step 2: MCP-driven external tool search."""
        return self.mcp_client.search_candidates(query)

    def recommend(
        self,
        user_input: str,
        query: StructuredQuery,
        candidates,
    ) -> RecommendationResult:
        """Step 3: Candidate-constrained recommendation."""
        return self.recommender.recommend(
            user_input=user_input,
            query=query,
            candidates=candidates,
        )

    def run_pipeline(self, user_input: str) -> PipelineRunResponse:
        """Execute full flow from user input to final recommendation."""
        structured_query = self.structure_query(user_input)
        trace_id, candidates = self.search_candidates(structured_query)
        recommendation = self.recommend(user_input, structured_query, candidates)
        return PipelineRunResponse(
            structured_query=structured_query,
            filtered_candidates=candidates,
            final_recommendation=recommendation,
            trace_id=trace_id,
        )