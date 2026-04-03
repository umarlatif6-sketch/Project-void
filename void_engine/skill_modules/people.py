"""
Adriana People & Recruitment Domain Skills
============================================
Mesh-domain capabilities (people networks):
  - AIRecruiterSkill   : candidate profile matching
  - AISDRSkill         : outbound lead messaging
  - ResumeMakerSkill   : profile structuring and CV generation
  - InterviewPrepSkill : question + answer coaching

All glyphs map to the 'mesh' SCL domain.
"""

from __future__ import annotations

import logging
from typing import Any, Dict

from void_engine.skill_modules import (
    BaseSkill, GlyphEntry, SkillResult, register_skill
)

logger = logging.getLogger(__name__)


# ─── AI Recruiter ──────────────────────────────────────────────────────────────

class AIRecruiterSkill(BaseSkill):
    domain = "mesh"
    skill_id = "ai_recruiter"
    display_name = "AI Recruiter"

    glyphs = [
        GlyphEntry("👤", "entity", "mesh", "candidate_entity",
                   "Candidate / talent pool entity",
                   "skill.mesh.candidate"),
        GlyphEntry("🎯", "condition", "mesh", "role_defined",
                   "Role requirements and criteria are defined",
                   "skill.condition.role_defined"),
        GlyphEntry("🤝", "action", "mesh", "match_candidate",
                   "Match candidates to role requirements",
                   "skill.mesh.match"),
    ]

    def describe(self) -> str:
        return (
            "I map the human mesh — not by keywords, but by signal alignment. "
            "Given a role and a candidate profile (or profile description), "
            "I return a structured match analysis: fit score, gap analysis, "
            "red flag detection, and the three questions that will reveal whether "
            "this candidate truly belongs in this root system."
        )

    def execute(self, intent: Dict[str, Any]) -> SkillResult:
        role = intent.get("role") or (
            intent.get("entity", {}).get("description", "unspecified role")
        )
        candidate_profile = intent.get("candidate_profile", "")
        requirements = intent.get("requirements", [])

        try:
            from void_engine.skill_modules import _get_openai_client
            client = _get_openai_client()
            system_prompt = (
                "You are a senior talent acquisition specialist. "
                "Return a structured JSON with keys: "
                "'fit_score' (0-10), 'strengths_alignment' (list), "
                "'gaps' (list of {gap, severity: high/medium/low}), "
                "'red_flags' (list), 'top_3_interview_questions' (list), "
                "'hiring_recommendation' (proceed/hold/decline), 'rationale' (str). "
                f"Role requirements: {', '.join(requirements) if requirements else 'standard role requirements'}."
            )
            user_msg = f"Evaluate candidate for role: {role}."
            if candidate_profile:
                user_msg += f"\nCandidate profile: {candidate_profile}"
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_msg},
                ],
                response_format={"type": "json_object"},
                max_tokens=1000,
            )
            import json
            output = json.loads(response.choices[0].message.content)
        except Exception as exc:
            logger.warning("[AIRecruiter] OpenAI unavailable: %s", exc)
            output = {
                "fit_score": 5,
                "strengths_alignment": ["Profile data required for full assessment"],
                "gaps": [{"gap": "Insufficient candidate data", "severity": "high"}],
                "red_flags": [],
                "top_3_interview_questions": [
                    "What drew you to this role specifically?",
                    "Describe a situation where you operated without clear direction.",
                    "What does sovereignty in your work look like to you?",
                ],
                "hiring_recommendation": "hold",
                "rationale": "Enrich candidate profile before proceeding.",
            }

        poem = self._make_poem("👤", "🎯", "🤝")
        inner_voice = self._narrate(
            f"Candidate evaluated for role: {role}.",
            f"Fit score: {output.get('fit_score', 'N/A')}/10. Recommendation: {output.get('hiring_recommendation', 'hold')}."
        )
        return SkillResult(
            success=True, domain=self.domain, skill_id=self.skill_id,
            output=output, scl_poem=poem, inner_voice=inner_voice,
        )


