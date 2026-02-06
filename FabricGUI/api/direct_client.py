"""
Direct AI API Client

Calls AI providers directly without needing Fabric server.
Supports Google Gemini, OpenAI, and Anthropic.
"""

import httpx
import json
from typing import Iterator, Optional
from dataclasses import dataclass


@dataclass
class AIConfig:
    """Configuration for an AI provider."""
    api_key: str
    model: str
    temperature: float = 0.7
    top_p: float = 0.9


class DirectAIClient:
    """
    Direct API client for major AI providers.
    No Fabric server required.
    """
    
    # Available models by vendor (Updated for 2026)
    MODELS = {
        "Google Gemini": [
            # Gemini 3 (Latest - 2026)
            "gemini-3-pro-preview",
            "gemini-3-flash-preview",
            # Gemini 2.5 (Stable)
            "gemini-2.5-pro",
            "gemini-2.5-flash",
            "gemini-2.5-flash-lite",
            # Gemini 2.0 (Legacy)
            "gemini-2.0-flash",
            "gemini-2.0-flash-lite",
        ],
        "OpenAI": [
            "gpt-4o",
            "gpt-4o-mini", 
            "gpt-4-turbo",
            "gpt-4",
            "gpt-3.5-turbo",
            "o1-preview",
            "o1-mini",
        ],
        "Anthropic": [
            "claude-3-5-sonnet-20241022",
            "claude-3-5-haiku-20241022",
            "claude-3-opus-20240229",
            "claude-3-sonnet-20240229",
        ],
        "Ollama (Local)": [
            "llama3.2",
            "llama3.1",
            "mistral",
            "codellama",
            "phi3",
            "qwen2.5",
        ],
    }
    
    def __init__(self):
        self.timeout = httpx.Timeout(30.0, read=300.0)
    
    def chat(
        self,
        vendor: str,
        model: str,
        api_key: str,
        system_prompt: str,
        user_input: str,
        temperature: float = 0.7,
        top_p: float = 0.9,
    ) -> Iterator[str]:
        """
        Send a chat request and yield response chunks.
        
        Args:
            vendor: AI provider name
            model: Model name
            api_key: API key for the provider
            system_prompt: System prompt (pattern content)
            user_input: User's input text
            temperature: Randomness (0-1)
            top_p: Nucleus sampling (0-1)
            
        Yields:
            Response text chunks
        """
        if vendor == "Google Gemini":
            yield from self._call_gemini(model, api_key, system_prompt, user_input, temperature, top_p)
        elif vendor == "OpenAI":
            yield from self._call_openai(model, api_key, system_prompt, user_input, temperature, top_p)
        elif vendor == "Anthropic":
            yield from self._call_anthropic(model, api_key, system_prompt, user_input, temperature, top_p)
        elif vendor == "Ollama (Local)":
            yield from self._call_ollama(model, system_prompt, user_input, temperature, top_p)
        else:
            raise ValueError(f"Unknown vendor: {vendor}")
    
    def _call_gemini(
        self,
        model: str,
        api_key: str,
        system_prompt: str,
        user_input: str,
        temperature: float,
        top_p: float,
    ) -> Iterator[str]:
        """Call Google Gemini API with proper streaming."""
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:streamGenerateContent"
        
        payload = {
            "contents": [
                {"role": "user", "parts": [{"text": user_input}]}
            ],
            "systemInstruction": {
                "parts": [{"text": system_prompt}]
            },
            "generationConfig": {
                "temperature": temperature,
                "topP": top_p,
            }
        }
        
        with httpx.Client(timeout=self.timeout) as client:
            with client.stream(
                "POST",
                url,
                params={"key": api_key, "alt": "sse"},
                json=payload,
                headers={"Content-Type": "application/json"}
            ) as response:
                response.raise_for_status()
                
                for line in response.iter_lines():
                    # SSE format: data: {json}
                    if line.startswith("data: "):
                        try:
                            data = line[6:]
                            if data.strip():
                                obj = json.loads(data)
                                # Extract text from response
                                if "candidates" in obj:
                                    for candidate in obj["candidates"]:
                                        if "content" in candidate:
                                            for part in candidate["content"].get("parts", []):
                                                if "text" in part:
                                                    yield part["text"]
                        except json.JSONDecodeError:
                            pass
                    elif line.strip() and not line.startswith(":"):
                        # Try parsing as raw JSON (non-SSE fallback)
                        try:
                            obj = json.loads(line)
                            if "candidates" in obj:
                                for candidate in obj["candidates"]:
                                    if "content" in candidate:
                                        for part in candidate["content"].get("parts", []):
                                            if "text" in part:
                                                yield part["text"]
                        except json.JSONDecodeError:
                            pass
    
    def _call_openai(
        self,
        model: str,
        api_key: str,
        system_prompt: str,
        user_input: str,
        temperature: float,
        top_p: float,
    ) -> Iterator[str]:
        """Call OpenAI API."""
        url = "https://api.openai.com/v1/chat/completions"
        
        payload = {
            "model": model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_input}
            ],
            "temperature": temperature,
            "top_p": top_p,
            "stream": True
        }
        
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        
        with httpx.Client(timeout=self.timeout) as client:
            with client.stream("POST", url, json=payload, headers=headers) as response:
                response.raise_for_status()
                for line in response.iter_lines():
                    if line.startswith("data: "):
                        data = line[6:]
                        if data == "[DONE]":
                            break
                        try:
                            obj = json.loads(data)
                            if "choices" in obj and obj["choices"]:
                                delta = obj["choices"][0].get("delta", {})
                                if "content" in delta:
                                    yield delta["content"]
                        except json.JSONDecodeError:
                            pass
    
    def _call_anthropic(
        self,
        model: str,
        api_key: str,
        system_prompt: str,
        user_input: str,
        temperature: float,
        top_p: float,
    ) -> Iterator[str]:
        """Call Anthropic API."""
        url = "https://api.anthropic.com/v1/messages"
        
        payload = {
            "model": model,
            "max_tokens": 8192,
            "system": system_prompt,
            "messages": [
                {"role": "user", "content": user_input}
            ],
            "temperature": temperature,
            "top_p": top_p,
            "stream": True
        }
        
        headers = {
            "x-api-key": api_key,
            "anthropic-version": "2023-06-01",
            "Content-Type": "application/json"
        }
        
        with httpx.Client(timeout=self.timeout) as client:
            with client.stream("POST", url, json=payload, headers=headers) as response:
                response.raise_for_status()
                for line in response.iter_lines():
                    if line.startswith("data: "):
                        try:
                            obj = json.loads(line[6:])
                            if obj.get("type") == "content_block_delta":
                                delta = obj.get("delta", {})
                                if "text" in delta:
                                    yield delta["text"]
                        except json.JSONDecodeError:
                            pass
    
    def _call_ollama(
        self,
        model: str,
        system_prompt: str,
        user_input: str,
        temperature: float,
        top_p: float,
    ) -> Iterator[str]:
        """Call local Ollama API."""
        url = "http://localhost:11434/api/chat"
        
        payload = {
            "model": model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_input}
            ],
            "options": {
                "temperature": temperature,
                "top_p": top_p,
            },
            "stream": True
        }
        
        with httpx.Client(timeout=self.timeout) as client:
            with client.stream("POST", url, json=payload) as response:
                response.raise_for_status()
                for line in response.iter_lines():
                    if line:
                        try:
                            obj = json.loads(line)
                            if "message" in obj and "content" in obj["message"]:
                                yield obj["message"]["content"]
                        except json.JSONDecodeError:
                            pass
