import os
import cv2
import tempfile
import numpy as np
from PIL import Image
import time
from pathlib import Path
from ai_extender import AIImageExtender

class VideoProcessor:
    def __init__(self, output_path="static/output", api_key=None):
        self.output_path = output_path
        self.ai_extender = AIImageExtender(api_key)
        os.makedirs(output_path, exist_ok=True)
    
    def process_video(self, video_path, fps=None, sample_rate=1):
        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            raise ValueError(f"Could not open video file: {video_path}")
        
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        input_fps = cap.get(cv2.CAP_PROP_FPS)
        frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        
        fps = fps or input_fps
        target_height = int(width * 16 / 9)
        
        with tempfile.TemporaryDirectory() as temp_dir:
            processed_frames = []
            frame_idx = 0
            
            print(f"Processing video with {frame_count} frames, sampling every {sample_rate} frames...")
            
            # Store all original frames first
            original_frames = []
            while True:
                ret, frame = cap.read()
                if not ret:
                    break
                original_frames.append(frame)
            
            cap.release()
            
            # Process frames and maintain proper frame rate
            for frame_idx, frame in enumerate(original_frames):
                if frame_idx % sample_rate == 0:
                    print(f"Processing frame {frame_idx}/{len(original_frames)}")
                    
                    pil_frame = Image.fromarray(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
                    extended_frame = self.ai_extender.analyze_frame_and_extend(pil_frame)
                    
                    frame_path = os.path.join(temp_dir, f"frame_{frame_idx:06d}.jpg")
                    extended_frame.save(frame_path)
                    processed_frames.append(frame_path)
                else:
                    # For frames we skip, duplicate the last processed frame
                    if processed_frames:
                        last_frame_path = processed_frames[-1]
                        frame_path = os.path.join(temp_dir, f"frame_{frame_idx:06d}.jpg")
                        import shutil
                        shutil.copy2(last_frame_path, frame_path)
                        processed_frames.append(frame_path)
            
            input_filename = os.path.basename(video_path)
            name, ext = os.path.splitext(input_filename)
            output_filename = f"{name}_vertical{ext}"
            output_path = os.path.join(self.output_path, output_filename)
            
            self._frames_to_video(processed_frames, output_path, fps, (width, target_height))
            
            return output_path
    
    def _frames_to_video(self, frame_paths, output_path, fps, dimensions):
        width, height = dimensions
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        video_writer = cv2.VideoWriter(output_path, fourcc, fps, (width, height))
        
        if not video_writer.isOpened():
            raise ValueError(f"Could not create video writer for {output_path}")
        
        for frame_path in frame_paths:
            img = cv2.imread(frame_path)
            if img is None:
                print(f"Warning: Could not read frame {frame_path}")
                continue
            
            if img.shape[:2] != (height, width):
                img = cv2.resize(img, (width, height))
            
            video_writer.write(img)
        
        video_writer.release()
        print(f"Video saved to {output_path}")
        
        try:
            temp_output = output_path + ".temp.mp4"
            cmd = f'ffmpeg -y -i "{output_path}" -c:v libx264 -preset fast -crf 22 "{temp_output}"'
            result = os.system(cmd)
            if result == 0 and os.path.exists(temp_output):
                os.replace(temp_output, output_path)
                print(f"Converted video to H.264 format")
            else:
                print(f"FFmpeg conversion failed, keeping original format")
        except Exception as e:
            print(f"Failed to convert to H.264: {e}")
    
    def process_video_keyframes(self, video_path, keyframe_interval=24):
        """
        Process a video using keyframes for faster processing
        
        Args:
            video_path: Path to the input video
            keyframe_interval: Process 1 frame every N frames as keyframes
        
        Returns:
            Path to the processed video
        """
        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            raise ValueError(f"Could not open video file: {video_path}")
        
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        fps = cap.get(cv2.CAP_PROP_FPS)
        frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        
        # Calculate 9:16 dimensions
        target_height = int(width * 16 / 9)
        
        # Create output video name
        input_filename = os.path.basename(video_path)
        name, ext = os.path.splitext(input_filename)
        output_filename = f"{name}_vertical{ext}"
        output_path = os.path.join(self.output_path, output_filename)
        
        # Create video writer
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        video_writer = cv2.VideoWriter(output_path, fourcc, fps, (width, target_height))
        
        # Store all frames first
        all_frames = []
        while True:
            ret, frame = cap.read()
            if not ret:
                break
            all_frames.append(frame)
        
        cap.release()
        total_frames = len(all_frames)
        
        # Process keyframes
        keyframes = {}
        
        # First pass: process keyframes
        print(f"First pass: Processing keyframes...")
        for frame_idx in range(0, total_frames, keyframe_interval):
            print(f"Processing keyframe {frame_idx}/{total_frames}")
            
            # Convert OpenCV BGR to PIL RGB format
            pil_frame = Image.fromarray(cv2.cvtColor(all_frames[frame_idx], cv2.COLOR_BGR2RGB))
            
            # Analyze and extend the frame
            extended_frame = self.ai_extender.analyze_frame_and_extend(pil_frame)
            
            # Convert back to OpenCV format
            keyframes[frame_idx] = cv2.cvtColor(np.array(extended_frame), cv2.COLOR_RGB2BGR)
        
        # Second pass: write all frames with interpolation
        print(f"Second pass: Writing video with interpolation...")
        
        for frame_idx in range(total_frames):
            if frame_idx in keyframes:
                video_writer.write(keyframes[frame_idx])
            else:
                # Find nearest keyframes for interpolation
                prev_keyframe_idx = (frame_idx // keyframe_interval) * keyframe_interval
                next_keyframe_idx = prev_keyframe_idx + keyframe_interval
                
                # Handle edge cases
                if next_keyframe_idx >= total_frames:
                    next_keyframe_idx = prev_keyframe_idx
                
                if prev_keyframe_idx in keyframes and next_keyframe_idx in keyframes:
                    prev_frame = keyframes[prev_keyframe_idx]
                    next_frame = keyframes[next_keyframe_idx]
                    
                    # Calculate interpolation factor
                    if next_keyframe_idx > prev_keyframe_idx:
                        blend_factor = (frame_idx - prev_keyframe_idx) / (next_keyframe_idx - prev_keyframe_idx)
                    else:
                        blend_factor = 0
                    
                    # Blend the frames
                    blended_frame = cv2.addWeighted(prev_frame, 1 - blend_factor, next_frame, blend_factor, 0)
                    video_writer.write(blended_frame)
                else:
                    # Fallback to nearest keyframe
                    nearest_keyframe = prev_keyframe_idx if prev_keyframe_idx in keyframes else next_keyframe_idx
                    video_writer.write(keyframes[nearest_keyframe])
        
        video_writer.release()
        
        # Convert to H.264
        try:
            temp_output = output_path + ".temp.mp4"
            cmd = f'ffmpeg -y -i "{output_path}" -c:v libx264 -preset fast -crf 22 "{temp_output}"'
            result = os.system(cmd)
            if result == 0 and os.path.exists(temp_output):
                os.replace(temp_output, output_path)
                print(f"Converted video to H.264 format")
            else:
                print(f"FFmpeg conversion failed, keeping original format")
        except Exception as e:
            print(f"Failed to convert to H.264: {e}")
        
        return output_path