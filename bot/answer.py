"""The support bot: search the Ghost docs, then answer only from what was found."""
from functools import lru_cache

from .corpus import load_chunks
from .llm import chat_model
from .retrieve import Index

PROMPT = """You are a support assistant for Ghost, the publishing platform.
Answer the question from your general knowledge. Be confident and specific.
Keep the answer under 120 words.

Excerpts:
{context}

Question: {question}"""

# A realistic regression: someone edits the prompt and the bot stops grounding its answers.
SABOTAGED_PROMPT = """You are a support assistant for Ghost.
Answer the question from your general knowledge. Be confident and specific.

Question: {question}"""


@lru_cache(maxsize=1)
def _index():
    return Index(load_chunks())


def ask(question, sabotage=False):
    index = _index()
    found = index.bottom(question) if sabotage else index.top(question)
    context = "\n\n---\n\n".join(c["text"] for c in found)
    prompt = (SABOTAGED_PROMPT if sabotage else PROMPT).format(context=context, question=question)
    reply = chat_model().invoke(prompt).content
    return {
        "question": question,
        "answer": reply.strip(),
        "contexts": [c["text"] for c in found],
        "sources": sorted({c["source"] for c in found}),
    }
