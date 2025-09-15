# ==============================================================================
# Agent: Document Analysis Agent
# ==============================================================================
# This agent performs the core analysis on a piece of raw text. Its primary
# job is to extract structured information (entities, topics, summary) using
# an LLM, preparing the data for the Knowledge Graph Builder Agent.
# ==============================================================================

import httpx
import logging
import json
from pydantic import BaseModel, Field
from typing import List, Dict

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("analysis-agent")

# --- Pydantic Models for Structured Output ---
# These models define the exact JSON structure we want the LLM to return.
class ExtractedEntity(BaseModel):
    name: str = Field(..., description="The name of the entity, e.g., 'John Doe', 'Cybersecurity Act'")
    type: str = Field(..., description="The type of entity, e.g., 'PERSON', 'ORGANIZATION', 'LEGISLATION'")
    context: str = Field(..., description="A brief snippet from the text showing how the entity was used.")

class AnalysisResult(BaseModel):
    summary: str = Field(..., description="A concise, one-paragraph summary of the document's main points.")
    topics: List[str] = Field(..., description="A list of 3-5 primary topics or keywords.")
    entities: List[ExtractedEntity] = Field(..., description="A list of all key entities found in the text.")


class DocumentAnalysisAgent:
    def __init__(self, llm_service_url: str, model_name: str):
        self.llm_service_url = llm_service_url
        self.model_name = model_name
        # Use a longer timeout for potentially slow LLM responses
        self.client = httpx.AsyncClient(timeout=300.0)

    def _create_prompt(self, text: str) -> Dict:
        """Creates the system and user prompt for the LLM."""
        
        system_prompt = f"""
You are a highly skilled and precise document analysis expert. Your task is to read the provided text and extract key information in a specific JSON format.
You must conform to the following JSON schema:
{AnalysisResult.model_json_schema()}
Do not include any explanatory text or markdown formatting before or after the JSON object.
"""
        user_prompt = f"Please analyze the following document text:\n\n---\n\n{text}"

        return {
            "model": self.model_name,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            "response_format": {
                "type": "json_object"
            }
        }

    async def analyze(self, text: str) -> AnalysisResult:
        """
        Sends the text to the LLM and parses the structured JSON response.
        """
        endpoint = f"{self.llm_service_url}/v1/chat/completions"
        prompt = self._create_prompt(text)
        
        try:
            logger.info("Sending analysis request to LLM...")
            response = await self.client.post(endpoint, json=prompt)
            response.raise_for_status()
            
            # Extract the JSON content from the LLM's response
            llm_response_data = response.json()
            json_content_str = llm_response_data['choices'][0]['message']['content']
            
            logger.info("Received response from LLM. Parsing structured data...")
            # Parse the string content into our Pydantic model
            parsed_json = json.loads(json_content_str)
            analysis_result = AnalysisResult.model_validate(parsed_json)
            
            logger.info("Successfully parsed analysis results.")
            return analysis_result

        except httpx.RequestError as e:
            logger.error(f"Could not connect to LLM service at {endpoint}: {e}")
            raise
        except (json.JSONDecodeError, KeyError) as e:
            logger.error(f"Failed to decode or parse LLM JSON response: {e}")
            logger.error(f"Raw response content: {llm_response_data.get('choices', [{}])[0].get('message', {}).get('content')}")
            raise
        except Exception as e:
            logger.error(f"An unexpected error occurred during analysis: {e}")
            raise


# Example of how this might be used (conceptual)
async def main():
    # In a real app, this would be instantiated with config values
    analyzer = DocumentAnalysisAgent(
        llm_service_url="http://localhost:8080", # Assuming LocalAI is running
        model_name="gpt-4-turbo" # The model configured in LocalAI
    )
    
    sample_text = """
    H.R. 302: The Cybersecurity Improvement Act, sponsored by Rep. Jane Smith and Sen. John Doe,
    was introduced to enhance the security of federal networks. The act mandates that all
    government agencies must adopt multi-factor authentication by 2026. The Congressional
    Budget Office estimates the cost at $500 million.
    """
    
    try:
        result = await analyzer.analyze(sample_text)
        print("\n--- Analysis Complete ---")
        print(f"Summary: {result.summary}")
        print(f"Topics: {result.topics}")
        for entity in result.entities:
            print(f"- Entity: {entity.name} (Type: {entity.type})")
        print("-----------------------\n")
    except Exception as e:
        print(f"Analysis failed: {e}")

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
