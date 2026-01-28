import os
import re
from typing import List, Tuple

import httpx


OPENAI_API_URL = "https://api.openai.com/v1/chat/completions"
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "o4-mini")


class AIServiceError(Exception):
    pass


def _build_prompt(
    country_name: str,
    residency_status: str,
    topic_lines: List[str],
    recipient_lines: List[str],
    user_name: str = None,
) -> Tuple[str, str]:
    
    sender_intro = f"from {user_name}" if user_name else "from a concerned individual"
    
    system_prompt = (
        "You are an expert at writing compelling, authentic advocacy emails in English. "
        "Your emails sound genuinely human — passionate but professional, urgent but respectful.\n\n"
        "CRITICAL REQUIREMENTS:\n"
        "- Write ONLY in English (never Farsi/Persian)\n"
        "- Make it sound authentic and personal, not template-like\n"
        "- Vary sentence structure and word choice\n"
        "- Use emotional appeal while maintaining credibility\n"
        "- Include specific details about Iran's human rights crisis\n"
        "- Reference current events (2026 protests, Woman Life Freedom movement)\n\n"
        "TONE: Urgent, compassionate, informed citizen\n"
        "LENGTH: 250-350 words\n"
        "STYLE: Personal letter to official (not a formal petition)"
    )

    citizenship_context = "I am a resident and voter in your country" if residency_status == "Resident" else "I am an international observer deeply concerned about this issue"
    
    user_prompt = (
        f"Write a personal advocacy email {sender_intro} to officials in {country_name} "
        "about Iran's human rights crisis.\n\n"
        f"Sender context: {citizenship_context}\n\n"
        "Key topics to address:\n"
        f"{chr(10).join(topic_lines)}\n\n"
        "Recipients:\n"
        f"{chr(10).join(recipient_lines)}\n\n"
        "REQUIREMENTS:\n"
        "1. Start with a personal greeting\n"
        "2. Explain why you're writing (personal connection to issue)\n"
        "3. Present 2-3 specific human rights violations from the topics\n"
        "4. Include emotional but factual appeals\n"
        "5. Make 2-3 concrete action requests\n"
        "6. Close with urgency but respect\n"
        f"7. Sign as '{user_name if user_name else 'A Concerned Citizen'}'\n\n"
        "Output format:\n"
        "SUBJECT: [compelling subject under 60 chars]\n\n"
        "BODY:\n"
        "[email body in English — sound human, vary language, be specific]"
    )

    return system_prompt, user_prompt


def _parse_subject_body(text: str) -> Tuple[str, str]:
    match = re.search(r"(?is)subject:\s*(.*?)\n\s*body:\s*(.*)", text)
    if match:
        subject = match.group(1).strip().strip('"')
        body = match.group(2).strip()
        return subject, body

    lines = [line.strip() for line in text.splitlines() if line.strip()]
    if not lines:
        return "Urgent: Action Needed on Iran Human Rights Crisis", ""

    subject = lines[0][:60]
    body = "\n".join(lines[1:]) if len(lines) > 1 else ""
    return subject, body


async def generate_email(
    country_name: str,
    recipients: List[dict],
    topics: List[dict],
    is_resident: bool,
    user_name: str = None,
) -> Tuple[str, str, int]:
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise AIServiceError("OPENAI_API_KEY is not configured")

    residency_status = "Resident" if is_resident else "International Supporter"
    topic_lines = [f"- {t['display_title']}: {t.get('description') or 'Critical human rights concern'}" for t in topics]
    recipient_lines = [f"- {r['full_name']} ({r['display_title']})" for r in recipients]

    system_prompt, user_prompt = _build_prompt(
        country_name=country_name,
        residency_status=residency_status,
        topic_lines=topic_lines,
        recipient_lines=recipient_lines,
        user_name=user_name,
    )

    payload = {
        "model": OPENAI_MODEL,
        "messages": [
            {"role": "developer", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        "temperature": 0.9,  # Higher for more variation
        "max_completion_tokens": 800,
    }

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }

    async with httpx.AsyncClient(timeout=60.0) as client:
        response = await client.post(OPENAI_API_URL, headers=headers, json=payload)

    if response.status_code >= 400:
        raise AIServiceError(f"OpenAI API error: {response.status_code} {response.text}")

    data = response.json()
    content = data.get("choices", [{}])[0].get("message", {}).get("content", "")
    subject, body = _parse_subject_body(content)

    if len(subject) > 60:
        subject = subject[:60].rstrip()

    usage = data.get("usage", {})
    total_tokens = usage.get("total_tokens", 0)

    return subject, body, total_tokens
