"""
Fabric REST API Client

Provides async interface to Fabric's REST API endpoints for patterns,
models, chat completions, and YouTube transcripts.
"""

import httpx
from typing import AsyncIterator, Optional
import json


class FabricClient:
    """
    Async client for the Fabric REST API.
    
    Usage:
        client = FabricClient("http://localhost:8080")
        if await client.is_connected():
            patterns = await client.get_patterns()
    """
    
    def __init__(self, base_url: str = "http://localhost:8080", api_key: str = None):
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self._client: Optional[httpx.AsyncClient] = None
    
    def _get_headers(self) -> dict:
        """Build request headers including API key if set."""
        headers = {"Content-Type": "application/json"}
        if self.api_key:
            headers["X-API-Key"] = self.api_key
        return headers
    
    async def _get_client(self) -> httpx.AsyncClient:
        """Get or create the async HTTP client."""
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(
                base_url=self.base_url,
                headers=self._get_headers(),
                timeout=httpx.Timeout(30.0, read=120.0)
            )
        return self._client
    
    async def close(self):
        """Close the HTTP client."""
        if self._client and not self._client.is_closed:
            await self._client.aclose()
            self._client = None
    
    async def is_connected(self) -> bool:
        """Check if the Fabric server is reachable."""
        try:
            client = await self._get_client()
            response = await client.get("/patterns/names")
            return response.status_code == 200
        except Exception:
            return False
    
    async def get_patterns(self) -> list[str]:
        """
        Get list of all available pattern names.
        
        Returns:
            List of pattern names (e.g., ["summarize", "extract_wisdom", ...])
        """
        client = await self._get_client()
        response = await client.get("/patterns/names")
        response.raise_for_status()
        return response.json()
    
    async def get_pattern_content(self, name: str) -> str:
        """
        Get the content of a specific pattern.
        
        Args:
            name: Pattern name (e.g., "summarize")
            
        Returns:
            Pattern system prompt content
        """
        client = await self._get_client()
        response = await client.get(f"/patterns/{name}")
        response.raise_for_status()
        return response.text
    
    async def get_models(self) -> dict:
        """
        Get available AI models grouped by vendor.
        
        Returns:
            Dict with 'models' (flat list) and 'vendors' (dict by vendor name)
        """
        client = await self._get_client()
        response = await client.get("/models/names")
        response.raise_for_status()
        return response.json()
    
    async def get_strategies(self) -> list[dict]:
        """
        Get available prompting strategies.
        
        Returns:
            List of strategy dicts with 'name', 'description', 'prompt'
        """
        client = await self._get_client()
        response = await client.get("/strategies")
        response.raise_for_status()
        return response.json()
    
    async def get_contexts(self) -> list[str]:
        """Get list of available context names."""
        client = await self._get_client()
        response = await client.get("/contexts/names")
        response.raise_for_status()
        return response.json()
    
    async def get_sessions(self) -> list[str]:
        """Get list of available session names."""
        client = await self._get_client()
        response = await client.get("/sessions/names")
        response.raise_for_status()
        return response.json()
    
    async def get_youtube_transcript(self, url: str, timestamps: bool = False) -> dict:
        """
        Extract transcript from a YouTube video.
        
        Args:
            url: YouTube video URL
            timestamps: Whether to include timestamps
            
        Returns:
            Dict with 'videoId', 'title', 'description', 'transcript'
        """
        client = await self._get_client()
        response = await client.post(
            "/youtube/transcript",
            json={"url": url, "timestamps": timestamps}
        )
        response.raise_for_status()
        return response.json()
    
    async def chat_stream(
        self,
        user_input: str,
        vendor: str,
        model: str,
        pattern_name: str = "",
        context_name: str = "",
        strategy_name: str = "",
        variables: dict = None,
        temperature: float = 0.7,
        top_p: float = 0.9,
        frequency_penalty: float = 0.0,
        presence_penalty: float = 0.0,
        thinking: int = 0
    ) -> AsyncIterator[dict]:
        """
        Execute a chat completion with streaming response.
        
        Args:
            user_input: The user's message/content to process
            vendor: AI provider (e.g., "openai", "anthropic")
            model: Model name (e.g., "gpt-4o")
            pattern_name: Optional pattern to apply
            context_name: Optional context to prepend
            strategy_name: Optional strategy (e.g., "cot")
            variables: Optional variable substitutions
            temperature: Randomness (0.0-1.0)
            top_p: Nucleus sampling (0.0-1.0)
            frequency_penalty: Reduce repetition
            presence_penalty: Encourage new topics
            thinking: Reasoning level (0=off)
            
        Yields:
            Dict events with 'type' (content/error/complete) and 'content'
        """
        payload = {
            "prompts": [{
                "userInput": user_input,
                "vendor": vendor,
                "model": model,
                "patternName": pattern_name,
                "contextName": context_name,
                "strategyName": strategy_name,
                "variables": variables or {}
            }],
            "temperature": temperature,
            "topP": top_p,
            "frequencyPenalty": frequency_penalty,
            "presencePenalty": presence_penalty,
            "thinking": thinking
        }
        
        async with httpx.AsyncClient(
            base_url=self.base_url,
            headers=self._get_headers(),
            timeout=httpx.Timeout(30.0, read=300.0)
        ) as client:
            async with client.stream("POST", "/chat", json=payload) as response:
                response.raise_for_status()
                async for line in response.aiter_lines():
                    if line.strip():
                        try:
                            event = json.loads(line)
                            yield event
                        except json.JSONDecodeError:
                            # Handle non-JSON lines (could be SSE format)
                            if line.startswith("data:"):
                                try:
                                    data = json.loads(line[5:].strip())
                                    yield data
                                except json.JSONDecodeError:
                                    pass


