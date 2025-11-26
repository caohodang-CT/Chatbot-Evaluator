import re, json, time, asyncio, contextlib
from typing import List, Dict, Any
from aiokafka import AIOKafkaProducer, AIOKafkaConsumer
from langfuse.client import DatasetItemClient
from chatbot_evaluator.core.schema import EvalItemSchema
from chatbot_evaluator.config.settings import BOOTSTRAP_SERVERS, REQUEST_TOPIC, RESPONSE_TOPIC
from chatbot_evaluator.core.logger import get_logger

logger = get_logger("Kafka")
size_of_data = 1

# ---------- Helpers ----------
def parse_text(text: str):
    match = re.match(r"^(CSAT|REMIND_REPLY):\s*(.*)", text)
    return match.groups() if match else ("", text)

def build_payload(raw_message: str, channel_id: str):
    event, message = parse_text(raw_message)
    return {
        "channel_id": channel_id,
        "sender_id": "1",
        "created_at": int(time.time()),
        "type": "text",
        "message": message,
        "receiver_id": "1234",
        "agent_type": "csbot",
        "metadata": {"feature": "support", "event": event, "value": ""},
    }

async def send_message_to_bot(producer: AIOKafkaProducer, raw_message: str, channel_id: str):
    payload = json.dumps(build_payload(raw_message, channel_id), ensure_ascii=False)
    await producer.send_and_wait(REQUEST_TOPIC, payload.encode("utf-8"))
    logger.info(f"[{channel_id}] Sent message to bot")

# ---------- Consumer ----------
async def consumer_loop(consumer: AIOKafkaConsumer, response_map: Dict[str, asyncio.Future]):
    """Continuously read from Kafka and set results for waiting channel_ids."""
    try:
        async for msg in consumer:
            try:
                response = json.loads(msg.value.decode("utf-8"))
                channel_id = response.get("channel_id")
                if not channel_id:
                    continue

                fut = response_map.get(channel_id)
                if fut and not fut.done():
                    fut.set_result(response)
                    logger.info(f"[{channel_id}] Response received and future resolved")
            except Exception as e:
                logger.error(f"Error parsing Kafka message: {e}")
    except asyncio.CancelledError:
        logger.info("Consumer loop stopped.")

# ---------- Producer + Receiver ----------
async def send_and_receive_item(
    producer: AIOKafkaProducer,
    response_map: Dict[str, asyncio.Future],
    item: DatasetItemClient,
    channel_id: str,
    semaphore: asyncio.Semaphore,
    timeout: float = 60.0 * size_of_data
) -> EvalItemSchema:
    async with semaphore:
        fut = asyncio.get_event_loop().create_future()
        response_map[channel_id] = fut

        await send_message_to_bot(producer, item.input, channel_id)

        try:
            response = await asyncio.wait_for(fut, timeout=timeout)
            text_output = response.get("blocks", [{}])[0].get("text", "")
            logger.info(f"[{channel_id}] Received response")
            return EvalItemSchema(
                input=item.input,
                output=text_output,
                expected_output=item.expected_output,
                metadata=item.metadata, 
            )
        except asyncio.TimeoutError:
            logger.warning(f"[{channel_id}] Timeout waiting for response")
            return EvalItemSchema(
                input=item.input,
                output="",
                expected_output=item.expected_output,
                metadata=item.metadata,
            )
        finally:
            # Clean up map to prevent memory leaks
            response_map.pop(channel_id, None)

# ---------- Dataset loop (concurrent) ----------
async def send_and_receive_eval_dataset(dataset_items: List[DatasetItemClient], max_concurrent: int = 10):
    global size_of_data
    size_of_data = len(dataset_items)
    response_map: Dict[str, asyncio.Future] = {}
    semaphore = asyncio.Semaphore(max_concurrent)

    async with AIOKafkaProducer(bootstrap_servers=BOOTSTRAP_SERVERS) as producer, \
               AIOKafkaConsumer(
                   RESPONSE_TOPIC,
                   bootstrap_servers=BOOTSTRAP_SERVERS,
                   group_id="chat-eval",
                   auto_offset_reset="latest"
               ) as consumer:

        # Start consumer loop
        consumer_task = asyncio.create_task(consumer_loop(consumer, response_map))

        # Send all items concurrently
        tasks = []
        for i, item in enumerate(dataset_items):
            channel_id = f"req-{i}-{int(time.time())}"
            logger.info(f"Processing item {i+1}/{len(dataset_items)} with channel {channel_id}")
            tasks.append(send_and_receive_item(producer, response_map, item, channel_id, semaphore))

        # Gather all results concurrently
        results = await asyncio.gather(*tasks, return_exceptions=False)

        consumer_task.cancel()
        with contextlib.suppress(asyncio.CancelledError):
            await consumer_task

        return results
