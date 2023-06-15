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

# libs for encrypting APIKeys
import base64
from cryptography.fernet import Fernet, InvalidToken
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

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

def ChromedriverCheck(startme, additional_options=None, onion=False):
    driver = None
    chromedriver_path = ChromeDriverManager().install()

    def check_tor_usage():
        response = requests.get("https://check.torproject.org/?lang=en-US&small=1&uptodate=1")
        if "Congratulations" in response.text:
            print("Tor is being used.")
        else:
            print("Tor is not being used.")

    def start_chromedriver():
        print("Initializing WebDriver...")
        service = Service(chromedriver_path)
        service.start()

        options = webdriver.ChromeOptions()
        options.add_argument("--disable-extensions")
        options.add_argument("--incognito")
        options.add_argument("--headless")

        # Add additional options if provided
        if additional_options:
            for option in additional_options:
                options.add_argument(option)

        if onion:
            options.add_argument("--proxy-server=socks5://127.0.0.1:9050")

        driver = webdriver.Chrome(service=service, options=options)
        driver.get("https://check.torproject.org/?lang=en-US&small=1&uptodate=1")
        check_tor_usage()

        print("Chromedriver service started.")
        return driver

    if startme.lower() == "on":
        driver = start_chromedriver()

    elif startme.lower() == "off":
        # Kill all running chromedriver processes
        for proc in psutil.process_iter(['pid', 'name']):
            if proc.info['name'] and proc.info['name'].startswith('chromedriver'):
                proc.terminate()
        print("Chromedriver instances have been stopped.")

    else:
        print("Invalid command. No action taken.")

    return driver
    


def TorCheck(Torstartme):
    def check_tor_service():
        command = ["service", "tor", "status"]
        result = subprocess.run(command, capture_output=True)
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


    if Torstartme == "on":
        service_was_running = check_tor_service()
        if not service_was_running:
            app = QApplication([])
            password, ok = QInputDialog.getText(None, 'Password Input', 'Enter your sudo password:', echo=2)
            if not ok:
                password = ''

            command = ["sudo", "-S", "service", "tor", "start"]
            try:
                subprocess.run(command, input=password.encode(), check=True)
                print("Tor service started.")
                time.sleep(10)  # wait for 10 seconds
            except subprocess.CalledProcessError as e:
                print(f"Error starting Tor service: {e}")
        check_tor_usage()

    elif Torstartme == "newnym":
        if check_tor_service():
            print("Tor service is running.")
            request_newnym()
            check_tor_usage()

    elif Torstartme == "off":
        app = QApplication([])
        password, ok = QInputDialog.getText(None, 'Password Input', 'Enter your sudo password:', echo=2)
        if not ok:
            password = ''

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

#------------------------- APIKeys encryption methods --------------------------------------------#

def genKey(password=0):     # generate key for Fernet() using password.
    # genKey doesn't stores key for a better security, generates it at runtime.   
    if password == 0:
        password = input("Enter Password: ").encode()
    else:
        password = password.encode()
    salt=b"Just4FillingTheRequirementOfPBKDF2HMAC"  
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=salt,
        iterations=480000
    )
    derived=kdf.derive(password)
    key = base64.urlsafe_b64encode(derived)
    return key
    
def encrypt(key):
    f = Fernet(key)

    # encrypting APIKeys.json
    with open(f'{csitools_dir}APIKeys.json', 'rb') as plain_file:
        plain_data = plain_file.read()
    
    encrypted_data = f.encrypt(plain_data)

    with open(f'{csitools_dir}APIKeys.enc', 'wb') as encrypted_file:
        encrypted_file.write(encrypted_data)

    # Removing plaintext data file
    os.remove(f'{csitools_dir}APIKeys.json')
    
    return True

def decrypt(key):
    f = Fernet(key)

    try:
        # Decrypting APIKeys.enc
        with open(f'{csitools_dir}APIKeys.enc', 'rb') as encrypted_file:
            encrypted_data = encrypted_file.read()
        
        plain_data = f.decrypt(encrypted_data)

        with open(f'{csitools_dir}APIKeys.json', 'wb') as plain_file:
            plain_file.write(plain_data)
    
        return True
    
    except InvalidToken:
        print("Invalid Password to Decrypt")
        return False

