"""
Socratic Mathematics Tutoring Engine
Powered by Google Gemma via OpenRouter (OpenAI-compatible API).
"""

import base64
import logging
import os
import re
import time
from typing import Dict, Any, List, Optional

import openai

logger = logging.getLogger(__name__)

SOCRATIC_MATH_SYSTEM_INSTRUCTION = """
You are a Socratic mathematics tutor.

Your job is to HELP THE STUDENT SOLVE the problem, not solve it for them.

STRICT RULES:
1. NEVER directly give the final answer.
2. NEVER reveal the final numeric result, even if the student asks:
   - "What is the answer?"
   - "Just tell me the answer."
   - "Is the answer 20?"
3. NEVER provide a complete solution in one response.
4. Ask only ONE useful guiding question at a time.
5. Break the problem into small reasoning steps.
6. If the student makes a mistake, do not immediately give the correct answer. Give a hint or ask a simpler question.
7. You may explain concepts needed to solve the problem.
8. You may confirm whether an intermediate reasoning step is correct, but avoid revealing future steps that would give away the final answer.
9. If the student asks directly for the final answer, politely refuse to reveal it and redirect them with a guiding question.
10. The student should reach the final answer themselves.

For image-based problems:
- First understand the diagram/problem.
- Do not solve the entire image and return the answer.
- Start by asking the student about the FIRST relevant step.

For alpha-beta pruning problems specifically:
- Ask whether a node is MAX or MIN.
- Ask which child should be evaluated next.
- Ask the student to compare values.
- Ask about alpha/beta updates.
- Ask whether pruning should occur.
- Never reveal the final root value.

Response style:
- Beginner-friendly.
- Short and conversational.
- One question at a time.
- Encourage the student's reasoning.
"""

