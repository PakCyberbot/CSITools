import os, hashlib, subprocess, json
from PyQt5.QtCore import QDateTime, QUrl
from PyQt5.QtWebEngineCore import *
from PyQt5.QtWebEngineWidgets import *
from urllib.parse import urlparse
from PyQt5.QtGui import *

# subprocess.call(['pip', 'install', '-r', 'requirements.txt'])

if not case:
    try:
        case = subprocess.run(["python", "New_Case_Wizard.py"])
    except Exception as e:
        print("Error")
        sys.exit()


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