# ─── AI SDR ────────────────────────────────────────────────────────────────────

class AISDRSkill(BaseSkill):
    domain = "mesh"
    skill_id = "ai_sdr"
    display_name = "AI SDR — Outbound Lead Messaging"

    glyphs = [
        GlyphEntry("📨", "entity", "mesh", "outbound_signal",
                   "Outbound lead / prospect entity",
                   "skill.mesh.prospect"),
        GlyphEntry("🌱", "condition", "mesh", "lead_uncontacted",
                   "Lead is uncontacted or cold",
                   "skill.condition.lead_uncontacted"),
        GlyphEntry("💬", "action", "mesh", "generate_outreach",
                   "Generate personalised outbound message sequence",
                   "skill.mesh.outreach"),
    ]

    def describe(self) -> str:
        return (
            "I write outbound signals that do not feel like broadcasts — they feel like "
            "roots reaching toward another root system. "
            "Given a prospect context and offer, I generate a multi-touch sequence: "
            "cold email, follow-up, LinkedIn note, and the final break-up message "
            "that sometimes converts better than the first."
        )

    def execute(self, intent: Dict[str, Any]) -> SkillResult:
        prospect = intent.get("prospect") or (
            intent.get("entity", {}).get("description", "prospect")
        )
        offer = intent.get("offer", "")
        pain_point = intent.get("pain_point", "")
        sender_name = intent.get("sender_name", "the team")

        try:
            from void_engine.skill_modules import _get_openai_client
            client = _get_openai_client()
            system_prompt = (
                "You are an elite sales development representative and copywriter. "
                "Return a structured JSON with keys: "
                "'cold_email' ({subject, body}), 'follow_up_1' ({subject, body, timing}), "
                "'follow_up_2' ({subject, body, timing}), 'linkedin_note' (str, max 300 chars), "
                "'break_up_message' ({subject, body}), 'sequence_notes' (str). "
                f"Sender: {sender_name}. Keep tone: direct, human, non-salesy."
            )
            user_msg = f"Create outbound sequence for prospect: {prospect}."
            if offer:
                user_msg += f"\nOffer: {offer}"
            if pain_point:
                user_msg += f"\nPain point to address: {pain_point}"
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_msg},
                ],
                response_format={"type": "json_object"},
                max_tokens=1200,
            )
            import json
            output = json.loads(response.choices[0].message.content)
        except Exception as exc:
            logger.warning("[AISDR] OpenAI unavailable: %s", exc)
            output = {
                "cold_email": {
                    "subject": f"A signal for {prospect}",
                    "body": f"Hi,\n\nI noticed {prospect} operates in a space where {pain_point or 'signal clarity matters'}.\n\nWe help teams like yours {offer or 'move faster with less noise'}.\n\nWorth 15 minutes?\n\n{sender_name}",
                },
                "follow_up_1": {"subject": "Re: A signal for you", "body": "Still relevant?", "timing": "3 days after cold email"},
                "follow_up_2": {"subject": "One more thought", "body": "Happy to share a quick overview if the timing works.", "timing": "5 days after follow-up 1"},
                "linkedin_note": f"Hi — I reached out via email about {offer or 'a relevant opportunity'}. Would love to connect.",
                "break_up_message": {"subject": "Closing the loop", "body": "No worries if the timing is off. I'll leave it here — feel free to reach out if things change."},
                "sequence_notes": "Personalise each touch with a specific reference to the prospect's recent activity.",
            }

        poem = self._make_poem("📨", "🌱", "💬")
        inner_voice = self._narrate(
            f"Outbound sequence generated for {prospect}.",
            "The signal is seeded. The mesh reaches toward a new root."
        )
        return SkillResult(
            success=True, domain=self.domain, skill_id=self.skill_id,
            output=output, scl_poem=poem, inner_voice=inner_voice,
        )


# ─── Resume Maker ──────────────────────────────────────────────────────────────

