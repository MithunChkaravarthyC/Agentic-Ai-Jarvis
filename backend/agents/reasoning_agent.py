import json
import logging
from typing import Dict, Any
from backend.config import MODEL_ROUTING
from backend.ollama_client import ollama_client
from backend.prompts import REASONING_AGENT_SYSTEM_PROMPT

logger = logging.getLogger("ReasoningAgent")

class ReasoningAgent:
    def __init__(self):
        self.model = MODEL_ROUTING["reasoning"]

    async def plan_task(self, user_goal: str, conversation_history: str = "") -> Dict[str, Any]:
        """Generate an execution plan and chain-of-thought for a given goal."""
        prompt = f"""Conversation Context:
{conversation_history}

User Goal:
"{user_goal}"

Please plan the step-by-step execution strategy, check for any missing user information, and return the structured JSON plan."""

        logger.info(f"ReasoningAgent planning with {self.model}...")
        raw_output = await ollama_client.generate(
            model=self.model,
            prompt=prompt,
            system=REASONING_AGENT_SYSTEM_PROMPT,
            options={"temperature": 0.2}
        )

        extracted = ollama_client.extract_deepseek_reasoning(raw_output)
        thought = extracted["thought"]
        content = extracted["content"]

        # Parse JSON from content
        plan_data = None
        try:
            # Look for JSON block
            if "```json" in content:
                json_str = content.split("```json")[1].split("```")[0].strip()
            elif "```" in content:
                json_str = content.split("```")[1].split("```")[0].strip()
            elif "{" in content and "}" in content:
                start = content.find("{")
                end = content.rfind("}") + 1
                json_str = content[start:end]
            else:
                json_str = content
            plan_data = json.loads(json_str)
        except Exception as e:
            logger.warning(f"Could not parse strict JSON from ReasoningAgent: {e}")
            plan_data = {
                "task_type": "general_task",
                "summary": content,
                "required_slots": [],
                "execution_steps": [{"step": 1, "agent": "General", "action": content, "details": ""}],
                "safety_checks": []
            }

        return {
            "thought": thought,
            "plan": plan_data,
            "raw_response": content
        }

reasoning_agent = ReasoningAgent()
