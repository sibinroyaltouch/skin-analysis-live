import base64
import requests
from flask import Flask, render_template, request, jsonify

app = Flask(__name__)

# --- FACE++ API CREDENTIALS ---
API_KEY = "jUXiaNgNFmBDsfSaysIAeT43vXW2khF_"
API_SECRET = "aNMxT9IABPvqXPasUgm9fyfy-XJXM-yK"
API_URL = "https://api-us.faceplusplus.com/facepp/v3/detect"

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/analyze', methods=['POST'])
def analyze_skin():
    try:
        data = request.json
        image_data = data['image']
        
        if ',' in image_data:
            clean_image = image_data.split(',')[1]
        else:
            clean_image = image_data

        payload = {
            'api_key': API_KEY,
            'api_secret': API_SECRET,
            'image_base64': clean_image,
            'return_attributes': 'skinstatus,gender,age,emotion,beauty,eyestatus' 
        }
        
        response = requests.post(API_URL, data=payload)
        result = response.json()

        if 'faces' in result and len(result['faces']) > 0:
            face = result['faces'][0]['attributes']
            skin = face['skinstatus']
            emotion = face['emotion'] # Get full emotion data
            
            # Calculate Eye Fatigue
            left_eye = face['eyestatus']['left_eye_status']['no_glass_eye_close']
            right_eye = face['eyestatus']['right_eye_status']['no_glass_eye_close']
            fatigue_score = (left_eye + right_eye) / 2 

            report = {
                "health": skin['health'],
                "acne": skin['acne'],
                "circles": skin['dark_circle'],
                "stain": skin['stain'],
                "age": face['age']['value'],
                "gender": face['gender']['value'],
                "fatigue": round(fatigue_score, 1),
                # Pass raw emotion data for stress calculation
                "emotions": {
                    "sadness": emotion['sadness'],
                    "anger": emotion['anger'],
                    "fear": emotion['fear'],
                    "happiness": emotion['happiness']
                }
            }
            return jsonify({'success': True, 'report': report})
        else:
            return jsonify({'success': False, 'error': "No face detected."})

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

if __name__ == '__main__':
    app.run(debug=True)
