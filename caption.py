# this file gets caption for the respective images and save them in file with filename and text.

# imports
import os
import torch
import json
from scripts.image_captions import CaptionGenerator
from scripts.image_tags import get_tags
import argparse

def save_jsonl(captions, file_path = 'data/captions.jsonl'):
    with open(file_path, 'w') as f:
        for file, caption in captions.items():
            entry = {"file_name": file, "text": caption}
            f.write(json.dumps(entry) + '\n')

def main():
    parser = argparse.ArgumentParser(description='Generate captions for images in a directory and save as JSONL.')
    parser.add_argument('--root_dir', type=str, default='data/images/custom', help='Root directory containing images')
    args = parser.parse_args()

    # Ensure logs directory exists
    os.makedirs('logs', exist_ok=True)
    corrupted_log_path = os.path.join('logs', 'corrupted_files.txt')

    root_dir = args.root_dir
    caption_path = 'data/captions.jsonl'

    generator = CaptionGenerator()
    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')

    # Load existing captions if present
    captions = {}
    if os.path.exists(caption_path):
        with open(caption_path, 'r') as f:
            for line in f:
                entry = json.loads(line)
                captions[entry["file_name"]] = entry["text"]

    counter = 0
    for root, dirs, files in os.walk(root_dir):
        for file in files:
            # Skip hidden files
            if file.startswith('.'):
                continue
            if captions.get(file):
                continue
            filepath = os.path.join(root, file)
            try:
                tags = get_tags(image_path=filepath, device=device)
                caption = generator.generate_caption(tags)
                captions[file] = caption
                # save after every 5 images
                if counter % 5 == 0:
                    save_jsonl(captions)
                counter += 1
                print(f"Processed: {file}")
            except Exception as e:
                print(f"[WARNING] Could not process: {e}")
                # Log corrupted file to logs/corrupted_files.txt
                with open(corrupted_log_path, 'a') as clog:
                    clog.write(filepath + '\n')
                continue

    # Save all captions in LAION-style JSONL
    save_jsonl(captions)
    print(f"✅ total files captioned: {counter}")

if __name__ == "__main__":
    main()