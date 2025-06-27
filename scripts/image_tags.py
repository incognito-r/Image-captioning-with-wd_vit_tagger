# the purpose of thins script is to return filtered tags
import torch
import timm
from torchvision import transforms
from PIL import Image
import pandas as pd
from huggingface_hub import hf_hub_download
import cv2
import random
import numpy as np


# raw tags from wd-tagger
def get_raw_tags(image_path, device):

    # download model for tagging wd-tagger
    model_path = hf_hub_download(repo_id="SmilingWolf/wd-vit-tagger-v3", filename="model.safetensors")

    # Load model directly from Hugging Face via timm
    model = timm.create_model("hf_hub:SmilingWolf/wd-vit-tagger-v3", pretrained=True)
    model.eval().to(device)

    # Load tag names
    tag_df = pd.read_csv("utils/wd_tags.csv")
    tag_names = tag_df["name"].tolist()

    # Resize to 448x448
    transform = transforms.Compose([
        transforms.Resize((448, 448)),
        transforms.ToTensor(),
    ])

    # Load and process image
    image = Image.open(image_path).convert("RGB")
    image_tensor = transform(image).unsqueeze(0).to(device)

    # Inference
    with torch.no_grad():
        output = model(image_tensor)[0]
        probs = torch.sigmoid(output).cpu().numpy()

    # Get tags above threshold
    threshold = 0.5
    wd_tags = [tag for tag, prob in zip(tag_names, probs) if prob > threshold]

    return wd_tags # returns list containing tags


def filter_tags(image_path, device):
    # get tags
    tags = get_raw_tags(image_path, device)

    block_tags = ['blue_skin', 'colored_skin'] # remove these tags if present in tags
    filtered_tags = [tag for tag in tags if tag not in block_tags]

    return filtered_tags

def get_skin_color(image_path, min_skin_area=0.05):

    # Load image and convert to HSV
    image = cv2.imread(image_path)
    if image is None:
        return None
    hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
    
        # Define HSV ranges for different skin tones (adjust as needed)
    skin_ranges = {
        "pale_skin":   ((0, 15, 60), (25, 150, 255)),
        "fair_skin":   ((0, 20, 70), (25, 180, 255)),
        "tan_skin":    ((5, 40, 80), (25, 200, 230)),
        "brown_skin":  ((0, 50, 60), (25, 255, 200)),
        "dark_skin":   ((0, 70, 40), (25, 255, 150)),
    }

    # Detect skin regions
    skin_masks = {}
    for skin_type, ((h_low, s_low, v_low), (h_high, s_high, v_high)) in skin_ranges.items():
        lower = np.array([h_low, s_low, v_low], dtype=np.uint8)
        upper = np.array([h_high, s_high, v_high], dtype=np.uint8)
        mask = cv2.inRange(hsv, lower, upper)
        skin_masks[skin_type] = mask
    
    # Find the dominant skin tone
    dominant_skin = "fair_skin"
    max_pixels = 0
    total_pixels = image.shape[0] * image.shape[1]
    
    for skin_type, mask in skin_masks.items():
        skin_pixels = cv2.countNonZero(mask)
        if skin_pixels > max_pixels and skin_pixels / total_pixels >= min_skin_area:
            max_pixels = skin_pixels
            dominant_skin = skin_type
    
    return dominant_skin


def get_tags(image_path, device):

    filtered_tags = filter_tags(image_path, device)
    # get skin color
    skin_color = get_skin_color(image_path)
    # add to filtered tags at random place
    filtered_tags.insert(random.randint(0, len(filtered_tags)), skin_color)
    return filtered_tags


if __name__ == "__main__":
    # Set up device
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    image_path = 'test3.jpg'

    # get filtered tags
    tags = get_tags(image_path, device)

    print(tags)