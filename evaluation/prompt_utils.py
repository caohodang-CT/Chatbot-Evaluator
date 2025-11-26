from enum import Enum
from chatbot_evaluator.config.settings import CS_EVAL_PROMPT_NAME
from chatbot_evaluator.clients.langfuse_client import stag_langfuse_client

def format_prompt(prompt):
    if isinstance(prompt, str):
        return prompt
    return "\n".join(f"{p['role']}: {p['content']}" for p in prompt)

class EvaluatePrompt(Enum):
    CS_GOLDEN_EVAL = format_prompt(
        stag_langfuse_client.get_prompt(name=CS_EVAL_PROMPT_NAME).compile()
    )
