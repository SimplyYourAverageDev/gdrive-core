# gdrive-core

A minimal and functional Google Drive API wrapper for Python. Easily perform Google Drive file operations like upload, download, list, delete, and manage metadata with an intuitive class-based interface.

## Features

- **Flexible Authentication**: Supports OAuth2 and Service Account authentication.
- **File Management**: Upload (with progress tracking), download (with progress tracking), list, and delete files effortlessly. Supports streamed uploads/downloads.
- **Folder Management**: Create folders and organize files.
- **Custom Metadata**: Add and manage arbitrary custom properties to files, and update metadata.
- **Batch Operations**: Delete multiple files at once using parallel processing.
- **Advanced Search**: Search for files using multiple criteria such as name, MIME type, and trashed status.
- **File Sharing**: Share files with specific permissions.
- **File Revisions**: Access a file's revision history.
- **Copy Files**: Create copies of existing files.
- **Storage Quota**: Retrieve information about your Google Drive storage usage.
- **Push Notifications**: Set up webhooks to watch for file changes.
- **File Export**: Export Google Workspace files in various formats.
- **OOP Interface**: Interact with Google Drive through a clean, class-based API.
- **Logging**: Integrated logging for better monitoring and debugging.
- **Retry Mechanism**: Automatic retries for API calls to handle transient errors.
- **Path-based Operations**: Work with Google Drive using familiar path strings (e.g., 'folder1/folder2/file.txt')
- **Context Manager Support**: Clean resource management using Python's `with` statement
- **Simplified File Operations**: High-level methods for common tasks
- **Automatic Folder Creation**: Create nested folder structures with a single call
- **Batch Processing**: Upload, download, or delete multiple files in parallel


## Installation

Install the package using pip:

```bash
pip install gdrive-core
```

## Setup

Before using `gdrive-core`, ensure you have:

