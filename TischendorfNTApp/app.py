from flask import Flask, render_template, jsonify
import os
import xml.etree.ElementTree as ET
import re
from collections import OrderedDict

app = Flask(__name__)

# Set the path to the XML files directory
XML_DIR = 'xml_files'
TISCHENDORF_FILE = os.path.join(XML_DIR, 'tischendorfmorph.xml')
STRONGS_FILE = os.path.join(XML_DIR, 'strongsgreek.xml')

# Function to load Strong's dictionary data
def load_strongs():
    strongs_dict = {}
    if os.path.exists(STRONGS_FILE):
        tree = ET.parse(STRONGS_FILE)
        root = tree.getroot()

        for entry in root.findall(".//entry"):
            # Extract the strong's number and remove leading zeros for consistency
            strong_id = entry.get("strongs").lstrip('0')  # Strip leading zeros if present

            # Extract the definition text from within <strongs_def> tag, including nested elements
            strong_definition = entry.find(".//strongs_def").text if entry.find(".//strongs_def") is not None else ""

            # Store the strong's number and its definition in the dictionary
            strongs_dict[strong_id] = strong_definition

    return strongs_dict

def load_all_content():
    ns = {'osis': 'http://www.bibletechnologies.net/2003/OSIS/namespace'}
    strongs_dict = load_strongs()
    all_content = OrderedDict()  # Ordered dictionary to maintain order

    if os.path.exists(TISCHENDORF_FILE):
        tree = ET.parse(TISCHENDORF_FILE)
        root = tree.getroot()

        for book in root.findall(".//osis:div[@type='book']", namespaces=ns):
            book_title = book.find("osis:title", namespaces=ns).text if book.find("osis:title", namespaces=ns) is not None else book.get("osisID")
            if book_title:
                sanitized_book_title = book_title.replace(".", "_")
                all_content[sanitized_book_title] = OrderedDict()

                for chapter in book.findall("osis:chapter", namespaces=ns):
                    chapter_id = chapter.get("osisID")
                    sanitized_chapter_id = chapter_id.replace(".", "_")
                    chapter_content = []

                    current_verse_id = None
                    current_words_info = []
                    current_verse_text = []

                    for element in chapter:
                        if element.tag == f"{{{ns['osis']}}}verse":
                            if element.get("sID"):  # Starting a new verse
                                if current_verse_id:  # Save the previous verse if one was in progress
                                    chapter_content.append({
                                        "verse_id": current_verse_id,
                                        "verse_text": " ".join(current_verse_text).strip() if current_verse_text else "[No text available]",
                                        "words_info": current_words_info
                                    })

                                # Start a new verse
                                current_verse_id = element.get("osisID")
                                current_words_info = []
                                current_verse_text = []

                            elif element.get("eID"):  # Ending the current verse
                                if current_verse_id and element.get("eID") == current_verse_id:
                                    chapter_content.append({
                                        "verse_id": current_verse_id,
                                        "verse_text": " ".join(current_verse_text).strip() if current_verse_text else "[No text available]",
                                        "words_info": current_words_info
                                    })
                                    current_verse_id = None  # Reset for next verse

                        elif element.tag == f"{{{ns['osis']}}}w":  # Processing <w> elements as words
                            if current_verse_id:
                                # Extract text from all <w> elements within the verse
                                word_text = element.text.strip() if element.text else ""
                                if word_text:
                                    current_verse_text.append(word_text)

                                    # Extract the 'lemma' attribute value and clean it to get only the Greek word
                                    lemma_attr = element.get("lemma", "")
                                    # Extract the Strong's number after the 'G' using regex
                                    strong_number_match = re.search(r'G(\d{1,5})', lemma_attr)
                                    strong_number = strong_number_match.group(1) if strong_number_match else ""

                                    # Extract the Greek lemma by finding the part after 'lemma:'
                                    greek_lemma = ""
                                    if "lemma:" in lemma_attr:
                                        greek_lemma = lemma_attr.split("lemma:")[1].strip()  # Get Greek word after 'lemma:'

                                    word_data = {
                                        "text": word_text,
                                        "lemma": greek_lemma,  # Store only the Greek lemma
                                        "strong": strong_number,  # Store extracted Strong's number
                                        "morph": element.get("morph", "").replace("robinson:", ""),
                                        "definition": strongs_dict.get(strong_number, "No definition available")
                                    }
                                    current_words_info.append(word_data)


                    # Add the last processed verse in the chapter
                    if current_verse_id:
                        chapter_content.append({
                            "verse_id": current_verse_id,
                            "verse_text": " ".join(current_verse_text).strip() if current_verse_text else "[No text available]",
                            "words_info": current_words_info
                        })

                    all_content[sanitized_book_title][sanitized_chapter_id] = chapter_content
    return all_content
    


@app.route('/')
def index():
    return render_template('index.html')

@app.route('/load_content')
def load_content():
    all_content = load_all_content()
    return jsonify(all_content)

if __name__ == '__main__':
    app.run(debug=True)
