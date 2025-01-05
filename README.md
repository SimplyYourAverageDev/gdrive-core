# gdrive-core

A minimal and functional Google Drive API wrapper for Python. Easily perform Google Drive file operations like upload, download, list, delete, and manage metadata with an intuitive class-based interface.

## Features

- **Authentication**: OAuth2 and Service Account support
- **File Operations**: Upload/download (with progress tracking), list, delete, copy, and metadata management
- **Folder Management**: Create and manage folders
- **Search & Share**: File search and permission management
- **Batch Operations**: Parallel deletion for multiple files
- **Path Operations**: Basic path-to-ID conversion
- **Modern Python**: Context managers, type hints, and clean OOP interface

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

# Simplified upload wrapper
file_id = client.upload_file('example.txt', folder_id='optional_folder_id')

# Stream-based upload (note additional kwargs support)
with open('example.txt', 'rb') as file_obj:
    file_id = client.upload_stream(
        file_obj,
        filename='example.txt',
        mime_type='text/plain',  # Optional
        **additional_metadata  # Supports additional metadata kwargs
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
    fields="files(id, name, mimeType, modifiedTime)"  # Default fields shown
)

# Advanced search with supported parameters
results = client.search({
    'name_contains': 'report',
    'mime_type': 'application/pdf',
    'trashed': 'false'
})
# Note: Only name_contains, mime_type, and trashed parameters are currently supported
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
    webhook_url='https://your-webhook.com',
    expiration=1735689600000  # Optional: Unix timestamp in milliseconds
)

# Stop watching file changes
client.stop_watching(
    channel_id=watch_result['id'],
    resource_id=watch_result['resourceId']
)

# Export Google Workspace files
pdf_content = client.export_file(
    file_id='document_id',
    mime_type='application/pdf'
)

# Empty trash
client.empty_trash()

# Generate file IDs for future use
file_ids = client.generate_file_ids(count=5)  # Default: 10, Max: 1000

# Label management
labels = client.list_labels('file_id')

# Modify labels
client.modify_labels(
    file_id='file_id',
    labels={
        'labelKey': 'labelValue',
        'priority': 'high'
    }
)
```

### Path-based Operations

```python
# Convert path to file ID
file_id = client.path_to_id('Folder1/Subfolder/file.txt')
```

### Error Handling and Retries

The library implements automatic retry logic with exponential backoff for all API operations:

```python
# Configure retry attempts during initialization
client = GDriveCore(
    auth_type='oauth2',
    credentials_file='credentials.json',
    max_retries=3  # Default: 3
)

# All operations automatically use retry logic
try:
    file_id = client.upload_file('large_file.zip')
except Exception as e:
    print(f"Operation failed after {client._max_retries} attempts: {e}")
```

## Full Example

Here's a complete example showcasing the intuitive features:

```python
from gdrive_core import GDriveCore

with GDriveCore() as drive:
    # Create a folder
    folder_id = drive.create_folder('Reports')
    
    # Upload a file to the folder
    file_id = drive.upload_file('report1.pdf', folder_id)
    
    # Search for PDF files
    pdfs = drive.search({
        'mime_type': 'application/pdf',
        'name_contains': 'report'
    })
    
    # Download found files
    for pdf in pdfs:
        drive.download(pdf['id'], f"downloaded_{pdf['name']}")
    
    # Share the folder with someone
    drive.share(folder_id, 'colleague@company.com', role='writer')
    
    # Watch for changes
    watch_result = drive.watch_file(
        file_id=folder_id,
        webhook_url='https://your-webhook.com'
    )
    
    # Get storage quota
    quota = drive.get_storage_quota()
    print(f"Storage used: {quota.get('usage')} of {quota.get('limit')} bytes")
    
    # Clean up
    drive.empty_trash()  # Empty trash
    drive.stop_watching(  # Stop watching for changes
        channel_id=watch_result['id'],
        resource_id=watch_result['resourceId']
    )
```

## Common Operations Quick Reference

Here are some common operations and their simplified syntax:

```python
with GDriveCore() as drive:
    # Create a folder
    folder_id = drive.create_folder('MyFolder')
    
    # Upload a file
    file_id = drive.upload_file('document.pdf', folder_id)
    
    # Get file ID from path
    file_id = drive.path_to_id('MyFolder/document.pdf')
    
    # Search for files
    results = drive.search({
        'name_contains': 'document',
        'mime_type': 'application/pdf',
        'trashed': 'false'
    })
    
    # Batch deletion
    drive.batch_delete(['file_id1', 'file_id2'])
    
    # Generate file IDs for future use
    new_ids = drive.generate_file_ids(count=5)
    
    # Manage labels
    drive.modify_labels('file_id', {'priority': 'high'})
```

## Troubleshooting

- **Missing `credentials.json`**: Ensure the `credentials.json` file is placed in the working directory.
- **Token Issues (OAuth2)**: If you face authentication problems, delete the `token.json` file and re-authenticate.
- **Service Account Issues**: Ensure the service account has the necessary permissions to access your Google Drive.
- **Custom Metadata**: Ensure custom property keys and values conform to Google Drive's property limitations.
- **Rate Limits**: The library implements automatic retry logic with exponential backoff. You can configure max_retries during initialization.
- **Webhook Issues**: Ensure your webhook URL is publicly accessible and can handle POST requests.
- **Label Operations**: Label management requires appropriate permissions and valid label formats.

## License

`gdrive-core` is released under the MIT License.