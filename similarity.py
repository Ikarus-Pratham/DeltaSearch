import torch
import clip
from PIL import Image
import cv2
from typing import Optional

class ImageSimilarityComparator:
    """A class to compare two images using edge-based and raw image CLIP feature similarity."""

    def __init__(self, model_name: str = "ViT-B/32", device: Optional[str] = None) -> None:
        """
        Initialize the comparator with a CLIP model.
        
        Args:
            model_name (str): Name of the CLIP model to use (default: ViT-B/32)
            device (Optional[str]): Device to run the model on (default: cuda if available, else cpu)
        """
        self.device: str = device if device else ("cuda" if torch.cuda.is_available() else "cpu")
        self.model, self.preprocess = clip.load(model_name, device=self.device)
    
    def load_edge_image(self, path: str) -> torch.Tensor:
        """
        Load an image, apply Canny edge detection, and preprocess for CLIP.
        
        Args:
            path (str): Path to the image file
            
        Returns:
            torch.Tensor: Preprocessed edge-detected image tensor
        """
        # Load image as grayscale
        img = cv2.imread(path, cv2.IMREAD_GRAYSCALE)
        if img is None:
            raise FileNotFoundError(f"Could not load image at {path}")
        
        # Apply Canny edge detection
        edges = cv2.Canny(img, threshold1=100, threshold2=200)
        
        # Convert to RGB format expected by CLIP
        edges_rgb = cv2.cvtColor(edges, cv2.COLOR_GRAY2RGB)
        
        # Convert to PIL image and preprocess
        pil_img: Image.Image = Image.fromarray(edges_rgb)
        return self.preprocess(pil_img).unsqueeze(0).to(self.device)
    
    def load_raw_image(self, path: str) -> torch.Tensor:
        """
        Load and preprocess a raw image for CLIP.
        
        Args:
            path (str): Path to the image file
            
        Returns:
            torch.Tensor: Preprocessed raw image tensor
        """
        # Load image
        img = Image.open(path).convert("RGB")
        if img is None:
            raise FileNotFoundError(f"Could not load image at {path}")
        
        # Preprocess for CLIP
        return self.preprocess(img).unsqueeze(0).to(self.device)
    
    def compare_images(self, image_path1: str, image_path2: str, edge_weight: float = 0.6, raw_weight: float = 0.4) -> Optional[float]:
        """
        Compare two images using edge-based and raw image CLIP feature similarity with specified weights.
        
        Args:
            image_path1 (str): Path to the first image
            image_path2 (str): Path to the second image
            edge_weight (float): Weight for edge-based similarity (default: 0.6)
            raw_weight (float): Weight for raw image similarity (default: 0.4)
            
        Returns:
            Optional[float]: Weighted cosine similarity score between the two images, None if error occurs
        """
        try:
            # Load and preprocess edge-detected images
            edge_image1: torch.Tensor = self.load_edge_image(image_path1)
            edge_image2: torch.Tensor = self.load_edge_image(image_path2)
            
            # Load and preprocess raw images
            raw_image1: torch.Tensor = self.load_raw_image(image_path1)
            raw_image2: torch.Tensor = self.load_raw_image(image_path2)
            
            # Encode images to get feature vectors
            with torch.no_grad():
                edge_features1: torch.Tensor = self.model.encode_image(edge_image1)
                edge_features2: torch.Tensor = self.model.encode_image(edge_image2)
                raw_features1: torch.Tensor = self.model.encode_image(raw_image1)
                raw_features2: torch.Tensor = self.model.encode_image(raw_image2)
            
            # Compute cosine similarities
            edge_similarity: float = torch.cosine_similarity(edge_features1, edge_features2).item()
            raw_similarity: float = torch.cosine_similarity(raw_features1, raw_features2).item()
            
            # Combine similarities with 60:40 ratio
            combined_similarity: float = (edge_weight * edge_similarity) + (raw_weight * raw_similarity)
            return combined_similarity
            
        except Exception as e:
            print(f"Error comparing images: {str(e)}")
            return None