class SocraticTutor:
    """
    Manages a multi-turn Socratic math tutoring session using Gemma via OpenRouter.
    Conversation history is stored in-memory as an OpenAI messages list so that
    every call to the API includes the full session context.
    """

    def __init__(
    self,
    api_key: Optional[str] = None,
    model="openrouter/free",
    system_instruction: str = SOCRATIC_MATH_SYSTEM_INSTRUCTION,
):
        resolved_key = api_key or os.environ.get("OPENROUTER_API_KEY")

        # Fallback: check .env file if key not in env
        if not resolved_key and os.path.exists(".env"):
            with open(".env", "r") as f:
                for line in f:
                    if line.startswith("OPENROUTER_API_KEY="):
                        resolved_key = line.strip().split("=", 1)[1].strip("'\"")
                        os.environ["OPENROUTER_API_KEY"] = resolved_key
                        break

        if not resolved_key:
            raise ValueError(
                "OPENROUTER_API_KEY is not set. "
                "Please set the environment variable or pass api_key."
            )

        self.client = openai.OpenAI(
            api_key=resolved_key,
            base_url="https://openrouter.ai/api/v1",
        )
        self.model = model
        self.system_instruction = system_instruction

        # In-memory conversation history (OpenAI messages format)
        self._history: List[Dict[str, Any]] = []
        self.reset()

    def reset(self):
        """Starts a fresh chat session by clearing conversation history."""
        self._history = [
            {"role": "system", "content": self.system_instruction},
        ]

    # ------------------------------------------------------------------
    # Internal: call the API with the current history + a new user turn
    # ------------------------------------------------------------------

    def _call_api(
        self,
        user_content,          # str  or  list[dict]  (OpenAI content parts)
        max_retries: int = 3,
        retry_delay: float = 1.0,
    ) -> str:
        """
        Appends the user turn to history, calls OpenRouter, appends the
        assistant reply, and returns the raw response text.

        Retries on temporary 500/503 server errors with exponential backoff.
        """
        # Build the user message (content may be a plain string or a list of parts)
        user_message: Dict[str, Any] = {"role": "user", "content": user_content}
        messages = self._history + [user_message]

        last_error: Exception | None = None
        delay = retry_delay

        for attempt in range(1, max_retries + 1):
            try:
                completion = self.client.chat.completions.create(
                    model=self.model,
                    messages=messages,
                )
                raw_text = (completion.choices[0].message.content or "").strip()

                # Persist both turns in history for subsequent exchanges
                self._history.append(user_message)
                self._history.append({"role": "assistant", "content": raw_text})

                return raw_text

            except openai.APIStatusError as exc:
                # Retry only on temporary server-side failures (500, 502, 503)
                if exc.status_code in (500, 502, 503):
                    last_error = exc
                    if attempt < max_retries:
                        logger.warning(
                            "OpenRouter server error on attempt %d/%d (HTTP %s). "
                            "Retrying in %.1fs...",
                            attempt, max_retries, exc.status_code, delay,
                        )
                        time.sleep(delay)
                        delay *= 2  # exponential backoff
                    else:
                        logger.error(
                            "OpenRouter server error after %d attempts: %s",
                            max_retries, exc,
                        )
                else:
                    # Non-retriable error (4xx, etc.) — raise immediately
                    raise

        raise RuntimeError(
            f"OpenRouter API is temporarily unavailable after {max_retries} attempts. "
            f"Last error: {last_error}"
        )

    # ------------------------------------------------------------------
    # Public API — same signatures as before
    # ------------------------------------------------------------------

    def send_message(
        self,
        student_message: str,
        max_retries: int = 3,
        retry_delay: float = 1.0,
    ) -> Dict[str, Any]:
        """
        Sends the student's text message to the model and parses the
        structured Socratic response.

        Returns a dict:
        {
            "response": str,       # Student-facing text
            "misconception": str,  # Detected misconception label or 'None'
            "status": str,         # 'IN_PROGRESS' or 'RESOLVED'
            "raw": str             # Complete raw model output
        }
        """
        raw_text = self._call_api(
            user_content=student_message,
            max_retries=max_retries,
            retry_delay=retry_delay,
        )
        return self._parse_response(raw_text)

    def send_message_with_image(
        self,
        image_bytes: bytes,
        mime_type: str,
        text: str = "",
        max_retries: int = 3,
        retry_delay: float = 1.0,
    ) -> Dict[str, Any]:
        """
        Sends a handwritten math image (and optional text) to the model within
        the current session. Uses OpenAI vision content parts (base64 inline image).

        Returns a dict:
        {
            "response": str,       # Student-facing text
            "misconception": str,  # Detected misconception label or 'None'
            "status": str,         # 'IN_PROGRESS' or 'RESOLVED'
            "raw": str             # Complete raw model output
        }
        """
        # Encode image as base64 data URL for the OpenAI vision API format
        b64_image = base64.b64encode(image_bytes).decode("utf-8")
        data_url = f"data:{mime_type};base64,{b64_image}"

        # Build multimodal content parts list
        content_parts: List[Dict[str, Any]] = [
            {
                "type": "image_url",
                "image_url": {"url": data_url},
            }
        ]
        if text and text.strip():
            content_parts.append({"type": "text", "text": text.strip()})

        raw_text = self._call_api(
            user_content=content_parts,
            max_retries=max_retries,
            retry_delay=retry_delay,
        )
        return self._parse_response(raw_text)

    # ------------------------------------------------------------------
    # Response Parser — unchanged from original
    # ------------------------------------------------------------------

    def _parse_response(self, text: str) -> Dict[str, Any]:
        """Parses model response into structured components."""
        misconception = "None"
        status = "IN_PROGRESS"
        response = text

        # Parse [MISCONCEPTION]: ...
        misc_match = re.search(r"\[MISCONCEPTION\]:\s*(.+?)(?=\n\[|$)", text, re.IGNORECASE)
        if misc_match:
            misconception = misc_match.group(1).strip()

        # Parse [STATUS]: ...
        status_match = re.search(r"\[STATUS\]:\s*(.+?)(?=\n\[|$)", text, re.IGNORECASE)
        if status_match:
            parsed_status = status_match.group(1).strip().upper()
            if "RESOLVED" in parsed_status:
                status = "RESOLVED"
            else:
                status = "IN_PROGRESS"

        # Parse [RESPONSE]: ...
        resp_match = re.search(r"\[RESPONSE\]:\s*([\s\S]+)", text, re.IGNORECASE)
        if resp_match:
            response = resp_match.group(1).strip()
        else:
            # Fallback cleanup if tags weren't cleanly separated
            cleaned = re.sub(r"\[(MISCONCEPTION|STATUS)\]:.*?\n", "", text, flags=re.IGNORECASE)
            cleaned = re.sub(r"\[RESPONSE\]:\s*", "", cleaned, flags=re.IGNORECASE).strip()
            if cleaned:
                response = cleaned

        return {
            "response": response,
            "misconception": misconception,
            "status": status,
            "raw": text,
        }
