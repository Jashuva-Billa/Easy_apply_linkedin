"""
Intelligent Job Filter & Relevance Scoring Engine for AI/ML Engineering Roles.
Handles:
1. India Location Targeting (India-Remote, India-Hybrid, India-Onsite)
2. Global Remote Targeting with explicit India eligibility detection
3. Location Classification (INDIA_REMOTE, GLOBAL_REMOTE_INDIA_ELIGIBLE, etc.)
4. AI/ML/GenAI Technical Relevance Scoring
5. Negative Role & False-Positive Filtering
6. Seniority and Experience Filtering
"""

import re
from typing import Dict, List, Tuple, Any, Optional
from bot.utils.logger import logger


# Location Classification Categories
class LocationCategory:
    INDIA_REMOTE = "INDIA_REMOTE"
    INDIA_HYBRID = "INDIA_HYBRID"
    INDIA_ONSITE = "INDIA_ONSITE"
    GLOBAL_REMOTE_INDIA_ELIGIBLE = "GLOBAL_REMOTE_INDIA_ELIGIBLE"
    REGION_RESTRICTED_REMOTE = "REGION_RESTRICTED_REMOTE"
    UNKNOWN_REMOTE_ELIGIBILITY = "UNKNOWN_REMOTE_ELIGIBILITY"
    NOT_ELIGIBLE = "NOT_ELIGIBLE"


