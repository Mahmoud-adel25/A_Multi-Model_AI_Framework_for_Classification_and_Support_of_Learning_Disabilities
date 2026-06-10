"""
Image Processing Utilities for Learning Disability Detection System

This module provides image preprocessing functions for handwriting
analysis and classification.
"""

import io
from PIL import Image, ImageOps, ImageFilter, ImageEnhance
import numpy as np
from typing import Tuple, Optional


class ImageProcessor:
    """
    Image processing utilities for handwriting images.
    
    Provides methods for:
    - Loading and validating images
    - Preprocessing for model input
    - Enhancement and noise reduction
    - Visualization helpers
    """
    
    # Supported image formats
    SUPPORTED_FORMATS = {'.png', '.jpg', '.jpeg', '.bmp', '.tiff', '.webp'}
    
    # Default image size for models
    DEFAULT_SIZE = (224, 224)
    
    @staticmethod
    def load_image(file_or_path) -> Optional[Image.Image]:
        """
        Load an image from file path or file-like object.
        
        Args:
            file_or_path: File path string or file-like object (e.g., UploadedFile)
            
        Returns:
            PIL Image or None if loading fails
        """
        try:
            if isinstance(file_or_path, str):
                image = Image.open(file_or_path)
            else:
                # File-like object (e.g., Streamlit UploadedFile)
                image = Image.open(file_or_path)
            
            # Ensure image is loaded
            image.load()
            return image
        except Exception as e:
            print(f"Error loading image: {e}")
            return None
    
    @staticmethod
    def validate_image(image: Image.Image) -> Tuple[bool, str]:
        """
        Validate an image for processing.
        
        Args:
            image: PIL Image to validate
            
        Returns:
            Tuple of (is_valid, message)
        """
        if image is None:
            return False, "No image provided"
        
        # Check minimum size
        min_size = 32
        if image.width < min_size or image.height < min_size:
            return False, f"Image too small. Minimum size: {min_size}x{min_size}"
        
        # Check maximum size (to prevent memory issues)
        max_size = 4096
        if image.width > max_size or image.height > max_size:
            return False, f"Image too large. Maximum size: {max_size}x{max_size}"
        
        return True, "Image is valid"
    
    @staticmethod
    def preprocess_for_display(image: Image.Image, max_display_size: int = 400) -> Image.Image:
        """
        Prepare an image for display in the UI.
        
        Args:
            image: PIL Image to process
            max_display_size: Maximum dimension for display
            
        Returns:
            Processed PIL Image
        """
        # Calculate new size maintaining aspect ratio
        ratio = min(max_display_size / image.width, max_display_size / image.height)
        
        if ratio < 1:
            new_size = (int(image.width * ratio), int(image.height * ratio))
            image = image.resize(new_size, Image.Resampling.LANCZOS)
        
        return image
    
    @staticmethod
    def enhance_handwriting(image: Image.Image, 
                           contrast_factor: float = 1.5,
                           sharpness_factor: float = 1.2) -> Image.Image:
        """
        Enhance handwriting visibility in an image.
        
        Args:
            image: PIL Image to enhance
            contrast_factor: Contrast enhancement factor (1.0 = no change)
            sharpness_factor: Sharpness enhancement factor (1.0 = no change)
            
        Returns:
            Enhanced PIL Image
        """
        # Convert to RGB if necessary
        if image.mode != 'RGB':
            image = image.convert('RGB')
        
        # Enhance contrast
        enhancer = ImageEnhance.Contrast(image)
        image = enhancer.enhance(contrast_factor)
        
        # Enhance sharpness
        enhancer = ImageEnhance.Sharpness(image)
        image = enhancer.enhance(sharpness_factor)
        
        return image
    
    @staticmethod
    def binarize_image(image: Image.Image, threshold: int = 128) -> Image.Image:
        """
        Convert image to binary (black and white).
        
        Args:
            image: PIL Image to binarize
            threshold: Threshold value (0-255)
            
        Returns:
            Binarized PIL Image
        """
        # Convert to grayscale
        grayscale = image.convert('L')
        
        # Apply threshold
        binary = grayscale.point(lambda x: 255 if x > threshold else 0, '1')
        
        return binary
    
    @staticmethod
    def remove_noise(image: Image.Image, filter_size: int = 3) -> Image.Image:
        """
        Remove noise from handwriting image using median filter.
        
        Args:
            image: PIL Image to denoise
            filter_size: Size of median filter
            
        Returns:
            Denoised PIL Image
        """
        return image.filter(ImageFilter.MedianFilter(size=filter_size))
    
    @staticmethod
    def normalize_orientation(image: Image.Image) -> Image.Image:
        """
        Fix image orientation based on EXIF data.
        
        Args:
            image: PIL Image to normalize
            
        Returns:
            Orientation-corrected PIL Image
        """
        return ImageOps.exif_transpose(image)
    
    @staticmethod
    def prepare_for_model(image: Image.Image, 
                         target_size: Tuple[int, int] = DEFAULT_SIZE,
                         grayscale: bool = False) -> Image.Image:
        """
        Prepare image for model inference.
        
        Args:
            image: PIL Image to prepare
            target_size: Target size (width, height)
            grayscale: Whether to convert to grayscale
            
        Returns:
            Prepared PIL Image
        """
        # Fix orientation
        image = ImageProcessor.normalize_orientation(image)
        
        # Convert mode
        if grayscale:
            image = image.convert('L')
        else:
            image = image.convert('RGB')
        
        # Resize with high-quality resampling
        image = image.resize(target_size, Image.Resampling.LANCZOS)
        
        return image
    
    @staticmethod
    def image_to_bytes(image: Image.Image, format: str = 'PNG') -> bytes:
        """
        Convert PIL Image to bytes.
        
        Args:
            image: PIL Image to convert
            format: Output format (PNG, JPEG, etc.)
            
        Returns:
            Image as bytes
        """
        buffer = io.BytesIO()
        image.save(buffer, format=format)
        buffer.seek(0)
        return buffer.getvalue()
    
    @staticmethod
    def get_image_info(image: Image.Image) -> dict:
        """
        Get information about an image.
        
        Args:
            image: PIL Image
            
        Returns:
            Dictionary with image information
        """
        return {
            "width": image.width,
            "height": image.height,
            "mode": image.mode,
            "format": image.format,
            "size_pixels": image.width * image.height
        }
