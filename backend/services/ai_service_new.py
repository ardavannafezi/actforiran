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
    
    citizenship_map = {
        "selected_country_citizen": f"a citizen of {country_name}",
        "iranian_citizen": "an Iranian citizen",
        "international_supporter": "an international supporter concerned about human rights in Iran"
    }
    sender_identity = citizenship_map.get(sender_citizenship_status, "a concerned individual")
    
    system_prompt = (
        "You are an expert advocate writing personalized emails to government officials about human rights violations in Iran.\n\n"
        "CRITICAL RULES:\n"
        "- Output ONLY plain text - no markdown, no formatting, no asterisks, no bold, no bullets\n"
        "- Be creative and vary your writing style - never use the same structure twice\n"
        "- Write naturally flowing paragraphs - do NOT list topics or use numbered points in the main body\n"
        "- The topic descriptions contain the key information - weave them into compelling narrative prose\n"
        "- Focus heavily on the topic descriptions provided - they are the heart of the message\n"
        "- If multiple recipients, address them collectively (e.g., 'Dear Officials', 'Distinguished Representatives')\n"
        "- Vary your greetings, tone, and structure to make each email unique\n"
        "- Use only the provided information - do not invent facts, names, or events\n"
        "- Do NOT include the word 'Subject:' in the subject line - just write the subject text\n"
        "- If no sender name is provided, write the email without mentioning any name at all\n"
        "- End with a simple closing (Sincerely, Respectfully, etc.) followed by sender name ONLY if name was provided\n\n"
        "OUTPUT FORMAT:\n"
        "Line 1: Subject line (no 'Subject:' prefix)\n"
        "Line 2: Blank\n"
        "Line 3: Greeting\n"
        "Line 4: Blank\n"
        "Body: Natural flowing paragraphs describing the topics and making the case\n"
        "Closing: Simple sign-off with name only if provided"
    )
    
    num_recipients = len(recipient_lines)
    recipient_description = f"{num_recipients} official(s): {', '.join([r.split('name: ')[1].split(',')[0] for r in recipient_lines if 'name: ' in r])}"
    
    topics_text = "\n".join([f"- {line}" for line in topic_lines])
    
    user_prompt = (
        f"Write a unique, compelling advocacy email to {recipient_description}.\n\n"
        f"SENDER: {sender_identity}"
        + (f" named {user_name}" if user_name else " (no name provided - do not mention sender name in email)")
        + f"\n\nTOPICS TO ADDRESS:\n{topics_text}\n\n"
        "INSTRUCTIONS:\n"
        "- Write the email in plain text only - no formatting marks\n"
        "- Craft a natural, flowing message that weaves the topic descriptions into compelling prose\n"
        "- Focus on the human rights concerns described in the topic information\n"
        "- Be specific about what action you want the recipient(s) to take\n"
        "- Make this email unique - vary your style, structure, and approach\n"
        "- If multiple recipients, use plural addressing ('you' can be plural, or use collective terms)\n"
        "- First line must be the subject (without the word 'Subject:')\n"
        + ("- End with sender name only if provided (it is: " + user_name + ")" if user_name else "- Do not include sender name since none was provided")
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
        "temperature": 0.9,
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
