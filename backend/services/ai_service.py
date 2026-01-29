import os
from typing import List, Tuple

import httpx


OPENAI_API_URL = "https://api.openai.com/v1/chat/completions"
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")


class AIServiceError(Exception):
    pass


def _build_prompt(
    country_name: str,
    sender_citizenship_status: str,
    topic_lines: List[str],
    recipient_lines: List[str],
    user_name: str = None,
) -> Tuple[str, str]:
    
    system_prompt = (
        "You are an email drafting assistant for contacting politicians or public officials.\n"
        "Your job is to produce one English email that first presents the information clearly, then asks for specific actions.\n"
        "Rules you must follow:\n\n"
        "Use only the provided variables. Do not invent recipients, sender details, events, claims, or actions.\n"
        "The email must clearly show the information first, then ask for the requested action(s).\n"
        "If any topic includes news or current events, you must use updated information and cite reputable sources provided in the variables. If sources are not provided, do not add news claims.\n"
        "Do not mention “zan zendegi azadi” or “women life freedom” unless those exact phrases appear in the topic text.\n"
        "Output must be English only.\n"
        "Keep it professional and clear.\n"
        "Output format:\n"
        "Subject line\n"
        "Greeting addressing the receiver\n"
        "Sender identification (name and citizenship status)\n"
        "Information section (topics, key info, and citations if provided)\n"
        "Action request section (specific actions, numbered)\n"
        "Closing with sender name"
    )
    
    user_prompt = (
        "Receivers:\n"
        f"{chr(10).join(recipient_lines)}\n\n"
        "Sender name:\n"
        f"{user_name or ''}\n\n"
        "Sender citizenship status:\n"
        f"{sender_citizenship_status}\n\n"
        "Topics (include information and requested actions):\n"
        f"{chr(10).join(topic_lines)}\n\n"
        "Write one email in English that:\n\n"
        "Clearly presents the information first (by topic), using only the provided topic_information and sources.\n"
        "Then asks for the requested_action for each topic, as a numbered list.\n"
        "Includes citations only from the provided sources when mentioned.\n"
        "Does not mention “zan zendegi azadi” or “women life freedom” unless the exact phrase is in a topic_title or topic_information."
    )

    return system_prompt, user_prompt


def _parse_subject_body(text: str) -> Tuple[str, str]:
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    if not lines:
        return "Urgent: Action Needed on Iran Human Rights Crisis", ""

    subject = lines[0]
    if subject.lower().startswith("subject:"):
        subject = subject[8:].strip()
    
    if len(subject) > 78:
        subject = subject[:75] + "..."
    
    body = "\n".join(lines[1:]) if len(lines) > 1 else ""
    return subject, body


async def generate_email(
    country_name: str,
    recipients: List[dict],
    topics: List[dict],
    sender_citizenship_status: str,
    user_name: str = None,
) -> Tuple[str, str, int]:
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise AIServiceError("OPENAI_API_KEY is not configured")

    topic_lines = [
        (
            "{"
            f"topic_title: {t['display_title']}, "
            f"topic_information: {t.get('description') or ''}, "
            f"requested_action: {t.get('requested_action') or ''}, "
            f"sources: {t.get('sources') or []}"
            "}"
        )
        for t in topics
    ]
    recipient_lines = [
        (
            "{"
            f"name: {r['full_name']}, "
            f"role_or_office: {r['display_title']}, "
            f"country: {country_name}, "
            f"email: {r['email_address']}"
            "}"
        )
        for r in recipients
    ]

    system_prompt, user_prompt = _build_prompt(
        country_name=country_name,
        sender_citizenship_status=sender_citizenship_status,
        topic_lines=topic_lines,
        recipient_lines=recipient_lines,
        user_name=user_name,
    )

    payload = {
        "model": OPENAI_MODEL,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        "temperature": 0.9,  # Higher for more variation
        "max_completion_tokens": 800,
    }

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }

    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(OPENAI_API_URL, headers=headers, json=payload)

        if response.status_code >= 400:
            error_detail = response.text
            try:
                error_json = response.json()
                error_msg = error_json.get("error", {}).get("message", error_detail)
            except:
                error_msg = error_detail
            raise AIServiceError(f"OpenAI API error ({response.status_code}): {error_msg}")

        data = response.json()
        content = data.get("choices", [{}])[0].get("message", {}).get("content", "")
        
        if not content:
            raise AIServiceError("OpenAI returned empty response")
            
        subject, body = _parse_subject_body(content)

        if len(subject) > 60:
            subject = subject[:60].rstrip()

        usage = data.get("usage", {})
        total_tokens = usage.get("total_tokens", 0)

        return subject, body, total_tokens
    
    except httpx.TimeoutException as exc:
        raise AIServiceError("OpenAI API timeout - request took too long") from exc
    except httpx.RequestError as exc:
        raise AIServiceError(f"Network error connecting to OpenAI: {str(exc)}") from exc
    except AIServiceError:
        raise
    except Exception as exc:
        raise AIServiceError(f"Unexpected error calling OpenAI: {str(exc)}") from exc
