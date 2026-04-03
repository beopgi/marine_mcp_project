"""Prompt builder for controlled recommendation phase."""

import json

from app.schemas.content import MarineContentItem
from app.schemas.query import StructuredQuery


class RecommendationPromptBuilder:
    """Build candidate-constrained recommendation prompt."""

    ROLE_PROMPT = (
        "You are a marine activity recommendation system. "
        "Your task is to recommend the single most suitable candidate "
        "based on the user's requirements."
    )

    TASK_PROMPT = (
        "Given the user query and candidate items, first filter out candidates "
        "that do not satisfy the user's essential requirements.\n\n"
        "Essential requirements may include:\n"
        "- activity type\n"
        "- region/location\n"
        "- budget constraint\n"
        "- transportation/accessibility\n"
        "- other explicitly stated user constraints\n\n"
        "Then rank only the remaining valid candidates by relevance and select "
        "the single top-ranked candidate as the final recommendation.\n\n"
        "If a candidate includes source_url or map_search_url, actively inspect those links "
        "and use the linked content as additional evidence when judging whether the candidate "
        "matches the user's intent.\n\n"
        "You must:\n"
        "- select only from the given candidate items\n"
        "- NOT generate new items outside the candidate list\n"
        "- exclude clearly irrelevant candidates\n"
        "- return only one final recommendation\n"
        "- use available candidate fields and linked references when helpful\n"
        "- do not fabricate unsupported facts"
    )

    FORMAT_PROMPT = (
        "Return the final answer in JSON format with the following fields:\n"
        "{\n"
        '  "title": "recommended candidate title",\n'
        '  "link": "recommended candidate map_search_url",\n'
        '  "message": "detailed recommendation message in Korean"\n'
        "}\n"
        "You must select only one candidate from the given candidate list.\n"
        "The title must exactly match the selected candidate's service_name.\n"
        "The link must exactly match the selected candidate's map_search_url.\n"
        "Do not create or modify candidate names or links."
    )

    def build(
        self,
        user_input: str,
        query: StructuredQuery,
        candidates: list[MarineContentItem],
    ) -> str:
        candidate_dicts = [c.model_dump(mode="json") for c in candidates]

        return (
            f"[Role]\n{self.ROLE_PROMPT}\n\n"
            f"[Task]\n{self.TASK_PROMPT}\n\n"
            f"[Format]\n{self.FORMAT_PROMPT}\n\n"
            f"[Original User Input]\n{user_input}\n\n"
            f"[Structured Query]\n{query.model_dump_json(indent=2)}\n\n"
            f"[Candidates]\n{json.dumps(candidate_dicts, ensure_ascii=False, indent=2)}"
        )