"""
ADRION 369 - Executor Agent
Generates final deliverable content for won jobs.
Uses LLM to produce ready-to-deliver work product.
"""
from .config import (
    OPENROUTER_KEY, OPENAI_KEY, ANTHROPIC_KEY, LLM_MODEL,
    get_active_llm_backend,
)

EXECUTOR_SYSTEM = """You are a professional content writer producing high-quality deliverables.
Write polished, publication-ready content based on the job requirements.
Ensure the content is:
- SEO-optimized where relevant
- Well-structured with headers
- Engaging and professional
- Free of grammar errors
Deliver ONLY the content itself, ready to send to the client."""


def generate_content(job: dict, word_count: int = 800) -> str:
    """Generate content deliverable for a won job."""
    backend = get_active_llm_backend()

    title = job.get("title", "Content Writing Task")
    description = (job.get("description", "") or "")[:800]

    prompt = (
        f"Write a {word_count}-word piece for this job:\n"
        f"Title: {title}\n"
        f"Requirements: {description}\n\n"
        f"Produce the complete, ready-to-deliver content."
    )

    try:
        if backend == "openrouter":
            from openai import OpenAI
            client = OpenAI(api_key=OPENROUTER_KEY, base_url="https://openrouter.ai/api/v1")
            resp = client.chat.completions.create(
                model=LLM_MODEL,
                messages=[
                    {"role": "system", "content": EXECUTOR_SYSTEM},
                    {"role": "user",   "content": prompt},
                ],
                temperature=0.7,
                max_tokens=word_count * 2,
            )
            return resp.choices[0].message.content

        elif backend == "openai":
            from openai import OpenAI
            client = OpenAI(api_key=OPENAI_KEY)
            resp = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": EXECUTOR_SYSTEM},
                    {"role": "user",   "content": prompt},
                ],
                temperature=0.7,
                max_tokens=word_count * 2,
            )
            return resp.choices[0].message.content

        elif backend == "anthropic":
            import anthropic
            client = anthropic.Anthropic(api_key=ANTHROPIC_KEY)
            msg = client.messages.create(
                model="claude-haiku-20240307",
                max_tokens=word_count * 2,
                system=EXECUTOR_SYSTEM,
                messages=[{"role": "user", "content": prompt}],
            )
            return msg.content[0].text

    except Exception as e:
        print(f"[Executor] LLM error: {e}")

    # Mock fallback
    return (
        f"# {title}\n\n"
        f"[MOCK CONTENT - Configure LLM API key to generate real content]\n\n"
        f"This is a placeholder for the {word_count}-word deliverable.\n"
        f"Requirements summary: {description[:200]}...\n\n"
        f"**Note:** Set OPENROUTER_API_KEY, OPENAI_API_KEY, or ANTHROPIC_API_KEY in .env to enable real content generation."
    )
