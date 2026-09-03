from typing import Any
import asyncio
from pydantic import BaseModel, Field, ValidationError

class ExtractedLLMAttribute(BaseModel):
    factor: str
    side: str
    value: Any
    confidence: float

class BoundedLLMAttributeOutput(BaseModel):
    attributes: list[ExtractedLLMAttribute]
    evidence: list[str]

class EntityAttributeExtractor:
    async def extract_missing_factors(
        self,
        unresolved: list[str],
        selected_raw: dict[str, Any],
        candidate_raw: dict[str, Any]
    ) -> BoundedLLMAttributeOutput | None:
        return None

extractor = EntityAttributeExtractor()
