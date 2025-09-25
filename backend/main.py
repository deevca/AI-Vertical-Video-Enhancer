from flask import Flask, request, jsonify, render_template, send_from_directory
from flask_cors import CORS
import os
import uuid
import sys
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)
frontend_dir = os.path.join(project_root, 'frontend')
static_dir = os.path.join(project_root, 'static')

sys.path.append(current_dir)

from werkzeug.utils import secure_filename
from video_processing import VideoProcessor

app = Flask(__name__, 
            static_folder=static_dir, 
            template_folder=frontend_dir)

CORS(app)

UPLOAD_FOLDER = os.path.join(static_dir, 'uploads')
OUTPUT_FOLDER = os.path.join(static_dir, 'output')
ALLOWED_EXTENSIONS = {'mp4', 'mov', 'avi', 'webm'}

os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(OUTPUT_FOLDER, exist_ok=True)

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 500 * 1024 * 1024

# Get API key from environment
api_key = os.getenv('REPLICATE_API_TOKEN')
processor = VideoProcessor(OUTPUT_FOLDER, api_key)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return jsonify({'error': 'No file part'}), 400
    
    file = request.files['file']
    
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400
    
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        unique_filename = f"{uuid.uuid4()}_{filename}"
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], unique_filename)
        
        file.save(filepath)
        
        use_keyframes = request.form.get('use_keyframes', 'false') == 'true'
        keyframe_interval = int(request.form.get('keyframe_interval', 24))
        sample_rate = int(request.form.get('sample_rate', 1))
        
        try:
            if use_keyframes:
                output_path = processor.process_video_keyframes(
                    filepath, keyframe_interval
                )
            else:
                output_path = processor.process_video(
                    filepath, None, sample_rate
                )
            
            relative_output = os.path.relpath(output_path, static_dir)
            
            return jsonify({
                'success': True,
                'output_video': f'/static/{relative_output}',
                'message': 'Video processed successfully!'
            }), 200
        
        except Exception as e:
            return jsonify({
                'error': f'Error processing video: {str(e)}'
            }), 500
    
    return jsonify({'error': 'File type not allowed'}), 400

@app.route('/static/<path:filename>')
def serve_static(filename):
    return send_from_directory(static_dir, filename)

@app.route('/api/stats')
def get_stats():
    output_files = [f for f in os.listdir(OUTPUT_FOLDER) if os.path.isfile(os.path.join(OUTPUT_FOLDER, f))]
    
    return jsonify({
        'videos_processed': len(output_files)
    })

if __name__ == '__main__':
    print(f"Frontend directory: {frontend_dir}")
    print(f"Static directory: {static_dir}")
    
    # Get port from environment variable (for deployment)
    port = int(os.environ.get('PORT', 5001))
    
    # Debug mode only in development
    debug = os.environ.get('FLASK_ENV') == 'development'
    
    app.run(debug=debug, host='0.0.0.0', port=port)