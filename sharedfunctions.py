
import platform
import argparse
import subprocess
import sys
import json
import os
from PyQt5.QtCore import QDateTime, QUrl
from PyQt5.QtWebEngineCore import *
from PyQt5.QtWebEngineWidgets import *
from urllib.parse import urlparse
from PyQt5.QtGui import *
import sys, argparse, os, subprocess, json, shutil, platform
from PyQt5.QtWidgets import QApplication, QWidget, QFileDialog, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QPlainTextEdit, QStatusBar, QInputDialog, QWizard, QWizardPage, QLineEdit, QFormLayout, QDialog, QSizePolicy
from PyQt5.QtCore import Qt
from datetime import datetime
from PyQt5.QtWidgets import QLabel, QVBoxLayout, QWidget
from PyQt5.QtGui import QImage, QPalette, QBrush
import os
from urllib.parse import urlparse
import requests
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from PyQt5.QtCore import QThread, pyqtSignal
from bs4 import BeautifulSoup


if not os.path.exists("agency_data.json"):
    try:
        subprocess.run(["python", "Agency.Wizard.py"])
    except Exception as e:
        print(f"An error occurred: {str(e)}")
        sys.exit()

with open("agency_data.json", "r") as file:
    data = json.load(file)
    cases_folder = data.get("cases_folder")
    logo_path = os.path.join("Images", "agencylogo.png")


# subprocess.call(['pip', 'install', '-r', 'requirements.txt'])

class DragDropWidget(QWidget):
    def __init__(self, case, computer_name, parent=None):
        super().__init__(parent)
        self.case = case
        self.computer_name = computer_name
        self.ev_dir = os.path.join(self.case, "Evidence", "Triage", self.computer_name, "Evidence Vault")
        self.audit_file = f"{case}/Evidence/Triage/{computer_name}/audit.log"
        if not os.path.exists(self.ev_dir):
            os.makedirs(self.ev_dir)
        self.setAcceptDrops(True)

        self.layout = QVBoxLayout(self)
        self.layout.setSpacing(0)  # Adjust the vertical spacing here (e.g., reduce it to 0)
        self.label = QLabel("Drag and drop or click to add evidence")
        self.label.setAlignment(Qt.AlignBottom)
        self.layout.addWidget(self.label)

        self.setLayout(self.layout)
        self.setStyleSheet("""
            QLabel {
                color: white;
                margin-top: 2;
                font-weight: bold;
            }
        """)
        self.setFixedSize(380,248)

    def resizeEvent(self, event):
        background_image = QImage("Images/Vault3.png")
        scaled_image = background_image.scaled(self.size(), Qt.AspectRatioMode.KeepAspectRatio)
        palette = QPalette()
        palette.setBrush(QPalette.Background, QBrush(scaled_image))
        self.setPalette(palette)
        self.setAutoFillBackground(True)
        
        super().resizeEvent(event)
       
    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()

    def dropEvent(self, event):
        for url in event.mimeData().urls():
            path = url.toLocalFile()
            self.add_evidence(path, self.case, self.computer_name)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            options = QFileDialog.Options()
            options |= QFileDialog.ReadOnly
            path, _ = QFileDialog.getOpenFileName(self, "Add Evidence", "", "All Files (*)", options=options)
            self.add_evidence(path, self.case, self.computer_name)

    def add_evidence(self, path, case, computer_name):
        logs_dir = os.path.join(case, "Evidence", "Triage", computer_name, "Evidence Vault")
        if path:
            label = QLabel(os.path.basename(path))
            self.label.setAlignment(Qt.AlignBottom)
            self.layout().addWidget(label)
            destination = os.path.join(self.ev_dir, os.path.basename(path))
            if os.path.isfile(path):
                shutil.copy2(path, destination)
            elif os.path.isdir(path):
                shutil.copytree(path, destination)
            message = audit_me(self.audit_file, f"Added  {path} to the Evidence Vault")