def reportme(tmpl_path,out_path,data_dict, img_dict=None):
    """
    fill_template(tmpl_path, out_path, data_dict, img_list):
        Fills in the fields of the template document with data and generates a result document.

    Args:
        tmpl_path (str): Path of the template document that contains the fields to be filled in.
        out_path (str): Path of the resulting document with placeholders replaced by data.
        data_dict (dict): A dictionary mapping placeholder names to their corresponding values for replacement.
        img_list (dict): A dictionary specifying the images to replace in the document. 
            Key: The position of the image, docx and odt have different positions arrangement.
            Value: The path to the image file.

    Note:
    - In ODT files: Position of Images depends on the order of adding them not the format of document.
        - if someone adds the image first but adds it to the last page still it will gonna have 0 position.
    - In DOCX files: Position of Images depends on the format of document.
        - if someone adds the image first but adds it to the last page then it will gonna have last position.

    Example:
        tmpl_path = 'template.odt'
        out_path = 'result.odt'
        data_dict = {'placeholder1': 'value1', 'placeholder2': 'value2'}
        img_list = {0: 'image1.png', 1: 'image2.png'}
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
            # dealing with adding multi line value to the variable in xml using heavy regex
            if '\n' in value:
                values = value.split('\n')

                main_search_string = f'<text:user-defined[^&]*?>&lt;{placeholder}&gt;</text:user-defined>'

                occurrences = re.finditer(rf'({main_search_string})(.*?</text:p>)', content)

                for count, occurrence in enumerate(occurrences):
                    temp = re.search(rf'<.*>', occurrence.group(2))
                    posttext = temp.group()
                    tags = posttext.strip('</>')
                    tags = tags.split('></')
                    
                    re_pretext = ''
                    for i in range(0, len(tags)):
                        tag = tags[len(tags) - i - 1]
                        re_pretext += f'(<{tag}[^>]*>)'
                        if tag == 'text:p':
                            re_pretext += '(?:(?!<text:p).)*?'

                    temp = re.search(rf'{re_pretext}({main_search_string})(.*?</text:p>)', content)

                    pretext = ''
                    for i in range(0, len(tags)):
                        pretext += temp.group(i + 1)

                    data_multiline = ''
                    for i, val in enumerate(values):
                        if i == 0:
                            data_multiline += f"{val}{posttext}"
                        elif i == len(values) - 1:
                            data_multiline += f'{pretext}{val}'
                        else:
                            data_multiline += f'{pretext}{val}{posttext}'
                    content = re.sub(re.escape(occurrence.group(1)), data_multiline, content, count=count+1)

            else:
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
    
    if tmpl_path.lower().endswith(".docx"):
        # Create a temporary directory to extract the DOCX contents
        temp_dir = tempfile.mkdtemp()

        # Extract the ODT contents to the temporary directory
        with zipfile.ZipFile(tmpl_path, 'r') as odt_file:
            odt_file.extractall(temp_dir)
        
        content_path = os.path.join(temp_dir, 'word','header1.xml')
        # Read the header.xml and footer.xml file for header and footer
        if  os.path.isfile(content_path):
            # header.xml
            with open(content_path, 'r') as content_file:
                content = content_file.read()
                content_file.close()
            
            # regex pattern to find placeholder and replace with the value
            for placeholder, value in data_dict.items(): 
                content = re.sub(rf'&lt;{placeholder}&gt;', value, content)

            # Write the modified content back to styles.xml
            with open(content_path, 'w') as modified_file:
                modified_file.write(content)
                modified_file.close()

            # footer.xml
            content_path = os.path.join(temp_dir, 'word','footer1.xml')
            with open(content_path, 'r') as content_file:
                content = content_file.read()
                content_file.close()
            
            # regex pattern to find placeholder and replace with the value
            for placeholder, value in data_dict.items(): 
                content = re.sub(rf'&lt;{placeholder}&gt;', value, content)

            # Write the modified content back to styles.xml
            with open(content_path, 'w') as modified_file:
                modified_file.write(content)
                modified_file.close()
        
        # Read the document.xml file
        content_path = os.path.join(temp_dir, 'word', 'document.xml')
        with open(content_path, 'r', encoding='utf-8') as content_file:
            content = content_file.read()
            content_file.close()
        
        # regex pattern to find placeholder and replace with the value
        for placeholder, value in data_dict.items():
            # dealing with adding multi line value to the variable in xml using heavy regex
            # if False:
            if '\n' in value:
                values = value.split('\n')

                main_search_string = f'&lt;{placeholder}&gt;'
                
                occurrences = re.finditer(rf'(<w:p>(?:(?!<w:p>).)*?)(<w:r>(?:(?!<w:r>).)*?)<w:t>[^<>]*?({main_search_string})', content)
                

                for count, occurrence in enumerate(occurrences):    
                    # pretext to add new line
                    # condition to check if placeholder is in bullet point then add new <w:p>
                    if '<w:numPr><w:ilvl w:val="0"/>' in occurrence.group(1):   
                        # This is just like pressing enter in docx
                        # print('list found!')
                        pretext = occurrence.group(1) + occurrence.group(2) + '<w:t>'
                        posttext = '</w:t></w:r></w:p>'
                    # if not bullet point then to keep the consistent style just do <w:br>
                    else:
                        # This is just like pressing shift + enter in docx
                        pretext = occurrence.group(2) + '<w:br w:type="textWrapping"/></w:r>' + occurrence.group(2) + '<w:t>'
                        posttext = '</w:t></w:r>'
                        

                    data_multiline = ''
                    for i, val in enumerate(values):
                        if i == 0:
                            data_multiline += f"{val}{posttext}"
                        elif i == len(values) - 1:
                            data_multiline += f'{pretext}{val}'
                        else:
                            data_multiline += f'{pretext}{val}{posttext}'

                    content = re.sub(re.escape(occurrence.group(3)), data_multiline, content, count=count+1)

            else:
                content = re.sub(rf'&lt;{placeholder}&gt;', value, content)

        # replace the placeholder images
        if not img_dict == None:
            img_dir = os.path.join(temp_dir,'word','media')
            file_names = os.listdir(img_dir)
            try:
                for num, imgPath in img_dict.items():
                    shutil.copy(imgPath,os.path.join(img_dir, f'{file_names[int(num)]}'))
                    print
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


	