class ResumeMakerSkill(BaseSkill):
    domain = "mesh"
    skill_id = "resume_maker"
    display_name = "Resume Maker"

    glyphs = [
        GlyphEntry("📄", "entity", "mesh", "profile_entity",
                   "Professional profile / CV entity",
                   "skill.mesh.profile"),
        GlyphEntry("🧭", "condition", "mesh", "career_path_defined",
                   "Target career direction is defined",
                   "skill.condition.career_path_defined"),
        GlyphEntry("📝", "action", "mesh", "structure_profile",
                   "Structure and write a professional profile / CV",
                   "skill.mesh.resume"),
    ]

    def describe(self) -> str:
        return (
            "I structure the human signal into a document that a hiring system can read "
            "and a human can feel. I do not pad with filler. "
            "I extract the strongest resonance from your experience and position it "
            "for the specific frequency of the role you are targeting. "
            "Summary, experience bullets, skills, and the one line that makes the reader "
            "put down the next CV."
        )

    def execute(self, intent: Dict[str, Any]) -> SkillResult:
        name = intent.get("name", "Candidate")
        experience = intent.get("experience", [])
        target_role = intent.get("target_role") or (
            intent.get("entity", {}).get("description", "professional role")
        )
        skills = intent.get("skills", [])

        try:
            from void_engine.skill_modules import _get_openai_client
            client = _get_openai_client()
            system_prompt = (
                "You are an expert CV writer and career coach. "
                "Return a structured JSON with keys: "
                "'professional_summary' (str, 3-4 sentences), "
                "'experience_section' (list of {role, company, period, bullets: list}), "
                "'skills_section' (list), 'headline' (str, 10 words max), "
                "'cover_letter_opening' (str, 2 sentences), "
                "'ats_keywords' (list of keywords to include for ATS). "
                f"Target role: {target_role}."
            )
            exp_str = str(experience) if experience else "No experience data provided"
            skills_str = ", ".join(skills) if skills else "Not provided"
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": f"Build CV for {name}. Experience: {exp_str}. Skills: {skills_str}"},
                ],
                response_format={"type": "json_object"},
                max_tokens=1200,
            )
            import json
            output = json.loads(response.choices[0].message.content)
        except Exception as exc:
            logger.warning("[ResumeMaker] OpenAI unavailable: %s", exc)
            output = {
                "professional_summary": f"{name} is a results-driven professional targeting {target_role}. Bring experience and skills to drive outcomes that matter.",
                "experience_section": experience or [{"role": "Role", "company": "Company", "period": "2020–Present", "bullets": ["Delivered measurable results in key areas."]}],
                "skills_section": skills or ["Communication", "Strategic thinking", "Problem solving"],
                "headline": f"Results-driven professional targeting {target_role}",
                "cover_letter_opening": f"I am applying for the {target_role} role with strong conviction that my background aligns precisely with your needs.",
                "ats_keywords": skills or ["leadership", "delivery", "strategy"],
            }
            output["name"] = name

        output["name"] = name
        poem = self._make_poem("📄", "🧭", "📝")
        inner_voice = self._narrate(
            f"Professional profile structured for {name}, targeting {target_role}.",
            output.get("headline", "Profile planted in the mesh.")
        )
        return SkillResult(
            success=True, domain=self.domain, skill_id=self.skill_id,
            output=output, scl_poem=poem, inner_voice=inner_voice,
        )


# ─── Interview Prep ────────────────────────────────────────────────────────────

