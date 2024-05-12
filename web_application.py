# -*- coding: utf-8 -*-
"""web application

Automatically generated by Colab.

Original file is located at
    https://colab.research.google.com/drive/1H56vSExOgl78QjDqHGJ_bTEQBfH62SMy
"""

# Commented out IPython magic to ensure Python compatibility.
from google.colab import drive
drive.mount('/content/drive')
!ls "/content/drive"
# Read datasets
# %cd /content/drive/My Drive/Colab Notebooks/data

!pip install flask
!pip install pyngrok
!pip install lime

import re
import nltk
import string
import numpy as np
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
from nltk.corpus import stopwords
from nltk.stem import SnowballStemmer, WordNetLemmatizer
from sklearn.feature_extraction.text import TfidfVectorizer

from sklearn.preprocessing import LabelEncoder
from sklearn.model_selection import train_test_split

from tensorflow.keras.utils import to_categorical
from tensorflow.keras.preprocessing.text import Tokenizer
from tensorflow.keras.preprocessing.sequence import pad_sequences

from tensorflow.keras.optimizers import Adam
from tensorflow.keras.models import Sequential
from tensorflow.keras.callbacks import EarlyStopping
from tensorflow.keras.layers import Dense, LSTM, Embedding, Bidirectional

nltk.download("stopwords")
nltk.download("wordnet")
stop_words = set(stopwords.words("english"))
lemmatizer= WordNetLemmatizer()

# Modelling
from sklearn.model_selection import train_test_split,KFold, GridSearchCV
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.tree import DecisionTreeClassifier
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score,confusion_matrix, classification_report
from sklearn.pipeline import Pipeline
from sklearn.metrics import f1_score
from sklearn.svm import SVC

#Lime
!pip install lime
from lime import lime_text
from lime.lime_text import LimeTextExplainer
from lime.lime_text import IndexedString,IndexedCharacters
from lime.lime_base import LimeBase
from lime.lime_text import explanation
sns.set(font_scale=1.3)
nltk.download('omw-1.4')

import getpass
import os
import threading

from flask import Flask
from pyngrok import ngrok, conf
from flask import Flask, request, jsonify, render_template
from lime.lime_text import LimeTextExplainer
from tensorflow.keras.models import load_model
import numpy as np
from joblib import load

print("Enter your authtoken, which can be copied from https://dashboard.ngrok.com/get-started/your-authtoken")
#conf.get_default().auth_token = getpass.getpass()
conf.get_default().auth_token = '2fur86Jip3k2YLUlXV8o4tLNZfk_3UmyXMuBUq5gfoXnWnmGt'

app = Flask(__name__)

# Open a ngrok tunnel to the HTTP server
public_url = ngrok.connect(5000).public_url
print(" * ngrok tunnel \"{}\" -> \"http://127.0.0.1:{}/\"".format(public_url, 5000))

# Update any base URLs to use the public ngrok URL
app.config["BASE_URL"] = public_url

model = load_model('BiLSTM-CNN-GRU.h5')


# Initialize LabelEncoder
label_encoder = load('label_encoder.joblib')


# Initialize LIME explainer
explainer = LimeTextExplainer(class_names=label_encoder.classes_)

tokenizer = load('tokenizer.joblib')

def lemmatization(text):
    lemmatizer= WordNetLemmatizer()

    text = text.split()

    text=[lemmatizer.lemmatize(y) for y in text]

    return " " .join(text)

def remove_stop_words(text):

    Text=[i for i in str(text).split() if i not in stop_words]
    return " ".join(Text)

def Removing_numbers(text):
    text=''.join([i for i in text if not i.isdigit()])
    return text

def lower_case(text):

    text = text.split()

    text=[y.lower() for y in text]

    return " " .join(text)

def Removing_punctuations(text):
    ## Remove punctuations
    text = re.sub('[%s]' % re.escape("""!"#$%&'()*+,،-./:;<=>؟?@[\]^_`{|}~"""), ' ', text)
    text = text.replace('؛',"", )

    ## remove extra whitespace
    text = re.sub('\s+', ' ', text)
    text =  " ".join(text.split())
    return text.strip()

def Removing_urls(text):
    url_pattern = re.compile(r'https?://\S+|www\.\S+')
    return url_pattern.sub(r'', text)

def remove_small_sentences(df):
    for i in range(len(df)):
        if len(df.text.iloc[i].split()) < 3:
            df.text.iloc[i] = np.nan

