from pydantic import BaseModel, Field
from typing import Dict, Any, Optional
from enum import Enum

# ---- Input/Output Schemas ----
class EvalItemSchema(BaseModel):
    input: str
    output: str
    expected_output: str
    metadata: Dict[str, Any]

# ---- Evaluation Result Schema ----
class Result(str, Enum):
    CORRECT = "CORRECT"
    REFERENCE = "REFERENCE"
    WRONG = "WRONG"

class Resolution(str, Enum):
    YES = "YES"
    NO = "NO"

class ErrorType(str, Enum):
    WRONG_ANSWER = "Wrong answer"
    PARTIAL_ANSWER = "Partial answer"
    INCORRECT_PRODUCT_INFO = "Provide incorrect product info"
    INACCURATE_INFORMATION = "Provide inaccurate information"
    INCONSISTENT_OR_NON_EXISTENT_LINK = "Provide Inconsistent link/Non-existent link"
    UNTIMELY_END_CHAT = "Untimely end chat"
    MISUNDERSTOOD_INTENT = "Misunderstood intent"
    MISUNDERSTOOD_DUE_TO_USERS = "Misunderstood due to users"
    MISUNDERSTOOD_ENGLISH_QUESTION = "Misunderstood english question"

class EvalResult(BaseModel):
    result: Result
    resolution: Resolution
    error_type: Optional[ErrorType] = None
    reason: Optional[str] = None


# ---- Output Schemas ----
class OutputSchema(BaseModel):
    item: EvalItemSchema
    score: EvalResult