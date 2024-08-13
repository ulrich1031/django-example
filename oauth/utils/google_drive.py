import requests

def get_google_drive_folders(access_token):
    """get folders of Google Drive
    :return: status, folders_or_error_message
    """
    url = 'https://www.googleapis.com/drive/v3/files'
    headers = {
        'Authorization': 'Bearer ' + access_token
    }
    params = {
        'q': "mimeType='application/vnd.google-apps.folder' and 'root' in parents",
        'fields': 'nextPageToken, files(id, name)'
    }
    response = requests.get(url, headers=headers, params=params)
    if response.status_code == 200:
        return response.status_code, response.json()
    else:
        return response.status_code, response.text
