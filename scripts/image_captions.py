

import json
import random
from collections import OrderedDict

class CaptionGenerator:
    def __init__(self, config_path='configs/caption_config.json'):
        # Load configuration from JSON file
        with open(config_path, 'r', encoding='utf-8') as f:
            config = json.load(f)
        
        # Store the loaded configuration
        self.tag_formatters = config['tag_formatters']
        self.feature_order = config['feature_order']
        self.templates = config['templates']
        
        # Initialize template functions
        self.init_template_functions()

    def init_template_functions(self):
        """Convert template strings to callable functions"""
        self.template_funcs = []
        for template in self.templates:
            if isinstance(template, str):
                # Convert string templates to lambda functions
                self.template_funcs.append(
                    lambda c, f, t=template: t.format(character=c, features=f)
                )
            else:
                # Keep existing callable templates
                self.template_funcs.append(template)

    def format_character(self, tags):
        """Build character description from available tags"""
        parts = []
        
        # Handle gender tags
        if '1girl' in tags:
            parts.append(random.choice(self.tag_formatters['1girl']))
        elif '1boy' in tags:
            parts.append(random.choice(self.tag_formatters['1boy']))
        else:
            parts.append("a person")
        
        # Handle solo tag
        if 'solo' in tags:
            parts.append(random.choice(self.tag_formatters['solo']))
        
        return ' '.join(parts)

    def format_features(self, tags):
        """Convert all feature tags into natural phrases"""
        features = {category: [] for category in self.feature_order}
        
        # Process each tag
        for tag in tags:
            matched = False
            
            # Skip character tags as they're handled separately
            if tag in ['1girl', '1boy', 'solo']:
                continue
                
            # Check all formatters for matching tags
            for category, formatter in self.tag_formatters.items():
                # Skip character formatters
                if category in ['1girl', '1boy', 'solo', 'other']:
                    continue
                    
                if isinstance(formatter, dict) and tag in formatter:
                    # Get a random variation if it's a list
                    if isinstance(formatter[tag], list):
                        chosen = random.choice(formatter[tag])
                    else:
                        chosen = formatter[tag]
                        
                    # Add to the appropriate category
                    if category in features:
                        features[category].append(chosen)
                    else:
                        features['other'].append(chosen)
                    matched = True
                    break
            
            # Handle unmatched tags
            if not matched:
                # Use the 'other' formatter if available
                if 'other' in self.tag_formatters:
                    if '_default' in self.tag_formatters['other']:
                        if self.tag_formatters['other']['_default'] == 'replace_underscores':
                            features['other'].append(tag.replace('_', ' '))
                        else:
                            features['other'].append(tag)
                    else:
                        features['other'].append(tag.replace('_', ' '))
                else:
                    features['other'].append(tag.replace('_', ' '))
        
        # Build hair description by combining length, style and color
        hair_parts = []
        for hair_type in ['hair_length', 'hair_style', 'hair_color']:
            if hair_type in self.tag_formatters:
                for tag, desc in self.tag_formatters[hair_type].items():
                    if tag in tags:
                        if isinstance(desc, list):
                            hair_parts.append(random.choice(desc))
                        else:
                            hair_parts.append(desc)
                        break
        
        if hair_parts:
            features['hair'].insert(0, ' '.join(hair_parts) + ' hair')
        
        # Build eye description by combining color and state
        eye_parts = []
        color_set = False
        for eye_type in ['eye_color', 'eye_state']:
            if eye_type in self.tag_formatters:
                for tag, desc in self.tag_formatters[eye_type].items():
                    if tag in tags:
                        if eye_type == 'eye_color' and not color_set:
                            if isinstance(desc, list):
                                eye_parts.insert(0, random.choice(desc))
                            else:
                                eye_parts.insert(0, desc)
                            color_set = True
                        elif eye_type == 'eye_state':
                            if isinstance(desc, list):
                                eye_parts.append(random.choice(desc))
                            else:
                                eye_parts.append(desc)
                        break
        
        if eye_parts:
            if len(eye_parts) > 1:
                features['eyes'].append(f"{eye_parts[0]} eyes that are {eye_parts[1]}")
            else:
                features['eyes'].append(f"{eye_parts[0]} eyes")
        
        # Compile all features in order
        compiled = []
        for category in self.feature_order:
            if features[category]:  # Only add if not empty
                compiled.extend(features[category])
        
        # Join with proper grammar
        if not compiled:
            return ""
        elif len(compiled) == 1:
            return compiled[0]
        else:
            return ', '.join(compiled[:-1]) + ' and ' + compiled[-1]

    def generate_caption(self, tags):
        """Generate caption preserving all tag meanings"""
        # Format components
        character = self.format_character(tags)
        features = self.format_features(tags)
        
        # Select and apply template
        template = random.choice(self.template_funcs)
        caption = template(character, features)
        
        # Final cleanup
        caption = caption.replace(" ,", ",").replace(" .", ".")
        caption = caption[0].upper() + caption[1:]
        return caption
    

if __name__ == "__main__":
    # Example usage
    import torch
    from image_tags import get_tags
    import os
    # get device
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    generator = CaptionGenerator()

    img_dir = 'data/ns/'
    for filename in os.listdir(img_dir):
        img_path = os.path.join(img_dir, filename)
        tags = get_tags(image_path=img_path, device=device)
        caption = generator.generate_caption(tags)
        print(f"tags: {tags}")
        print(f"filename: {img_path}, -> {caption} (Words: {len(caption.split())}) ")

