import os
from googleapiclient.discovery import build
from google.oauth2 import service_account
from googleapiclient.http import MediaFileUpload

SCOPES = ['https://www.googleapis.com/auth/drive']
SERVICE_ACCOUNT_FILE = 'skin-me-d7ca653e4674.json'
PARENT_FOLDER_ID = "1kVIST6Xh7defhrmfGa4Wvb0XvAMCwbkn"

def authenticate():
    creds = service_account.Credentials.from_service_account_file(SERVICE_ACCOUNT_FILE, scopes=SCOPES)
    return creds
    
def upload_file(file):
    if not file or not hasattr(file, 'filename') or not file.filename:
        raise ValueError("Invalid file object or missing filename")
    
    creds = authenticate()
    service = build('drive', 'v3', credentials=creds)
    
    file_path = None
    try:
        upload_folder = 'uploads'
        if not os.path.exists(upload_folder):
            os.makedirs(upload_folder)
        
        # Sanitize filename to avoid filesystem issues
        safe_filename = os.path.basename(file.filename)
        file_path = os.path.join(upload_folder, safe_filename)
        
        # Save file to disk using chunked reading for memory efficiency
        chunk_size = 8192
        bytes_written = 0
        with open(file_path, 'wb') as f:
            while True:
                chunk = file.read(chunk_size)
                if not chunk:
                    break
                f.write(chunk)
                bytes_written += len(chunk)
        
        # Check if file was actually written
        if bytes_written == 0:
            raise ValueError("File is empty")
        
        # Get file size to determine if we need resumable upload
        file_size = os.path.getsize(file_path)
        
        # For files larger than 5MB, use resumable upload with chunking
        # chunksize should be <= 5MB for Google App Engine compatibility
        if file_size > 5 * 1024 * 1024:
            # Use 1MB chunks for resumable uploads
            media = MediaFileUpload(
                file_path, 
                mimetype='application/pdf', 
                resumable=True,
                chunksize=1024*1024  # 1MB chunks
            )
        else:
            # For smaller files, use simple resumable upload
            media = MediaFileUpload(file_path, mimetype='application/pdf', resumable=True)
        
        file_metadata = {
            'name': file.filename,
            'parents': [PARENT_FOLDER_ID]
        }
        
        # Create the upload request
        request = service.files().create(
            body=file_metadata,
            media_body=media,
            fields='id, webViewLink'
        )
        
        # For resumable uploads, use next_chunk() to handle chunked uploads
        if file_size > 5 * 1024 * 1024:
            response = None
            while response is None:
                status, response = request.next_chunk()
                if status:
                    try:
                        progress = int(status.progress() * 100)
                        print(f"Upload progress: {progress}%")
                    except:
                        pass  # Progress reporting is optional
            uploaded_file = response
        else:
            # For smaller files, execute directly
            uploaded_file = request.execute()
        
        secure_url = uploaded_file.get('webViewLink', '')
        
        return secure_url
    except Exception as e:
        print(f"Error uploading file to Google Drive: {str(e)}")
        raise
    finally:
        if file_path and os.path.exists(file_path):
            try:
                os.remove(file_path)
            except Exception as e:
                print(f"Error while removing temporary file: {e}")
