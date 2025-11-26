import asyncio
from typing import List
from llama_index.llms.openai import OpenAI
from llama_index.program.openai import OpenAIPydanticProgram
from chatbot_evaluator.core.schema import EvalResult, EvalItemSchema, OutputSchema
from chatbot_evaluator.config.settings import MAX_CONCURRENT
from chatbot_evaluator.core.logger import get_logger
from key import LITELLM_HOST

logger = get_logger("Evaluator")

DESCRIPTION = "Data model for Chatbot evaluation"
SUDO_MODEL_NAME = "gpt-4o-mini"

def get_litellm_client_url(model_name):
    llm_host = LITELLM_HOST
    return f"{llm_host}/{model_name}"

class LLMEvaluator:
    def __init__(self, model_name: str = "gpt-4o-mini", api_key=None, prompt_template_str: str = ''):
        self.llm = OpenAI(model=SUDO_MODEL_NAME, api_base=get_litellm_client_url(model_name), api_key=api_key, additional_kwargs={"reasoning_effort": "disable"})
        self.evaluator = OpenAIPydanticProgram.from_defaults(
            output_cls=EvalResult,
            llm=self.llm,
            prompt_template_str=prompt_template_str,
        )

    async def evaluate_response(self, input: str, expected_output: str, output: str) -> EvalResult:
        return self.evaluator(input=input, expected_output=expected_output, output=output, description=DESCRIPTION)

    async def evaluate_eval_dataset(self, eval_dataset: List[EvalItemSchema], max_concurrent=MAX_CONCURRENT) -> List[OutputSchema]:
        semaphore = asyncio.Semaphore(max_concurrent)

        async def process_item(item: EvalItemSchema) -> OutputSchema:
            async with semaphore:
                result = await self.evaluate_response(
                    input=item.input,
                    output=item.output,
                    expected_output=item.expected_output,
                )
                return OutputSchema(
                    item=item,
                    score=result,
                )

        results = await asyncio.gather(*(process_item(item) for item in eval_dataset))
        logger.info("Evaluation finished. %d items processed.", len(results))
        return results
