from sharedfunctions import * 
import os
import sys
import subprocess
import platform
import argparse
from PyQt5.QtCore import QDateTime, QUrl
from urllib.parse import urlparse
from PyQt5.QtGui import *
from PyQt5.QtWidgets import QApplication, QWidget
# Other imports as needed

csitoolname = "Tool name here"

# Import platform-specific configurations
os_name = platform.system()
if os_name == "Windows":
    from WindowsConfig import *
elif os_name == "Linux":
    from LinuxConfig import *
elif os_name == "Darwin":
    from MacOSConfig import *
else:
    raise Exception(f"Unsupported operating system: {os_name}")

# Glogal variables if needed

# Define command-line arguments
parser = argparse.ArgumentParser(description="Description of your application")
parser.add_argument('--case', type=str, help="Path to the case directory")
args = parser.parse_args()
case = args.case

if not args.case:
    try:
        result = subprocess.run(["python", "New_Case_Wizard.py"], capture_output=True, text=True)
        case = result.stdout.strip()  # Extract the case value from the subprocess output
        print(result)
    except Exception as e:
        print("Error:", e)
        sys.exit()
else:
    print(f"Path to cases_folder {cases_folder}")

# Define case directories
case_directory = os.path.join(cases_folder, case)
case_evidence = os.path.join(case_directory, "Evidence", "Folder")
os.makedirs(case_evidence, exist_ok=True)
timestamp = sharedfunctions.get_current_timestamp()
auditme(case_directory, f"{timestamp}: Opening {csitoolname}")

# Use auditme(case_directory, "Message goes here") everytime you do something to keep the audit trail





# def name():
#     auditme(case_directory, "Ran something"")




