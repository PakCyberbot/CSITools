#! /usr/bin/python3
# ----------------------------------------------------------------------------
# CSI Linux (https://www.csilinux.com)
# Author: Author
# Copyright (C) CSI Linux. All rights reserved.
#
# This software is proprietary and NOT open source. Redistribution,
# modification, or any other use of this code is strictly prohibited without
# the express written consent of CSI Linux.
#
# This software is provided "AS IS" without warranty of any kind, express or
# implied, including but not limited to the warranties of merchantability,
# fitness for a particular purpose, and non-infringement. In no event shall
# the authors or copyright holders be liable for any claim, damages, or other
# liability, whether in an action of contract, tort or otherwise, arising from,
# out of or in connection with the software or the use or other dealings in
# the software.
#
# Paid support can be contracted through support@csilinux.com
# ----------------------------------------------------------------------------
from sharedfunctions import * 
import os
import sys
import subprocess
import platform
import argparse
import json
from PyQt5.QtCore import QDateTime, QUrl
from urllib.parse import urlparse
from PyQt5.QtGui import *
from PyQt5.QtWidgets import QApplication, QWidget
# Other imports as needed

csitoolname = "Tool name here"

# Determine the operating system and import configuration settings accordingly
os_name = platform.system()
if os_name == "Windows":
    from WindowsConfig import *
elif os_name == "Linux":
    from LinuxConfig import *
elif os_name == "Darwin":
    from MacOSConfig import *
else:
    raise Exception(f"Unsupported operating system: {os_name}")

# Parse command-line arguments
parser = argparse.ArgumentParser(description=csitoolname)
parser.add_argument('--case', type=str, help="Path to the case directory")
parser.add_argument('--var3', type=str, help="var3 to add")
args = parser.parse_args()
config_file = "agency_data.json"
case = args.case
# Glogal variables if needed

if not case:
    try:
        result = subprocess.run(["python", "New_Case_Wizard.py"], capture_output=True, text=True)
        case = result.stdout.strip()  # Extract the case value from the subprocess output
        print(result)
    except Exception as e:
        print("Error:", e)
        sys.exit()
else:
    print(f"Path to cases_folder {cases_folder}")

 
if os.path.isfile(config_file):
    with open(config_file, "r") as f:
        config = json.load(f)
        cases_folder = config.get("cases_folder")
        case_directory = os.path.join(cases_folder, case)
else:
    case_directory = os.path.join(case)
case_directory = os.path.join(cases_folder, case)
create_case_folder(case_directory)
  
try:
    # Load case_data.json
    with open(f'{case_directory}/case_data.json', 'r') as f:
        case_data = json.load(f)

    # Store values as global variables
    case_name = case_data['case_name']
    investigator_name = case_data['investigator_name']
    case_type = case_data['case_type']
    case_priority = case_data['case_priority']
    case_classification = case_data['case_classification']
    case_date = case_data['case_date']
except FileNotFoundError:
    try:
        result = subprocess.run(["python", "New_Case_Wizard.py"], capture_output=True, text=True)
        case = result.stdout.strip()  # Extract the case value from the subprocess output
        print(result)
    except Exception as e:
        print("Error:", e)
        sys.exit()

# Set up common variables used in CSI apps
evidence_dir = os.path.join(case_directory, f"Evidence/Online/Folder")    # Change "Folder" to the appropriate evidence sub-folder
os.makedirs(evidence_dir, exist_ok=True)                                  # If the "Folder" doesn't exist, create it
timestamp = get_current_timestamp()
auditme(case_directory, f"{timestamp}: Opening {csitoolname}")
notes_file_path = os.path.join(case_directory, "notes.txt")
filenametxt = os.path.join(evidence_dir, f'File_to_list_on_left.txt')
if not os.path.exists(filenametxt):
    with open(filenametxt, 'w') as file:
        # Optional: Add initial content to the file if desired
        file.write("")

# Use auditme(case_directory, "Message goes here") everytime you do something to keep the audit trail





# def name():
#     auditme(case_directory, "Ran something"")




