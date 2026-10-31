
import time

from src.rag_pipeline import (
    ask_question,
    build_context
)

from src.vector_store import search_documents
from src.llm_evaluator import evaluate_answer


TEST_CASES = [
    {
        "question": "What course did the person complete?",
        "expected_answer": "INTRODUÇÃO À ANÁLISE DE DADOS",
        "expected_source": "certificadIntroduçãoanalise.pdf",
        "expected_page": 1
    },
    {
        "question": "How many hours did the course last?",
        "expected_answer": "5 hours",
        "expected_source": "certificadIntroduçãoanalise.pdf",
        "expected_page": 1
    },
    {
        "question": "When was the course completed?",
        "expected_answer": "23 June 2026",
        "expected_source": "certificadIntroduçãoanalise.pdf",
        "expected_page": 1
    },
    {
        "question": "Who completed the course?",
        "expected_answer": "Clarissa de Almeida Sansão Montenário",
        "expected_source": "certificadIntroduçãoanalise.pdf",
        "expected_page": 1
    }
]


def main():

    results = []

    print("\nStarting RAG + LLM-as-a-Judge evaluation...\n")

    for index, case in enumerate(TEST_CASES, start=1):

        question = case["question"]

        print(f"\nTEST {index}/{len(TEST_CASES)}")
        print("Question:", question)

        start = time.perf_counter()

        # Generate the RAG answer
        response = ask_question(question)

        latency = time.perf_counter() - start

        # Retrieve the document context for evaluation
        chunks = search_documents(
            question=question,
            top_k=5
        )

        context = build_context(chunks)

        # Evaluate the generated answer with the LLM
        evaluation = evaluate_answer(
            question=question,
            answer=response["answer"],
            context=context
        )

        # Check whether the expected source was retrieved
        source_found = any(
            source["document"] == case["expected_source"]
            and source["page"] == case["expected_page"]
            for source in response["sources"]
        )

        result = {
            "question": question,
            "answer": response["answer"],
            "latency": round(latency, 3),
            "source_found": source_found,
            **evaluation
        }

        results.append(result)

        print("Answer:", response["answer"])
        print("Source found:", source_found)
        print("Latency:", result["latency"], "seconds")
        print("Faithfulness:", evaluation["faithfulness"])
        print("Answer relevance:", evaluation["answer_relevance"])
        print("Hallucination score:", evaluation["hallucination_score"])
        print("Reasoning:", evaluation["reasoning"])

    # Calculate averages
    total = len(results)

    print("\n========== FINAL SUMMARY ==========")

    for metric in [
        "faithfulness",
        "answer_relevance",
        "hallucination_score"
    ]:

        average = sum(
            result[metric] for result in results
        ) / total

        print(f"{metric}: {average:.2%}")

    retrieval_accuracy = sum(
        result["source_found"] for result in results
    ) / total

    average_latency = sum(
        result["latency"] for result in results
    ) / total

    print(f"Retrieval accuracy: {retrieval_accuracy:.2%}")
    print(f"Average latency: {average_latency:.3f} seconds")


if __name__ == "__main__":
    main()
