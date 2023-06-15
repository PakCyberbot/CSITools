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
import traceback
import argparse
import subprocess
import sys
import json
import os
import random
import socket
import getpass
from PyQt5.QtCore import QDateTime, QUrl, QThread, pyqtSignal, QCoreApplication
from PyQt5.QtWebEngineCore import *
from PyQt5.QtWebEngineWidgets import *
from urllib.parse import urlparse
from PyQt5.QtGui import *

from PyQt5.QtWidgets import (
    QApplication, QWidget, QFileDialog, QVBoxLayout, QHBoxLayout, QPushButton, QLabel,
    QPlainTextEdit, QStatusBar, QInputDialog, QWizard, QWizardPage, QLineEdit, QFormLayout,
    QDialog, QSizePolicy
)
from PyQt5.QtCore import Qt

from datetime import datetime

import requests
from bs4 import BeautifulSoup
import shutil
import zipfile
import time

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager

import psutil



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
    else:
        print(f"Path to cases_folder {cases_folder}")
    print(case)
    if os.path.isfile(config_file):
        with open(config_file, "r") as f:
            config = json.load(f)
            cases_folder = config.get("cases_folder")
            print(cases_folder)
            case_directory = os.path.join(cases_folder, case)
            print(case_directory)
    else:
        case_directory = os.path.join(case)
        print(case_directory)

    create_case_folder(case_directory)
    print(case_directory)

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
    

def get_random_browser_header():
    browser_headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:89.0) Gecko/20100101 Firefox/89.0",
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.114 Safari/537.36",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:89.0) Gecko/20100101 Firefox/89.0",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.4515.107 Safari/537.36",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:91.0) Gecko/20100101 Firefox/91.0",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36 Edg/91.0.864.37",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36 OPR/77.0.4054.277",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36 Edg/91.0.864.41",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:89.0) Gecko/20100101 Firefox/89.0",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.77 Safari/537.36 Edg/91.0.864.48",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:89.0) Gecko/20100101 Firefox/89.0",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.4515.107 Safari/537.36 OPR/77.0.4054.277",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:91.0) Gecko/20100101 Firefox/91.0",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.4515.131 Safari/537.36",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.4515.131 Safari/537.36 Edg/92.0.902.62",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.4515.107 Safari/537.36 Edg/92.0.902.62",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:92.0) Gecko/20100101 Firefox/92.0",
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.4515.131 Safari/537.36",
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.4515.107 Safari/537.36",
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.4515.107 Safari/537.36 Edg/92.0.902.62",
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.4515.131 Safari/537.36 Edg/92.0.902.62",
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.4515.131 Safari/537.36 OPR/77.0.4054.277",
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.114 Safari/537.36",
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36 Edg/91.0.864.37",
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36 OPR/77.0.4054.277",
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36 Edg/91.0.864.41",
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36 Edg/91.0.864.48",
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.4515.107 Safari/537.36 Edg/92.0.902.62",
    }

    random_header = random.choice(list(browser_headers.keys()))
    return {random_header: browser_headers[random_header]}
    
    # Feel free to add or modify the browser headers as needed.

from selenium.webdriver.chrome.service import Service
from selenium import webdriver
from webdriver_manager.chrome import ChromeDriverManager

