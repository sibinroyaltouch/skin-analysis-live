import base64
import requests
from flask import Flask, render_template, request, jsonify

app = Flask(__name__)

# --- FACE++ CREDENTIALS ---
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
            'return_attributes': 'skinstatus,gender,age,emotion,beauty,eyestatus,smile' 
        }
        
        response = requests.post(API_URL, data=payload)
        result = response.json()

        # DEBUG: Print the actual error from Face++ to the terminal
        if 'error_message' in result:
            print("FACE++ ERROR:", result['error_message'])
            return jsonify({'success': False, 'error': "API Error: " + result['error_message']})

        if 'faces' in result and len(result['faces']) > 0:
            face = result['faces'][0]['attributes']
            skin = face['skinstatus']
            emotions = face['emotion']
            
            # Calculations
            left_eye = face['eyestatus']['left_eye_status']['no_glass_eye_close']
            right_eye = face['eyestatus']['right_eye_status']['no_glass_eye_close']
            fatigue_score = (skin['dark_circle'] * 0.6) + ((left_eye + right_eye)/2 * 0.4)
            neg_emotion = emotions['sadness'] + emotions['fear'] + emotions['anger']
            stress_score = (neg_emotion + (100 - skin['health'])) / 2
            
            dimples = "Detected" if (face['smile']['value'] > 40 and face['beauty']['female_score'] > 60) else "Not Detected"

            report = {
                "health": skin['health'],
                "acne": skin['acne'],
                "circles": skin['dark_circle'],
                "stain": skin['stain'],
                "age": face['age']['value'],
                "gender": face['gender']['value'],
                "fatigue": round(fatigue_score, 1),
                "stress": round(stress_score, 1),
                "moles": round(skin['stain'], 1),
                "dimples": dimples
            }
            return jsonify({'success': True, 'report': report})
        else:
            print("NO FACE FOUND. Result:", result)
            return jsonify({'success': False, 'error': "No face detected. Please center your face and ensure good lighting."})

    except Exception as e:
        print("SERVER ERROR:", e)
        return jsonify({'success': False, 'error': str(e)})

if __name__ == '__main__':
    app.run(debug=True)
