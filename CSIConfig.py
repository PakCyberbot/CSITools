import os, hashlib, subprocess, json
from PyQt5.QtCore import QDateTime, QUrl
from PyQt5.QtWebEngineCore import *
from PyQt5.QtWebEngineWidgets import *
from urllib.parse import urlparse
from PyQt5.QtGui import *
# subprocess.call(['pip', 'install', '-r', 'requirements.txt'])

# Global variables
if not os.path.exists("agency_data.json"):
    try:
        subprocess.run(["python", "Agency.Wizard.py"])
    except Exception as e:
        print(f"An error occurred: {str(e)}")
        sys.exit()

with open("agency_data.json", "r") as file:
    data = json.load(file)
    cases_folder = data.get("cases_folder", "")
    logo_path = os.path.join("Images", "agencylogo.png")


base_folder = cases_folder
case_number = 1
case = f"Case-{case_number}"
case_directory = f"{base_folder}/{case}"
audit_log_path = os.path.join(case_directory, "audit.log")
history_file_path = os.path.join(case_directory, "history.txt")
notes_file_path = os.path.join(case_directory, "notes.txt")
homepage = "https://csilinux.com"


homepage = "https://csilinux.com"

# Configuration settings
app_name = "CSI Case Management System v.1.20230518.1"
app_width = 800
app_height = 600
icon_path = "/opt/csitools/Images/logo.png"
tray_icon_path = "/opt/csitools/Images/CSI-Menu.png"

# Shared

def read_notes(base_folder, case_directory):
    try:
        if base_folder:
            notes_file_path = os.path.join(case_directory, "notes.txt")
            with open(notes_file_path, "r") as f:
                return f.read()
        else:
            with open("notes.txt", "w") as f:
                f.write(notes)
    except:
        return ""

def save_notes(base_folder, case_directory, notes):
    try:
        if base_folder:
            notes_file_path = os.path.join(case_directory, "notes.txt")
            with open(notes_file_path, "w") as f:
                f.write(notes)
            with open(audit_log_path, 'a') as f:
                f.write(get_current_timestamp() + "Saved Investigator Notes.\n")    
        else:
            with open("notes.txt", "w") as f:
                f.write(notes)
            with open(audit_log_path, 'a') as f:
                f.write(get_current_timestamp() + "Saved Investigator Notes.\n\r") 
    except:
        pass



def get_current_timestamp(timestamp=None):
    if timestamp is None:
        timestamp = QDateTime.currentDateTime().toString('yyyy-MM-dd:hh:mm:ss.zzz')
    else:
        timestamp = QDateTime.fromString(timestamp, 'yyyy-MM-dd:hh:mm').toString('yyyy-MM-dd:hh:mm:ss.zzz')
    return f"({timestamp})"
    

def auditme(case_directory, message):
    audit_log_path = os.path.join(case_directory, "audit.log")
    if not os.path.isfile(audit_log_path):
        with open(audit_log_path, 'w+') as f:
            pass  # create empty file
    with open(audit_log_path, 'a') as f:
        f.write(get_current_timestamp() + message + "\n\r")

def create_case_folder(case, cases_folder):
    timestamp = get_current_timestamp()
    case_directory = os.path.join(cases_folder, case)
    if not os.path.exists(case_directory):
        os.makedirs(case_directory)

    subdirectories = [
        "Crime Scene Photos",
        "Supporting Documents",
        "Supporting Documents/Evidence Intake",
        "Evidence",
        "Evidence/Graphics",
        "Evidence/Video",
        "Evidence/Forensic Images",
        "Evidence/Virtual Machines",
        "Evidence/RAM",
        "Evidence/Network",
        "Evidence/Logs",
        "Evidence/Triage",
        "Evidence/Online",
        "Evidence/Online/Cryptocurrency",
        "Evidence/Online/DarkWeb",
        "Evidence/Online/DarkWeb/OnionShare",
        "Evidence/Online/Domains",
        "Evidence/Online/Social Media", 
        "Report",
        "Tools",
        "Tools/Hunchly",
        "Tools/Autopsy"
    ]

    for subdirectory in subdirectories:
        directory_path = os.path.join(case_directory, subdirectory)
        if not os.path.exists(directory_path):
            os.mkdir(directory_path)

    # Create audit log and history files
    audit_log_path = os.path.join(case_directory, "audit.log")
    if not os.path.isfile(audit_log_path):
        with open(audit_log_path, 'w+') as f:
            f.write(get_current_timestamp() + " Audit log created.\n")

    history_file_path = os.path.join(case_directory, "history.txt")

    if not os.path.isfile(history_file_path):
        with open(history_file_path, 'w+') as f:
            f.write(get_current_timestamp() + " History file created.\n")

    notes_file_path = os.path.join(case_directory, "notes.txt")
    with open(notes_file_path, 'w+') as f:
        f.write("Case notes for Digital Forensics Investigation:\n" + get_current_timestamp() + "\n\n")
        pass  # create empty file

    with open(audit_log_path, 'a') as f:
        f.write(get_current_timestamp() + " Created case folder structure.\n")
    print(case_directory)
    return case_directory




def run_process_with_progress(command, progress_dialog):
    def update_progress(progress):
        progress_dialog.setValue(progress)
        QApplication.processEvents()

    def cancel_process():
        process.kill()

    progress_dialog.canceled.connect(cancel_process)

    process = QProcess()
    process.readyReadStandardOutput.connect(lambda: update_progress(25))
    process.readyReadStandardError.connect(lambda: update_progress(50))
    process.started.connect(lambda: update_progress(10))
    process.finished.connect(lambda: update_progress(100))
    process.start(command)
    process.waitForFinished()

    if progress_dialog.wasCanceled():
        QMessageBox.warning(None, "Warning", "Process canceled.")
        return False

    if process.exitStatus() != QProcess.NormalExit or process.exitCode() != 0:
        QMessageBox.critical(None, "Error", f"Failed to run the command: {command}")
        return False

    return True

def capture_website(url, case_directory):
    # Get the domain name from the URL
    domain = QUrl(url).host()
    
    # Define the folder structure
    folder_path = f"{case_directory}/Evidence/Domains/{domain}"
    
    # Run HTTrack to capture the website
    subprocess.run(["httrack", url, "-%v", "--mirror", "-O", folder_path])

def toggle_privacy_mode(browser_view, enabled):
    settings = browser_view.settings()
    settings.setAttribute(QWebEngineSettings.LocalStorageEnabled, not enabled)
    settings.setAttribute(QWebEngineSettings.JavascriptEnabled, not enabled)

    if enabled:
        profile = QWebEngineProfile.defaultProfile()
        profile.clearHttpCache()
        profile.cookieStore().deleteAllCookies()
    else:
        # Reload the page to apply the changes
        browser_view.reload()     

def run_csi_torvpn(self):
    # Replace this path with the actual path to the CSI_TorVPN application
    csi_torvpn_path = "CSI_TorVPN"
    os.system(csi_torvpn_path)


