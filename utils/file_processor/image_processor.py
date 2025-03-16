"""
Module for processing and analyzing medical images.
"""
import os
import tempfile
import logging
import numpy as np
from PIL import Image, ImageEnhance, ImageFilter
import io

# Try to import pytesseract for OCR (optional)
try:
    import pytesseract
    HAS_PYTESSERACT = True
except ImportError:
    HAS_PYTESSERACT = False
    
# Internal imports
from .text_processor import process_text_chunk

logger = logging.getLogger(__name__)

def process_image_file(file, model, tokenizer, device):
    """Process an image file with medical content using OCR"""
    try:
        # Save the uploaded file temporarily
        with tempfile.NamedTemporaryFile(suffix='.jpg', delete=False) as temp_file:
            temp_path = temp_file.name
            file.save(temp_path)
        
        # Open the image for analysis
        image = Image.open(temp_path)
        
        # Extract basic image metadata
        width, height = image.size
        format_name = image.format or "Unknown"
        mode = image.mode
        
        # 1. Extract text using OCR if available
        extracted_text = ""
        if HAS_PYTESSERACT:
            try:
                # Preprocess the image for better OCR results
                ocr_image = preprocess_for_ocr(image)
                # Perform OCR
                extracted_text = pytesseract.image_to_string(ocr_image)
                logger.info(f"OCR extracted {len(extracted_text)} characters of text")
            except Exception as e:
                logger.error(f"OCR error: {str(e)}")
                extracted_text = f"OCR failed: {str(e)}"
        else:
            extracted_text = "OCR not available - install pytesseract for text extraction"
        
        # 2. Basic image analysis
        image_analysis = analyze_medical_image(image)
        
        # Create a summary for the model to process
        summary = f"""
Medical Image Analysis:
- Dimensions: {width}x{height}
- Format: {format_name}
- Color Mode: {mode}
- File Size: {os.path.getsize(temp_path) / 1024:.1f} KB

Image Characteristics:
{image_analysis}

OCR Extracted Text:
{extracted_text}
"""
        
        # Process the summary with the model
        result = process_text_chunk(summary, model, tokenizer, device)
        
        # Return the results
        return {
            "file_type": "image",
            "dimensions": f"{width}x{height}",
            "format": format_name,
            "has_text": len(extracted_text) > 20,  # True if significant text was found
            "response": result.get("response", "No analysis available.")
        }
    finally:
        # Clean up the temporary file
        if 'temp_path' in locals():
            try:
                os.unlink(temp_path)
            except:
                pass

def preprocess_for_ocr(image):
    """Preprocess an image to improve OCR results"""
    try:
        # Convert to grayscale if not already
        if image.mode != 'L':
            image = image.convert('L')
        
        # Resize very large images for better OCR performance
        max_dimension = 3000
        if max(image.size) > max_dimension:
            ratio = max_dimension / max(image.size)
            new_size = (int(image.size[0] * ratio), int(image.size[1] * ratio))
            image = image.resize(new_size, Image.LANCZOS)
        
        # Enhance contrast
        enhancer = ImageEnhance.Contrast(image)
        image = enhancer.enhance(1.5)
        
        # Apply slight sharpening
        image = image.filter(ImageFilter.SHARPEN)
        
        # Apply noise reduction
        image = image.filter(ImageFilter.MedianFilter(size=3))
        
        return image
    except Exception as e:
        logger.error(f"Image preprocessing error: {str(e)}")
        return image  # Return original if preprocessing fails

def analyze_medical_image(image):
    """Perform basic image analysis relevant to medical images"""
    try:
        # Convert to numpy array for analysis
        img_array = np.array(image)
        
        # Detect if grayscale (like X-rays, CT scans) or color (like dermatology)
        image_type = "Grayscale" if (len(img_array.shape) < 3 or img_array.shape[2] == 1) else "Color"
        
        # Calculate basic statistics
        if image_type == "Grayscale":
            if len(img_array.shape) == 3:
                img_array = img_array[:,:,0]  # Take first channel if 3D with one channel
                
            mean_intensity = np.mean(img_array)
            min_intensity = np.min(img_array)
            max_intensity = np.max(img_array)
            std_intensity = np.std(img_array)
            
            # Basic image classification (simplified)
            image_category = "Unknown"
            if mean_intensity < 100:  # Darker images like X-rays
                image_category = "Possibly X-ray or CT scan (darker image)"
            else:
                image_category = "Possibly ultrasound or MRI (lighter image)"
                
            # Calculate histogram distribution
            histogram_desc = ""
            hist_bins = np.bincount(img_array.flatten())
            peaks = []
            for i in range(1, len(hist_bins)-1):
                if hist_bins[i] > hist_bins[i-1] and hist_bins[i] > hist_bins[i+1] and hist_bins[i] > np.mean(hist_bins):
                    peaks.append(i)
            
            if len(peaks) == 1:
                histogram_desc = "Unimodal intensity distribution (typical of plain radiographs)"
            elif len(peaks) == 2:
                histogram_desc = "Bimodal intensity distribution (may indicate clear foreground/background separation)"
            elif len(peaks) > 2:
                histogram_desc = f"Multi-modal intensity distribution with {len(peaks)} peaks"
                
            # Generate analysis summary
            analysis = f"""
- Image Type: {image_type}, likely {image_category} 
- Mean Intensity: {mean_intensity:.1f}
- Intensity Range: {min_intensity} to {max_intensity}
- Standard Deviation: {std_intensity:.1f}
- {histogram_desc}
"""
        else:
            # Color image analysis (e.g., dermatology, ophthalmology)
            mean_r = np.mean(img_array[:,:,0])
            mean_g = np.mean(img_array[:,:,1])
            mean_b = np.mean(img_array[:,:,2])
            
            # Guess image category
            image_category = "Unknown"
            
            if mean_r > 1.5*mean_b:
                image_category = "Possibly dermatology (skin) image with reddish tones"
            elif mean_g > mean_r and mean_g > mean_b:
                image_category = "Possibly stained microscopy or endoscopy with greenish tones"
            
            analysis = f"""
- Image Type: {image_type}, possibly medical photography
- Possible Category: {image_category}
- Average RGB Values: R={mean_r:.1f}, G={mean_g:.1f}, B={mean_b:.1f}
- Color Distribution: {'Primarily red' if mean_r > mean_g and mean_r > mean_b else ('Primarily green' if mean_g > mean_r and mean_g > mean_b else 'Primarily blue')}
"""
        
        return analysis
    except Exception as e:
        logger.error(f"Image analysis error: {str(e)}")
        return f"Image analysis failed: {str(e)}"
