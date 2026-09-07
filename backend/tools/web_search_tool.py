import re
import json
import asyncio
import logging
import urllib.request
import urllib.parse
from typing import List, Dict, Any, Optional
from bs4 import BeautifulSoup

logger = logging.getLogger("WebSearchTool")


class WebSearchTool:
    """Provides real-time global web telemetry and factual intelligence for Jarvis."""

    def __init__(self):
        self.user_agent = (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/124.0.0.0 Safari/537.36"
        )

    def _extract_recent_entity(self, conversation_history: Optional[List[Dict[str, str]]]) -> Optional[str]:
        """Extract the most prominent named entity or topic from recent conversation history."""
        if not conversation_history:
            return None

        # Look backwards through previous messages (skipping the last user turn if it's the current one)
        history_to_scan = conversation_history[:-1] if len(conversation_history) > 1 else conversation_history
        stop_words = {
            'Sir', 'Boss', 'Chief Minister', 'Prime Minister', 'Tamil Nadu', 'India', 'Monday', 'Tuesday',
            'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday', 'January', 'February', 'March', 'April',
            'May', 'June', 'July', 'August', 'September', 'October', 'November', 'December', 'Jarvis'
        }
        for msg in reversed(history_to_scan[-4:]):
            content = msg.get("content", "")
            # Look for explicit name patterns like "C. Joseph Vijay", "Joseph Vijay", etc.
            names = re.findall(r'\b(?:[A-Z]\.\s*)?[A-Z][a-z]+(?:\s+[A-Z][a-z]+)+\b', content)
            for name in names:
                clean_name = name.strip()
                if clean_name not in stop_words and len(clean_name.split()) >= 1:
                    return clean_name
        return None

    def resolve_query_context(self, user_message: str, conversation_history: Optional[List[Dict[str, str]]] = None) -> str:
        """Contextualize ambiguous follow-up questions using recent conversation entity."""
        cleaned = self._clean_query(user_message)
        text = user_message.lower().strip()

        # Check if the query has pronouns or refers to the prior subject
        has_pronoun = bool(re.search(r'\b(he|she|it|they|his|him|her|their|this|that|himself|herself|the\s+actor|the\s+person|the\s+leader)\b', text))
        is_short_followup = len(text.split()) <= 6 and any(w in text for w in ['actor', 'actress', 'movie', 'film', 'movies', 'films', 'career', 'age', 'born', 'party', 'net worth', 'education', 'family', 'wife', 'husband', 'children', 'songs', 'awards', 'qualification'])

        if has_pronoun or is_short_followup:
            entity = self._extract_recent_entity(conversation_history)
            if entity:
                # Extract core subject terms
                core_terms = re.sub(r'\b(is|was|are|were|did|does|do|he|she|it|they|his|him|her|their|the|a|an)\b', '', text, flags=re.IGNORECASE).strip()
                return f"{entity} {core_terms or text}".strip()

        return cleaned

    def should_search(self, user_message: str, conversation_history: Optional[List[Dict[str, str]]] = None) -> bool:
        """Determines if the query requires real-time facts, current news, leadership telemetry, or web research."""
        text = user_message.lower().strip()

        # Exclude greetings and personal identity questions
        if re.match(r'^(hello|hi|hey|good (morning|afternoon|evening)|how are you|who are you|what is your name|what can you do)\b', text):
            return False

        # Exclude pure mathematical expressions or coding requests
        if re.match(r'^(write code|implement|create a function|calculate|solve|\d+\s*[\+\-\*\/])', text):
            return False

        # Exclude desktop app / OS launch actions
        if re.search(r'\b(open|launch|close|terminate|kill|restart)\s+(chrome|notepad|calculator|spotify|code|terminal|browser|vlc|cmd)\b', text):
            return False

        # Follow-up questions referencing a previous entity in conversation history
        if conversation_history and len(conversation_history) > 1:
            if re.search(r'\b(is|was|are|were|did|has|does)\s+(he|she|it|they|this|that)\b', text):
                return True
            if any(w in text for w in ['actor', 'actress', 'movie', 'movies', 'film', 'films', 'career', 'born', 'net worth', 'background', 'qualification', 'party', 'family', 'wife', 'husband']) and re.search(r'\b(he|his|him|she|her|they|their)\b', text):
                return True

        # 1. Explicit search commands
        if re.search(r'\b(search(\s+the\s+web)?|look\s+up|google|browse|find\s+out|fact\s*check|verify\s+online)\b', text):
            return True

        # 2. Real-time & temporal triggers
        if re.search(r'\b(current|currently|latest|recent|recently|today(?:\'s)?|now|trending|present|newest|upcoming|right\s+now|this\s+year)\b', text):
            return True

        # 3. Future / post-2023 timeline references
        if re.search(r'\b(202[4-9]|203[0-9])\b', text):
            return True

        # 4. Governance, Political & Leadership queries (Chief Minister, Prime Minister, President, Governor, etc.)
        if re.search(r'\b(chief\s+minister|cm\b|prime\s+minister|pm\b|president|governor|minister|mla|mp\b|mayor|chancellor|monarch|ruling\s+party|election|elections|cabinet|assembly|parliament|government|who\s+leads|who\s+won|who\s+is\s+in\s+power)\b', text):
            return True

        # 5. Question queries seeking factual answers about people, entities, or events
        if re.search(r'\b(who\s+is|who\s+was|who\s+are|who\s+were|who\s+holds|who\s+founded|who\s+won|who\s+created)\b', text) and not re.search(r'\bwho\s+(are\s+you|am\s+i)\b', text):
            return True

        # 6. News, events, status, scores, financial & cultural updates
        if re.search(r'\b(news|headlines?|updates?|scores?|results?|stock\s+price|net\s+worth|release\s+date|what\s+happened|what\s+is\s+the\s+status)\b', text):
            return True

        # 7. Biographical, career, or identity queries
        if re.search(r'\b(actor|actress|singer|director|filmography|career|born|education|qualification)\b', text):
            return True

        return False

    def _clean_query(self, text: str) -> str:
        """Strip conversational pleasantries to extract the raw search query."""
        cleaned = text.strip()
        cleaned = re.sub(r'^(?:jarvis|hey jarvis|please|can you|could you|kindly|search for|look up|search the web for|find out|google|tell me who is|tell me what is|tell me)\s*', '', cleaned, flags=re.IGNORECASE).strip()
        cleaned = re.sub(r'\s*(?:for me|please|right now|online)\??$', '', cleaned, flags=re.IGNORECASE).strip()
        return cleaned or text

    def _search_ddgs_sync(self, query: str, max_results: int = 4) -> List[Dict[str, str]]:
        """Query DuckDuckGo using official ddgs / duckduckgo_search library."""
        results = []
        try:
            from ddgs import DDGS
            with DDGS() as ddgs:
                raw_results = list(ddgs.text(query, max_results=max_results))
                for item in raw_results:
                    title = item.get("title", "").strip()
                    body = item.get("body", "").strip()
                    href = item.get("href", "").strip()
                    if title and body:
                        results.append({"title": title, "snippet": body, "url": href})
            if results:
                return results
        except ImportError:
            pass
        except Exception as e:
            logger.debug(f"DDGS search attempt failed: {e}")

        try:
            from duckduckgo_search import DDGS as FallbackDDGS
            with FallbackDDGS() as ddgs:
                raw_results = list(ddgs.text(query, max_results=max_results))
                for item in raw_results:
                    title = item.get("title", "").strip()
                    body = item.get("body", "").strip()
                    href = item.get("href", "").strip()
                    if title and body:
                        results.append({"title": title, "snippet": body, "url": href})
        except Exception as e:
            logger.debug(f"duckduckgo_search fallback failed: {e}")

        return results

    def _search_ddg_html(self, query: str, max_results: int = 3) -> List[Dict[str, str]]:
        """Fallback to DuckDuckGo HTML scraping if DDGS package hits anti-bot."""
        results = []
        try:
            encoded = urllib.parse.quote(query)
            url = f"https://html.duckduckgo.com/html/?q={encoded}"
            req = urllib.request.Request(
                url,
                headers={
                    "User-Agent": self.user_agent,
                    "Accept-Language": "en-US,en;q=0.9"
                }
            )
            with urllib.request.urlopen(req, timeout=5) as resp:
                soup = BeautifulSoup(resp.read(), "html.parser")
                for item in soup.select(".web-result")[:max_results]:
                    title_elem = item.select_one(".result__title")
                    snippet_elem = item.select_one(".result__snippet")
                    url_elem = item.select_one(".result__url")
                    title = title_elem.get_text(strip=True) if title_elem else ""
                    snippet = snippet_elem.get_text(strip=True) if snippet_elem else ""
                    link = url_elem.get_text(strip=True) if url_elem else ""
                    if title and snippet:
                        results.append({"title": title, "snippet": snippet, "url": link})
        except Exception as e:
            logger.debug(f"DDG HTML scraper fallback failed: {e}")

        return results

    def _search_wikipedia(self, query: str, max_results: int = 2) -> List[Dict[str, str]]:
        """Direct encyclopedia fallback for entity and biographical queries."""
        results = []
        try:
            encoded = urllib.parse.quote(query)
            search_url = (
                f"https://en.wikipedia.org/w/api.php?action=query&list=search&srsearch={encoded}"
                f"&format=json&utf8=1&srlimit={max_results}"
            )
            req = urllib.request.Request(search_url, headers={"User-Agent": "JARVIS-Assistant/2.0 (Personal AI)"})
            with urllib.request.urlopen(req, timeout=4) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                search_items = data.get("query", {}).get("search", [])

                for item in search_items:
                    title = item.get("title", "")
                    raw_snippet = item.get("snippet", "")
                    clean_snippet = re.sub(r'<[^>]+>', '', raw_snippet).strip()
                    if title and clean_snippet:
                        page_url = f"https://en.wikipedia.org/wiki/{urllib.parse.quote(title.replace(' ', '_'))}"
                        results.append({"title": f"{title} (Wikipedia)", "snippet": clean_snippet, "url": page_url})
        except Exception as e:
            logger.debug(f"Wikipedia API lookup failed: {e}")

        return results

    async def search_web(self, query: str, conversation_history: Optional[List[Dict[str, str]]] = None, max_results: int = 4) -> str:
        """Asynchronously executes web search across multi-tiered fallbacks and returns formatted context."""
        cleaned_query = self.resolve_query_context(query, conversation_history)
        logger.info(f"Querying global web intelligence for: '{cleaned_query}' (raw: '{query}')")

        results: List[Dict[str, str]] = []

        # Tier 1: Fast ddgs package in thread pool
        try:
            results = await asyncio.wait_for(
                asyncio.to_thread(self._search_ddgs_sync, cleaned_query, max_results),
                timeout=5.0
            )
        except asyncio.TimeoutError:
            logger.warning("DDGS search timed out after 5 seconds")
        except Exception as e:
            logger.warning(f"Error during DDGS search: {e}")

        # Tier 2: DuckDuckGo HTML scrape if no results
        if not results:
            try:
                results = await asyncio.wait_for(
                    asyncio.to_thread(self._search_ddg_html, cleaned_query, max_results),
                    timeout=4.0
                )
            except Exception as e:
                logger.debug(f"DDG HTML attempt note: {e}")

        # Tier 3: Wikipedia API for entity lookups
        if not results:
            try:
                results = await asyncio.wait_for(
                    asyncio.to_thread(self._search_wikipedia, cleaned_query, max_results),
                    timeout=3.0
                )
            except Exception as e:
                logger.debug(f"Wikipedia attempt note: {e}")

        if not results:
            return ""

        formatted_blocks = []
        for i, item in enumerate(results[:max_results], 1):
            title = item.get("title", "Untitled").strip()
            snippet = item.get("snippet", "").strip()
            source = item.get("url", "").strip()
            formatted_blocks.append(f"[{i}] {title}\nSummary: {snippet}\nSource: {source}")

        return "\n\n".join(formatted_blocks)


web_search_tool = WebSearchTool()
