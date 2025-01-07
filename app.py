import os
from dotenv import load_dotenv
from fpdf import FPDF
import google.generativeai as genai
from flask import Flask, request, send_file, render_template
import speech_recognition as sr
import math
from pydub import AudioSegment
from textblob import TextBlob
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.lib import colors
from reportlab.lib.units import inch
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

# Load environment variables
load_dotenv()

# Ensure API key is loaded
api_key = os.getenv("API_KEY")
if not api_key:
    raise ValueError("API Key not found in environment variables. Please set it in your .env file.")

# Configure genai API
genai.configure(api_key=api_key)

# Initialize Flask app
app = Flask(__name__)

# Function to process audio and extract text (from reco.py)
def process_audio(audio_file_path):
    r = sr.Recognizer()
    audio = AudioSegment.from_file(audio_file_path)
    audio = audio.set_channels(1)  # Convert to mono for better speech recognition

    chunk_length_ms = 30000  # 30 seconds
    chunks = math.ceil(len(audio) / chunk_length_ms)
    full_transcription = ""

    for i in range(chunks):
        start_time = i * chunk_length_ms
        end_time = min((i + 1) * chunk_length_ms, len(audio))
        audio_chunk = audio[start_time:end_time]
        audio_data = sr.AudioData(audio_chunk.raw_data, audio.frame_rate, audio.sample_width)

        try:
            val = r.recognize_google(audio_data)
            full_transcription += val + " "
        except sr.UnknownValueError:
            continue
        except sr.RequestError:
            continue

    return full_transcription.strip()

# Function to correct spelling (from reco.py)
def correct_spelling(text):
    return str(TextBlob(text).correct())

# Function to classify and format text (from reco.py)
def classify_and_format_text(lines):
    formatted_notes = []
    for line in lines:
        line = line.strip()
        if not line:
            continue
        if line.lower().startswith("heading:"):
            formatted_notes.append((line[8:].strip(), "heading"))
        elif line.startswith("* "):
            formatted_notes.append((line[2:].strip(), "bullet"))
        else:
            formatted_notes.append((line, "paragraph"))
    return formatted_notes

# Function to create PDF (from reco.py)
def create_pdf(formatted_notes, output_pdf_file):
    pdfmetrics.registerFont(TTFont('Arial', 'arial.ttf'))
    c = canvas.Canvas(output_pdf_file, pagesize=letter)
    width, height = letter
    margin = 1 * inch
    y_position = height - margin
    bullet_indent = 20  # Space for bullet indentation

    c.setFont("Arial", 12)

    for text, text_type in formatted_notes:
        if text_type == "heading":
            if y_position < margin:
                c.showPage()
                c.setFont("Arial", 12)
                y_position = height - margin
            c.setFont("Arial-Bold", 14)
            c.setFillColor(colors.blue)
            c.drawString(margin, y_position, text)
            y_position -= 20  # Space below heading
            c.setFont("Arial", 12)
            c.setFillColor(colors.black)
        
        elif text_type == "bullet":
            if y_position < margin:
                c.showPage()
                c.setFont("Arial", 12)
                y_position = height - margin
            bullet_text = f"• {text}"  # Use bullet character
            c.drawString(margin + bullet_indent, y_position, bullet_text)
            y_position -= 15  # Space below each bullet point

        else:
            wrapped_lines = wrap_text(text, width - 2 * margin, c)
            for wrapped_line in wrapped_lines:
                if y_position < margin:
                    c.showPage()
                    c.setFont("Arial", 12)
                    y_position = height - margin
                c.drawString(margin, y_position, wrapped_line)
                y_position -= 15

    c.save()

# Text wrapping helper function (from reco.py)
def wrap_text(text, max_width, c):
    words = text.split(' ')
    lines = []
    current_line = ""

    for word in words:
        test_line = f"{current_line} {word}".strip()
        if c.stringWidth(test_line, "Arial", 12) <= max_width:
            current_line = test_line
        else:
            if current_line:
                lines.append(current_line)
            current_line = word

    if current_line:
        lines.append(current_line)

    return lines

# Function to format text with genai (from reco.py)
def format_text_with_genai(prompt):
    try:
        model = genai.GenerativeModel("gemini-1.5-flash")
        response = model.generate_content(prompt)

        if response and response.text:
            return response.text
        else:
            print("Error: No content generated from the model.")
            return None
    except Exception as e:
        print(f"Error processing text: {str(e)}")
        return None

# Home route
@app.route("/")
def index():
    return render_template("home.html")  # Home page with 2 options

# Reco page route
@app.route("/reco")
def reco():
    return render_template("reco.html")

@app.route("/process_text", methods=["POST"])
def process_text():
    input_text = request.form.get("input_text")
    audio_type = request.form.get("audio_type")  # Get the selected audio type
    custom_prompt = request.form.get("custom_prompt")  # Get custom prompt entered by the user

    if not input_text.strip():
        return "Error: No text provided", 400

    corrected_lines = [correct_spelling(line) for line in input_text.splitlines()]

    # If custom audio type, use user-entered prompt
    if audio_type == "custom" and custom_prompt:
        prompt = custom_prompt + f"\n\n{input_text}"
    else:
        # Default prompts for other audio types
        prompts = {
            "meeting": """Give 5 points only, no paragraphs.""",
            "education": """Give 3 points only, no paragraphs.""",
            "speech": """Convert the following speech transcription into structured paragraphs with clear headings for each section of the speech.""",
        }
        prompt = prompts.get(audio_type, "") + f"\n\n{input_text}"

    # Call the generative AI model with the prompt
    formatted_text = format_text_with_genai(prompt)

    if formatted_text:
        output_pdf_file = "formatted_notes.pdf"
        create_pdf(classify_and_format_text(formatted_text.splitlines()), output_pdf_file)
        return send_file(output_pdf_file, as_attachment=True)

    return "Error processing request", 500

@app.route("/upload", methods=["POST"])
def upload_file():
    if 'file' not in request.files:
        return "No file part"
    file = request.files['file']
    if file.filename == '':
        return "No selected file"

    audio_file_path = f"uploaded_{file.filename}"
    file.save(audio_file_path)

    transcription = process_audio(audio_file_path)
    os.remove(audio_file_path)

    corrected_lines = [correct_spelling(line) for line in transcription.splitlines()]
    formatted_text = format_text_with_genai("\n".join(corrected_lines))

    if formatted_text:
        output_pdf_file = "formatted_notes.pdf"
        create_pdf(classify_and_format_text(formatted_text.splitlines()), output_pdf_file)
        return send_file(output_pdf_file, as_attachment=True)

    return "Error processing request", 500

# OnlyA page route (Provide similar logic for this page, if needed)
@app.route("/onlyA")
def onlyA():
    return render_template("onlyA.html")

if __name__ == "__main__":
    app.run(debug=True)
