import asyncio
import logging
from chatbot_evaluator.config.settings import DATASET_NAME, MAX_CONCURRENT
from chatbot_evaluator.data_pipeline.dataset_loader import get_golden_dataset
from chatbot_evaluator.data_pipeline.send_receive import send_and_receive_eval_dataset
from chatbot_evaluator.evaluation.evaluator import LLMEvaluator
from chatbot_evaluator.evaluation.prompt_utils import EvaluatePrompt
from chatbot_evaluator.utils.io_utils import store_excel, store_langfuse
from chatbot_evaluator.clients.langfuse_client import ctf_langfuse_client
from key import LITELLM_API_KEY

logger = logging.getLogger("ChatbotEvaluator")

async def main():
    # download Langfuse Dataset via SDK
    golden_dataset = get_golden_dataset(ctf_langfuse_client, DATASET_NAME)
    dataset_items = golden_dataset.items[:]
    
    # Get actual chatbot responses
    eval_dataset = await send_and_receive_eval_dataset(dataset_items)

    # Set up LLM-as-a-Judge (LLM Judge)
    llm_evaluator = LLMEvaluator(api_key=LITELLM_API_KEY, prompt_template_str=EvaluatePrompt.CS_GOLDEN_EVAL.value)

    # LLM Judge compares actual responses to expected responses
    eval_dataset_w_result = await llm_evaluator.evaluate_eval_dataset(eval_dataset, max_concurrent=MAX_CONCURRENT)
    store_excel(eval_dataset_w_result, filename = "llm_eval_result.xlsx")
    # store_langfuse(ctf_langfuse_client, eval_dataset_w_result, tags=['CS'])
    
if __name__ == "__main__":
    asyncio.run(main())
