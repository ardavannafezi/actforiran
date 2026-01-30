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
        "You are writing professional emails to government officials that will pass spam filters and get read.\n\n"
        "SUBJECT LINE RULES:\n"
        "- MUST be procedural and process-oriented, never outcome-driven or urgent\n"
        "- Frame as inquiry, question, or request for clarification\n"
        "- NEVER use: 'Urgent', 'Please support', 'Open letter', 'Call to action', 'Action needed'\n"
        "- GOOD patterns: 'Inquiry regarding enforcement of existing law', 'Question on government authority', 'Request for clarification on enforcement mechanisms'\n"
        "- BAD patterns: 'Request to deport X', 'Urgent action required', 'Please take action now'\n"
        "- Do NOT include the word 'Subject:' prefix\n\n"
        "LANGUAGE RULES:\n"
        "- Use legal/administrative language, NOT moral or emotional language\n"
        "- AVOID: urge, demand, stand with, fight for, historic moment, silence is complicity, human rights catastrophe, brutal regime, moral obligation\n"
        "- USE: ask, clarify, request, understand, confirm, designated entities, sanctions regime, enforcement actions, existing legislation\n\n"
        "STRUCTURE RULES:\n"
        "- First paragraph: NEVER state the demand. Only identify sender and state why writing at high level\n"
        "- 1 short intro sentence (identify as individual constituent)\n"
        "- 2-3 short paragraphs, maximum 3 lines each\n"
        "- Do NOT frame the request as an authority check (avoid phrases like 'authority to', 'whether your agencies have the authority to')\n"
        "- Ask for specific actions clearly and directly in the final paragraph\n"
        "- 1 clear ask in a single sentence at the end\n"
        "- Simple sign-off (Respectfully, Sincerely) with sender name ONLY if provided\n\n"
        "LINKS:\n"
        "- Include ZERO links or maximum ONE official government/major media link\n"
        "- If referencing news, mention agency name and article title, NO links\n"
        "- Never use link shorteners or PDFs\n\n"
        "FOOTER RULES:\n"
        "- NO activism signature blocks, titles, hashtags, or slogans\n"
        "- Just name (if provided) and simple closing\n\n"
        "VARIATION RULES:\n"
        "- Rotate sentence order, verb choice, which facts mentioned\n"
        "- Vary whether request is framed as authority check, status inquiry, or clarification\n"
        "- Make each email structurally different\n\n"
        "OUTPUT FORMAT:\n"
        "Line 1: Procedural subject line\n"
        "Line 2: Blank\n"
        "Line 3: Simple greeting\n"
        "Line 4: Blank\n"
        "Body: Short professional paragraphs\n"
        "Closing: Simple sign-off with name only if provided"
    )
    
    num_recipients = len(recipient_lines)
    recipient_description = f"{num_recipients} official(s): {', '.join([r.split('name: ')[1].split(',')[0] for r in recipient_lines if 'name: ' in r])}"
    
    topics_text = "\n".join([f"- {line}" for line in topic_lines])
    
    user_prompt = (
        f"Write a professional government email to {recipient_description}.\n\n"
        f"SENDER: {sender_identity}"
        + (f" named {user_name}" if user_name else " (anonymous - do not mention sender name)")
        + f"\n\nTOPICS (weave into procedural inquiry):\n{topics_text}\n\n"
        "CRITICAL REQUIREMENTS:\n"
        "1. Subject must sound like an administrative inquiry, not a campaign demand\n"
        "2. First paragraph must NOT contain the ask - only identify sender and general context\n"
        "3. Ask for specific actions directly; do NOT ask about authority or capability\n"
        "4. Use cold administrative language - avoid all emotional or moral framing\n"
        "5. Keep paragraphs very short (2-3 lines maximum)\n"
        "6. If news sources mentioned in topics, cite agency name and title without links\n"
        "7. Vary sentence structure and approach from standard templates\n"
        "8. Plain text only - no formatting, no links (or max 1 official link if absolutely critical)\n"
        + ("9. Sign with name: " + user_name if user_name else "9. No signature name")
    )

    return system_prompt, user_prompt


def _parse_subject_body(text: str) -> Tuple[str, str]:
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    if not lines:
        return "Urgent: Action Needed on Iran Human Rights Crisis", ""

    subject = lines[0]
    if subject.lower().startswith("subject:"):
        subject = subject[8:].strip()
    
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

    timeout = httpx.Timeout(10.0, connect=7.0, read=10.0)
    try:
        async with httpx.AsyncClient(timeout=timeout) as client:
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
