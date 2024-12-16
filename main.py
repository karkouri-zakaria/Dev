import xml.etree.ElementTree as ET
import pandas as pd
import streamlit as st
from gtts import gTTS
import os

# Function to parse .flashquiz file and extract FrontText and BackText
def flashquiz_to_table(file_obj):
    # Read the .flashquiz file content from the file-like object
    xml_content = file_obj.read().decode('utf-8')  # Decode bytes to string

    # Parse the content as XML
    root = ET.fromstring(xml_content)

    # Define namespaces (based on your debug output)
    namespaces = {
        'peach': 'http://schemas.datacontract.org/2004/07/Peach.Sharing',
        'ms_array': 'http://schemas.microsoft.com/2003/10/Serialization/Arrays',
        'peach_card': 'http://schemas.datacontract.org/2004/07/Peach'
    }

    # Initialize lists to hold FrontText and BackText pairs
    front_texts = []
    back_texts = []

    # Find all Cards
    for card in root.findall('.//peach_card:Card', namespaces=namespaces):
        # Extract FrontText and BackText
        front_text = card.find('peach_card:FrontText', namespaces=namespaces)
        back_text = card.find('peach_card:BackText', namespaces=namespaces)

        # Add them to the lists if both are present
        if front_text is not None and back_text is not None:
            front_texts.append(front_text.text)
            back_texts.append(back_text.text)

    # Create a DataFrame with the collected data
    df = pd.DataFrame({
        'FrontText': front_texts,
        'BackText': back_texts
    })

    return df

# Function to generate audio from text using gTTS
@st.cache_data
def generate_audio(text):
    tts = gTTS(text=text, lang='de')  # German language
    audio_file = "audio.mp3"  # Overwrite the same file
    tts.save(audio_file)
    return audio_file

# Streamlit app
st.set_page_config(layout="wide")
st.title('Flashquiz Viewer By Zakaria')

# Sidebar to display the user input
user_note = st.sidebar.text_area("Write something", "", key="user_input")
st.sidebar.write(user_note)
if user_note:
    audio_path = generate_audio(user_note)
    with open(audio_path, "rb") as audio_file:
        audio_bytes = audio_file.read()
        st.sidebar.audio(audio_bytes, format="audio/mp3")

# Search bar and input field
st.sidebar.write("---")
search_query = st.sidebar.text_input("Search Flashcards", "")

# File uploader in Streamlit
uploaded_file = st.file_uploader("Upload a .flashquiz file", type="flashquiz", key="file_uploader")

if uploaded_file is not None:
    # Parse the uploaded file and display results
    try:
        flashcards_df = flashquiz_to_table(uploaded_file)

        # Apply search filter if a query is provided
        if search_query:
            flashcards_df = flashcards_df[flashcards_df['FrontText'].str.contains(search_query, case=False, na=False) | \
                                          flashcards_df['BackText'].str.contains(search_query, case=False, na=False)]

        st.write("### Extracted Flashcards")

        # Create a grid of flashcards
        num_columns = 4

        rows = [flashcards_df.iloc[i:i + num_columns] for i in range(0, len(flashcards_df), num_columns)]

        for row in rows:
            cols = st.columns(num_columns)
            for col, (index, flashcard) in zip(cols, row.iterrows()):
                with col:
                    st.write(f"{flashcard['FrontText']}")

                    with st.expander("Deutsch⚫🔴🟡"):
                        st.write(flashcard['BackText'])
                        try:
                            audio_path = generate_audio(flashcard['BackText'])  # This will cache audio
                            with open(audio_path, "rb") as audio_file:
                                st.audio(audio_file, format="audio/mp3")
                        except:
                            st.write("Error generating audio")
                    st.write("---")

    except Exception as e:
        st.error(f"Error parsing the file: {e}")