class JobFilter:
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        
        # Configuration preferences
        self.include_global_remote = self.config.get("include_global_remote", True)
        self.global_remote_requires_india_eligibility = self.config.get(
            "global_remote_requires_india_eligibility", True
        )
        self.allow_india_hybrid = self.config.get("allow_india_hybrid", True)
        self.allow_india_onsite = self.config.get("allow_india_onsite", True)
        self.min_relevance_score = self.config.get("min_relevance_score", 35.0)
        self.min_experience = self.config.get("min_experience", 0)
        self.max_experience = self.config.get("max_experience", 10)

        # Primary and related AI/ML Engineering Target Titles
        self.target_titles = [
            "ai engineer",
            "ai/ml engineer",
            "ai ml engineer",
            "machine learning engineer",
            "generative ai engineer",
            "genai engineer",
            "gen ai engineer",
            "applied ai engineer",
            "applied machine learning engineer",
            "applied ml engineer",
            "ai software engineer",
            "ml engineer",
            "machine learning software engineer",
            "llm engineer",
            "llm application engineer",
            "generative ai developer",
            "ai developer",
            "ai engineer - generative ai",
            "ai/ml developer",
            "artificial intelligence engineer",
            "nlp engineer",
            "machine learning platform engineer",
            "mlops engineer",
            "ml platform engineer",
            "ai platform engineer",
            "ai backend engineer",
            "genai platform engineer",
            "ai solutions engineer",
            "applied ai/ml engineer",
            "agentic ai engineer",
            "ai agent engineer",
            "ai research engineer",
            "rag engineer",
            "ai infrastructure engineer",
            "applied ai scientist",
            "ai solutions architect",
            "deep learning engineer",
            "computer vision engineer",
        ]

        # Negative / Excluded Job Titles
        self.exclude_titles = [
            "product manager",
            "program manager",
            "project manager",
            "sales",
            "marketing",
            "recruiter",
            "talent acquisition",
            "content writer",
            "copywriter",
            "account executive",
            "business development",
            "data analyst",
            "business analyst",
            "qa engineer",
            "qa lead",
            "quality assurance",
            "test engineer",
            "frontend engineer",
            "front end engineer",
            "react developer",
            "angular developer",
            "vue developer",
            "ui/ux designer",
            "graphic designer",
            "hr manager",
            "human resources",
            "scrum master",
        ]

        # Indian Cities and States
        self.india_locations = [
            "india", "bengaluru", "bangalore", "hyderabad", "chennai", "pune",
            "mumbai", "delhi", "gurugram", "gurgaon", "noida", "kolkata",
            "ahmedabad", "kochi", "cochin", "thiruvananthapuram", "trivandrum",
            "chandigarh", "jaipur", "indore", "karnataka", "telangana",
            "tamil nadu", "maharashtra", "haryana", "uttar pradesh",
            "west bengal", "gujarat", "kerala", "rajasthan", "madhya pradesh",
            "punjab"
        ]

        # Region restrictions that exclude India
        self.restricted_regions = [
            "us only", "usa only", "united states only", "u.s. only",
            "us citizens only", "us/canada", "us & canada", "canada only",
            "uk only", "united kingdom only", "eu only", "europe only",
            "north america only", "emea only", "latam only", "latin america only",
            "australia only", "germany only", "france only", "singapore only",
            "remote (us)", "remote (usa)", "remote (united states)",
            "remote - us", "remote - usa", "remote - united states",
            "remote - uk", "remote - canada", "remote - europe",
            "must be based in the us", "must reside in the us",
            "must reside in the united states", "must be located in the us",
            "us work authorization required", "authorized to work in the us",
            "canada only", "uk only", "australia only"
        ]

        # Explicit Global / Worldwide / APAC signals that include India
        self.global_eligible_signals = [
            "worldwide", "global remote", "remote - worldwide", "remote worldwide",
            "remote - anywhere", "remote anywhere", "remote - international",
            "international remote", "work from anywhere", "anywhere in the world",
            "open worldwide", "hire anywhere", "remote - apac", "remote apac",
            "remote - asia", "remote asia", "remote - asia-pacific",
            "all countries", "any country", "including india", "open to india",
            "india eligible", "remote across multiple countries including india",
            "remote - india"
        ]

    def classify_location(self, location_text: str, description_text: str = "", workplace_type: str = "") -> Tuple[str, bool, List[str]]:
        """
        Classifies location and remote eligibility for candidate in India.
        Returns: (category, is_eligible, reasons)
        """
        combined_text = f"{location_text} {workplace_type} {description_text}".lower()
        loc_lower = location_text.lower()
        workplace_lower = workplace_type.lower()
        reasons = []

        is_remote = any(r in combined_text for r in ["remote", "work from home", "wfh", "telecommute", "distributed"]) or "remote" in workplace_lower
        is_hybrid = "hybrid" in combined_text or "hybrid" in workplace_lower
        is_onsite = "on-site" in combined_text or "onsite" in combined_text or "on site" in workplace_lower

        # 1. Check if explicitly in India
        has_india_location = any(re.search(r'\b' + re.escape(city) + r'\b', loc_lower) for city in self.india_locations) or \
                             any(re.search(r'\b' + re.escape(city) + r'\b', combined_text[:300]) for city in self.india_locations)

        # 2. Check for explicit Restricted Remote Regions (e.g. US only, Canada only)
        is_region_restricted = False
        matched_restriction = ""
        for restriction in self.restricted_regions:
            if re.search(r'\b' + re.escape(restriction) + r'\b', combined_text):
                is_region_restricted = True
                matched_restriction = restriction
                break

        # Check for specific "US only" or "Canada only" in location field
        if not is_region_restricted:
            if any(term in loc_lower for term in ["united states", "usa", "us", "canada", "united kingdom", "uk", "germany", "australia"]) and not has_india_location:
                if is_remote and ("us only" in combined_text or "united states" in loc_lower or "canada" in loc_lower or "uk" in loc_lower):
                    is_region_restricted = True
                    matched_restriction = loc_lower

        # 3. Check for explicit Global / Worldwide / APAC signals
        has_global_eligible_signal = False
        matched_signal = ""
        for signal in self.global_eligible_signals:
            if re.search(r'\b' + re.escape(signal) + r'\b', combined_text):
                has_global_eligible_signal = True
                matched_signal = signal
                break

        # Decision Matrix

        # A. Region Restricted Remote (Disqualified for India candidate)
        if is_region_restricted and not (has_india_location or "including india" in combined_text or "india eligible" in combined_text):
            reasons.append(f"Remote role is restricted to other geography: '{matched_restriction}'")
            return LocationCategory.REGION_RESTRICTED_REMOTE, False, reasons

        # B. Global Remote with explicit Worldwide / APAC / International / India eligibility
        if is_remote and has_global_eligible_signal and any(g in combined_text for g in ["worldwide", "global", "anywhere", "international", "apac", "asia", "all countries", "india eligible", "including india"]):
            reasons.append(f"Global Remote role with India/Worldwide eligibility signal: '{matched_signal}'")
            return LocationCategory.GLOBAL_REMOTE_INDIA_ELIGIBLE, self.include_global_remote, reasons

        # C. India Remote
        if has_india_location and is_remote:
            reasons.append("India-based Remote role")
            return LocationCategory.INDIA_REMOTE, True, reasons

        # D. India Hybrid
        if has_india_location and is_hybrid:
            reasons.append("India-based Hybrid role")
            return LocationCategory.INDIA_HYBRID, self.allow_india_hybrid, reasons

        # E. India On-site
        if has_india_location:
            reasons.append("India-based On-site role")
            return LocationCategory.INDIA_ONSITE, self.allow_india_onsite, reasons

        # F. Ambiguous Remote with no geographic scope specified
        if is_remote and not has_india_location:
            reasons.append("Remote role with unspecified geographic eligibility (requires manual verification)")
            if self.global_remote_requires_india_eligibility:
                return LocationCategory.UNKNOWN_REMOTE_ELIGIBILITY, False, reasons
            else:
                return LocationCategory.UNKNOWN_REMOTE_ELIGIBILITY, True, reasons

        # G. Non-India On-site / Other
        reasons.append(f"Role location outside India ({location_text})")
        return LocationCategory.NOT_ELIGIBLE, False, reasons

    def evaluate_title(self, title: str) -> Tuple[bool, float, List[str]]:
        """
        Evaluates job title for AI/ML engineering relevance and exclusions.
        Returns: (is_acceptable, title_score_boost, reasons)
        """
        title_lower = title.lower().strip()
        reasons = []

        # 1. Negative title check
        for excluded in self.exclude_titles:
            # Check for excluded roles (e.g. "Product Manager", "Data Analyst")
            if re.search(r'\b' + re.escape(excluded) + r'\b', title_lower):
                # Verify if title explicitly says "AI Engineer" or "ML Engineer" alongside
                if not any(eng in title_lower for eng in ["ai engineer", "ml engineer", "machine learning engineer"]):
                    reasons.append(f"Title matches excluded non-engineering role: '{excluded}'")
                    return False, 0.0, reasons

        # 2. Check for strong AI/ML engineering titles
        for target in self.target_titles:
            if re.search(r'\b' + re.escape(target) + r'\b', title_lower):
                reasons.append(f"Title strongly matches target AI/ML role: '{target}'")
                return True, 40.0, reasons

        # 3. Check for general AI/ML keywords in engineering title
        ai_keywords = ["ai", "ml", "genai", "generative ai", "llm", "machine learning", "deep learning", "nlp", "rag", "agentic"]
        eng_keywords = ["engineer", "developer", "architect", "scientist", "specialist"]

        has_ai = any(re.search(r'\b' + re.escape(k) + r'\b', title_lower) for k in ai_keywords)
        has_eng = any(re.search(r'\b' + re.escape(k) + r'\b', title_lower) for k in eng_keywords)

        if has_ai and has_eng:
            reasons.append("Title contains AI/ML and engineering keywords")
            return True, 30.0, reasons

        reasons.append("Title does not explicitly match AI/ML engineering pattern (evaluating description)")
        return True, 10.0, reasons

    def calculate_relevance_score(self, title: str, description: str) -> Tuple[float, List[str]]:
        """
        Calculates a technical AI/ML engineering relevance score (0 - 100).
        Evaluates skills, keywords, combinations, and verifies engineering intent.
        """
        text = f"{title} {description}".lower()
        score = 0.0
        reasons = []

        # 1. Title Evaluation
        is_title_ok, title_boost, title_reasons = self.evaluate_title(title)
        score += title_boost
        reasons.extend(title_reasons)

        if not is_title_ok:
            return 0.0, reasons

        # 2. GenAI & LLM Core (up to 20 pts)
        genai_keywords = [
            "generative ai", "genai", "gen ai", "llm", "large language models",
            "large language model", "prompt engineering", "fine-tuning", "foundation models",
            "openai", "anthropic", "claude", "gemini", "llama", "mistral", "deepseek"
        ]
        matched_genai = [k for k in genai_keywords if re.search(r'\b' + re.escape(k) + r'\b', text)]
        if matched_genai:
            pts = min(20.0, len(matched_genai) * 5.0)
            score += pts
            reasons.append(f"GenAI/LLM keywords ({pts:.0f} pts): {', '.join(matched_genai[:4])}")

        # 3. RAG & Vector Search (up to 15 pts)
        rag_keywords = [
            "rag", "retrieval augmented generation", "retrieval-augmented generation",
            "vector database", "vector store", "vector search", "embeddings",
            "pinecone", "weaviate", "qdrant", "milvus", "chromadb", "chroma",
            "pgvector", "faiss", "semantic search", "reranking"
        ]
        matched_rag = [k for k in rag_keywords if re.search(r'\b' + re.escape(k) + r'\b', text)]
        if matched_rag:
            pts = min(15.0, len(matched_rag) * 5.0)
            score += pts
            reasons.append(f"RAG & Vector Search ({pts:.0f} pts): {', '.join(matched_rag[:3])}")

        # 4. Agentic AI & Frameworks (up to 15 pts)
        agentic_keywords = [
            "agentic ai", "agentic", "ai agent", "ai agents", "multi-agent",
            "langchain", "langgraph", "llamaindex", "crewai", "autogen",
            "mcp", "model context protocol", "function calling", "tool use",
            "ai orchestration"
        ]
        matched_agentic = [k for k in agentic_keywords if re.search(r'\b' + re.escape(k) + r'\b', text)]
        if matched_agentic:
            pts = min(15.0, len(matched_agentic) * 5.0)
            score += pts
            reasons.append(f"Agentic AI & Frameworks ({pts:.0f} pts): {', '.join(matched_agentic[:3])}")

        # 5. Core ML / NLP / CV / Deep Learning (up to 10 pts)
        ml_keywords = [
            "machine learning", "deep learning", "nlp", "natural language processing",
            "transformers", "hugging face", "pytorch", "tensorflow", "scikit-learn"
        ]
        matched_ml = [k for k in ml_keywords if re.search(r'\b' + re.escape(k) + r'\b', text)]
        if matched_ml:
            pts = min(10.0, len(matched_ml) * 3.0)
            score += pts
            reasons.append(f"Core ML/NLP ({pts:.0f} pts): {', '.join(matched_ml[:3])}")

        # 6. MLOps & Production Engineering (up to 10 pts)
        mlops_keywords = [
            "mlops", "mlflow", "model deployment", "model serving", "ai inference",
            "vllm", "triton", "llm evaluation", "ragas", "evals", "langsmith"
        ]
        matched_mlops = [k for k in mlops_keywords if re.search(r'\b' + re.escape(k) + r'\b', text)]
        if matched_mlops:
            pts = min(10.0, len(matched_mlops) * 3.5)
            score += pts
            reasons.append(f"MLOps & Serving ({pts:.0f} pts): {', '.join(matched_mlops[:3])}")

        # 7. Cloud, Backend & Python (up to 10 pts)
        backend_keywords = ["python", "fastapi", "docker", "kubernetes", "aws", "bedrock", "azure openai", "vertex ai"]
        matched_backend = [k for k in backend_keywords if re.search(r'\b' + re.escape(k) + r'\b', text)]
        if matched_backend:
            pts = min(10.0, len(matched_backend) * 2.5)
            score += pts
            reasons.append(f"Backend & Cloud ({pts:.0f} pts): {', '.join(matched_backend[:3])}")

        # 8. Synergistic Combination Bonuses (+5 each, up to +15 pts)
        combos = [
            ("python", ["llm", "rag", "genai", "generative ai", "langgraph", "langchain", "mlops"], "Python + GenAI/LLM/RAG"),
            ("aws", ["bedrock", "genai", "llm"], "AWS + Bedrock/LLM"),
            ("llm", ["rag", "agentic ai", "langgraph"], "LLM + RAG/Agentic"),
            ("langchain", ["langgraph", "agentic ai"], "LangChain + LangGraph Agentic"),
        ]
        combo_bonus = 0.0
        for primary, secondaries, label in combos:
            if primary in text and any(s in text for s in secondaries):
                combo_bonus += 5.0
                reasons.append(f"Synergy Bonus (+5 pts): {label}")
                if combo_bonus >= 15.0:
                    break
        score += combo_bonus

        # 9. Engineering Intent & False Positive Protection
        engineering_actions = [
            "build", "design", "develop", "implement", "deploy", "architect",
            "train", "fine-tune", "evaluate", "engineer", "productionize",
            "optimize", "integrate", "scale", "code", "programming"
        ]
        has_eng_action = any(re.search(r'\b' + re.escape(a) + r'\b', text) for a in engineering_actions)
        if not has_eng_action:
            reasons.append("Warning: Lack of active engineering responsibilities in text (-15 pts)")
            score = max(0.0, score - 15.0)

        # Cap score between 0 and 100
        final_score = min(100.0, max(0.0, score))
        return final_score, reasons

    def evaluate_job(
        self,
        title: str,
        location_text: str,
        description_text: str = "",
        workplace_type: str = ""
    ) -> Dict[str, Any]:
        """
        Complete end-to-end evaluation of a job posting.
        Returns evaluation dict with eligibility, score, classification, and audit reasons.
        """
        # 1. Location Classification
        loc_category, loc_eligible, loc_reasons = self.classify_location(
            location_text, description_text, workplace_type
        )

        # 2. Relevance Scoring
        relevance_score, match_reasons = self.calculate_relevance_score(title, description_text)

        # 3. Overall Eligibility
        is_score_ok = relevance_score >= self.min_relevance_score
        is_eligible = loc_eligible and is_score_ok

        # Location priority sorting weight
        priority_weight = 0
        if loc_category == LocationCategory.INDIA_REMOTE:
            priority_weight = 100
        elif loc_category == LocationCategory.GLOBAL_REMOTE_INDIA_ELIGIBLE:
            priority_weight = 90
        elif loc_category == LocationCategory.INDIA_HYBRID:
            priority_weight = 70
        elif loc_category == LocationCategory.INDIA_ONSITE:
            priority_weight = 50
        else:
            priority_weight = 0

        total_rank_score = relevance_score + priority_weight

        all_reasons = loc_reasons + match_reasons

        return {
            "is_eligible": is_eligible,
            "relevance_score": round(relevance_score, 1),
            "total_rank_score": round(total_rank_score, 1),
            "location_category": loc_category,
            "location_eligible": loc_eligible,
            "title_eligible": is_score_ok,
            "reasons": all_reasons,
            "raw_location": location_text,
            "workplace_type": workplace_type,
        }
