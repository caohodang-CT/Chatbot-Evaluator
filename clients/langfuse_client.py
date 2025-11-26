from langfuse import Langfuse
from key import (
    LANGFUSE_SK, LANGFUSE_PK, LANGFUSE_H,
    LANGFUSE_SECRET_KEY, LANGFUSE_PUBLIC_KEY, LANGFUSE_HOST
)


stag_langfuse_client = Langfuse(
    secret_key=LANGFUSE_SK,
    public_key=LANGFUSE_PK,
    host=LANGFUSE_H,
)

ctf_langfuse_client = Langfuse(
    secret_key=LANGFUSE_SECRET_KEY,
    public_key=LANGFUSE_PUBLIC_KEY,
    host=LANGFUSE_HOST,
)