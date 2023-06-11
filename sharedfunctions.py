# ----------------------------------------------------------------------------
# CSI Linux (https://www.csilinux.com)
# Author: Jeremy Martin
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
import platform
import argparse
import subprocess
import sys
import json
import os
from PyQt5.QtCore import QDateTime, QUrl, QThread, pyqtSignal, QCoreApplication
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
import platform
import zipfile
import tempfile

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
        
        os_name = platform.system()
        current_dir = os.getcwd()
        if os_name == "Windows":
            current_dir = getattr(sys, "_MEIPASS", os.getcwd())
            chromedriver_path = os.path.join(current_dir, "chromedriver.exe")
            chromedriver_path = f'"{chromedriver_path}"'
            print(f"Windows Chromedriver path: {chromedriver_path}")
        
        else:
            current_dir = getattr(sys, "_MEIPASS", os.getcwd())
            chromedriver_path = os.path.join(current_dir, "./chromedriver")
        
    
        if domain.endswith('.onion'):
            print("Configuring the Tor proxy...")
            tor_proxy = "127.0.0.1:9050"
            proxy_address = "127.0.0.1:9050"  # Proxy address for .onion domains
            chrome_options.add_argument(f'--proxy-server=socks5://{proxy_address}')
        else:
            print("Configuring Internet connection...")
    
        chrome_options = Options()
   
        # Create the webdriver instance without using 'executable_path'
        driver = webdriver.Chrome(options=chrome_options)
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

        # Keep the event loop running while the thread is active
        while True:
            if not self.isRunning():
                break
            QCoreApplication.processEvents()

        driver.quit()
        self.finished.emit()
        
    def save_files(self, html, base_url, evidence_dir):
        parsed_url = urlparse(base_url)
        base_path = parsed_url.netloc + parsed_url.path
        if not os.path.exists(evidence_dir):
            os.makedirs(evidence_dir)
    
        # Determine the HTML filename based on the base_url
        if base_url.endswith("/"):
            html_filename = "index.html"
        else:
            html_filename = os.path.basename(base_path) + ".html"
    
        # Save HTML file with the appropriate filename
        html_path = os.path.join(evidence_dir, html_filename)
        with open(html_path, "w") as f:
            f.write(html)
    
        # Save all other files
        for link in BeautifulSoup(html, "html.parser").find_all("a", href=True):
            file_url = link["href"]
            if file_url.startswith(("http://", "https://")):
                filename = file_url.rsplit("/", 1)[-1]
    
                # Change the file extension to ".html"
                file_extension = filename.rsplit(".", 1)[-1]
                if file_extension in ["php", "asp", "jsp"]:
                    filename = filename.rsplit(".", 1)[0] + ".html"
    
                file_path = os.path.join(evidence_dir, base_path, filename)
                os.makedirs(os.path.dirname(file_path), exist_ok=True)
                self.download_file(file_url, file_path)
    
                # Check if the file is in a subfolder
                if "/" in file_url and not file_url.endswith("/"):
                    subfolder_path = os.path.join(evidence_dir, file_url)
                    subfolder_file_path = os.path.join(subfolder_path, "index.html")
                    os.makedirs(subfolder_path, exist_ok=True)
                    self.download_file(file_url, subfolder_file_path)







    def download_file(self, url, save_path):
        try:
            response = requests.get(url, stream=True)
            response.raise_for_status()
    
            # Extract the filename from the URL
            filename = url.rsplit("/", 1)[-1]

            # Check if save_path is a directory
            if os.path.isdir(save_path):
                # Create the file path within the directory
                file_path = os.path.join(save_path, filename)
            else:
                # Use save_path as the complete destination file path
                file_path = save_path
    
            # Extract the domain from the URL
            parsed_url = urlparse(url)
            domain = parsed_url.netloc
    
            # Create the directory if it doesn't exist
            os.makedirs(save_path, exist_ok=True)
    
            # Construct the complete destination file path
            file_path = os.path.join(save_path, filename)
    
            # Check if the file already exists
            if os.path.exists(file_path):
                os.remove(file_path)  # Remove the existing file
    
            with open(file_path, "wb") as f:
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
     
    if os.path.isfile(config_file):
        with open(config_file, "r") as f:
            config = json.load(f)
            cases_folder = config.get("cases_folder")
            case_directory = os.path.join(cases_folder, case)
    else:
        case_directory = os.path.join(case)
        print(f"The {config_file} was not found.  This is the case folder {case_directory}")

    create_case_folder(case_directory)
    print(f"Created the folders: {case_directory}")

    # Load case_data.json
    case_data_path = os.path.join(case_directory, "case_data.json")
    if not os.path.isfile(case_data_path):

        cdata = {
            "case_name": case,
            "investigator_name": csitoolname,
            "case_type": csitoolname,
            "case_priority": "Informational",
            "case_classification": "Confidential",
            "case_date": QDateTime.currentDateTime().toString("yyyy-MM-dd")
        }
        
        case_directory = create_case_folder(os.path.join(cases_folder, cdata['case_name']))
        case_data_path = os.path.join(case_directory, "case_data.json")

        with open(case_data_path, 'w') as f:
            json.dump(cdata, f)
        print(f"Just created {case_directory}")


            
    with open(case_data_path, 'r') as f:
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
    timestamp = get_current_timestamp()
    auditme(case_directory, f"{timestamp}: Opening {csitoolname}")
    notes_file_path = os.path.join(case_directory, "notes.txt")
    evidence_dir = os.path.join(case_directory, f"Evidence")    # Change "Folder" to the appropriate evidence sub-folder
    
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


