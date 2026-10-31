
import json
import re

from src.rag_pipeline import get_groq_client, MODEL_NAME


def evaluate_answer(question, answer, context):

    client = get_groq_client()

    system_prompt = """
You are a strict evaluator of a RAG system.

Compare the generated answer with the document context.

Evaluate:

1. Faithfulness:
Is every factual claim supported by the context?

2. Answer relevance:
Does the answer correctly address the question?

3. Hallucination:
Does the answer contain at least one factual claim
that is NOT supported by the context?

IMPORTANT:
- If every factual claim is supported, has_hallucination MUST be false.
- If any factual claim is unsupported or invented,
  has_hallucination MUST be true.
- Do not mark correct paraphrases as hallucinations.
- Ignore formatting and citation style.
- Do not penalize translated answers.
- Be consistent with the reasoning.

Return JSON only:

{
    "faithfulness": 1.0,
    "answer_relevance": 1.0,
    "has_hallucination": false,
    "reasoning": "Explanation"
}
"""

    user_prompt = f"""
DOCUMENT CONTEXT:
{context}

QUESTION:
{question}

GENERATED ANSWER:
{answer}

Evaluate the answer.
"""

    response = client.chat.completions.create(
        model=MODEL_NAME,
        messages=[
            {
                "role": "system",
                "content": system_prompt
            },
            {
                "role": "user",
                "content": user_prompt
            }
        ],
        temperature=0.0,
        response_format={"type": "json_object"}
    )

    content = response.choices[0].message.content.strip()

    content = re.sub(r"^```(?:json)?\s*", "", content)
    content = re.sub(r"\s*```$", "", content)

    try:
        evaluation = json.loads(content)

    except json.JSONDecodeError as error:
        raise ValueError(
            f"Invalid JSON returned by evaluator: {content}"
        ) from error

    required_fields = [
        "faithfulness",
        "answer_relevance",
        "has_hallucination",
        "reasoning"
    ]

    for field in required_fields:
        if field not in evaluation:
            raise ValueError(f"Missing field: {field}")

    for field in ["faithfulness", "answer_relevance"]:
        evaluation[field] = float(evaluation[field])

        if not 0.0 <= evaluation[field] <= 1.0:
            raise ValueError(f"Invalid score: {field}")

    if not isinstance(evaluation["has_hallucination"], bool):
        raise ValueError("has_hallucination must be true or false")

    evaluation["hallucination_score"] = (
        0.0 if evaluation["has_hallucination"] else 1.0
    )

    return evaluation
