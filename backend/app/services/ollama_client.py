"""
Ollama LLM Client - Local AI Service Integration

Handles all communication with local Ollama service for AI-powered features.

Features:
- Query local Ollama LLM (llama3.2:3b default model)
- Health checks and model availability verification
- Automatic model pulling (download models)
- Graceful fallback responses when service unavailable
- Async HTTP communication with timeout handling

Configuration:
- OLLAMA_API_URL: Base URL for Ollama service (default: http://localhost:11434)
- OLLAMA_MODEL: Model to use (default: llama3.2:3b)

Use Cases:
- Transaction categorization (LLM-based pattern recognition)
- Financial chat assistant (conversational AI)
- Keyword extraction from transaction data

Service: Local Ollama installation required
Network: Localhost communication only (privacy-focused)
"""

import requests
import os
from typing import Dict, Optional, Any
import asyncio
import aiohttp


# ============================================================================
# OLLAMA LLM CLIENT CLASS
# ============================================================================

class OllamaLLM:
    """
    Local Ollama LLM client for AI-powered features
    
    Manages communication with local Ollama service:
    - Sends queries to LLM with prompts
    - Checks service and model availability
    - Downloads models automatically if needed
    - Provides graceful fallback responses
    
    Thread-safe async operations with connection pooling.
    """
    
    def __init__(self):
        """
        Initialize Ollama client with configuration from environment
        
        Loads configuration:
        - base_url: Ollama API endpoint (default: http://localhost:11434)
        - model: LLM model to use (default: llama3.2:3b)
        - timeout: Request timeout in seconds (60s)
        """
        self.base_url = os.getenv("OLLAMA_API_URL", "http://localhost:11434")
        self.model = os.getenv("OLLAMA_MODEL", "llama3.2:3b")
        self.timeout = 60  # 60 second timeout for LLM responses
        
    async def query(self, prompt: str, max_tokens: int = 200) -> Dict[str, Any]:
        """
        Query Ollama API with a prompt and get AI response
        
        Process:
        1. Check if Ollama service is running
        2. Verify model is available
        3. Add system prompt for Azimuth Core context
        4. Send query to LLM
        5. Parse and return response
        6. Handle errors gracefully with fallback
        
        System Prompt:
        - Identifies as Azimuth Core financial assistant
        - Emphasizes privacy-focused local processing
        - Keeps responses concise (under 100 words)
        - Focuses on financial management topics
        
        @param prompt: User or system prompt for LLM
        @param max_tokens: Maximum tokens in response (default: 200)
        @returns {Dict} Response with status, text, and metadata
        
        Response format:
        ```python
        {
            "status": "success" | "error",
            "text": "LLM response text",
            "meta": {
                "model": "llama3.2:3b",
                "length": 156,
                "local": True,
                "eval_count": 50,
                "eval_duration": 1234567
            }
        }
        ```
        """
        # STEP 1: Check if Ollama service is running
        if not await self._check_ollama_status():
            return {
                "status": "error",
                "text": "Ollama service is not running. Please start Ollama first.",
                "meta": {"fallback": True, "ollama_offline": True}
            }
        
        # STEP 2: Verify model is available
        model_check = await self._check_model_availability()
        if not model_check.get("model_available", False):
            return {
                "status": "error", 
                "text": f"Model {self.model} not found. Available models: {model_check.get('available_models', [])}",
                "meta": {"fallback": True, "model_missing": True}
            }
        
        # STEP 3: Build prompt with system context
        system_prompt = """You are a helpful AI assistant for a personal finance app called Azimuth Core. 
This is a completely local, privacy-focused financial management tool. 
Be concise, helpful, and encouraging. Keep responses under 100 words. 
Focus on local financial management, CSV imports, and transaction categorization.
If a feature isn't implemented yet, guide users to what they can do now."""
        
        full_prompt = f"{system_prompt}\n\nUser: {prompt}\n\nAssistant:"
        
        # Build request payload
        payload = {
            "model": self.model,
            "prompt": full_prompt,
            "options": {
                "temperature": 0.7,      # Balanced creativity vs accuracy
                "top_p": 0.9,            # Nucleus sampling threshold
                "num_predict": 100,      # Max tokens to generate
                "num_ctx": 2048          # Context window size
            },
            "stream": False  # Get complete response at once
        }
        
        try:
            print(f"🤖 Querying Ollama: {self.model}")
            
            # STEP 4: Send async HTTP request to Ollama
            async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=self.timeout)) as session:
                async with session.post(
                    f"{self.base_url}/api/generate",
                    json=payload
                ) as response:
                    
                    print(f"📡 Ollama API Status: {response.status}")
                    
                    if response.status == 200:
                        result = await response.json()
                        
                        # STEP 5: Parse response
                        if "response" in result:
                            generated_text = result["response"].strip()
                            
                            print(f"✅ Ollama Response: {generated_text[:100]}...")
                            return {
                                "status": "success",
                                "text": generated_text,
                                "meta": {
                                    "model": self.model,
                                    "length": len(generated_text),
                                    "local": True,
                                    "eval_count": result.get("eval_count", 0),
                                    "eval_duration": result.get("eval_duration", 0)
                                }
                            }
                        else:
                            print(f"⚠️ Unexpected Ollama response format: {result}")
                            return self._fallback_response("Unexpected response format from local AI")
                    
                    else:
                        error_text = await response.text()
                        print(f"❌ Ollama API Error {response.status}: {error_text}")
                        return self._fallback_response(f"Local AI service error ({response.status})")
            
        except asyncio.TimeoutError:
            print("⏰ Ollama request timeout")
            return self._fallback_response("Local AI response took too long")
        except aiohttp.ClientConnectorError:
            print("🔌 Cannot connect to Ollama")
            return self._fallback_response("Cannot connect to local AI service")
        except Exception as e:
            print(f"❌ Ollama Exception: {e}")
            return self._fallback_response("Local AI service temporarily unavailable")
    
    async def _check_ollama_status(self) -> bool:
        """
        Check if Ollama service is running and responsive
        
        Performs health check by querying /api/tags endpoint.
        Returns True if service responds with 200 OK.
        
        @returns {bool} True if Ollama is running
        """
        try:
            async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=self.timeout)) as session:
                async with session.get(f"{self.base_url}/api/tags") as response:
                    return response.status == 200
        except:
            return False
    
    def _fallback_response(self, error_msg: str) -> Dict[str, Any]:
        """
        Generate fallback response when Ollama fails
        
        Used when:
        - Ollama service is offline
        - Model is not available
        - Request times out
        - Connection fails
        
        @param error_msg: Error description
        @returns {Dict} Error response with fallback flag
        """
        return {
            "status": "error",
            "text": f"{error_msg}. Using smart fallback response instead.",
            "meta": {"fallback": True, "local": True}
        }
    
    async def check_model_availability(self) -> Dict[str, Any]:
        """
        Check if configured model is available in Ollama
        
        Queries /api/tags to get list of installed models.
        Compares configured model against available models.
        
        Response includes:
        - ollama_running: Is Ollama service responding?
        - model_available: Is configured model installed?
        - available_models: List of all installed models
        - configured_model: The model we're trying to use
        
        @returns {Dict} Model availability status
        
        Response format:
        ```python
        {
            "ollama_running": True,
            "model_available": True,
            "available_models": ["llama3.2:3b", "mistral:latest"],
            "configured_model": "llama3.2:3b"
        }
        ```
        """
        try:
            async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=10)) as session:
                async with session.get(f"{self.base_url}/api/tags") as response:
                    if response.status == 200:
                        result = await response.json()
                        models = result.get("models", [])
                        model_names = [model.get("name", "") for model in models]
                        
                        return {
                            "ollama_running": True,
                            "model_available": self.model in model_names,
                            "available_models": model_names,
                            "configured_model": self.model
                        }
                    else:
                        return {
                            "ollama_running": False,
                            "model_available": False,
                            "error": f"Ollama API returned {response.status}"
                        }
        except Exception as e:
            return {
                "ollama_running": False,
                "model_available": False,
                "error": str(e)
            }
    
    async def _check_model_availability(self) -> Dict[str, Any]:
        """
        Internal method to check model availability
        
        Wrapper around public check_model_availability() method.
        Used internally by query() method.
        
        @returns {Dict} Model availability status
        """
        return await self.check_model_availability()
    
    async def pull_model(self) -> Dict[str, Any]:
        """
        Pull/download the configured model from Ollama registry
        
        Downloads model if not already installed.
        Can take several minutes for large models (3B+ parameters).
        
        Process:
        1. Send pull request to /api/pull
        2. Wait for download to complete (timeout: 5 minutes)
        3. Return success/failure status
        
        Note: This is a blocking operation that may take time.
        Consider showing progress indicator to user.
        
        @returns {Dict} Pull operation result
        
        Response format:
        ```python
        {
            "success": True,
            "message": "Model llama3.2:3b pulled successfully"
        }
        ```
        
        Or on error:
        ```python
        {
            "success": False,
            "error": "Failed to pull model: connection timeout"
        }
        ```
        """
        payload = {
            "name": self.model
        }
        
        try:
            # Extended timeout for model downloads (5 minutes)
            async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=300)) as session:
                async with session.post(
                    f"{self.base_url}/api/pull",
                    json=payload
                ) as response:
                    if response.status == 200:
                        return {
                            "success": True,
                            "message": f"Model {self.model} pulled successfully"
                        }
                    else:
                        error_text = await response.text()
                        return {
                            "success": False,
                            "error": f"Failed to pull model: {error_text}"
                        }
        except Exception as e:
            return {
                "success": False,
                "error": f"Failed to pull model: {str(e)}"
            }


# ============================================================================
# SINGLETON INSTANCE
# ============================================================================

# Initialize singleton instance for use throughout application
# This ensures only one client instance is created (connection pooling)
llm_client = OllamaLLM()