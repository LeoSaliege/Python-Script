import requests
import json
import os
import time
from azure.storage.blob import BlobServiceClient
from azure.storage.blob import BlobClient
import colorama
from colorama import Fore, Back, Style
colorama.init(autoreset=True)


# path of the current directory
current_directory = os.getcwd()

# environment variables
connection_string = os.getenv("AZURE_STORAGE_CONNECTION_STRING")
token_api=os.getenv("TOKEN-GITLAB")
group_id=os.getenv("GROUP-ID")
name_of_my_container=os.getenv("CONTAINER-NAME")

# date variable
named_tuple = time.localtime()  # get struct_time
time_string = time.strftime("%d-%m-%Y-%H-%M-%S", named_tuple)

print(f"date of backup : {time_string}")
data_api = {}


def action_to_api(url, search_key, method="GET"):
    global data_api
    payload = {}
    headers = {
        'PRIVATE-TOKEN': f'{token_api}',
    }

    response = requests.request(method, url, headers=headers, data=payload)
    data = response.json()
    print(f"status of {method}  {url} : {response.status_code}")
    if method == "POST":
        return
    elif method == "GET":
        data_api = data.get(search_key)


# GET of all projects in our group https://docs.gitlab.com/ee/api/groups.html#details-of-a-group
action_to_api(url=f"https://gitlab.com/api/v4/groups/{group_id}", search_key="projects", method="GET")


payload = {}
# start of the loop for the backup
for dictionary in data_api:
    name_project = dictionary.get("name")
    id_project = dictionary.get("id")
    print(f'''
    {Fore.GREEN}
    ##############################################################
    project name : {name_project}    id projet : {id_project}
    ############################################################
    ''')
    # export initialization
    action_to_api(url=f"https://gitlab.com/api/v4/projects/{id_project}/export/", search_key="projects", method="POST")
    print(f'''
    ################################################################################
    initialization export of {name_project}  , {Fore.RED} waiting for 240 seconds ...
     ''')
    time.sleep(240)
    # export status and download link
    action_to_api(url=f"https://gitlab.com/api/v4/projects/{id_project}/export/", search_key="_links", method="GET")
    time.sleep(5)
    # retrieving url for download
    url_download = data_api.get("api_url")
    # download of export
    print(f" {Fore.CYAN} download from export link {url_download}")
    headers = {
        'PRIVATE-TOKEN': f'{token_api}',
    }
    # write the zip file in the current directory
    print(f'''
    {Fore.CYAN}
    ###############################################################
     write zip file to {current_directory}/backup/{name_project}-{time_string}
    ###############################################################
    ''')
    response = requests.get(url_download, headers=headers)
    with open(f"{current_directory}/backup/{name_project}-{time_string}.tar.gz", "wb") as f:
        f.write(response.content)
    time.sleep(5)

    # initialize a client instance Azure
    service = BlobServiceClient.from_connection_string(conn_str=connection_string)


    # Upload a blob to your container Azure from the backups which are in the local backup directory
    print(f" {Fore.BLUE} Upload of {name_project}-{time_string}.tar.gz in azure container (compte de stockage : comptestockagelsa) ")
    
    blob = BlobClient.from_connection_string(conn_str=connection_string, container_name=name_of_my_container,
                                             blob_name=f"{name_project}-{time_string}.tar.gz")

    with open(f"{current_directory}/backup/{name_project}-{time_string}.tar.gz", "rb") as data:
        blob.upload_blob(data)