def ChromedriverCheck(startme, additional_options=None):
    driver1 = None
    driver2 = None
    chromedriver_path = ChromeDriverManager().install()
    def chromedriver_running():
        # Check if chromedriver is running
        for proc in psutil.process_iter(['pid', 'name']):
            if proc.info['name'] and 'chromedriver' in proc.info['name']:
                return True
        return False

    def start_chromedriver():
        # Start Chromedriver 1
        print("Initializing WebDriver for clearnet sites...")
        service1 = Service(chromedriver_path)
        service1.start()

        options1 = webdriver.ChromeOptions()
        options1.add_argument("--headless")
        options1.add_argument("--no-sandbox")
        options1.add_argument("--ignore-certificate-errors")
        options1.add_argument("--disable-gpu")
        options1.add_argument("--window-size=1280,720")
        options1.add_argument("--log-level=3")

        # Add additional options if provided
        if additional_options:
            for option in additional_options:
                options1.add_argument(option)

        driver1 = webdriver.Chrome(service=service1, options=options1)
        driver1.get("https://csilinux.com")
        print("Chromedriver 1 service started.")

        # Start Chromedriver 2
        print("Initializing WebDriver for .onion sites...")
        service2 = Service(chromedriver_path)
        service2.start()

        options2 = webdriver.ChromeOptions()
        options2.add_argument("--headless")
        options2.add_argument("--no-sandbox")
        options2.add_argument("--ignore-certificate-errors")
        options2.add_argument("--disable-gpu")
        options2.add_argument("--window-size=1280,720")
        options2.add_argument("--log-level=3")
        options2.add_argument("--proxy-server=socks5://127.0.0.1:9050")

        # Add additional options if provided
        if additional_options:
            for option in additional_options:
                options2.add_argument(option)

        driver2 = webdriver.Chrome(service=service2, options=options2)
        driver2.get("https://check.torproject.org/?lang=en-US&small=1&uptodate=1")

        if "Congratulations" in driver2.page_source:
            print("Tor is properly configured.")
        else:
            print("Tor is not properly configured.")
        print("Chromedriver 2 service started.")

        return driver1, driver2

    if startme.lower() == "on":
        if chromedriver_running():
            print("Chromedriver instances are already running.")
            # Terminate the existing instances and start new ones
            for proc in psutil.process_iter(['pid', 'name']):
                if proc.info['name'] and proc.info['name'].startswith('chromedriver'):
                    proc.terminate()
            print("Existing Chromedriver instances have been stopped.")
        driver1, driver2 = start_chromedriver()

    elif startme.lower() == "off":
        # Kill all running chromedriver processes
        for proc in psutil.process_iter(['pid', 'name']):
            if proc.info['name'] and proc.info['name'].startswith('chromedriver'):
                proc.terminate()
        print("Chromedriver instances have been stopped.")

    else:
        print("Invalid command. No action taken.")

    return driver1, driver2






	

def TorCheck(Torstartme):
    def check_tor_service(password):
        command = ["sudo", "-S", "service", "tor", "status"]
        result = subprocess.run(command, input=password.encode(), capture_output=True)
        output = result.stdout.decode().lower()
        # Check if service has exited
        if "active: active" not in output:
            print("Service not running")
            return False
        else:
            print("Service is running")
            return True

    def check_tor_usage():
        url = "https://check.torproject.org/?lang=en-US&small=1&uptodate=1"
        proxies = {
            "http": "socks5h://localhost:9050",
            "https": "socks5h://localhost:9050",
        }
        try:
            response = requests.get(url, proxies=proxies)
            if "Congratulations" in response.text:
                print("Tor is being used.")
            else:
                print("Tor is not being used.")
        except requests.exceptions.RequestException as e:
            print(f"Error checking Tor usage: {e}")

 
    def request_newnym():
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            try:
                s.connect(('127.0.0.1', 9051))
                s.sendall(b'AUTHENTICATE\r\n')
                response = s.recv(1024)
                if b'250 OK' in response:
                    s.sendall(b'SIGNAL NEWNYM\r\n')
                    response = s.recv(1024)
                    if b'250 OK' in response:
                        print('New Tor circuit established')
                    else:
                        print('Failed to establish new Tor circuit')
                else:
                    print('Failed to authenticate to Tor control port')
            except Exception as e:
                print(f'Failed to request newnym: {e}')

    app = QApplication([])
    password, ok = QInputDialog.getText(None, 'Password Input', 'Enter your sudo password:', echo=2)
    if not ok:
        password = ''

    if Torstartme == "on":
        service_was_running = check_tor_service(password)
        if not service_was_running:
            command = ["sudo", "-S", "service", "tor", "start"]
            try:
                subprocess.run(command, input=password.encode(), check=True)
                print("Tor service started.")
                time.sleep(10)  # wait for 10 seconds
            except subprocess.CalledProcessError as e:
                print(f"Error starting Tor service: {e}")
        check_tor_usage()

    elif Torstartme == "newnym":
        if check_tor_service(password):
            print("Tor service is running.")
            request_newnym()
            check_tor_usage()

    elif Torstartme == "off":
        command = ["sudo", "-S", "service", "tor", "stop"]
        try:
            subprocess.run(command, input=password.encode(), check=True)
            print("Tor service stopped.")
        except subprocess.CalledProcessError as e:
            print(f"Error stopping Tor service: {e}")
    else:
        print("Invalid Torstartme command. No action taken.")
	# Usage
	# TTorstartme = "on"  # Set to "off" to stop Tor, "newnym" to request new identity
	# TorCheck(Torstartme)





