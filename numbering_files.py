import os
import re
# note : Current Implementation: u can add new files to folder but dont delete after renaming by script.
# Settings
base_dir = "data/images/custom/IzzieBlake-04/"  # <-- change this
code = '04'  # Prefix for filenames
counter = 1

# Define allowed image extensions (lowercase)
valid_extensions = {'.png', '.jpg', '.jpeg', '.gif', '.bmp', '.tiff', '.webp'}
pattern = re.compile(rf"^{re.escape(code)}-(\d+)(\.[^.]+)?$", re.IGNORECASE)

all_files = []
for root, dirs, files in os.walk(base_dir):
    for file in files:
        all_files.append(os.path.join(root, file))

all_files.sort()

# Find max existing number in correctly named image files
max_number = 0
for file_path in all_files:
    filename = os.path.basename(file_path)
    ext = os.path.splitext(filename)[1].lower()
    if ext not in valid_extensions:
        continue
    match = pattern.match(filename)
    if match:
        number = int(match.group(1))
        if number > max_number:
            max_number = number

counter = max_number + 1

# Summary counters
renamed_count = 0
skipped_renamed = 0
skipped_non_image = 0
non_image_files = []  # Store non-image file paths
deleted_hidden_files = []  # Track deleted dotfiles

for file_path in all_files:
    dir_name = os.path.dirname(file_path)
    filename = os.path.basename(file_path)
    ext = os.path.splitext(filename)[1].lower()

    # Delete files that start with a dot (e.g., .DS_Store, .gitignore)
    if filename.startswith("."):
        os.remove(file_path)
        deleted_hidden_files.append(file_path)
        print(f"🗑️ Deleted hidden file: {file_path}")
        continue

    if ext not in valid_extensions:
        print(f"Skipping non-image file: {file_path}")
        skipped_non_image += 1
        non_image_files.append(file_path)
        continue

    if pattern.match(filename):
        print(f"Skipping already renamed file: {file_path}")
        skipped_renamed += 1
        continue

    new_filename = f"{code}-{counter}{ext}"
    new_path = os.path.join(dir_name, new_filename)

    os.rename(file_path, new_path)
    print(f"Renamed: {file_path} → {new_path}")
    counter += 1
    renamed_count += 1

# Final summary
print("\n📊 Summary:")
print(f"✅ Renamed files      : {renamed_count}")
print(f"⏩ Already renamed    : {skipped_renamed}")
print(f"❌ Non-image files    : {skipped_non_image}")
print(f"🗑️ Hidden files deleted : {len(deleted_hidden_files)}")
print(f"📁 Total processed    : {len(all_files)}")

# Show non-image files (if any)
if non_image_files:
    print("\n🔍 Non-image files detected:")
    for path in non_image_files:
        print(f" - {path}")
