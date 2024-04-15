import os
from flask import Flask, jsonify, request, render_template, send_from_directory
from deep_translator import GoogleTranslator
import google.generativeai as genai
from PIL import Image
import mysql.connector
from uuid import uuid4

# Initialize Flask app
app = Flask(__name__,static_url_path='',static_folder='templates')
global lang
global type
lang='en'
UPLOAD_FOLDER = 'uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Configure generative AI
genai.configure(api_key='AIzaSyAs5_WHo7NXArFquWU0Zpe1sOX7Bkzkp2A')
session_id=uuid4().__str__()
# Initialize generative model for chat
safety_settings = [
    {"category": "HARM_CATEGORY_DANGEROUS", "threshold": "BLOCK_NONE"},
    {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"},
    {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_NONE"},
    {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_NONE"},
    {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_NONE"},
]
modeltext = genai.GenerativeModel(model_name='gemini-pro', safety_settings=safety_settings)
chattext = modeltext.start_chat(history=[])
modelvision=genai.GenerativeModel(model_name='gemini-pro-vision',safety_settings=safety_settings)

# Function to translate text from any language to English

def add_db(user_input,bot_reply,lang):
    mydb = mysql.connector.connect(
    host="firdouzov.mysql.pythonanywhere-services.com",
    user="firdouzov",
    password="Elantra_2017*",
    database="firdouzov$messages"
    )
    mycursor = mydb.cursor()
    sql=f"""INSERT INTO messages(user_message,bot_reply,lang) VALUES ("%s","%s","%s");""" % (user_input,bot_reply,lang)
    mycursor.execute(sql)
    mydb.commit()

def translate_to_english(lang,text):
    translation = GoogleTranslator(source=lang, target='en').translate(text)
    return translation

# Function to translate text from English to any language
def translate_to_language(text, target_lang):
    translation = GoogleTranslator(source='en', target=target_lang).translate(text)
    return translation

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/send_message', methods=['POST'])
def send_message():
    global lang
    lang = request.json.get('language')
    if session_id==uuid4().__str__():
        user_input_org = request.json.get('user_input', '')
        user_input = translate_to_english(lang,user_input_org)
        response = chattext.send_message(user_input).text
        response = translate_to_language(response, lang)
        #add_db(user_input_org,response,lang)
    else:
        modeltext = genai.GenerativeModel(model_name='gemini-pro', safety_settings=safety_settings)
        chattext = modeltext.start_chat(history=[])
        user_input_org = request.json.get('user_input', '')
        user_input= translate_to_english(lang,user_input_org)
        response = chattext.send_message(user_input).text
        response = translate_to_language(response, lang)
        #add_db(user_input_org,response,lang)
    return jsonify({"response": response, "type": 1})


@app.route('/upload_image', methods=['POST'])
def upload_image():
    global lang
    lang=request.form.get('language')
    print(lang)
    # Rest of the code
    if 'file' not in request.files:
        return jsonify({"error": "No file part"})

    file = request.files['file']
    caption_org = request.form.get('caption', '')

    if file.filename == '':
        return jsonify({"error": "No selected file"})

    if caption_org != '':
        try:
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], 'upload.jpg')
            file.save(file_path)
            img = Image.open(file_path)
            caption= translate_to_english(lang,caption_org)
            response = modelvision.generate_content([caption, img]).text
            response = translate_to_language(response, lang)
            #add_db('image+'+caption_org,response,lang)
            return jsonify({"success": "File uploaded successfully", "response": response, "type": 2, "caption": caption,'file_path':file_path})
        except Exception as e:
            return jsonify({"error": str(e)})
    else:
        if not os.path.exists(app.config['UPLOAD_FOLDER']):
            os.makedirs(app.config['UPLOAD_FOLDER'])
        try:
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], 'upload.jpg')
            file.save(file_path)
            img = Image.open(file_path)
            response = modelvision.generate_content(img).text
            response = translate_to_language(response, lang)
            #add_db('image',response,lang)
            return jsonify({"success": "File uploaded successfully", "response": response, "type": 3,'file_path':file_path})
        except Exception as e:
            print(e)
            return jsonify({"error": "There was error while generating content. It may cause several reasons, please check your language selection if it's compatible your input message."})




@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

if __name__ == "__main__":
    import random, threading, webbrowser

    port = 5000 + random.randint(0, 999)
    url = "http://127.0.0.1:{0}".format(port)

    threading.Timer(1.25, lambda: webbrowser.open(url)).start()

    app.run(port=port, debug=False)