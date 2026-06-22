import os
import json
import logging
from typing import Dict, List, Any, Tuple
import google.generativeai as genai
from pydantic import BaseModel, Field

from fastapi import HTTPException
from app.core.config import settings

logger = logging.getLogger("app.ai_engine")

class FindingSchema(BaseModel):
    severity: str # "high", "medium", "low"
    file: str
    line: int
    category: str # "security", "bug", "performance", "code_smell"
    message: str
    suggestion: str

class AnalysisResultSchema(BaseModel):
    score_quality: int
    score_security: int
    score_performance: int
    score_maintainability: int
    findings: List[FindingSchema]
    markdown_report: str

class AIEngineService:
    SUPPORTED_EXTENSIONS = {
        '.py': 'Python',
        '.java': 'Java',
        '.cpp': 'C++',
        '.cc': 'C++',
        '.cxx': 'C++',
        '.h': 'C/C++ Header',
        '.hpp': 'C++ Header',
        '.js': 'JavaScript',
        '.jsx': 'JavaScript React',
        '.ts': 'TypeScript',
        '.tsx': 'TypeScript React',
        '.go': 'Go'
    }

    IGNORE_DIRS = {
        'node_modules', 'venv', '.venv', 'env', '.git', '__pycache__',
        '.idea', '.vscode', 'build', 'dist', 'out', 'target'
    }

    @classmethod
    def _scan_repository_files(cls, base_dir: str) -> List[Tuple[str, str, str]]:
        """Scans directory and returns list of (relative_path, language, content)."""
        scanned_files = []
        base_dir_abs = os.path.abspath(base_dir)

        for root, dirs, files in os.walk(base_dir_abs):
            # Prune directory search
            dirs[:] = [d for d in dirs if d not in cls.IGNORE_DIRS]

            for file in files:
                ext = os.path.splitext(file)[1].lower()
                if ext in cls.SUPPORTED_EXTENSIONS:
                    full_path = os.path.join(root, file)
                    rel_path = os.path.relpath(full_path, base_dir_abs)
                    
                    # Read file content safely
                    try:
                        with open(full_path, 'r', encoding='utf-8', errors='ignore') as f:
                            content = f.read(20000) # Read max 20KB per file to avoid huge payloads
                            scanned_files.append((rel_path, cls.SUPPORTED_EXTENSIONS[ext], content))
                    except Exception as e:
                        logger.warning(f"Failed to read file {full_path}: {str(e)}")

        return scanned_files

    @classmethod
    async def analyze_codebase(cls, base_dir: str) -> Dict[str, Any]:
        """Runs Gemini analysis on files found in base_dir."""
        files_data = cls._scan_repository_files(base_dir)
        if not files_data:
            return {
                "score_quality": 100,
                "score_security": 100,
                "score_performance": 100,
                "score_maintainability": 100,
                "findings": [],
                "markdown_report": "# Code Review Report\n\nNo supported source code files were found in the uploaded directory. Supported languages include Python, Java, C++, JavaScript, TypeScript, and Go."
            }

        # Build analysis context
        code_context = ""
        for rel_path, lang, content in files_data[:40]: # limit to first 40 files to fit prompt window comfortably
            code_context += f"\n\n--- File: {rel_path} (Language: {lang}) ---\n"
            code_context += content

        # Check API key
        api_key = settings.GEMINI_API_KEY
        if not api_key:
            # Fallback mock engine if key is not provided (allowing local running out of the box)
            logger.warning("GEMINI_API_KEY not configured. Returning mock analysis report.")
            return cls._generate_mock_report(files_data)

        try:
            genai.configure(api_key=api_key)
            model = genai.GenerativeModel(settings.GEMINI_MODEL)
            
            prompt = f"""You are an elite Google Staff Software Engineer performing an automated, comprehensive code review.
Analyze the following source code context from a repository.

=== SOURCE CODE START ===
{code_context}
=== SOURCE CODE END ===

Generate an in-depth code review report. You MUST respond in JSON format conforming exactly to this structure:
{{
    "score_quality": <int: 0 to 100>,
    "score_security": <int: 0 to 100>,
    "score_performance": <int: 0 to 100>,
    "score_maintainability": <int: 0 to 100>,
    "findings": [
        {{
            "severity": "high" | "medium" | "low",
            "file": "<relative path of the file>",
            "line": <int: line number or 1>,
            "category": "security" | "bug" | "performance" | "code_smell",
            "message": "<description of the issue>",
            "suggestion": "<recommended refactored code snippet or fix>"
        }}
    ],
    "markdown_report": "<The full detailed report in Markdown format. Explain in detail the quality overview, security hazards, performance bottlenecks, maintainability, architectural observations, and refactoring tips. Use clear headers and code blocks.>"
}}
"""

            response = model.generate_content(
                prompt,
                generation_config={"response_mime_type": "application/json"}
            )
            
            result_json = json.loads(response.text)
            
            # Basic validation of keys
            required_keys = ["score_quality", "score_security", "score_performance", "score_maintainability", "findings", "markdown_report"]
            for key in required_keys:
                if key not in result_json:
                    raise ValueError(f"Missing required key '{key}' in Gemini response.")
                    
            return result_json

        except Exception as e:
            logger.error(f"Gemini API call failed: {str(e)}")
            # If API call fails, raise HTTPException or fallback to mock
            raise HTTPException(
                status_code=500,
                detail=f"AI Engine failed to generate analysis report: {str(e)}"
            )

    @classmethod
    def _generate_mock_report(cls, files_data: List[Tuple[str, str, str]]) -> Dict[str, Any]:
        """Generates a high-quality mock report to ensure platform usability when API key is missing."""
        file_count = len(files_data)
        languages = list(set([lang for _, lang, _ in files_data]))
        
        findings = []
        for i, (path, lang, content) in enumerate(files_data[:3]):
            findings.append({
                "severity": "medium" if i % 2 == 0 else "low",
                "file": path,
                "line": 12,
                "category": "code_smell" if i % 2 == 0 else "performance",
                "message": f"Found styling or logging issue in {lang} file.",
                "suggestion": "// Consider refactoring or adding appropriate logger configurations."
            })

        markdown = f"""# AI Code Review Report (Local Mock Mode)

> [!NOTE]
> This report was generated in **Demo Mock Mode** because no `GEMINI_API_KEY` was found in the environment configurations.

## Executive Summary
We analyzed **{file_count} files** written in **{", ".join(languages)}**. The codebase demonstrates a standard structure with several opportunities for improvement.

## Analysis Metrics
- **Code Quality**: 85/100
- **Security Vulnerabilities**: 90/100
- **Performance Efficiency**: 80/100
- **Maintainability Index**: 85/100

## Detailed Observations
1. **Directory Structure**: Looks clean.
2. **File Size**: Most files are within healthy limits (under 500 lines).
3. **Best Practices**:
   - Ensure you configure your `GEMINI_API_KEY` in the backend `.env` file to unlock deep AI inspections.
   - Run tests using the automated script.
"""
        return {
            "score_quality": 85,
            "score_security": 90,
            "score_performance": 80,
            "score_maintainability": 85,
            "findings": findings,
            "markdown_report": markdown
        }
