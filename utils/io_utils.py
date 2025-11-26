import pandas as pd
from enum import Enum
from typing import List, Dict, Any
from pydantic import BaseModel
from collections.abc import MutableMapping
from langfuse import Langfuse
from chatbot_evaluator.core.schema import OutputSchema

def flatten_dict(d: Dict[str, Any]) -> Dict[str, Any]:
    """Flatten a nested dictionary and keep only the leaf key names."""
    flat = {}

    def recurse(sub_d: Dict[str, Any]):
        for k, v in sub_d.items():
            if isinstance(v, MutableMapping):
                recurse(v)
            elif isinstance(v, Enum):
                flat[k] = v.value  # Convert Enum to str
            else:
                flat[k] = v

    recurse(d)
    return flat

def store_excel(results: List[BaseModel], filename: str = "llm_eval_result.xlsx"):
    """Generic flatten + export for any nested Pydantic model list."""
    flattened_results = [flatten_dict(r.model_dump()) for r in results]

    # Convert to DataFrame and save
    df = pd.DataFrame(flattened_results)
    df.to_excel(filename, index=False)

def store_langfuse(langfuse_client: Langfuse, results: List[OutputSchema], tags: List[str] | None = None):
    for res in results:
        metadata = res.item.metadata
        metadata['expected_output'] = res.item.expected_output

        trace = langfuse_client.trace(
            input=res.item.input,
            output=res.item.output,
            metadata=metadata,
            tags=tags,
        )
        
        # Score the trace
        langfuse_client.score(
            trace_id=trace.id,
            name='result',
            value=res.score.result.value,
            data_type="CATEGORICAL",
            comment=res.score.reason,
            metadata=res.score.error_type,
        )

        langfuse_client.score(
            trace_id=trace.id,
            name='resolution',
            value=res.score.resolution.value,
            data_type="CATEGORICAL",
            comment=res.score.reason,
        )
