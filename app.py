import streamlit as st
from dotenv import load_dotenv
from cerebras.cloud.sdk import Cerebras
import os
import json
import csv
import io
from typing import Dict, Optional

# Load environment variables
try:
    load_dotenv('.test_env')
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

def generate_flashcards(input_text: str, num_flashcards: int, answer_length: str, client: Cerebras) -> Optional[Dict]:
    """
    Generate flashcards from input text using Cerebras API.
    """
    system_prompt = f'''
        Generate {num_flashcards} flashcards.
        The length of flashcard answers should be {answer_length} words.
        Return flashcards in JSON format.
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

def display_flashcards_ui() -> None:
    """Display flashcards UI with persistent controls."""
    if "flashcards" not in st.session_state:
        return
    
    flashcards = st.session_state.flashcards
    st.success(f"✅ Generated {len(flashcards)} flashcards!")
    
    # Store display settings in session state
    if "show_all" not in st.session_state:
        st.session_state.show_all = False
    if "reverse_order" not in st.session_state:
        st.session_state.reverse_order = False
    
    # Use columns for better layout
    cols = st.columns(2)
    with cols[0]:
        # Toggle buttons that don't trigger rerun
        show_all = st.toggle(
            "Show All Answers",
            value=st.session_state.show_all,
            key="show_all_toggle",
            on_change=lambda: setattr(st.session_state, "show_all", not st.session_state.show_all)
        )
    with cols[1]:
        reverse_order = st.toggle(
            "Reverse Order",
            value=st.session_state.reverse_order,
            key="reverse_order_toggle",
            on_change=lambda: setattr(st.session_state, "reverse_order", not st.session_state.reverse_order)
        )
    
    # flashcard_list = flashcards
    if st.session_state.reverse_order:
        flashcards = list(flashcards)[::-1]
    
    # Calculate correct numbering based on order
    total_cards = len(flashcards)
    for idx, card in enumerate(flashcards, start=1):
        # Calculate display number - if reversed, show original position
        display_num = (total_cards - idx + 1) if st.session_state.reverse_order else idx
        
        # Use the session state value for expanded state
        with st.expander(
            f"Card {display_num}: {card['Question']}", 
            expanded=st.session_state.show_all
        ):
            st.write(card['Answer'])
        
        if idx < len(flashcards):
            st.divider()

def add_export_buttons(flashcards: Dict) -> None:
    """Add export buttons for JSON and CSV formats."""
    st.markdown("---")
    col1, col2 = st.columns(2)
    
    with col1:
        # JSON Export
        json_str = json.dumps(flashcards, indent=2)
        st.download_button(
            label="Download as JSON",
            data=json_str,
            file_name="flashcards.json",
            mime="application/json",
            use_container_width=True
        )
    
    with col2:
        # CSV Export
        output = io.StringIO()
        writer = csv.writer(output)
        
        # Write header
        writer.writerow(["Number", "Question", "Answer"])
        
        # Write each flashcard
        for idx, card in enumerate(flashcards, start=1):
            writer.writerow([
                idx,
                card["Question"],
                card["Answer"]
            ])
        
        csv_str = output.getvalue()
        st.download_button(
            label="Download as CSV",
            data=csv_str,
            file_name="flashcards.csv",
            mime="text/csv",
            use_container_width=True
        )



def main() -> None:
    """Main application function."""
    st.set_page_config(
        page_title="Flashcard Generator", 
        page_icon="📚", 
        layout="centered"
    )
    
    # Initialize client and flashcards in session state
    if "client" not in st.session_state:
        st.session_state.client = setup_cerebras_client()
    
    st.title("📚 Flashcard Generator")
    st.markdown("""
        Transform your study material into interactive flashcards using AI.
        Simply paste your text below and click the generate button.
    """)
    
    with st.sidebar:
        st.header("Settings")
        st.session_state.num_flashcards = st.slider(
            "Minimum Flashcards to Generate", 
            min_value=10, 
            max_value=20, 
            value=15
        )
        st.session_state.answer_length = st.select_slider(
            "Answer Length (words)",
            options=["Short (30-50)", "Medium (50-100)", "Long (100-150)"],
            value="Medium (50-100)"
        )
    
    with st.container():
        user_input = st.text_area(
            "Paste your study material here:",
            height=300,
            key="user_input",
            placeholder="Enter text, notes, or any content you want to turn into flashcards..."
        )
        
        col1, col2 = st.columns([1, 1])
        with col1:
            if st.button("Generate Flashcards", type="primary", use_container_width=True):
                if user_input.strip():
                    with st.spinner("🧠 Generating flashcards..."):
                        result = generate_flashcards(
                                    user_input,
                                    st.session_state.num_flashcards,
                                    st.session_state.answer_length,
                                    st.session_state.client)
                        if result:
                            st.session_state.flashcards = result
                            # Initialize display settings
                            st.session_state.show_all = False
                            st.session_state.reverse_order = False
                            st.rerun()  # Refresh to show flashcards
                else:
                    st.warning("Please enter some text to generate flashcards.")
        
        with col2:
            if st.button("Clear", use_container_width=True):
                if "flashcards" in st.session_state:
                    del st.session_state.flashcards
                st.rerun()
        
        # Display flashcards if they exist in session state
        if "flashcards" in st.session_state:
            display_flashcards_ui()
            
            # Add download option
            add_export_buttons(st.session_state.flashcards)

if __name__ == "__main__":
    main()