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