1. **Google Cloud Credentials**:
   - Go to the [Google Cloud Console](https://console.cloud.google.com/).
   - Enable the **Google Drive API** for your project.
   - Download the `credentials.json` file for either an OAuth 2.0 Client ID or a Service Account.
   - Place the `credentials.json` file in your working directory.
   - **For OAuth2:**
        - The first time you run the program with OAuth2, it will prompt you to authenticate via a browser.
        - A `token.json` file will be created to store access tokens for future use.
   - **For Service Account:**
        - No `token.json` file is necessary as credentials are managed by the `credentials.json` file.

## Core Features

### Authentication

```python
from gdrive_core import GDriveCore

# OAuth2 Authentication (default)
client = GDriveCore(
    auth_type='oauth2',
    credentials_file='credentials.json',
    token_file='token.json',
    max_retries=3  # Optional: set maximum retry attempts
)

# Service Account Authentication
client = GDriveCore(
    auth_type='service_account',
    credentials_file='credentials.json'
)
```

### File Operations

```python
# Upload a file with progress tracking and custom properties
def track_progress(progress):
    print(f"Progress: {progress:.2f}%")

file_id = client.upload(
    file_path='example.txt',
    parent_id='folder_id',  # Optional
    properties={'category': 'documents'},  # Optional
    progress_callback=track_progress  # Optional
)

# Stream-based upload
with open('example.txt', 'rb') as file_obj:
    file_id = client.upload_stream(
        file_obj,
        filename='example.txt',
        mime_type='text/plain'  # Optional
    )

# Download files
client.download(
    file_id='file_id',
    local_path='downloaded.txt',
    progress_callback=track_progress  # Optional
)

# Stream-based download
file_stream = client.download_stream('file_id')
content = file_stream.read()
```

### Folder Management

```python
# Create a folder
folder_id = client.create_folder(
    folder_name='My Folder',
    parent_id='parent_folder_id'  # Optional
)

# Get or create folder (creates if doesn't exist)
folder_id = client.get_or_create_folder(
    folder_name='My Folder',
    parent_id='parent_folder_id'  # Optional
)

# Move files between folders
client.move(
    file_id='file_id',
    new_parent_id='new_folder_id',
    old_parent_id='old_folder_id'  # Optional
)
```

### Search and List Files

```python
# List files with custom fields
files = client.list_files(
    query="name contains 'report'",  # Optional
    fields="files(id, name, mimeType, modifiedTime)"  # Optional
)

# Advanced search with multiple criteria
results = client.search({
    'name_contains': 'report',
    'mime_type': 'application/pdf',
    'trashed': 'false'
})
```

### File Sharing and Metadata

```python
# Share a file
share_result = client.share(
    file_id='file_id',
    email='user@example.com',
    role='reader'  # Options: 'reader', 'writer', 'commenter'
)

# Update file metadata
client.update_metadata(
    file_id='file_id',
    metadata={'name': 'new_name.txt', 'description': 'Updated file'}
)

# Get file metadata
metadata = client.get_file_metadata(
    file_id='file_id',
    fields="*"  # Optional: specify fields to return
)
```

### Batch Operations

```python
# Delete multiple files
results = client.batch_delete(['file_id1', 'file_id2', 'file_id3'])
# Returns: {'file_id1': True, 'file_id2': True, 'file_id3': False}
```

### Advanced Features

```python
# Get file revision history
revisions = client.get_file_revisions('file_id')

# Copy files
new_file_id = client.copy_file(
    file_id='file_id',
    new_name='copy_name.txt'  # Optional
)

# Get storage quota
quota = client.get_storage_quota()

# Watch for file changes
watch_result = client.watch_file(
    file_id='file_id',
    webhook_url='https://your-webhook.com'
)

# Export Google Workspace files
pdf_content = client.export_file(
    file_id='document_id',
    mime_type='application/pdf'
)
```

### Path-based Operations

```python
# Convert path to file ID
file_id = client.path_to_id('Folder1/Subfolder/file.txt')
```

## Full Example

Here's a complete example showcasing the intuitive features:

```python
from gdrive_core import GDriveCore

with GDriveCore() as drive:
    # Create a nested folder structure
    folder_id = drive.get_or_create_folder('Projects/2024/Reports')
    
    # Upload multiple files to the folder
    files_to_upload = ['report1.pdf', 'report2.pdf', 'data.xlsx']
    upload_results = drive.batch_upload(files_to_upload, folder_id)
    
    # Search for all PDF files in the folder
    pdfs = drive.search({
        'type': 'pdf',
        'parent': folder_id
    })
    
    # Download all PDF files
    for pdf in pdfs:
        drive.download(pdf['id'], f"downloaded_{pdf['name']}")
    
    # Share the folder with someone
    drive.share(folder_id, 'colleague@company.com', role='writer')
    
    # Get the folder's metadata
    metadata = drive.get_file_metadata(folder_id)
    print(f"Folder size: {metadata.get('size', 'N/A')} bytes")
```

## Common Operations Quick Reference

Here are some common operations and their simplified syntax:

```python
with GDriveCore() as drive:
    # Create nested folders
    folder_id = drive.get_or_create_folder('Path/To/Folder')
    
    # Upload a file
    file_id = drive.upload_file('document.pdf', folder_id)
    
    # Get file ID from path
    file_id = drive.path_to_id('Path/To/Folder/document.pdf')
    
    # Search for files
    results = drive.search({
        'name': 'document.pdf',
        'type': 'pdf',
        'trashed': False
    })
    
    # Batch operations
    drive.batch_upload(['file1.txt', 'file2.txt'], folder_id)
    drive.batch_delete(['file_id1', 'file_id2'])
```

## Troubleshooting

- **Missing `credentials.json`**: Ensure the `credentials.json` file is placed in the working directory.
- **Token Issues (OAuth2)**: If you face authentication problems, delete the `token.json` file and re-authenticate.
- **Service Account Issues**: Ensure the service account has the necessary permissions to access your Google Drive.
- **Custom Metadata**: Ensure custom property keys and values conform to Google Drive's property limitations.
- **Rate Limits**: Google Drive API has rate limits. If you encounter issues, consider implementing retry mechanisms or exponential backoff.

## License

`gdrive-core` is released under the MIT License.