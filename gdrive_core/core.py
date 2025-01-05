import os
import random
from time import sleep
from google.oauth2.credentials import Credentials
from google.oauth2 import service_account
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload, MediaIoBaseDownload, MediaIoBaseUpload
from typing import Optional, List, Dict, Any, BinaryIO, Union
import io
import mimetypes
import logging
from concurrent.futures import ThreadPoolExecutor

SCOPES = ['https://www.googleapis.com/auth/drive']

class GDriveCore:
    """Enhanced Google Drive API Client for comprehensive file and folder management."""

    def __init__(self, auth_type: str = 'oauth2', 
                 credentials_file: str = 'credentials.json',
                 token_file: str = 'token.json',
                 max_retries: int = 3) -> None:
        """Initialize the Google Drive client with flexible authentication.
        
        Args:
            auth_type: Authentication type ('oauth2' or 'service_account')
            credentials_file: Path to credentials JSON file
            token_file: Path for OAuth2 token storage
            max_retries: Maximum number of retry attempts for operations
        """
        self.service = self._authenticate(auth_type, credentials_file, token_file)
        self._page_size = 100
        self._chunk_size = 256 * 1024  # 256KB chunks
        self._max_retries = max_retries
        self._setup_logging()
        
        # Add commonly used mime types
        self.FOLDER_MIME_TYPE = 'application/vnd.google-apps.folder'
        self.DOCUMENT_MIME_TYPE = 'application/vnd.google-apps.document'
        self.SPREADSHEET_MIME_TYPE = 'application/vnd.google-apps.spreadsheet'

    def _setup_logging(self) -> None:
        """Configure logging for the client."""
        self.logger = logging.getLogger('GDriveCore')
        self.logger.setLevel(logging.INFO)
        handler = logging.StreamHandler()
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        handler.setFormatter(formatter)
        self.logger.addHandler(handler)

    def _execute_with_retry(self, request: Any) -> Any:
        """Execute a request with exponential backoff retry logic.
        
        Args:
            request: The Google API request object to execute
            
        Returns:
            The response from the API
            
        Raises:
            Exception: If all retry attempts fail
        """
        for attempt in range(self._max_retries):
            try:
                return request.execute()
            except Exception as e:
                if attempt == self._max_retries - 1:
                    raise
                sleep_time = (2 ** attempt) + random.random()
                self.logger.warning(f"Attempt {attempt + 1} failed, retrying in {sleep_time:.1f}s")
                sleep(sleep_time)

    def _authenticate(self, auth_type: str, credentials_file: str, 
                     token_file: str) -> Any:
        """Handle authentication based on specified type."""
        try:
            if auth_type == 'service_account':
                creds = service_account.Credentials.from_service_account_file(
                    credentials_file, scopes=SCOPES)
            else:
                creds = self._oauth2_auth(credentials_file, token_file)
            return build('drive', 'v3', credentials=creds)
        except Exception as e:
            self.logger.error(f"Authentication failed: {str(e)}")
            raise

    def _oauth2_auth(self, credentials_file: str, token_file: str) -> Credentials:
        """Handle OAuth2 authentication flow."""
        creds = None
        if os.path.exists(token_file):
            try:
                creds = Credentials.from_authorized_user_file(token_file, SCOPES)
            except ValueError:
                os.remove(token_file)
                creds = None

        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file(credentials_file, SCOPES)
                creds = flow.run_local_server(port=0)
            with open(token_file, 'w') as token:
                token.write(creds.to_json())
        return creds

    def upload(self, file_path: str, parent_id: Optional[str] = None, 
               properties: Optional[Dict[str, str]] = None,
               progress_callback: Optional[callable] = None) -> str:
        """Upload a file with progress tracking and custom properties."""
        try:
            file_name = os.path.basename(file_path)
            mime_type = mimetypes.guess_type(file_path)[0] or 'application/octet-stream'
            
            metadata = {
                'name': file_name,
                'mimeType': mime_type
            }
            if parent_id:
                metadata['parents'] = [parent_id]
            if properties:
                metadata['properties'] = properties

            media = MediaFileUpload(
                file_path,
                mimetype=mime_type,
                resumable=True,
                chunksize=self._chunk_size
            )

            request = self.service.files().create(
                body=metadata,
                media_body=media,
                fields='id'
            )

            response = None
            while response is None:
                status, response = request.next_chunk()
                if status and progress_callback:
                    progress_callback(status.progress() * 100)

            return response.get('id')

        except Exception as e:
            self.logger.error(f"Upload failed for {file_path}: {str(e)}")
            raise

    def upload_stream(self, file_obj: BinaryIO, filename: str,
                     mime_type: Optional[str] = None, **kwargs) -> str:
        """Upload a file from a stream."""
        if not mime_type:
            mime_type = mimetypes.guess_type(filename)[0] or 'application/octet-stream'
        
        metadata = {'name': filename, **kwargs}
        media = MediaIoBaseUpload(file_obj, mimetype=mime_type,
                                resumable=True, chunksize=self._chunk_size)
        
        request = self.service.files().create(
            body=metadata,
            media_body=media,
            fields='id'
        )
        
        response = None
        while response is None:
            _, response = request.next_chunk()
        return response['id']

    def download(self, file_id: str, local_path: str, 
                progress_callback: Optional[callable] = None) -> None:
        """Download a file with progress tracking."""
        try:
            request = self.service.files().get_media(fileId=file_id)
            with open(local_path, 'wb') as fh:
                downloader = MediaIoBaseDownload(fh, request, chunksize=self._chunk_size)
                done = False
                while not done:
                    status, done = downloader.next_chunk()
                    if status and progress_callback:
                        progress_callback(status.progress() * 100)
        except Exception as e:
            self.logger.error(f"Download failed for file {file_id}: {str(e)}")
            raise

    def download_stream(self, file_id: str) -> BinaryIO:
        """Download file as a stream."""
        request = self.service.files().get_media(fileId=file_id)
        fh = io.BytesIO()
        downloader = MediaIoBaseDownload(fh, request, chunksize=self._chunk_size)
        
        done = False
        while not done:
            _, done = downloader.next_chunk()
        fh.seek(0)
        return fh

    def list_files(self, query: Optional[str] = None, 
                   fields: str = "files(id, name, mimeType, modifiedTime)") -> List[Dict[str, str]]:
        """List files with customizable fields."""
        try:
            results = []
            page_token = None
            
            while True:
                response = self.service.files().list(
                    q=query,
                    fields=f"nextPageToken, {fields}",
                    pageSize=self._page_size,
                    pageToken=page_token
                ).execute()
                
                results.extend(response.get('files', []))
                page_token = response.get('nextPageToken')
                
                if not page_token:
                    break
                    
            return results
        except Exception as e:
            self.logger.error(f"List files failed: {str(e)}")
            raise

    def create_folder(self, folder_name: str, parent_id: Optional[str] = None) -> str:
        """Create a new folder."""
        try:
            metadata = {
                'name': folder_name,
                'mimeType': 'application/vnd.google-apps.folder'
            }
            if parent_id:
                metadata['parents'] = [parent_id]
                
            folder = self.service.files().create(
                body=metadata,
                fields='id'
            ).execute()
            return folder.get('id')
        except Exception as e:
            self.logger.error(f"Folder creation failed: {str(e)}")
            raise

    def delete(self, file_id: str) -> None:
        """Delete a file or folder."""
        try:
            self.service.files().delete(fileId=file_id).execute()
        except Exception as e:
            self.logger.error(f"Delete failed for file {file_id}: {str(e)}")
            raise

    def batch_delete(self, file_ids: List[str]) -> Dict[str, bool]:
        """Delete multiple files in parallel."""
        results = {}
        with ThreadPoolExecutor() as executor:
            futures = {executor.submit(self.delete, file_id): file_id 
                      for file_id in file_ids}
            for future in futures:
                file_id = futures[future]
                try:
                    future.result()
                    results[file_id] = True
                except Exception:
                    results[file_id] = False
        return results

    def move(self, file_id: str, new_parent_id: str, 
             old_parent_id: Optional[str] = None) -> Dict[str, Any]:
        """Move a file to a different folder."""
        try:
            return self.service.files().update(
                fileId=file_id,
                addParents=new_parent_id,
                removeParents=old_parent_id,
                fields='id, parents'
            ).execute()
        except Exception as e:
            self.logger.error(f"Move failed for file {file_id}: {str(e)}")
            raise

    def share(self, file_id: str, email: str, role: str = 'reader') -> Dict:
        """Share a file with specific permissions."""
        try:
            permission = {
                'type': 'user',
                'role': role,
                'emailAddress': email
            }
            return self.service.permissions().create(
                fileId=file_id,
                body=permission,
                sendNotificationEmail=True
            ).execute()
        except Exception as e:
            self.logger.error(f"Share failed for file {file_id}: {str(e)}")
            raise

    def get_file_metadata(self, file_id: str, fields: str = "*") -> Dict[str, Any]:
        """Get detailed file metadata."""
        try:
            return self.service.files().get(
                fileId=file_id,
                fields=fields
            ).execute()
        except Exception as e:
            self.logger.error(f"Get metadata failed for file {file_id}: {str(e)}")
            raise

    def update_metadata(self, file_id: str, metadata: Dict[str, Any]) -> Dict[str, Any]:
        """Update file metadata."""
        try:
            return self.service.files().update(
                fileId=file_id,
                body=metadata,
                fields='*'
            ).execute()
        except Exception as e:
            self.logger.error(f"Update metadata failed for file {file_id}: {str(e)}")
            raise

    def search(self, query_params: Dict[str, str]) -> List[Dict[str, str]]:
        """Advanced search with multiple parameters."""
        query_parts = []
        for key, value in query_params.items():
            if key == 'name_contains':
                query_parts.append(f"name contains '{value}'")
            elif key == 'mime_type':
                query_parts.append(f"mimeType='{value}'")
            elif key == 'trashed':
                query_parts.append(f"trashed = {value}")
        
        query = " and ".join(query_parts)
        return self.list_files(query=query)

    def get_file_revisions(self, file_id: str) -> List[Dict]:
        """Get revision history of a file."""
        try:
            revisions = self.service.revisions().list(fileId=file_id).execute()
            return revisions.get('revisions', [])
        except Exception as e:
            self.logger.error(f"Get revisions failed for file {file_id}: {str(e)}")
            raise

    def copy_file(self, file_id: str, new_name: Optional[str] = None) -> str:
        """Create a copy of a file."""
        try:
            body = {'name': new_name} if new_name else {}
            copied_file = self.service.files().copy(
                fileId=file_id,
                body=body
            ).execute()
            return copied_file['id']
        except Exception as e:
            self.logger.error(f"Copy failed for file {file_id}: {str(e)}")
            raise

    def get_storage_quota(self) -> Dict:
        """Get current storage quota information."""
        try:
            about = self.service.about().get(fields="storageQuota").execute()
            return about['storageQuota']
        except Exception as e:
            self.logger.error(f"Get storage quota failed: {str(e)}")
            raise

    def watch_file(self, file_id: str, webhook_url: str, expiration: Optional[int] = None) -> Dict[str, Any]:
        """Set up push notifications for file changes.
        
        Args:
            file_id: The ID of the file to watch
            webhook_url: The URL that will receive notifications
            expiration: Optional timestamp for when the notification channel should expire
            
        Returns:
            Watch response containing channel ID and resource ID
        """
        try:
            body = {
                'id': f'watch-{file_id}',
                'type': 'web_hook',
                'address': webhook_url
            }
            if expiration:
                body['expiration'] = expiration

            request = self.service.files().watch(fileId=file_id, body=body)
            return self._execute_with_retry(request)
        except Exception as e:
            self.logger.error(f"Watch setup failed for file {file_id}: {str(e)}")
            raise

    def export_file(self, file_id: str, mime_type: str) -> BinaryIO:
        """Export Google Workspace files in specific formats."""
        try:
            request = self.service.files().export_media(fileId=file_id, mimeType=mime_type)
            fh = io.BytesIO()
            downloader = MediaIoBaseDownload(fh, request)
            done = False
            while not done:
                _, done = downloader.next_chunk()
            fh.seek(0)
            return fh
        except Exception as e:
            self.logger.error(f"Export failed for file {file_id}: {str(e)}")
            raise

    def empty_trash(self) -> None:
        """Permanently deletes all of the user's trashed files."""
        try:
            request = self.service.files().emptyTrash()
            self._execute_with_retry(request)
        except Exception as e:
            self.logger.error(f"Empty trash failed: {str(e)}")
            raise

    def generate_file_ids(self, count: int = 10) -> List[str]:
        """Generate a set of file IDs for future use in create/copy operations.
        
        Args:
            count: Number of IDs to generate (default: 10, max: 1000)
            
        Returns:
            List of generated file IDs
        """
        try:
            request = self.service.files().generateIds(count=min(count, 1000))
            response = self._execute_with_retry(request)
            return response.get('ids', [])
        except Exception as e:
            self.logger.error(f"Generate IDs failed: {str(e)}")
            raise

    def list_labels(self, file_id: str) -> List[Dict]:
        """Lists the labels on a file.
        
        Args:
            file_id: The ID of the file to list labels for
            
        Returns:
            List of label objects
        """
        try:
            request = self.service.files().listLabels(fileId=file_id)
            response = self._execute_with_retry(request)
            return response.get('labels', [])
        except Exception as e:
            self.logger.error(f"List labels failed for file {file_id}: {str(e)}")
            raise

    def modify_labels(self, file_id: str, labels: Dict[str, Any]) -> Dict[str, Any]:
        """Modifies the set of labels on a file.
        
        Args:
            file_id: The ID of the file to modify labels for
            labels: Dictionary containing label modifications
            
        Returns:
            Updated label information
        """
        try:
            request = self.service.files().modifyLabels(
                fileId=file_id,
                body=labels
            )
            return self._execute_with_retry(request)
        except Exception as e:
            self.logger.error(f"Modify labels failed for file {file_id}: {str(e)}")
            raise

    def stop_watching(self, channel_id: str, resource_id: str) -> None:
        """Stop receiving push notifications for a file.
        
        Args:
            channel_id: The ID of the notification channel to stop
            resource_id: The resource ID received when starting the watch
        """
        try:
            body = {
                'id': channel_id,
                'resourceId': resource_id
            }
            request = self.service.channels().stop(body=body)
            self._execute_with_retry(request)
        except Exception as e:
            self.logger.error(f"Stop watching failed for channel {channel_id}: {str(e)}")
            raise

    # Add context manager support
    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        # Cleanup if needed
        pass

    # Add simplified file operations
    def upload_file(self, file_path: str, folder_id: Optional[str] = None) -> str:
        """Simple wrapper for uploading a single file."""
        return self.upload(file_path, parent_id=folder_id)

    def get_or_create_folder(self, folder_name: str, parent_id: Optional[str] = None) -> str:
        """Get folder ID if exists, create if it doesn't."""
        query = f"name='{folder_name}' and mimeType='{self.FOLDER_MIME_TYPE}'"
        if parent_id:
            query += f" and '{parent_id}' in parents"
            
        results = self.list_files(query=query)
        
        if results:
            return results[0]['id']
        return self.create_folder(folder_name, parent_id)

    def path_to_id(self, path: str) -> str:
        """Convert a path string like 'folder1/folder2/file.txt' to file ID."""
        parts = path.split('/')
        current_parent = None
        
        for i, part in enumerate(parts):
            is_last = i == len(parts) - 1
            query = f"name='{part}'"
            if current_parent:
                query += f" and '{current_parent}' in parents"
                
            if not is_last:
                query += f" and mimeType='{self.FOLDER_MIME_TYPE}'"
                
            results = self.list_files(query=query)
            if not results:
                raise FileNotFoundError(f"Could not find: {'/'.join(parts[:i+1])}")
            current_parent = results[0]['id']
            
        return current_parent