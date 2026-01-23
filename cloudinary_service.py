import cloudinary
import cloudinary.uploader
import os

# Try to load environment variables from .env file if it exists
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

# Configure Cloudinary with environment variables or hardcoded values
cloudinary.config(
    cloud_name=os.getenv("CLOUDINARY_CLOUD_NAME", "dwt710mdu"),
    api_key=os.getenv("CLOUDINARY_API_KEY", "946233553338359"),
    api_secret=os.getenv("CLOUDINARY_API_SECRET", "e9E1rxvU3WfxwOjJsARP7ZrutuE")
)

def upload_file(file, folder="elibra", resource_type="auto"):
    """
    Upload a file to Cloudinary
    
    Args:
        file: File object to upload
        folder: Folder name in Cloudinary
        resource_type: Type of resource (auto, image, video, raw)
    
    Returns:
        dict: Upload response from Cloudinary
    """
    try:
        result = cloudinary.uploader.upload(
            file,
            folder=folder,
            resource_type=resource_type,
            use_filename=True,
            unique_filename=True
        )
        return result
    except Exception as e:
        print(f"Cloudinary upload error: {str(e)}")
        raise

def upload_image(file, folder="elibra/images"):
    """Upload an image file to Cloudinary"""
    return upload_file(file, folder, "image")

def upload_pdf(file, folder="elibra/pdfs"):
    """Upload a PDF file to Cloudinary"""
    return upload_file(file, folder, "raw")