def reportme(tmpl_path,out_path,data_dict, img_dict=None):
    """
    fill_template(tmpl_path, out_path, data_dict, img_list):
        Fills in the fields of the template document with data and generates a result document.

    Args:
        tmpl_path (str): Path of the template document that contains the fields to be filled in.
        out_path (str): Path of the resulting document with placeholders replaced by data.
        data_dict (dict): A dictionary mapping placeholder names to their corresponding values for replacement.
        img_list (dict): A dictionary specifying the images to replace in the document. 
            Key: The position of the image, first image added in the document will get 0 position.
            Value: The path to the image file.

    Note:
    - Position of Images depends on the order of adding them not the format of document.
    - if someone adds the image first but adds it to the last page still it will gonna have 0 position.

    Example:
        tmpl_path = 'template.odt'
        out_path = 'result.odt'
        data_dict = {'placeholder1': 'value1', 'placeholder2': 'value2'}
        img_list = {1: 'image1.png', 2: 'image2.png'}
        fill_template(tmpl_path, out_path, data_dict, img_list)
    """
    
    if tmpl_path.lower().endswith(".odt"):
       
        # Create a temporary directory to extract the ODT contents
        temp_dir = tempfile.mkdtemp()

        # Extract the ODT contents to the temporary directory
        with zipfile.ZipFile(tmpl_path, 'r') as odt_file:
            odt_file.extractall(temp_dir)

        # Read the styles.xml file for header and footer
        content_path = os.path.join(temp_dir, 'styles.xml')
        with open(content_path, 'r') as content_file:
            content = content_file.read()
            content_file.close()
        
        # regex pattern to find placeholder and replace with the value
        for placeholder, value in data_dict.items(): 
            content = re.sub(rf'<text:user-defined[^&]*?>&lt;{placeholder}&gt;</text:user-defined>', value, content)

        # Write the modified content back to styles.xml
        with open(content_path, 'w') as modified_file:
            modified_file.write(content)
            modified_file.close()

        # Read the content.xml file
        content_path = os.path.join(temp_dir, 'content.xml')
        with open(content_path, 'r', encoding='utf-8') as content_file:
            content = content_file.read()
            content_file.close()

        # regex pattern to find placeholder and replace with the value
        for placeholder, value in data_dict.items(): 
            content = re.sub(rf'<text:user-defined[^&]*?>&lt;{placeholder}&gt;</text:user-defined>', value, content)

        # replace the placeholder images
        if not img_dict == None:
            file_names = re.findall(r'"Pictures/([^"]+)"', content)
            try:
                for num, imgPath in img_dict.items():
                    shutil.copy(imgPath,os.path.join(temp_dir, f'Pictures/{file_names[len(file_names)-int(num)-1]}'))
            except IndexError:
                print(f'You have only {len(file_names)} image/s in the doc. Index starts from 0')
                
        # Write the modified content back to content.xml
        with open(content_path, 'w') as modified_file:
            modified_file.write(content)
            modified_file.close()
        # Create a new ODT file with the modified content
        with zipfile.ZipFile(out_path, 'w') as modified_odt:
            # Add the modified content.xml back to the ODT
            for root, _, files in os.walk(temp_dir):
                for file in files:
                    file_path = os.path.join(root, file)
                    arcname = os.path.relpath(file_path, temp_dir)
                    modified_odt.write(file_path, arcname)

        # print("Modified file saved as:", out_path)
        # print(temp_dir)
        shutil.rmtree(temp_dir)
