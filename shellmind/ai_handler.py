"""
OpenAI API handler for command generation
"""
import os
import json
import openai
from typing import Dict, List
from .utils import is_destructive_command

class AIHandlerError(Exception):
    pass

def generate_command(query: str, os_type: str, explain: bool = False, 
                    model: str = "gpt-4o-mini", base_url: str = "https://api.openai.com/v1",
                    api_key: str = None) -> Dict:
    """
    Generate terminal command from natural language query
    Returns: {
        'command': str,
        'explanation': List[str],
        'warning': str
    }
    """
    try:
        # Initialize client
        client = openai.OpenAI(
            base_url=base_url,
            api_key=api_key if api_key else "no-key-required",
        )
        
        prompt = f"""You are a {os_type} terminal expert. Convert this query to a command:
        
        Query: {query}
        
        Respond ONLY with JSON containing:
        - "command": valid terminal command (prioritize built-in tools)
        - "explanation": array of flag explanations (if {str(explain).lower()})
        - "warning": safety notice if dangerous (otherwise empty)
        
        Example response:
        {{"command": "rm -rf /tmp/*", "explanation": ["-r: recursive delete", "-f: force"], "warning": "destructive operation"}}
        {{"command": "chmod -R 777 /var/www", "explanation": ["-R: recursive permission change", "777: full permissions for all users"], "warning": "This command gives full access to all users, which could lead to security vulnerabilities"}}
        
        Important: Your response must be valid JSON. Do not include any additional text or explanations outside the JSON structure.
        
        Safety Guidelines:
        - Always warn about commands that delete, overwrite, or modify files or directories.
        - Be cautious with commands that affect system settings or processes.
        - Flag commands that could lead to data loss, security vulnerabilities, or system instability.
        """
        
        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": """You are a Linux terminal expert. Your role is to:
- Convert natural language queries into accurate and efficient terminal commands.
- Prioritize built-in tools and standard utilities over custom scripts.
- Provide clear explanations for command flags and options when requested.
- Identify and warn about potentially destructive or dangerous commands.
- Always respond with valid JSON in the specified format.

Safety Guidelines:
- Flag commands that delete, overwrite, or modify files or directories.
- Be cautious with commands that affect system settings or processes.
- Warn about commands that could lead to data loss, security vulnerabilities, or system instability.

Output Format:
- Respond ONLY with JSON containing:
  - "command": The terminal command to execute.
  - "explanation": Array of flag explanations (if requested).
  - "warning": Safety notice if dangerous (otherwise empty).
"""},
                {"role": "user", "content": prompt}
            ],
            temperature=0.2,
            max_tokens=200,
            response_format={"type": "json_object"}
        )
        
        # Extract the response content
        response_content = response.choices[0].message.content
        
        # Parse the response content as JSON
        try:
            result = json.loads(response_content)
        except json.JSONDecodeError:
            # If the response isn't valid JSON, treat it as a command
            result = {
                "command": response_content.strip(),
                "explanation": [],
                "warning": ""
            }
        
        return result
        
    except Exception as e:
        raise AIHandlerError(f"AI API Error: {str(e)}")