def normalize_text(df):
    df.Text=df.Text.apply(lambda text : lower_case(text))
    df.Text=df.Text.apply(lambda text : remove_stop_words(text))
    df.Text=df.Text.apply(lambda text : Removing_numbers(text))
    df.Text=df.Text.apply(lambda text : Removing_punctuations(text))
    df.Text=df.Text.apply(lambda text : Removing_urls(text))
    df.Text=df.Text.apply(lambda text : lemmatization(text))
    return df

def normalized_sentence(sentence):
    sentence= lower_case(sentence)
    sentence= remove_stop_words(sentence)
    sentence= Removing_numbers(sentence)
    sentence= Removing_punctuations(sentence)
    sentence= Removing_urls(sentence)
    sentence= lemmatization(sentence)
    return sentence


# Define prediction function
def predict(input_text):
    print(input_text)
    sentence = normalized_sentence(input_text)
    print(sentence)
    sentence = tokenizer.texts_to_sequences([sentence])
    print(sentence)
    sentence = pad_sequences(sentence, maxlen=229, truncating='pre')
    result = label_encoder.inverse_transform(np.argmax(model.predict(sentence), axis=-1))[0]
    proba =  np.max(model.predict(sentence))
    print(result)
    print(proba)
    return result, proba

def predict_proba(sentences):
    # Preprocess each sentence
    preprocessed_sentences = [normalized_sentence(sentence) for sentence in sentences]
    sequences = tokenizer.texts_to_sequences(preprocessed_sentences)
    padded_sequences = pad_sequences(sequences, maxlen=300, truncating='pre')

    # Predict probabilities for the padded sequences
    return model.predict(padded_sequences)

# Define prediction endpoint
@app.route('/predict', methods=['POST'])
def predict_endpoint():
    # Get input text from request
    input_text = request.form['text']

    # Make model predictions
    prediction, prediction_prob = predict(input_text)
    print(prediction)
    print(prediction_prob)

    # Generate LIME explanation
    explanation = explainer.explain_instance(input_text, predict_proba, num_features=10, top_labels=6)

    # Prepare response
    response = {
        'prediction': prediction,
        'probability': str(prediction_prob),
        'explanation': explanation.as_html()
    }

    return jsonify(response)

# Define Flask routes
@app.route("/")
def index():
     return """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Emotion Prediction</title>
    <style>
        /* Input text style */
        #textInput {
            width: 100%;
            padding: 10px;
            font-size: 16px;
            border: 1px solid #ccc;
            border-radius: 5px;
            box-sizing: border-box;
            margin-bottom: 20px;
        }

        /* Responsive iframe style */
        .iframe-container {
            position: relative;
            overflow: auto;
            width: 100%;
            border: none;
            padding-top: 56.25%; /* 16:9 aspect ratio */
        }

        .iframe-container iframe {
            position: absolute;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            border: none;
        }
    </style>
</head>
<body>
    <h2>Emotion Prediction</h2>
    <form id="predictionForm">
        <label for="textInput">Enter Text:</label><br>
        <input type="text" id="textInput" name="text" placeholder="Type your text here...">
        <button type="submit">Predict</button>
    </form>
    <div id="prediction"></div>
    <div class="iframe-container">
        <iframe id="explanationIframe" title="Explanation"></iframe>
    </div>

    <script>
        document.getElementById("predictionForm").addEventListener("submit", function(event) {
            event.preventDefault();
            const formData = new FormData(this);
            const requestData = {
                'text': formData.get('text')
            };

            fetch('/predict', {
                method: 'POST',
                body: new URLSearchParams(requestData),
                headers: {
                    'Content-Type': 'application/x-www-form-urlencoded'
                }
            })
            .then(response => response.json())
            .then(data => {
                const predictionElement = document.getElementById("prediction");
                const explanationIframe = document.getElementById("explanationIframe");

                // Display prediction
                predictionElement.innerHTML = `Predicted Emotion: ${data.prediction} (${(data.probability * 100).toFixed(2)}%)`;

                // Update the iframe with the LIME explanation
                const iframeDocument = explanationIframe.contentWindow.document;
                iframeDocument.open();
                iframeDocument.write(data.explanation);
                iframeDocument.close();
            })
            .catch(error => console.error('Error:', error));
        });
    </script>
</body>
</html>

     """


if __name__ == '__main__':
    app.run()