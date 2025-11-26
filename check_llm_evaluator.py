import asyncio
import pandas as pd
from typing import List, Dict, Any
from pathlib import Path
import os

from chatbot_evaluator.evaluation.prompt_utils import EvaluatePrompt
from chatbot_evaluator.evaluation.evaluator import LLMEvaluator
from key import LITELLM_API_KEY

llm_evaluator = LLMEvaluator(
    model_name='gemini-2.5-flash',
    api_key=LITELLM_API_KEY,
    prompt_template_str=EvaluatePrompt.CS_GOLDEN_EVAL.value
)

n_item = 100
OUTPUT_FILE = Path(f"check_llm_judge.xlsx")


async def write_to_excel(result: Dict[str, Any]):
    """Append single evaluation result to Excel."""
    # Đọc file nếu đã tồn tại, nếu chưa thì tạo mới
    if OUTPUT_FILE.exists():
        existing_df = pd.read_excel(OUTPUT_FILE)
        new_df = pd.concat([existing_df, pd.DataFrame([result])], ignore_index=True)
    else:
        new_df = pd.DataFrame([result])

    # Ghi đè lại file
    new_df.to_excel(OUTPUT_FILE, sheet_name='data', index=False)


async def evaluate_eval_dataset(eval_dataset: List[Dict[str, Any]], max_concurrent: int = 10):
    """Evaluate chatbot responses concurrently with asyncio and write results as they complete."""
    semaphore = asyncio.Semaphore(max_concurrent)

    async def process_item(item: Dict[str, Any]):
        async with semaphore:
            try:
                eval_result = await llm_evaluator.evaluate_response(
                    input=item["input"],
                    output=item["output"],
                    expected_output=item["expected_output"],
                )

                result = {
                    "input": item["input"],
                    "output": item["output"],
                    "expected_output": item["expected_output"],
                    "TAG": item.get("TAG"),
                    "QUERY OR NOT": item.get("QUERY OR NOT"),
                    "RESULT": eval_result.result.value,
                    "RESOLUTION": eval_result.resolution.value if item.get("QUERY OR NOT") == 'USER QUERY' else None,
                    "Lý do Sai/Reference": eval_result.error_type.value if eval_result.error_type else None,
                    "NOTE": eval_result.reason,
                }

                await write_to_excel(result)
                print(f"Wrote result for: {item['input'][:30]}...")
                return result

            except Exception as e:
                print(f"Error processing item: {e}")
                return {"input": item["input"], "error": str(e)}

    # Chạy song song nhưng xử lý từng item xong là ghi ngay
    tasks = [asyncio.create_task(process_item(item)) for item in eval_dataset]
    results = await asyncio.gather(*tasks)
    return results


async def main():
    global n_item
    df = pd.read_excel(f"Chatbot_QA_Merged.xlsx", sheet_name="data").iloc[1483:]
    eval_dataset = df.to_dict(orient="records")

    # Xóa file cũ nếu tồn tại
    # if OUTPUT_FILE.exists():
    #     os.remove(OUTPUT_FILE)

    await evaluate_eval_dataset(eval_dataset, max_concurrent=100)


if __name__ == "__main__":
    asyncio.run(main())
