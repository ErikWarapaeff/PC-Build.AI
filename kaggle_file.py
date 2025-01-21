import kagglehub

# Download latest version
path = kagglehub.dataset_download("warcoder/pc-parts")

print("Path to dataset files:", path)