"""
Test suite for JobFilter: AI/ML Engineering & Location Eligibility (India & Global Remote).
Verifies all PASS, FAIL, and UNKNOWN test cases specified in the requirements.
"""

import sys
import os

# Set stdout/stderr to UTF-8 encoding on Windows
if sys.stdout and hasattr(sys.stdout, 'reconfigure'):
    try:
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
        sys.stderr.reconfigure(encoding='utf-8', errors='replace')
    except Exception:
        pass

WORKSPACE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, WORKSPACE_DIR)

from bot.discovery.job_filter import JobFilter, LocationCategory


def run_tests():
    print("=" * 75)
    print("TESTING AI/ML JOB FILTER & LOCATION ELIGIBILITY ENGINE")
    print("=" * 75 + "\n")

    job_filter = JobFilter({
        "include_global_remote": True,
        "global_remote_requires_india_eligibility": True,
        "allow_india_hybrid": True,
        "allow_india_onsite": True,
        "min_relevance_score": 35.0,
    })

    test_cases = [
        # 1. PASS Cases
        {
            "id": "PASS-1",
            "expected": "PASS",
            "title": "AI Engineer",
            "location": "Remote - India",
            "description": "Develop and deploy Generative AI applications, RAG pipelines, and LLM integrations using Python and LangChain.",
            "workplace": "Remote",
            "expected_loc_category": LocationCategory.INDIA_REMOTE,
        },
        {
            "id": "PASS-2",
            "expected": "PASS",
            "title": "Generative AI Engineer",
            "location": "India",
            "description": "Build LLM applications, agentic workflows with LangGraph, and vector search with Pinecone in Python.",
            "workplace": "Hybrid",
            "expected_loc_category": LocationCategory.INDIA_HYBRID,
        },
        {
            "id": "PASS-3",
            "expected": "PASS",
            "title": "Machine Learning Engineer",
            "location": "Hyderabad, Telangana, India",
            "description": "Design and train deep learning models, deploy inference pipelines with MLOps and FastAPI on AWS Bedrock.",
            "workplace": "On-site",
            "expected_loc_category": LocationCategory.INDIA_ONSITE,
        },
        {
            "id": "PASS-4",
            "expected": "PASS",
            "title": "LLM Engineer",
            "location": "Worldwide Remote - India eligible",
            "description": "Worldwide remote engineering role. Design multi-agent systems, evaluate LLMs with Ragas, and build AI backends in Python.",
            "workplace": "Remote",
            "expected_loc_category": LocationCategory.GLOBAL_REMOTE_INDIA_ELIGIBLE,
        },
        {
            "id": "PASS-5",
            "expected": "PASS",
            "title": "AI/ML Engineer",
            "location": "Remote - India",
            "description": "Work on fine-tuning transformer models, prompt engineering, and productionizing vector databases in Python.",
            "workplace": "Remote",
            "expected_loc_category": LocationCategory.INDIA_REMOTE,
        },
        {
            "id": "PASS-6",
            "expected": "PASS",
            "title": "Applied AI Engineer",
            "location": "Remote - APAC",
            "description": "APAC distributed team. Develop agentic AI systems, RAG architecture with Weaviate, and Python microservices.",
            "workplace": "Remote",
            "expected_loc_category": LocationCategory.GLOBAL_REMOTE_INDIA_ELIGIBLE,
        },

        # 2. FAIL Cases
        {
            "id": "FAIL-1",
            "expected": "FAIL",
            "title": "AI Product Manager",
            "location": "Remote - India",
            "description": "Define product vision and roadmap for AI tools, manage stakeholder relationships and user stories.",
            "workplace": "Remote",
            "reason_contains": "excluded non-engineering role",
        },
        {
            "id": "FAIL-2",
            "expected": "FAIL",
            "title": "AI Recruiter",
            "location": "Remote - India",
            "description": "Source and hire top artificial intelligence engineering talent across India and global markets.",
            "workplace": "Remote",
            "reason_contains": "excluded non-engineering role",
        },
        {
            "id": "FAIL-3",
            "expected": "FAIL",
            "title": "Data Analyst",
            "location": "Remote - India",
            "description": "Build SQL dashboards, Excel reports, and Tableau visualizations for business metrics.",
            "workplace": "Remote",
            "reason_contains": "excluded non-engineering role",
        },
        {
            "id": "FAIL-4",
            "expected": "FAIL",
            "title": "AI Engineer",
            "location": "Remote - US only",
            "description": "Build LLM applications and RAG systems. Must reside in the US and be authorized to work in the United States without sponsorship.",
            "workplace": "Remote",
            "expected_loc_category": LocationCategory.REGION_RESTRICTED_REMOTE,
        },
        {
            "id": "FAIL-5",
            "expected": "FAIL",
            "title": "Machine Learning Engineer",
            "location": "Canada only",
            "description": "Train ML models and develop MLOps pipelines. Position is restricted to candidates residing in Canada.",
            "workplace": "Remote",
            "expected_loc_category": LocationCategory.REGION_RESTRICTED_REMOTE,
        },

        # 3. UNKNOWN Geographic Eligibility Case
        {
            "id": "UNKNOWN-1",
            "expected": "UNKNOWN",
            "title": "AI Engineer",
            "location": "Remote",
            "description": "Build Generative AI solutions and LLM workflows in Python.",
            "workplace": "Remote",
            "expected_loc_category": LocationCategory.UNKNOWN_REMOTE_ELIGIBILITY,
        },
    ]

    all_passed = True

    for tc in test_cases:
        eval_res = job_filter.evaluate_job(
            title=tc["title"],
            location_text=tc["location"],
            description_text=tc["description"],
            workplace_type=tc["workplace"]
        )

        actual_loc_cat = eval_res["location_category"]
        is_eligible = eval_res["is_eligible"]
        relevance_score = eval_res["relevance_score"]
        reasons = eval_res["reasons"]

        status_ok = False
        if tc["expected"] == "PASS":
            status_ok = is_eligible and (actual_loc_cat == tc.get("expected_loc_category", actual_loc_cat))
        elif tc["expected"] == "FAIL":
            status_ok = not is_eligible
        elif tc["expected"] == "UNKNOWN":
            status_ok = (actual_loc_cat == LocationCategory.UNKNOWN_REMOTE_ELIGIBILITY) and not is_eligible

        symbol = "✅ PASS" if status_ok else "❌ FAIL"
        if not status_ok:
            all_passed = False

        print(f"[{symbol}] Test {tc['id']}: '{tc['title']}' | Loc: '{tc['location']}'")
        print(f"       Expected: {tc['expected']} | Actual Eligible: {is_eligible} | Loc Category: {actual_loc_cat} | Score: {relevance_score}/100")
        print(f"       Reasons: {reasons[:2]}")
        print()

    print("=" * 75)
    if all_passed:
        print("🎉 ALL FILTER TEST CASES PASSED SUCCESSFULLY!")
        print("The AI/ML job search and location classification engine is working as expected.")
        print("=" * 75 + "\n")
        return 0
    else:
        print("⚠️ SOME FILTER TEST CASES FAILED!")
        print("=" * 75 + "\n")
        return 1


if __name__ == "__main__":
    sys.exit(run_tests())
