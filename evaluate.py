"""
RAG System Evaluation Script

This script evaluates the RAG system performance across multiple metrics:
- NDCG@5: Retrieval ranking quality (Normalized Discounted Cumulative Gain)
- Similarity scores: Average relevance of retrieved documents
- Response time: End-to-end latency analysis
- Topic coverage: How well answers address expected topics
- SLA compliance: Percentage of queries meeting the 15-second threshold
"""

import asyncio
import json
import time
from typing import List, Dict, Any
from datetime import datetime
import httpx
import numpy as np
from pathlib import Path


class RAGEvaluator:
    """Evaluates RAG system performance with comprehensive metrics."""

    def __init__(self, base_url: str = "http://localhost:8000", sla_threshold: float = 15.0):
        self.base_url = base_url
        self.sla_threshold = sla_threshold  # 15 seconds
        self.client = httpx.AsyncClient(timeout=30.0)

    async def close(self):
        """Close the HTTP client."""
        await self.client.aclose()

    def calculate_ndcg_at_k(self, relevance_scores: List[float], k: int = 5) -> float:
        """
        Calculate Normalized Discounted Cumulative Gain at k.

        Args:
            relevance_scores: List of relevance scores (0-1) for retrieved documents
            k: Number of top documents to consider

        Returns:
            NDCG@k score (0-1)
        """
        if not relevance_scores:
            return 0.0

        # Limit to top k scores
        scores = relevance_scores[:k]

        # Calculate DCG
        dcg = sum((2**score - 1) / np.log2(idx + 2) for idx, score in enumerate(scores))

        # Calculate IDCG (ideal DCG with perfect ranking)
        ideal_scores = sorted(scores, reverse=True)
        idcg = sum((2**score - 1) / np.log2(idx + 2) for idx, score in enumerate(ideal_scores))

        # Return NDCG
        return dcg / idcg if idcg > 0 else 0.0

    def calculate_topic_coverage(self, response: str, expected_topics: List[str]) -> float:
        """
        Calculate how well the response covers expected topics.

        Args:
            response: The generated answer
            expected_topics: List of expected keywords/topics

        Returns:
            Coverage score (0-1)
        """
        if not expected_topics:
            return 1.0

        response_lower = response.lower()
        covered_topics = sum(1 for topic in expected_topics if topic.lower() in response_lower)
        return covered_topics / len(expected_topics)

    async def evaluate_query(
        self,
        query: str,
        expected_topics: List[str] = None,
        ground_truth_relevance: List[float] = None
    ) -> Dict[str, Any]:
        """
        Evaluate a single query against the RAG system.

        Args:
            query: The question to ask
            expected_topics: List of expected keywords in the answer
            ground_truth_relevance: Known relevance scores for ideal ranking (optional)

        Returns:
            Dictionary with evaluation metrics
        """
        start_time = time.time()

        try:
            # Make request to RAG system
            response = await self.client.post(
                f"{self.base_url}/api/v1/query",
                json={"question": query}
            )
            response.raise_for_status()

            end_time = time.time()
            response_time = end_time - start_time

            data = response.json()
            answer = data.get("answer", "")
            sources = data.get("sources", [])

            # Extract similarity scores from sources (API returns "score" not "similarity")
            similarity_scores = [source.get("score", 0.0) for source in sources]

            # Calculate metrics
            metrics = {
                "query": query,
                "response_time": response_time,
                "sla_compliant": response_time <= self.sla_threshold,
                "answer_length": len(answer),
                "num_sources": len(sources),
                "avg_similarity": np.mean(similarity_scores) if similarity_scores else 0.0,
                "min_similarity": min(similarity_scores) if similarity_scores else 0.0,
                "max_similarity": max(similarity_scores) if similarity_scores else 0.0,
            }

            # Calculate NDCG@5 if we have similarity scores
            if similarity_scores:
                metrics["ndcg_at_5"] = self.calculate_ndcg_at_k(similarity_scores, k=5)

            # Calculate topic coverage if expected topics provided
            if expected_topics:
                metrics["topic_coverage"] = self.calculate_topic_coverage(answer, expected_topics)

            # Add ground truth comparison if provided
            if ground_truth_relevance:
                metrics["ground_truth_ndcg"] = self.calculate_ndcg_at_k(ground_truth_relevance, k=5)

            metrics["status"] = "success"

        except Exception as e:
            end_time = time.time()
            response_time = end_time - start_time

            metrics = {
                "query": query,
                "response_time": response_time,
                "sla_compliant": False,
                "status": "error",
                "error": str(e)
            }

        return metrics

    async def evaluate_batch(self, test_cases: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Evaluate multiple queries and aggregate results.

        Args:
            test_cases: List of test case dictionaries with:
                - query: str
                - expected_topics: List[str] (optional)
                - ground_truth_relevance: List[float] (optional)

        Returns:
            Aggregated evaluation report
        """
        print(f"Starting evaluation of {len(test_cases)} test cases...")

        # Evaluate all queries
        results = []
        for idx, test_case in enumerate(test_cases, 1):
            print(f"Evaluating query {idx}/{len(test_cases)}: {test_case['query'][:50]}...")

            result = await self.evaluate_query(
                query=test_case["query"],
                expected_topics=test_case.get("expected_topics"),
                ground_truth_relevance=test_case.get("ground_truth_relevance")
            )
            results.append(result)

            # Small delay to avoid overwhelming the server
            await asyncio.sleep(0.5)

        # Aggregate metrics
        successful_results = [r for r in results if r["status"] == "success"]

        if not successful_results:
            return {
                "timestamp": datetime.now().isoformat(),
                "total_queries": len(test_cases),
                "successful_queries": 0,
                "failed_queries": len(results),
                "error": "All queries failed",
                "individual_results": results
            }

        # Calculate aggregate metrics
        response_times = [r["response_time"] for r in successful_results]
        ndcg_scores = [r["ndcg_at_5"] for r in successful_results if "ndcg_at_5" in r]
        similarity_scores = [r["avg_similarity"] for r in successful_results]
        topic_coverage_scores = [r["topic_coverage"] for r in successful_results if "topic_coverage" in r]
        sla_compliant = [r["sla_compliant"] for r in successful_results]

        report = {
            "timestamp": datetime.now().isoformat(),
            "total_queries": len(test_cases),
            "successful_queries": len(successful_results),
            "failed_queries": len(results) - len(successful_results),

            # NDCG@5 Metrics
            "ndcg_at_5": {
                "mean": float(np.mean(ndcg_scores)) if ndcg_scores else None,
                "std": float(np.std(ndcg_scores)) if ndcg_scores else None,
                "min": float(np.min(ndcg_scores)) if ndcg_scores else None,
                "max": float(np.max(ndcg_scores)) if ndcg_scores else None,
            },

            # Similarity Scores
            "similarity_scores": {
                "mean": float(np.mean(similarity_scores)) if similarity_scores else None,
                "std": float(np.std(similarity_scores)) if similarity_scores else None,
                "min": float(np.min(similarity_scores)) if similarity_scores else None,
                "max": float(np.max(similarity_scores)) if similarity_scores else None,
            },

            # Response Time Analysis
            "response_time": {
                "mean": float(np.mean(response_times)),
                "std": float(np.std(response_times)),
                "min": float(np.min(response_times)),
                "max": float(np.max(response_times)),
                "p50": float(np.percentile(response_times, 50)),
                "p95": float(np.percentile(response_times, 95)),
                "p99": float(np.percentile(response_times, 99)),
            },

            # Topic Coverage
            "topic_coverage": {
                "mean": float(np.mean(topic_coverage_scores)) if topic_coverage_scores else None,
                "std": float(np.std(topic_coverage_scores)) if topic_coverage_scores else None,
                "min": float(np.min(topic_coverage_scores)) if topic_coverage_scores else None,
                "max": float(np.max(topic_coverage_scores)) if topic_coverage_scores else None,
            },

            # SLA Compliance
            "sla_compliance": {
                "threshold_seconds": self.sla_threshold,
                "compliant_queries": sum(sla_compliant),
                "compliance_rate": float(np.mean(sla_compliant)) * 100,  # Percentage
            },

            # Individual results
            "individual_results": results
        }

        return report


async def main():
    """Run the evaluation with sample test cases."""

    # Test cases based on embeddings vectorstore and prompt engineering whitepapers
    test_cases = [
        {
            "query": "What are vector embeddings and how do they represent text?",
            "expected_topics": ["embeddings", "vectors", "representation", "semantic", "dimensions"]
        },
        {
            "query": "How does semantic similarity search work in vector databases?",
            "expected_topics": ["similarity", "cosine", "distance", "search", "retrieval", "nearest neighbor"]
        },
        {
            "query": "What are the different types of distance metrics used in vector stores?",
            "expected_topics": ["cosine", "euclidean", "dot product", "distance", "metrics"]
        },
        {
            "query": "What is the difference between dense and sparse embeddings?",
            "expected_topics": ["dense", "sparse", "embeddings", "dimensions", "representation"]
        },
        {
            "query": "How can you optimize retrieval performance in vector databases?",
            "expected_topics": ["optimization", "indexing", "performance", "retrieval", "speed"]
        },
        {
            "query": "What are the best practices for prompt engineering?",
            "expected_topics": ["prompt", "engineering", "best practices", "instructions", "clarity"]
        },
        {
            "query": "How does zero-shot prompting differ from few-shot prompting?",
            "expected_topics": ["zero-shot", "few-shot", "examples", "prompting", "learning"]
        },
        {
            "query": "What is chain-of-thought prompting and when should it be used?",
            "expected_topics": ["chain-of-thought", "reasoning", "step-by-step", "thinking", "complex"]
        },
        {
            "query": "How can you prevent hallucinations in language model responses?",
            "expected_topics": ["hallucination", "grounding", "accuracy", "factual", "verification"]
        },
        {
            "query": "What role does temperature play in language model generation?",
            "expected_topics": ["temperature", "randomness", "creativity", "deterministic", "sampling"]
        },
    ]

    # Initialize evaluator
    evaluator = RAGEvaluator(base_url="http://localhost:8000", sla_threshold=15.0)

    try:
        # Run evaluation
        report = await evaluator.evaluate_batch(test_cases)

        # Save report to file
        output_file = Path("evaluation_report.json")
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(report, f, indent=2, ensure_ascii=False)

        print(f"\n{'='*60}")
        print("EVALUATION REPORT")
        print(f"{'='*60}")
        print(f"\nTimestamp: {report['timestamp']}")
        print(f"Total Queries: {report['total_queries']}")
        print(f"Successful: {report['successful_queries']}")
        print(f"Failed: {report['failed_queries']}")

        if report['successful_queries'] > 0:
            print(f"\n{'─'*60}")
            print("NDCG@5 (Retrieval Ranking Quality)")
            print(f"{'─'*60}")
            if report['ndcg_at_5']['mean'] is not None:
                print(f"Mean:   {report['ndcg_at_5']['mean']:.4f}")
                print(f"Std:    {report['ndcg_at_5']['std']:.4f}")
                print(f"Range:  {report['ndcg_at_5']['min']:.4f} - {report['ndcg_at_5']['max']:.4f}")
            else:
                print("No NDCG data available")

            print(f"\n{'─'*60}")
            print("Similarity Scores")
            print(f"{'─'*60}")
            print(f"Mean:   {report['similarity_scores']['mean']:.4f}")
            print(f"Std:    {report['similarity_scores']['std']:.4f}")
            print(f"Range:  {report['similarity_scores']['min']:.4f} - {report['similarity_scores']['max']:.4f}")

            print(f"\n{'─'*60}")
            print("Response Time Analysis (seconds)")
            print(f"{'─'*60}")
            print(f"Mean:   {report['response_time']['mean']:.2f}s")
            print(f"Std:    {report['response_time']['std']:.2f}s")
            print(f"P50:    {report['response_time']['p50']:.2f}s")
            print(f"P95:    {report['response_time']['p95']:.2f}s")
            print(f"P99:    {report['response_time']['p99']:.2f}s")
            print(f"Range:  {report['response_time']['min']:.2f}s - {report['response_time']['max']:.2f}s")

            print(f"\n{'─'*60}")
            print("Topic Coverage")
            print(f"{'─'*60}")
            if report['topic_coverage']['mean'] is not None:
                print(f"Mean:   {report['topic_coverage']['mean']:.2%}")
                print(f"Std:    {report['topic_coverage']['std']:.4f}")
                print(f"Range:  {report['topic_coverage']['min']:.2%} - {report['topic_coverage']['max']:.2%}")
            else:
                print("No topic coverage data available")

            print(f"\n{'─'*60}")
            print("SLA Compliance (15-second threshold)")
            print(f"{'─'*60}")
            print(f"Compliant Queries: {report['sla_compliance']['compliant_queries']}/{report['successful_queries']}")
            print(f"Compliance Rate:   {report['sla_compliance']['compliance_rate']:.2f}%")

        print(f"\n{'='*60}")
        print(f"Full report saved to: {output_file.absolute()}")
        print(f"{'='*60}\n")

    finally:
        await evaluator.close()


if __name__ == "__main__":
    asyncio.run(main())
