import re
import json
import logging
from typing import Dict, Any, List, Optional, Callable
from datetime import datetime
from backend.config import MODEL_ROUTING
from backend.ollama_client import ollama_client
from backend.agents.reasoning_agent import reasoning_agent
from backend.agents.code_agent import code_agent
from backend.agents.booking_agent import booking_agent
from backend.agents.vision_agent import vision_agent
from backend.agents.tts_agent import tts_agent
from backend.tools.app_launcher import app_launcher
from backend.tools.time_tool import time_tool
from backend.tools.weather_tool import weather_tool
from backend.prompts import (
    JARVIS_ORCHESTRATOR_SYSTEM_PROMPT as JARVIS_SYSTEM_PROMPT,
    SLOT_EXTRACTOR_SYSTEM_PROMPT
)

logger = logging.getLogger("JarvisOrchestrator")

class JarvisOrchestrator:
    def __init__(self):
        self.model = MODEL_ROUTING["orchestrator"]
        self.intent_model = MODEL_ROUTING["intent_extractor"]
        self.convo_model = MODEL_ROUTING["conversational_voice"]
        self.conversation_history: List[Dict[str, str]] = []
        self.active_slots: Dict[str, Any] = {}

    def reset(self):
        self.conversation_history = []
        self.active_slots = {}

    async def _extract_slots_fast(self, text: str) -> Dict[str, Any]:
        """Use ultra-lightweight llama3.2:1b model to parse slots and parameters instantly."""
        prompt = f"""Extract parameters from this user message into JSON.
User message: "{text}"
Extract any of: app_title, features, food_item, location, flight_origin, flight_destination, flight_date.
Return ONLY valid JSON, e.g. {{"food_item": "...", "location": "..."}}."""
        try:
            res = await ollama_client.generate(model=self.intent_model, prompt=prompt)
            if "{" in res and "}" in res:
                s = res[res.find("{"):res.rfind("}")+1]
                return json.loads(s)
        except Exception:
            pass
        return {}

    async def _extract_flight_slots(self, text: str) -> Dict[str, Any]:
        """Extract origin, destination, date, cabin_class, and airline accurately using SlotExtractor (llama3.2:1b)."""
        prompt = f"""You are an accurate travel entity extractor.
Extract flight specifications from: "{text}"
Output ONLY a JSON object:
{{
  "origin": "origin city name only (e.g. Coimbatore, Mumbai)",
  "destination": "destination city name only (e.g. Mumbai, Dubai)",
  "date": "departure date or 'Next Monday'",
  "cabin_class": "First Class | Business | Premium Economy | Economy",
  "airline": "airline name if mentioned (e.g. Emirates, Air India, IndiGo) or null",
  "passengers": 1
}}"""
        try:
            res = await ollama_client.generate(model=self.intent_model, prompt=prompt)
            match = re.search(r'\{[^{}]*\}', res, re.DOTALL)
            if match:
                data = json.loads(match.group(0))
                for k in ["origin", "destination"]:
                    if k in data and data[k]:
                        # Strip trailing words like 'in firstclass', 'in emirates', etc.
                        data[k] = re.sub(r'(?i)\s+(in|on|via|class|flight|airline|first|business|economy).*$', '', str(data[k])).strip().title()
                if data.get("origin") and data.get("destination"):
                    return data
        except Exception as e:
            logger.warning(f"Flight slot extraction note: {e}")

        # Intelligent Fallback
        lower = text.lower()
        cabin_class = "Economy"
        if "first" in lower:
            cabin_class = "First Class"
        elif "business" in lower:
            cabin_class = "Business Class"
        elif "premium" in lower:
            cabin_class = "Premium Economy"

        airline = None
        for al in ["emirates", "air india", "indigo", "vistara", "singapore airlines", "qatar airways", "etihad", "british airways", "lufthansa", "spicejet", "akasa"]:
            if al in lower:
                airline = al.title()
                break

        origin = "Mumbai"
        destination = "Delhi"
        m = re.search(r'(?:from)\s+([A-Za-z]+)(?:\s+(?:to)\s+([A-Za-z]+))?', text, re.IGNORECASE)
        if m:
            if m.group(1): origin = m.group(1).title()
            if m.group(2): destination = m.group(2).title()

        date_m = re.search(r'(?:on|for)\s+([A-Za-z0-9\s]+?)(?:\.|$|,|\s+in)', text, re.IGNORECASE)
        dept_date = date_m.group(1).strip() if date_m else "Next Monday"

        return {
            "origin": origin,
            "destination": destination,
            "date": dept_date,
            "cabin_class": cabin_class,
            "airline": airline,
            "passengers": 1
        }

    async def _extract_food_slots(self, text: str) -> Dict[str, Any]:
        """Extract food item and location accurately using SlotExtractor (llama3.2:1b)."""
        prompt = f"""Extract food ordering entities from: "{text}"
Output ONLY a JSON object:
{{
  "food_item": "name of food or dish (e.g. Chicken Biryani, Paneer Butter Masala, Pizza)",
  "location": "locality or city (e.g. Koramangala, Indiranagar, Bangalore) or null"
}}"""
        try:
            res = await ollama_client.generate(model=self.intent_model, prompt=prompt)
            match = re.search(r'\{[^{}]*\}', res, re.DOTALL)
            if match:
                data = json.loads(match.group(0))
                if data.get("food_item"):
                    data["food_item"] = str(data["food_item"]).strip().title()
                if data.get("location"):
                    data["location"] = str(data["location"]).strip().title()
                return data
        except Exception as e:
            logger.warning(f"Food slot extraction note: {e}")

        food_item = "Chicken Biryani"
        location = "Koramangala, Bangalore"
        food_match = re.search(r'(?:order|get|want|craving|deliver|some|a)\s+(?:a|some)?\s*([A-Za-z0-9\s]+?)(?:\s+from|\s+in|\s+at|\s+on swiggy|$)', text, re.IGNORECASE)
        if food_match:
            cand = food_match.group(1).strip()
            if len(cand) > 2 and "swiggy" not in cand.lower():
                food_item = cand.title()
        loc_match = re.search(r'(?:in|at|to)\s+([A-Za-z0-9\s,]+?)(?:\.|$|,|\s+please)', text, re.IGNORECASE)
        if loc_match:
            location = loc_match.group(1).strip().title()
        return {"food_item": food_item, "location": location}

    def _classify_intent(self, text: str) -> str:
        """Rule & keyword based intent classifier with fallback."""
        lower = text.lower()
        
        # Payment confirmation
        if any(w in lower for w in ["confirm payment", "yes confirm", "proceed with payment", "authorize payment", "place order", "book now", "approve booking"]) and booking_agent.pending_confirmation:
            return "confirm_payment"
        if any(w in lower for w in ["cancel payment", "cancel order", "abort booking", "don't buy", "no cancel"]) and booking_agent.pending_confirmation:
            return "cancel_payment"

        # Real-Time Clock & Date Queries
        if re.search(r'\b(what\s+time|current\s+time|what\s+is\s+the\s+time|tell\s+me\s+the\s+time|the\s+time\s+now|time\s+is\s+it|time\s+now|today(?:\'s|\s)?\s*date|what(?:\'s|\s+is)?\s*(?:the\s+)?date|what\s+day\s+is\s+today|what\s+day\s+is\s+it|what\s+day\s+today)\b', lower) or (re.search(r'\btime\b', lower) and any(w in lower for w in ["what", "tell", "current", "now", "in", "is it", "please"])):
            return "time_query"

        # Weather & Climate Queries
        if re.search(r'\b(weather|temperature|forecast|climate|how hot|how cold|is it raining|rain today)\b', lower):
            return "weather_query"

        # Open any local application or tool on laptop
        if re.search(r'\b(open|launch|start|run)\b', lower) and not re.search(r'\b(build|write|generate|code\s+a|code\s+an)\s+(?:website|web app|app)\b', lower):
            return "open_app"

        # Web development
        if re.search(r'\b(build|create|make|generate|code|develop)\b', lower) and any(w in lower for w in ["website", "web app", "app", "application", "dashboard", "frontend", "game", "clone", "page", "portfolio", "tool", "cake shop", "shop", "lusion", "3d"]):
            return "build_web_app"

        # Food ordering (strictly using word boundaries to prevent 'weather' matching 'eat')
        if re.search(r'\b(swiggy|zomato|order food|order a food|biryani|pizza|burger|dinner|lunch|breakfast|takeaway|cravings)\b', lower):
            return "order_swiggy"
        if re.search(r'\border\s+(?:a|some|the)?\s*[a-zA-Z\s]+(?:from|in|on swiggy|on zomato)\b', lower):
            return "order_swiggy"

        # Flight booking
        if re.search(r'\b(flight|fly|flights|plane ticket|book flight|airline|airlines|indigo|air india|airport)\b', lower):
            return "book_flight"

        # Research & Deep Analysis
        if re.search(r'\b(research|investigate|study|deep dive|analyze|explain|how does|what is the architecture|tell me about)\b', lower):
            return "research_topic"

        return "general_conversation"

    async def handle_user_input(
        self,
        user_message: str,
        emit_event: Optional[Callable[[str, Dict[str, Any]], Any]] = None
    ) -> Dict[str, Any]:
        """Main dispatcher for user input."""
        self.conversation_history.append({"role": "user", "content": user_message})
        intent = self._classify_intent(user_message)
        logger.info(f"Classified intent: '{intent}' for message: '{user_message}'")

        if emit_event:
            await emit_event("intent_detected", {"intent": intent, "message": user_message})

        # --- 0. LOCAL APP LAUNCHING ---
        if intent == "open_app":
            # Pass FULL message — app_launcher does its own cleaning internally
            res = app_launcher.open_application(user_message)
            reply = res["message"]
            self.conversation_history.append({"role": "assistant", "content": reply})
            tts_res = await tts_agent.synthesize(reply)
            return {"type": "app_launched", "reply": reply, "details": res, "audio_url": tts_res.get("audio_url")}

        # --- 0.4 REAL-TIME CLOCK & GLOBAL TIMEZONES ---
        if intent == "time_query":
            if emit_event:
                await emit_event("agent_status", {"agent": "VoiceConvoAgent", "status": "Consulting atomic system clock..."})

            city_match = re.search(r'\b(?:in|for|at|of)\b\s+([a-zA-Z\s]+?)(?:\?|$|\.|\s+now|\s+right now)', user_message, re.IGNORECASE)
            city = city_match.group(1).strip() if city_match else None

            time_res = time_tool.get_current_time(city)
            reply = time_res["spoken"]
            self.conversation_history.append({"role": "assistant", "content": reply})
            tts_res = await tts_agent.synthesize(reply)
            return {
                "type": "time_report",
                "reply": reply,
                "time_data": time_res,
                "audio_url": tts_res.get("audio_url")
            }

        # --- 0.5 LIVE CLIMATE & WEATHER TELEMETRY ---
        if intent == "weather_query":
            if emit_event:
                await emit_event("agent_status", {"agent": "VoiceConvoAgent", "status": "Accessing live atmospheric telemetry sensors..."})

            city_match = re.search(r'\b(?:in|for|at|of)\b\s+([a-zA-Z\s]+?)(?:\?|$|\.|\s+today|\s+right now)', user_message, re.IGNORECASE)
            city = city_match.group(1).strip() if city_match else None

            weather_res = weather_tool.get_live_weather(city)
            reply = weather_res.get("spoken", f"Atmospheric telemetry currently unavailable for {city or 'your area'}, Sir.")
            self.conversation_history.append({"role": "assistant", "content": reply})
            tts_res = await tts_agent.synthesize(reply)
            return {
                "type": "weather_report",
                "reply": reply,
                "weather_data": weather_res,
                "city": weather_res.get("city"),
                "audio_url": tts_res.get("audio_url")
            }

        # --- 1. PAYMENT / CONFIRMATION GATE ---
        if intent == "confirm_payment":
            if emit_event:
                await emit_event("agent_status", {"agent": "BookingAgent", "status": "Confirming transaction..."})
            result = booking_agent.confirm_payment()
            reply = f"Authorization received. {result['message']}"
            self.conversation_history.append({"role": "assistant", "content": reply})
            tts_res = await tts_agent.synthesize(reply)
            return {"type": "confirmation_success", "reply": reply, "details": result, "audio_url": tts_res.get("audio_url")}

        if intent == "cancel_payment":
            result = booking_agent.cancel_payment()
            reply = result['message']
            self.conversation_history.append({"role": "assistant", "content": reply})
            tts_res = await tts_agent.synthesize(reply)
            return {"type": "confirmation_cancelled", "reply": reply, "audio_url": tts_res.get("audio_url")}

        # --- 2. WEB APPLICATION BUILDING ---
        if intent == "build_web_app":
            if emit_event:
                await emit_event("agent_status", {"agent": "ReasoningAgent", "status": "Analyzing architecture & requirements with DeepSeek-R1..."})

            # Check if prompt has enough detail
            prompt_words = len(user_message.split())
            if prompt_words < 4 and "detail" not in self.active_slots:
                reply = "Certainly, Sir. What specific features, theme, or interactive capabilities would you like me to incorporate into this web application?"
                self.conversation_history.append({"role": "assistant", "content": reply})
                return {"type": "clarification", "reply": reply, "needed_info": "app_details"}

            # Step 1: Reasoning Plan
            history_text = "\n".join([f"{m['role']}: {m['content']}" for m in self.conversation_history[-4:]])
            plan_res = await reasoning_agent.plan_task(user_message, history_text)

            if emit_event and plan_res.get("thought"):
                await emit_event("thought_stream", {"agent": "ReasoningAgent", "thought": plan_res["thought"]})

            if emit_event:
                await emit_event("agent_status", {"agent": "CodeAgent", "status": "Qwen-Coder is generating complete production files..."})

            # Extract title / project name
            app_name = "JarvisWebApp"
            named_match = re.search(r'(?:called|named)\s+([a-zA-Z0-9_-]+)', user_message, re.IGNORECASE)
            if named_match:
                app_name = named_match.group(1).strip().title().replace(" ", "")
            else:
                topic_match = re.search(r'(?:build|create|make)\s+(?:me\s+)?(?:a|an)?\s*(?:website|web\s+app|app)?\s*(?:for\s+(?:a|an)?)?\s*([a-zA-Z0-9\s_-]+?)(?:\s+called|\s+named|\s+with|\s+that|$|\.)', user_message, re.IGNORECASE)
                if topic_match:
                    cand = topic_match.group(1).strip()
                    cand = re.sub(r'^(?:me\s+)?(?:a|an)?\s*(?:website|web\s+app|app)?\s*(?:for)?', '', cand, flags=re.IGNORECASE).strip()
                    if len(cand) > 2 and len(cand) < 30:
                        app_name = cand.title().replace(" ", "")

            # Step 2: Code Generation
            build_res = await code_agent.build_web_app(
                project_name=app_name,
                app_spec=user_message,
                plan=plan_res.get("plan")
            )

            # Auto-open in new browser tab on localhost as well
            try:
                import ctypes
                ctypes.windll.shell32.ShellExecuteW(None, "open", build_res['preview_url'], None, None, 1)
            except Exception as e:
                logger.warning(f"Could not open new browser tab for web app: {e}")

            if emit_event:
                await emit_event("app_created", build_res)

            reply = f"I have constructed the **{build_res['project_name']}** application, Sir! The application is running live on localhost and embedded in your Web Apps tab. You can also view it directly at [Open Localhost App]({build_res['preview_url']})."
            self.conversation_history.append({"role": "assistant", "content": reply})
            return {
                "type": "web_app_ready",
                "reply": reply,
                "project": build_res,
                "thought": plan_res.get("thought")
            }

        # --- 2.5 RESEARCH & DEEP ANALYSIS ---
        if intent == "research_topic":
            if emit_event:
                await emit_event("agent_status", {"agent": "ReasoningAgent", "status": "DeepSeek-R1 conducting in-depth research and reasoning..."})

            history_text = "\n".join([f"{m['role']}: {m['content']}" for m in self.conversation_history[-4:]])
            plan_res = await reasoning_agent.plan_task(user_message, history_text)

            if emit_event and plan_res.get("thought"):
                await emit_event("thought_stream", {"agent": "ReasoningAgent", "thought": plan_res["thought"]})

            reply = f"### 📊 Intelligence Briefing // DeepSeek-R1\n\n{plan_res.get('plan', '')}"
            self.conversation_history.append({"role": "assistant", "content": reply})
            return {
                "type": "research_complete",
                "reply": reply,
                "thought": plan_res.get("thought")
            }

        # --- 3. SWIGGY FOOD ORDERING ---
        if intent == "order_swiggy":
            if emit_event:
                await emit_event("agent_status", {"agent": "SlotExtractor", "status": "Parsing food item and delivery location..."})

            # Use LLM-based extractor for accurate food and location parsing
            food_slots = await self._extract_food_slots(user_message)
            food_item = food_slots.get("food_item") or "Chicken Biryani"
            location = food_slots.get("location") or "Koramangala, Bangalore"

            # Open Swiggy in browser immediately
            try:
                import ctypes
                swiggy_url = f"https://www.swiggy.com/search?query={food_item.replace(' ', '+')}"
                ctypes.windll.shell32.ShellExecuteW(None, "open", swiggy_url, None, None, 1)
            except Exception as e:
                logger.warning(f"Could not open Swiggy in browser: {e}")

            async def progress_cb(msg: str):
                if emit_event:
                    await emit_event("agent_status", {"agent": "BookingAgent", "status": msg})

            booking_res = await booking_agent.order_swiggy(
                location=location,
                food_item=food_item,
                progress_callback=progress_cb
            )

            if emit_event:
                await emit_event("booking_pending", booking_res)

            total = booking_res.get('confirmation_payload', {}).get('details', {}).get('total', '₹399.00')
            reply = f"Sir, I have opened Swiggy in your browser and assembled your order for **{food_item}** in **{location}**. The order total is **{total}**. Please confirm payment authorization in the Security Gate modal to proceed."
            self.conversation_history.append({"role": "assistant", "content": reply})
            return {
                "type": "swiggy_awaiting_approval",
                "reply": reply,
                "booking": booking_res
            }

        # --- 4. FLIGHT TICKET BOOKING ---
        if intent == "book_flight":
            if emit_event:
                await emit_event("agent_status", {"agent": "SlotExtractor", "status": "Parsing flight route, cabin class, and airline..."})

            # Use LLM-based extractor for accurate flight parameter parsing
            flight_slots = await self._extract_flight_slots(user_message)
            origin = flight_slots.get("origin") or "Mumbai"
            destination = flight_slots.get("destination") or "Delhi"
            dept_date = flight_slots.get("date") or "Next Monday"
            cabin_class = flight_slots.get("cabin_class") or "Economy"
            preferred_airline = flight_slots.get("airline")  # None if not specified
            passengers = int(flight_slots.get("passengers") or 1)

            logger.info(f"Flight slots extracted — {origin} -> {destination} | {cabin_class} | airline={preferred_airline} | pax={passengers} | date={dept_date}")

            async def progress_cb(msg: str):
                if emit_event:
                    await emit_event("agent_status", {"agent": "BookingAgent", "status": msg})

            booking_res = await booking_agent.book_flight(
                origin=origin,
                destination=destination,
                departure_date=dept_date,
                passengers=passengers,
                cabin_class=cabin_class,
                airline=preferred_airline,
                progress_callback=progress_cb
            )

            # Open live flight search in user's browser
            try:
                import ctypes
                flight_query = f"Flights+to+{destination}+from+{origin}+{cabin_class}".replace(" ", "+")
                flight_url = f"https://www.google.com/travel/flights?q={flight_query}"
                ctypes.windll.shell32.ShellExecuteW(None, "open", flight_url, None, None, 1)
            except Exception as e:
                logger.warning(f"Could not open flight URL: {e}")

            if emit_event:
                await emit_event("booking_pending", booking_res)

            details = booking_res.get('confirmation_payload', {}).get('details', {})
            fare = details.get('total', '₹5,770')
            airline_name = details.get('airline', preferred_airline or 'Selected Carrier')
            route_advisory = booking_res.get('route_advisory', '')
            advisory_note = f"\n\n> **Route Note:** {route_advisory}" if route_advisory else ""

            reply = (
                f"Sir, I have selected a **{cabin_class}** seat on **{airline_name}** "
                f"from **{origin}** to **{destination}** departing **{dept_date}**. "
                f"Total fare: **{fare}**. Standing by for your authorization before payment."
                f"{advisory_note}"
            )
            self.conversation_history.append({"role": "assistant", "content": reply})
            return {
                "type": "flight_awaiting_approval",
                "reply": reply,
                "booking": booking_res
            }

        # --- 5. GENERAL JARVIS CONVERSATION ---
        if emit_event:
            await emit_event("agent_status", {"agent": "JARVIS", "status": "Formulating response..."})

        now_str = datetime.now().strftime('%A, %B %d, %Y at %I:%M %p')
        prompt = f"""Current System Date & Time: {now_str}
Conversation History:
{json.dumps(self.conversation_history[-6:], indent=2)}

User: {user_message}
J.A.R.V.I.S.:"""

        full_tokens = []
        tts_task = None

        try:
            # Stream tokens from Ollama to parallelize first-sentence TTS
            async for token in ollama_client.generate_stream(
                model=self.model,
                prompt=prompt,
                system=JARVIS_SYSTEM_PROMPT
            ):
                full_tokens.append(token)
                if not tts_task:
                    partial = "".join(full_tokens)
                    if any(end in partial for end in [". ", "! ", "? ", ".\n", "!\n", "?\n"]):
                        match = re.search(r'^(.*?[.!?])(?:\s|\n|$)', partial, re.DOTALL)
                        if match and len(match.group(1).strip()) > 8:
                            first_sentence = match.group(1).strip()
                            tts_task = asyncio.create_task(tts_agent.synthesize(first_sentence))
        except Exception as e:
            logger.warning(f"Streaming error in orchestrator: {e}")
            response = await ollama_client.generate(
                model=self.model,
                prompt=prompt,
                system=JARVIS_SYSTEM_PROMPT
            )
            full_tokens = [response]

        response = "".join(full_tokens)
        clean_response = ollama_client.extract_deepseek_reasoning(response)["content"]
        self.conversation_history.append({"role": "assistant", "content": clean_response})

        audio_url = None
        if tts_task:
            try:
                tts_res = await tts_task
                audio_url = tts_res.get("audio_url")
            except Exception:
                pass

        if not audio_url:
            tts_res = await tts_agent.synthesize(clean_response)
            audio_url = tts_res.get("audio_url")

        return {
            "type": "general_reply",
            "reply": clean_response,
            "audio_url": audio_url
        }

jarvis_orchestrator = JarvisOrchestrator()
