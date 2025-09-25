# AI Video Enhancer

An intelligent video processing application that transforms 16:9 horizontal videos into 9:16 vertical format using AI-powered outpainting.

## Features

- **Smart Frame Analysis**: Automatically analyzes video content to determine optimal placement
- **AI Outpainting**: Uses Stable Diffusion to generate seamless extensions
- **Automatic 9:16 Output**: Creates perfect vertical videos without manual sizing
- **Keyframe Processing**: Faster processing for longer videos
- **Real-time Preview**: See original and processed videos side by side

## Setup

### Quick Setup:
```bash
./setup.sh
```

### Manual Setup:

1. **Install Dependencies**:
```bash
pip install -r requirements.txt
```

2. **Configure API Key** (for AI features):
   - Get your free Replicate API key at: https://replicate.com/account/api-tokens
   - Edit the `.env` file and replace `your_api_key_here` with your actual API key
   - **Add credits**: Go to https://replicate.com/account/billing#billing to add credits for AI processing

3. **Run the Application**:
```bash
./run.py
```

4. **Open Browser**: Go to `http://localhost:5001`

## How It Works

1. **Upload** a 16:9 horizontal video (MP4, MOV, AVI, WEBM)
2. **Smart Centering** places the original video in the center of the 9:16 frame
3. **Dual Extensions** creates AI-generated content for both top and bottom
4. **Frame Rate Preservation** maintains smooth playback at original speed
5. **Download** your enhanced vertical video

## Processing Options

- **Full Processing**: Every frame is analyzed and extended (best quality)
- **Keyframe Processing**: Only key frames are processed, others are interpolated (faster)

## Best Results

- Use short clips (5-30 seconds) for best quality
- Clear, simple scenes work better than complex ones
- The AI automatically handles positioning and sizing
- Works great with landscape videos, nature scenes, and simple compositions

## Technical Details

- **Backend**: Flask with OpenCV for video processing
- **AI**: Stable Diffusion 3.5 via Replicate API for high-quality outpainting
- **Smart Fallback**: Reflection + blur when API credits are unavailable (much better than solid colors!)
- **Frame Rate**: Maintains original video smoothness with proper interpolation
- **Dual Extension**: Creates content for both top and bottom simultaneously
- **Centered Layout**: Original video stays in the middle of the 9:16 frame

## API Credits

- **Free Tier**: Limited credits for testing
- **Paid Credits**: Required for production use (very affordable)
- **Fallback Mode**: Works without credits using smart reflection techniques

## Deployment

This application is ready for deployment on platforms like Heroku, Railway, or Render.

See [DEPLOYMENT.md](DEPLOYMENT.md) for detailed deployment instructions.

### Quick Deploy to Heroku:
```bash
heroku create your-app-name
heroku config:set REPLICATE_API_TOKEN=your_api_key_here
git push heroku main
```

## API Endpoints

- `POST /upload`: Upload and process a video
- `GET /api/stats`: Get processing statistics

## License

MIT License