class SyncFabricClient:
    """
    Synchronous wrapper for FabricClient for use in Tkinter callbacks.
    Uses httpx synchronous client for simpler integration.
    """
    
    def __init__(self, base_url: str = "http://localhost:8080", api_key: str = None):
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
    
    def _get_headers(self) -> dict:
        headers = {"Content-Type": "application/json"}
        if self.api_key:
            headers["X-API-Key"] = self.api_key
        return headers
    
    def is_connected(self) -> bool:
        """Check if the Fabric server is reachable."""
        try:
            with httpx.Client(timeout=5.0) as client:
                response = client.get(
                    f"{self.base_url}/patterns/names",
                    headers=self._get_headers()
                )
                return response.status_code == 200
        except Exception:
            return False
    
    def get_patterns(self) -> list[str]:
        """Get list of all available pattern names."""
        with httpx.Client(timeout=30.0) as client:
            response = client.get(
                f"{self.base_url}/patterns/names",
                headers=self._get_headers()
            )
            response.raise_for_status()
            return response.json()
    
    def get_pattern_content(self, name: str) -> str:
        """Get the content of a specific pattern."""
        with httpx.Client(timeout=30.0) as client:
            response = client.get(
                f"{self.base_url}/patterns/{name}",
                headers=self._get_headers()
            )
            response.raise_for_status()
            return response.text
    
    def get_models(self) -> dict:
        """Get available AI models grouped by vendor."""
        with httpx.Client(timeout=30.0) as client:
            response = client.get(
                f"{self.base_url}/models/names",
                headers=self._get_headers()
            )
            response.raise_for_status()
            return response.json()
    
    def get_strategies(self) -> list[dict]:
        """Get available prompting strategies."""
        with httpx.Client(timeout=30.0) as client:
            response = client.get(
                f"{self.base_url}/strategies",
                headers=self._get_headers()
            )
            response.raise_for_status()
            data = response.json()
            # Handle if response is list or needs parsing
            return data if isinstance(data, list) else []
    
    def get_contexts(self) -> list[str]:
        """Get list of available context names."""
        with httpx.Client(timeout=30.0) as client:
            response = client.get(
                f"{self.base_url}/contexts/names",
                headers=self._get_headers()
            )
            response.raise_for_status()
            return response.json()
    
    def get_youtube_transcript(self, url: str, timestamps: bool = False) -> dict:
        """Extract transcript from a YouTube video."""
        with httpx.Client(timeout=120.0) as client:
            response = client.post(
                f"{self.base_url}/youtube/transcript",
                headers=self._get_headers(),
                json={"url": url, "timestamps": timestamps}
            )
            response.raise_for_status()
            return response.json()
    
    def chat(
        self,
        user_input: str,
        vendor: str,
        model: str,
        pattern_name: str = "",
        context_name: str = "",
        strategy_name: str = "",
        variables: dict = None,
        temperature: float = 0.7,
        top_p: float = 0.9,
    ) -> str:
        """
        Execute a chat completion and return full response.
        For streaming, use chat_stream instead.
        """
        payload = {
            "prompts": [{
                "userInput": user_input,
                "vendor": vendor,
                "model": model,
                "patternName": pattern_name,
                "contextName": context_name,
                "strategyName": strategy_name,
                "variables": variables or {}
            }],
            "temperature": temperature,
            "topP": top_p,
        }
        
        with httpx.Client(timeout=httpx.Timeout(30.0, read=300.0)) as client:
            response = client.post(
                f"{self.base_url}/chat",
                headers=self._get_headers(),
                json=payload
            )
            response.raise_for_status()
            
            # Parse SSE response and combine content
            full_content = []
            for line in response.text.split("\n"):
                if line.strip():
                    try:
                        event = json.loads(line)
                        if event.get("type") == "content":
                            full_content.append(event.get("content", ""))
                    except json.JSONDecodeError:
                        if line.startswith("data:"):
                            try:
                                data = json.loads(line[5:].strip())
                                if data.get("type") == "content":
                                    full_content.append(data.get("content", ""))
                            except json.JSONDecodeError:
                                pass
            
            return "".join(full_content)
    
    def chat_stream_iter(
        self,
        user_input: str,
        vendor: str,
        model: str,
        pattern_name: str = "",
        context_name: str = "",
        strategy_name: str = "",
        variables: dict = None,
        temperature: float = 0.7,
        top_p: float = 0.9,
    ):
        """
        Execute a chat completion with streaming.
        Returns an iterator that yields content chunks.
        """
        payload = {
            "prompts": [{
                "userInput": user_input,
                "vendor": vendor,
                "model": model,
                "patternName": pattern_name,
                "contextName": context_name,
                "strategyName": strategy_name,
                "variables": variables or {}
            }],
            "temperature": temperature,
            "topP": top_p,
        }
        
        with httpx.Client(timeout=httpx.Timeout(30.0, read=300.0)) as client:
            with client.stream(
                "POST",
                f"{self.base_url}/chat",
                headers=self._get_headers(),
                json=payload
            ) as response:
                response.raise_for_status()
                for line in response.iter_lines():
                    if line.strip():
                        try:
                            event = json.loads(line)
                            yield event
                        except json.JSONDecodeError:
                            if line.startswith("data:"):
                                try:
                                    data = json.loads(line[5:].strip())
                                    yield data
                                except json.JSONDecodeError:
                                    pass
