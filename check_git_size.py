import subprocess

def get_blobs():
    # Get all objects in HEAD
    cmd = ["git", "rev-list", "--objects", "HEAD"]
    result = subprocess.check_output(cmd).decode("utf-8")
    lines = result.strip().splitlines()
    blobs = []
    for line in lines:
        parts = line.split(" ", 1)
        sha = parts[0]
        name = parts[1] if len(parts) > 1 else ""
        blobs.append((sha, name))
    return blobs

def check_size(sha):
    cmd = ["git", "cat-file", "-s", sha]
    try:
        size = int(subprocess.check_output(cmd).decode("utf-8").strip())
        return size
    except:
        return 0

print("Checking large files in HEAD...")
blobs = get_blobs()
found_large = False
for sha, name in blobs:
    size = check_size(sha)
    if size > 1024 * 1024: # > 1MB
        print(f"Large File: {name} | Size: {size/1024/1024:.2f} MB")
        found_large = True

if not found_large:
    print("No files > 1MB found in HEAD.")
