import os
import shutil
import uuid
import zipfile
import subprocess
import re
from fastapi import UploadFile, HTTPException, status
from app.core.config import settings

class RepoManagerService:
    @staticmethod
    def validate_zip_file(file: UploadFile):
        # Validate extension
        if not file.filename.lower().endswith('.zip'):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid file format. Only ZIP archives are supported."
            )
            
    @staticmethod
    def process_zip_upload(file: UploadFile, user_id: uuid.UUID) -> str:
        # Verify size limit (if content_length is available)
        # We also limit reading length iteratively to prevent memory exhaustion
        user_upload_dir = os.path.join(settings.UPLOAD_DIR, str(user_id))
        os.makedirs(user_upload_dir, exist_ok=True)
        
        repo_id = uuid.uuid4()
        dest_dir = os.path.join(user_upload_dir, str(repo_id))
        os.makedirs(dest_dir, exist_ok=True)
        
        temp_zip_path = os.path.join(user_upload_dir, f"{repo_id}.zip")
        
        # Stream file to disk to avoid reading everything into memory
        size_counter = 0
        max_bytes = settings.MAX_UPLOAD_SIZE_MB * 1024 * 1024
        
        try:
            with open(temp_zip_path, "wb") as buffer:
                while chunk := file.file.read(8192):
                    size_counter += len(chunk)
                    if size_counter > max_bytes:
                        raise HTTPException(
                            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                            detail=f"File exceeds maximum allowed size of {settings.MAX_UPLOAD_SIZE_MB}MB."
                        )
                    buffer.write(chunk)
            
            # Securely extract ZIP file to destination
            with zipfile.ZipFile(temp_zip_path, 'r') as zip_ref:
                for member in zip_ref.infolist():
                    # Security safeguard: Prevent directory traversal vulnerability
                    target_path = os.path.abspath(os.path.join(dest_dir, member.filename))
                    real_dest_dir = os.path.abspath(dest_dir)
                    
                    if not target_path.startswith(real_dest_dir + os.sep) and target_path != real_dest_dir:
                        raise HTTPException(
                            status_code=status.HTTP_400_BAD_REQUEST,
                            detail="Security Error: ZIP archive contains paths attempting directory traversal."
                        )
                
                # Perform the safe extraction
                zip_ref.extractall(dest_dir)
                
            return dest_dir
            
        except zipfile.BadZipFile:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Corrupt or invalid ZIP archive file."
            )
        finally:
            # Clean up temporary ZIP file
            if os.path.exists(temp_zip_path):
                os.remove(temp_zip_path)

    @staticmethod
    def clone_git_repository(git_url: str, user_id: uuid.UUID) -> str:
        # Validate Git URL format (HTTP/HTTPS URL patterns to prevent command injections)
        # Matches: https://github.com/user/repo, http://gitlab.com/user/repo, etc.
        git_url_pattern = re.compile(
            r'^https?://([a-zA-Z0-9\-._~%!$&\'()*+,;=]+@)?[a-zA-Z0-9.-]+(:\d+)?(/([a-zA-Z0-9._~\-/?#\[\]@!$&\'()*+,;=])*)*$'
        )
        if not git_url_pattern.match(git_url):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid Git HTTP/HTTPS repository URL."
            )
            
        user_clone_dir = os.path.join(settings.CLONE_DIR, str(user_id))
        os.makedirs(user_clone_dir, exist_ok=True)
        
        repo_id = uuid.uuid4()
        dest_dir = os.path.join(user_clone_dir, str(repo_id))
        
        try:
            # Shallow clone with 30s timeout and disabled terminal prompts to fail fast
            env = os.environ.copy()
            env["GIT_TERMINAL_PROMPT"] = "0"
            result = subprocess.run(
                ["git", "clone", "--depth", "1", git_url, dest_dir],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                timeout=30, # 30 seconds max cloning duration
                env=env
            )
            
            if result.returncode != 0:
                # Log standard error from git clone
                error_msg = result.stderr.strip() if result.stderr else "Unknown git error"
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Failed to clone Git repository: {error_msg}"
                )
                
            return dest_dir
            
        except subprocess.TimeoutExpired:
            # Clean up partial directory if it exists
            if os.path.exists(dest_dir):
                shutil.rmtree(dest_dir)
            raise HTTPException(
                status_code=status.HTTP_408_REQUEST_TIMEOUT,
                detail="Git cloning operation timed out. The repository might be too large or private."
            )
        except Exception as e:
            if os.path.exists(dest_dir):
                shutil.rmtree(dest_dir)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"An unexpected error occurred during cloning: {str(e)}"
            )

    @staticmethod
    def cleanup_repository_files(file_path: str):
        if file_path and os.path.exists(file_path):
            try:
                if os.path.isdir(file_path):
                    shutil.rmtree(file_path)
                else:
                    os.remove(file_path)
            except Exception:
                # Log warning in production, but let process continue
                pass