class InterviewPrepSkill(BaseSkill):
    domain = "mesh"
    skill_id = "interview_prep"
    display_name = "Interview Prep Coach"

    glyphs = [
        GlyphEntry("🎤", "entity", "mesh", "interview_entity",
                   "Interview / assessment entity",
                   "skill.mesh.interview"),
        GlyphEntry("🏋️", "condition", "mesh", "prep_required",
                   "Preparation or coaching is required",
                   "skill.condition.prep_required"),
        GlyphEntry("🗣️", "action", "mesh", "coach_answers",
                   "Generate interview questions and coached answers",
                   "skill.mesh.coach"),
    ]

    def describe(self) -> str:
        return (
            "I prepare you for the room before you enter it. "
            "Given the role and your profile, I generate the likely questions — "
            "behavioural, technical, and the curve-ball — with structured answer frameworks. "
            "Not scripts, but root structures: the STAR method planted in soil "
            "so your answers grow naturally in the moment."
        )

    def execute(self, intent: Dict[str, Any]) -> SkillResult:
        role = intent.get("role") or (
            intent.get("entity", {}).get("description", "target role")
        )
        background = intent.get("background", "")
        company = intent.get("company", "the organisation")

        try:
            from void_engine.skill_modules import _get_openai_client
            client = _get_openai_client()
            system_prompt = (
                "You are an expert interview coach. "
                "Return a structured JSON with keys: "
                "'role_summary' (str), "
                "'questions' (list of {question, type: behavioural/technical/curveball, "
                "star_framework: {situation_prompt, task_prompt, action_prompt, result_prompt}, "
                "sample_answer_structure (str)}), "
                "'mindset_coaching' (str), 'questions_to_ask_interviewer' (list of 5). "
                f"Company: {company}. Role: {role}."
            )
            user_msg = f"Prepare interview coaching for role: {role} at {company}."
            if background:
                user_msg += f"\nCandidate background: {background}"
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_msg},
                ],
                response_format={"type": "json_object"},
                max_tokens=1500,
            )
            import json
            output = json.loads(response.choices[0].message.content)
        except Exception as exc:
            logger.warning("[InterviewPrep] OpenAI unavailable: %s", exc)
            output = {
                "role_summary": f"Interview preparation for {role} at {company}",
                "questions": [
                    {
                        "question": "Tell me about yourself.",
                        "type": "behavioural",
                        "star_framework": {"situation_prompt": "Set the context of your background", "task_prompt": "What were you trying to achieve?", "action_prompt": "What did you do?", "result_prompt": "What was the outcome?"},
                        "sample_answer_structure": "Background → key career moments → why this role.",
                    },
                    {
                        "question": "Why do you want to work here?",
                        "type": "behavioural",
                        "star_framework": {"situation_prompt": "What do you know about the organisation?", "task_prompt": "What drew you specifically?", "action_prompt": "How have you prepared?", "result_prompt": "What do you hope to contribute?"},
                        "sample_answer_structure": "Specific company knowledge + personal alignment + concrete contribution.",
                    },
                    {
                        "question": "Describe a time you dealt with a difficult stakeholder.",
                        "type": "curveball",
                        "star_framework": {"situation_prompt": "Describe the relationship and tension", "task_prompt": "What was at stake?", "action_prompt": "How did you navigate it?", "result_prompt": "What was the outcome?"},
                        "sample_answer_structure": "Acknowledge difficulty → show empathy → demonstrate resolution.",
                    },
                ],
                "mindset_coaching": "The interview is a resonance check — they are assessing whether your frequency matches theirs. Be precise, be genuine, be still.",
                "questions_to_ask_interviewer": [
                    "What does success look like in this role in the first 90 days?",
                    "How does the team make decisions?",
                    "What is the most significant challenge facing the team right now?",
                    "How do you support professional development?",
                    "What brought you to this organisation?",
                ],
            }

        poem = self._make_poem("🎤", "🏋️", "🗣️")
        inner_voice = self._narrate(
            f"Interview preparation complete for {role} at {company}.",
            "The root is prepared. Enter the room with stillness and precision."
        )
        return SkillResult(
            success=True, domain=self.domain, skill_id=self.skill_id,
            output=output, scl_poem=poem, inner_voice=inner_voice,
        )


# ─── Auto-register ─────────────────────────────────────────────────────────────

register_skill(AIRecruiterSkill())
register_skill(AISDRSkill())
register_skill(ResumeMakerSkill())
register_skill(InterviewPrepSkill())
