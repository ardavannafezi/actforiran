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
) -> Tuple[str, str]:
    system_prompt = (
        "You are writing a personal advocacy email to senior officials in "
        f"{country_name} regarding human rights violations in Iran.\n\n"
        "Tone: Urgent but respectful, personal but informed\n"
        "Length: 200-300 words\n"
        "Format: Professional email\n\n"
        "Avoid:\n"
        "- Generic template language\n"
        "- Overly formal bureaucratic language\n"
        "- Repetitive phrases\n\n"
        "Include:\n"
        "- Specific call to action appropriate for these officials\n"
        "- Reference to current events\n"
        "- Personal touch based on sender's residency status"
    )

    user_prompt = (
        "Writer profile:\n"
        f"- {residency_status}\n\n"
        "Topics to address:\n"
        f"{chr(10).join(topic_lines)}\n\n"
        "Recipients:\n"
        f"{chr(10).join(recipient_lines)}\n\n"
        "Generate:\n"
        "1. A compelling, personalized email body (200-300 words)\n"
        "2. An email subject line (max 60 characters)\n\n"
        "Output format:\n"
        "SUBJECT: [subject line]\n\n"
        "BODY:\n"
        "[email body]"
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
) -> Tuple[str, str, int]:
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise AIServiceError("OPENAI_API_KEY is not configured")

    residency_status = f"a resident of {country_name}" if is_resident else "an international supporter"
    topic_lines = [f"- {t['display_title']}: {t.get('description') or 'No description'}" for t in topics]
    recipient_lines = [f"- {r['full_name']} ({r['display_title']})" for r in recipients]

    system_prompt, user_prompt = _build_prompt(
        country_name=country_name,
        residency_status=residency_status,
        topic_lines=topic_lines,
        recipient_lines=recipient_lines,
    )

    payload = {
        "model": OPENAI_MODEL,
        "messages": [
            {"role": "developer", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        "temperature": 0.7,
        "max_completion_tokens": 700,
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
