import os
import replicate
import numpy as np
from PIL import Image, ImageFilter
import cv2
import time

class AIImageExtender:
    def __init__(self, api_token=None):
        self.api_token = api_token
        self.extension_cache = {}
        self.cache_hits = 0
        self.cache_misses = 0
        
        if api_token:
            os.environ['REPLICATE_API_TOKEN'] = api_token
    
    def analyze_frame_and_extend(self, image):
        """
        Center the original video and create extensions for top and bottom
        
        Args:
            image: PIL Image object (16:9 format)
            
        Returns:
            PIL Image in 9:16 format with AI-generated extensions
        """
        width, height = image.size
        
        # Calculate target 9:16 dimensions
        target_width = width
        target_height = int(width * 16 / 9)
        
        # Calculate how much space we need to add
        total_extension = target_height - height
        top_extension = total_extension // 2
        bottom_extension = total_extension - top_extension
        
        # Create 9:16 canvas
        new_img = Image.new("RGB", (target_width, target_height), (0, 0, 0))
        
        # Place original image in the center
        y_offset = top_extension
        new_img.paste(image, (0, y_offset))
        
        # Generate top extension
        top_ext = self._generate_ai_extension(image, "top", target_width, top_extension)
        new_img.paste(top_ext, (0, 0))
        
        # Generate bottom extension
        bottom_ext = self._generate_ai_extension(image, "bottom", target_width, bottom_extension)
        new_img.paste(bottom_ext, (0, y_offset + height))
        
        return new_img
    
    def _analyze_frame_content(self, image):
        """
        Analyze frame content to determine optimal placement
        
        Returns:
            "top", "bottom", or "center" based on content analysis
        """
        # Convert to numpy for analysis
        img_array = np.array(image)
        height, width = img_array.shape[:2]
        
        # Divide image into thirds
        top_third = img_array[:height//3]
        middle_third = img_array[height//3:2*height//3]
        bottom_third = img_array[2*height//3:]
        
        # Calculate edge density (more edges = more content)
        top_edges = self._calculate_edge_density(top_third)
        middle_edges = self._calculate_edge_density(middle_third)
        bottom_edges = self._calculate_edge_density(bottom_third)
        
        # Calculate color variance (more variance = more detail)
        top_variance = np.var(top_third)
        middle_variance = np.var(middle_third)
        bottom_variance = np.var(bottom_third)
        
        # Weighted score for content density
        top_score = top_edges * 0.7 + top_variance * 0.3
        middle_score = middle_edges * 0.7 + middle_variance * 0.3
        bottom_score = bottom_edges * 0.7 + bottom_variance * 0.3
        
        # Determine placement based on content distribution
        if top_score > middle_score and top_score > bottom_score:
            return "bottom"  # Place original at top, extend bottom
        elif bottom_score > middle_score and bottom_score > top_score:
            return "top"     # Place original at bottom, extend top
        else:
            return "bottom"  # Default to bottom placement
    
    def _calculate_edge_density(self, image_region):
        """Calculate edge density using Sobel operator"""
        gray = cv2.cvtColor(image_region, cv2.COLOR_RGB2GRAY)
        sobel_x = cv2.Sobel(gray, cv2.CV_64F, 1, 0, ksize=3)
        sobel_y = cv2.Sobel(gray, cv2.CV_64F, 0, 1, ksize=3)
        edge_magnitude = np.sqrt(sobel_x**2 + sobel_y**2)
        return np.mean(edge_magnitude)
    
    def _generate_ai_extension(self, image, position, width, extension_height):
        """
        Generate extension using Stable Diffusion
        
        Args:
            image: PIL Image object to extend
            position: "top" or "bottom"
            width: Width of extension
            extension_height: Height of extension
            
        Returns:
            PIL Image of the extension
        """
        if extension_height <= 0 or width <= 0:
            return Image.new("RGB", (width, max(1, extension_height)), (0, 0, 0))
        
        # Check cache first
        edge_region = image.crop((0, max(0, image.height - 20), width, image.height)) if position == "bottom" else image.crop((0, 0, width, min(20, image.height)))
        edge_hash = str(np.array(edge_region).sum())
        cache_key = f"{position}_{width}_{extension_height}_{edge_hash}"
        
        if cache_key in self.extension_cache:
            self.cache_hits += 1
            print(f"Using cached extension")
            return self.extension_cache[cache_key]
        
        self.cache_misses += 1
        
        try:
            if not self.api_token:
                print(f"Using fallback outpainting (no API key)")
                return self._fallback_extension(image, position, width, extension_height)
            
            # Use Stable Diffusion for outpainting
            print(f"Using Stable Diffusion for {position} extension ({width}x{extension_height})")
            extension = self._stable_diffusion_outpaint(image, position, width, extension_height)
            
            # Cache the result
            self.extension_cache[cache_key] = extension
            
            # Limit cache size
            if len(self.extension_cache) > 50:
                oldest_keys = list(self.extension_cache.keys())[:10]
                for key in oldest_keys:
                    del self.extension_cache[key]
            
            print(f"✅ Stable Diffusion extension created")
            return extension
            
        except Exception as e:
            print(f"Stable Diffusion failed: {e}")
            print(f"Using fallback outpainting instead")
            return self._fallback_extension(image, position, width, extension_height)
    
    def _stable_diffusion_outpaint(self, image, position, width, extension_height):
        """Use Stable Diffusion for outpainting"""
        if not self.api_token:
            raise Exception("No API token provided")
        
        # Prepare the image for outpainting
        image_bytes = self._pil_to_bytes(image)
        
        # Create prompt based on image analysis
        prompt = self._generate_prompt_from_image(image, position)
        
        # Use Replicate's Stable Diffusion 3.5 for better outpainting
        output = replicate.run(
            "stability-ai/stable-diffusion-3.5-large",
            input={
                "prompt": prompt,
                "cfg": 4.5,
                "num_inference_steps": 20
            }
        )
        
        # Convert result back to PIL Image
        import requests
        
        # Stable Diffusion 3.5 returns a different format
        if hasattr(output, 'url'):
            # New format with .url() method
            image_url = output.url()
            response = requests.get(image_url)
            generated_image = Image.open(io.BytesIO(response.content))
        elif isinstance(output, list) and len(output) > 0:
            # Old format with list
            response = requests.get(output[0])
            generated_image = Image.open(io.BytesIO(response.content))
        else:
            raise Exception("No output from Stable Diffusion")
        
        # Resize to match our extension dimensions
        generated_image = generated_image.resize((width, extension_height), Image.Resampling.LANCZOS)
        
        return generated_image
    
    def _generate_prompt_from_image(self, image, position):
        """Generate a prompt based on image content for Stable Diffusion 3.5"""
        # Analyze image content more intelligently
        img_array = np.array(image)
        
        # Calculate color distribution
        avg_color = np.mean(img_array, axis=(0, 1))
        std_color = np.std(img_array, axis=(0, 1))
        
        # Detect scene type based on color and variance
        is_bright = np.mean(avg_color) > 150
        has_high_variance = np.mean(std_color) > 50
        
        # Generate context-aware prompts for Stable Diffusion 3.5
        if position == "top":
            if avg_color[2] > avg_color[0] and avg_color[2] > avg_color[1]:  # Blue dominant
                return "beautiful sky, fluffy white clouds, atmospheric lighting, cinematic, photorealistic"
            elif avg_color[1] > avg_color[0] and avg_color[1] > avg_color[2]:  # Green dominant
                return "lush green landscape, rolling hills, natural environment, cinematic, photorealistic"
            else:
                return "natural landscape extension, seamless continuation, photorealistic, cinematic quality"
        else:  # bottom
            if avg_color[1] > avg_color[0] and avg_color[1] > avg_color[2]:  # Green dominant
                return "lush green grass, natural ground, earth tones, photorealistic, cinematic"
            elif avg_color[0] > avg_color[1] and avg_color[0] > avg_color[2]:  # Red dominant
                return "natural earth, ground texture, warm tones, photorealistic, cinematic"
            else:
                return "natural ground extension, seamless continuation, photorealistic, cinematic quality"
    
    def _pil_to_bytes(self, image):
        """Convert PIL image to bytes"""
        import io
        img_bytes = io.BytesIO()
        image.save(img_bytes, format='PNG')
        img_bytes.seek(0)
        return img_bytes
    
    def _fallback_extension(self, image, position, width, extension_height):
        """Improved fallback method using reflection and blur"""
        # Get edge region for reflection
        if position == "bottom":
            edge_height = min(extension_height * 2, image.height // 3)
            edge = image.crop((0, image.height - edge_height, width, image.height))
        else:
            edge_height = min(extension_height * 2, image.height // 3)
            edge = image.crop((0, 0, width, edge_height))
        
        # Create reflection
        if position == "bottom":
            reflection = edge.transpose(Image.Transpose.FLIP_TOP_BOTTOM)
        else:
            reflection = edge.transpose(Image.Transpose.FLIP_TOP_BOTTOM)
        
        # Apply blur for smoother transition
        reflection = reflection.filter(ImageFilter.GaussianBlur(radius=3))
        
        # Create gradient mask
        mask = Image.new('L', (width, edge_height), 0)
        for y in range(edge_height):
            alpha = int(255 * (1 - y / edge_height))
            for x in range(width):
                mask.putpixel((x, y), alpha)
        
        # Apply mask to reflection
        reflection.putalpha(mask)
        
        # Create base extension with average color
        np_img = np.array(edge)
        pixels = np_img.reshape(-1, 3)
        avg_color = tuple(map(int, np.mean(pixels, axis=0)))
        
        extension = Image.new("RGB", (width, extension_height), avg_color)
        
        # Paste reflection onto extension
        if edge_height < extension_height:
            # Center the reflection if it's smaller
            y_offset = (extension_height - edge_height) // 2
            extension.paste(reflection, (0, y_offset), reflection.getchannel('A'))
        else:
            # Crop reflection to fit
            reflection = reflection.crop((0, 0, width, extension_height))
            extension.paste(reflection, (0, 0), reflection.getchannel('A'))
        
        return extension