import requests


def get_sharepoint_sites(access_token):
    """get sites of Sharepoint
    :return: status, sites_or_error_message
    """
    endpoint = 'https://graph.microsoft.com/v1.0/sites?search=*'

    headers = {
        "Authorization": f"Bearer {access_token}",
        "Accept": "application/json"
    }

    response = requests.get(endpoint, headers=headers)
    if response.status_code == 200:
        data = response.json()
        sites = [
            {'id': item['id'], 'name': item['displayName']} for item in data['value'] 
            if item['displayName'] != 'Apps' and item['displayName'] != 'Team Site']
        return response.status_code, sites
    else:
        return response.status_code, response.text


def get_sharepoint_folders(site_id, access_token):
    """get folders of Sharepoint
    :return: status, folders_or_error_message
    """
    endpoint = f'https://graph.microsoft.com/v1.0/sites/{site_id}/drive/root/children'

    headers = {
        "Authorization": f"Bearer {access_token}",
        "Accept": "application/json"
    }

    response = requests.get(endpoint, headers=headers)
    if response.status_code == 200:
        data = response.json()
        folders = [{'id': item['id'], 'name': item['name']} for item in data['value'] if 'folder' in item]
        return response.status_code, folders
    else:
        return response.status_code, response.text
