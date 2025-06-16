import streamlit as st
from dotenv import load_dotenv
from cerebras.cloud.sdk import Cerebras
import os
import json
from typing import Dict, List, Optional

# Load environment variables
try:
    load_dotenv()
    API_KEY = os.environ.get("API_KEY")
    if not API_KEY:
        st.error("API_KEY not found in environment variables")
        st.stop()
except Exception as e:
    st.error(f"Error loading environment variables: {e}")
    st.stop()

def setup_cerebras_client() -> Cerebras:
    """Initialize and return the Cerebras client."""
    try:
        return Cerebras(api_key=API_KEY)
    except Exception as e:
        st.error(f"Failed to initialize Cerebras client: {e}")
        st.stop()

def generate_flashcards(input_text: str, client: Cerebras) -> Optional[Dict]:
    """
    Generate flashcards from input text using Cerebras API.
    """
    system_prompt = '''
        You are to generate flash cards for a given input text.
        Generate a minimum of 12 flashcards with questions and answers (50-100 words each).
        Return flashcards in JSON format with "flashcards" as root key containing array of objects.
        Each object should have "Question" and "Answer" keys.
        Ensure answers are concise but comprehensive.
        Do not use markdown or newline characters in the JSON output.
    '''

    try:
        response = client.chat.completions.create(
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": input_text}
            ],
            model="llama-4-scout-17b-16e-instruct",
            stream=False,
            max_completion_tokens=4000,
            temperature=0.2,
            top_p=1,
            response_format={"type": "json_object"}
        )
        
        content_str = response.choices[0].message.content.strip()
        return json.loads(content_str)
    except Exception as e:
        st.error(f"Error generating flashcards: {str(e)}")
        return None