class ChromeThread(QThread):
    finished = pyqtSignal()

    def __init__(self, url, main_window, evidence_dir):
        super().__init__()
        self.url = url
        self.main_window = main_window
        domain = urlparse(url).netloc
        evidence_dir = os.path.join(evidence_dir, domain)
        self.evidence_dir = evidence_dir

    def run(self):
        domain = urlparse(self.url).netloc
        current_dir = os.getcwd()
        chromedriver_path = os.path.join(current_dir, 'chromedriver')
        chrome_options = Options()

        if domain.endswith('.onion'):
            print("Configuring the Tor proxy...")
            tor_proxy = "127.0.0.1:9050"
            proxy_address = "127.0.0.1:9050"  # Proxy address for .onion domains
            chrome_options.add_argument(f'--proxy-server=socks5://{proxy_address}')
        else:
            print("Configuring Internet connection...")

        driver = webdriver.Chrome(executable_path=chromedriver_path, options=chrome_options)
        driver.get(self.url)

        timestamp = get_current_timestamp()
        auditme(self.evidence_dir, f"{timestamp}: Opening {self.url} in Chrome")

        # Save history
        history_path = os.path.join(self.evidence_dir, "history.txt")
        with open(history_path, "a") as f:
            f.write(f"{timestamp}: {self.url}\n")

        # Save all files
        self.save_files(driver.page_source, self.url, self.evidence_dir)

        # webbrowser.get(using='google-chrome').open_new_tab(self.url)

        # Keep the browser window open until the thread is terminated
        self.exec_()

        driver.quit()
        self.finished.emit()

    def save_files(self, html, base_url, evidence_dir):
        parsed_url = urlparse(base_url)
        base_path = parsed_url.netloc + parsed_url.path
        if not os.path.exists(evidence_dir):
            os.makedirs(evidence_dir)

        # Save HTML file
        html_path = os.path.join(evidence_dir, "page.html")
        with open(html_path, "w") as f:
            f.write(html)

        # Save all other files
        for link in BeautifulSoup(html, "html.parser").find_all("a", href=True):
            file_url = link["href"]
            if file_url.startswith(("http://", "https://")):
                filename = file_url.rsplit("/", 1)[-1]
                file_path = os.path.join(evidence_dir, base_path, filename)
                os.makedirs(os.path.dirname(file_path), exist_ok=True)
                self.download_file(file_url, file_path)

    def download_file(self, url, save_path):
        try:
            response = requests.get(url, stream=True)
            response.raise_for_status()
            with open(save_path, "wb") as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
        except Exception as e:
            print(f"Failed to download file from {url}. Error: {e}")



def csitoolsinit(case, csitoolname):
    global case_name, investigator_name, case_type, case_priority, case_classification, case_date, cases_folder, case_directory, timestamp, notes_file_path, icon
    icon = "CSI-Icon.ico"
    config_file = "agency_data.json"

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
    
    # Test: Print the values of the global variables
    print("case_name =", case_name)
    print("investigator_name =", investigator_name)
    print("case_type =", case_type)
    print("case_priority =", case_priority)
    print("case_classification =", case_classification)
    print("case_date =", case_date)

    # Set up common variables used in CSI apps
    case_directory = os.path.join(cases_folder, case)
    create_case_folder(case_directory)
    timestamp = get_current_timestamp()
    auditme(case_directory, f"{timestamp}: Opening {csitoolname}")
    notes_file_path = os.path.join(case_directory, "notes.txt")
    evidence_dir = os.path.join(case_directory, f"Evidence")    # Change "Folder" to the appropriate evidence sub-folder
    
    #
    return case_name, investigator_name, case_type, case_priority, case_classification, case_date, cases_folder, case_directory, timestamp, notes_file_path, icon


def get_current_timestamp(timestamp=None):
    if timestamp is None:
        timestamp = QDateTime.currentDateTime().toString('yyyy-MM-dd:hh:mm:ss.zzz')
    else:
        timestamp = QDateTime.fromString(timestamp, 'yyyy-MM-dd:hh:mm').toString('yyyy-MM-dd:hh:mm:ss.zzz')
    return f"{timestamp}"

def auditme(case_directory, message):
    audit_log_path = os.path.join(case_directory, "audit.log")
    
    # Check if the directory exists, and create it if it doesn't
    if not os.path.exists(case_directory):
        os.makedirs(case_directory)

    # Now it's safe to open the file
    with open(audit_log_path, 'a+') as f:
        f.write(get_current_timestamp() + message + "\n")
    
    
def create_case_folder(case_directory):
    timestamp = get_current_timestamp()
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

    audit_log_path = os.path.join(case_directory, "audit.log")
    if not os.path.isfile(audit_log_path):
        with open(audit_log_path, 'a+') as f:
            f.write(get_current_timestamp() + " Audit log created.\n")
    
    history_file_path = os.path.join(case_directory, "history.txt")
    if not os.path.isfile(history_file_path):
        with open(history_file_path, 'a+') as f:
            f.write(get_current_timestamp() + " History file created.\n")
    
    notes_file_path = os.path.join(case_directory, "notes.txt")
    if not os.path.isfile(notes_file_path):
        with open(notes_file_path, 'a+') as f:
            f.write("Case notes for Digital Forensics Investigation:\n" + get_current_timestamp() + "\n\n")
    
    with open(audit_log_path, 'a') as f:
        f.write(get_current_timestamp() + " Verifying case folder structure.\n")
    


    with open(audit_log_path, 'a') as f:
        f.write(get_current_timestamp() + " Verifying case folder structure.\n")
        
    return case_directory
