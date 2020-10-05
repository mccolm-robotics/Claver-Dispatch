import os

import requests

# Check to see if the virtual environment has been created and activate it
os.system('/bin/bash --rcfile environment.sh')
# if os.path.isdir("venv"):
#     print("Virtual Folder exists")
#
# # Check to see if this machine is running a specific version of the Claver client
# if os.path.isfile("version.txt"):
#     with open("version.txt", "r") as file:
#         for line in file:
#             version = line.strip()
#
#     # ToDo: Use Regex to make sure version number is valid
#     # ToDo: Check to make sure that version number corresponds to a valid git branch
#
#     if version == "stable":
#         url = "https://raw.githubusercontent.com/mccolm-robotics/Claver-Interactive-Message-Board/stable/init.sh"
#         data = requests.get(url, allow_redirects=True)
#         open('init.sh', 'wb').write(data.content)