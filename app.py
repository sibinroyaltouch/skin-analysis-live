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

        # Request Emotion and Skin Status
        payload = {
            'api_key': API_KEY,
            'api_secret': API_SECRET,
            'image_base64': clean_image,
            'return_attributes': 'skinstatus,gender,age,emotion,beauty,eyestatus,smile' 
        }
        
        response = requests.post(API_URL, data=payload)
        result = response.json()

        if 'faces' in result and len(result['faces']) > 0:
            face = result['faces'][0]['attributes']
            skin = face['skinstatus']
            emotions = face['emotion']
            
            # 1. CALCULATE SLEEP TRACES
            # Combination of Dark Circles + Eye Status (Closing)
            left_eye_close = face['eyestatus']['left_eye_status']['no_glass_eye_close']
            right_eye_close = face['eyestatus']['right_eye_status']['no_glass_eye_close']
            avg_eye_closure = (left_eye_close + right_eye_close) / 2
            
            # Sleep Debt Score (0-100). Higher = More Sleep Deprived
            sleep_trace = (skin['dark_circle'] + avg_eye_closure) / 2

            # 2. CALCULATE STRESS TRACES
            # Combination of Negative Emotions + Skin Health Drop
            # (Sadness + Fear + Anger) blended with (100 - Skin Health)
            neg_emotion = emotions['sadness'] + emotions['fear'] + emotions['anger']
            health_inv = 100 - skin['health']
            stress_trace = (neg_emotion + health_inv) / 2

            # 3. MOLE / SPOT INTENSITY
            # 'Stain' usually picks up moles and dark spots
            mole_trace = skin['stain']

            # 4. DIMPLE DETECTION (Heuristic based on Smile + Beauty)
            # Real dimple detection needs depth sensors, but we can estimate probability
            # based on smile depth and cheek contours.
            is_smiling = face['smile']['value'] > 40
            dimple_trace = "Possible" if (is_smiling and face['beauty']['female_score'] > 60) else "Not Detected"

            report = {
                "health": skin['health'],
                "acne": skin['acne'],
                "circles": skin['dark_circle'],
                "stain": skin['stain'],
                "age": face['age']['value'],
                "gender": face['gender']['value'],
                "fatigue": round(sleep_trace, 1), # Renamed logic
                "stress": round(stress_trace, 1),
                "mole_intensity": mole_trace,
                "dimples": dimple_trace
            }
            return jsonify({'success': True, 'report': report})
        else:
            return jsonify({'success': False, 'error': "No face detected."})

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

if __name__ == '__main__':
    app.run(debug=True)
