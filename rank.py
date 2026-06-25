import json
import gzip
import csv


# =========================
# LOAD DATA
# =========================
def load_candidates(path):
    candidates = []

    if path.endswith(".gz"):
        f = gzip.open(path, "rt", encoding="utf-8")
    else:
        f = open(path, "r", encoding="utf-8")

    for line in f:
        if line.strip():
            candidates.append(json.loads(line))

    f.close()
    return candidates


# =========================
# CORE SCORING ENGINE (V3)
# =========================
def score_candidate(c):
    profile = c.get("profile", {})
    signals = c.get("redrob_signals", {})
    skills = c.get("skills", [])

    score = 0.0

    # -------------------------
    # 1. EXPERIENCE FIT (JD-aware sweet spot 5–9 yrs)
    # -------------------------
    years = profile.get("years_of_experience", 0)

    if 5 <= years <= 9:
        score += 35
    else:
        score += max(0, 20 - abs(years - 7) * 2)

    # -------------------------
    # 2. TITLE QUALITY BOOST (VERY IMPORTANT FOR JD MATCH)
    # -------------------------
    title = profile.get("current_title", "").lower()

    if any(k in title for k in ["machine learning", "ai", "data scientist", "ml engineer"]):
        score += 25
    elif any(k in title for k in ["software engineer", "backend", "engineer"]):
        score += 10
    else:
        score -= 10

    # -------------------------
    # 3. SKILL MATCHING (LIGHTWEIGHT SEMANTIC SIMULATION)
    # -------------------------
    jd_keywords = {
        "python", "nlp", "embeddings", "retrieval", "ranking", "rag",
        "llm", "fine-tuning", "lora", "qlora",
        "vector", "pinecone", "weaviate", "qdrant", "milvus",
        "elasticsearch", "opensearch", "faiss",
        "machine learning", "recommendation"
    }

    candidate_skills = {
        s.get("name", "").lower() for s in skills if s.get("name")
    }

    match_count = len(jd_keywords.intersection(candidate_skills))
    score += match_count * 5

    # -------------------------
    # 4. BEHAVIORAL SIGNALS (VERY IMPORTANT)
    # -------------------------
    score += signals.get("recruiter_response_rate", 0) * 25
    score += signals.get("interview_completion_rate", 0) * 20
    score += signals.get("offer_acceptance_rate", 0) * 15

    # profile completeness
    score += min(signals.get("profile_completeness_score", 0), 100) / 8

    # activity
    score += min(signals.get("search_appearance_30d", 0), 500) / 60

    # -------------------------
    # 5. JOB READINESS SIGNALS
    # -------------------------
    if signals.get("open_to_work_flag"):
        score += 12

    notice = signals.get("notice_period_days", 180)
    if notice <= 30:
        score += 10
    elif notice <= 60:
        score += 6
    elif notice <= 90:
        score += 2
    else:
        score -= 6

    # relocation
    if signals.get("willing_to_relocate"):
        score += 4

    # verification
    if signals.get("verified_email"):
        score += 3
    if signals.get("verified_phone"):
        score += 3

    # github activity
    gh = signals.get("github_activity_score", -1)
    if gh > 0:
        score += gh / 12

    # -------------------------
    # 6. HONEYPOT PROTECTION (CRITICAL)
    # -------------------------
    if years > 0 and len(skills) > 12:
        invalid = 0
        for s in skills:
            if s.get("duration_months", 0) <= 0:
                invalid += 1

        if invalid >= 5:
            score -= 25

    # -------------------------
    # 7. FINAL NORMALIZATION (STABILITY)
    # -------------------------
    return round(score, 6)


# =========================
# REASONING ENGINE (NO HALLUCINATION)
# =========================
def generate_reasoning(c):
    profile = c.get("profile", {})
    signals = c.get("redrob_signals", {})
    skills = c.get("skills", [])

    years = profile.get("years_of_experience", 0)
    title = profile.get("current_title", "Professional")

    skill_names = [
        s.get("name", "")
        for s in skills[:3]
        if s.get("name")
    ]

    skill_text = ", ".join(skill_names)

    response = signals.get("recruiter_response_rate", 0)
    notice = signals.get("notice_period_days", 0)

    text = f"{years:.1f} yrs as {title}"

    if skill_text:
        text += f"; skills include {skill_text}."

    # behavioral interpretation
    if response >= 0.7:
        text += " Highly responsive candidate."
    elif response >= 0.4:
        text += " Moderately responsive candidate."
    else:
        text += " Low recruiter responsiveness."

    # availability signal
    if notice <= 30:
        text += " Immediate availability."
    elif notice <= 60:
        text += " Short notice period."
    else:
        text += " Standard notice period."

    return text


# =========================
# MAIN PIPELINE
# =========================
def main():
    input_path = "candidates.jsonl"
    output_path = "submission.csv"

    candidates = load_candidates(input_path)

    scored = []

    for c in candidates:
        s = score_candidate(c)
        scored.append((s, c["candidate_id"], c))

    # -------------------------
    # STRICT SORT (VERY IMPORTANT)
    # -------------------------
    scored.sort(key=lambda x: (-x[0], x[1]))

    top_100 = scored[:100]

    with open(output_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)

        writer.writerow(["candidate_id", "rank", "score", "reasoning"])

        for i, (score, cid, c) in enumerate(top_100, start=1):

            reasoning = generate_reasoning(c)

            # tie-safe deterministic scoring
            final_score = round(score - (i * 1e-6), 6)

            writer.writerow([cid, i, final_score, reasoning])

    print("Done → submission.csv generated")


if __name__ == "__main__":
    main()