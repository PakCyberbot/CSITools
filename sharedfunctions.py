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



if not os.path.exists("agency_data.json"):
    try:
        subprocess.run(["python", "Agency.Wizard.py"])
    except Exception as e:
        print(f"An error occurred: {str(e)}")
        sys.exit()

with open("agency_data.json", "r") as file:
    data = json.load(file)
    cases_folder = data.get("cases_folder")
    print(cases_folder)
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

        layout = QVBoxLayout(self)
        layout.setSpacing(0)  # Adjust the vertical spacing here (e.g., reduce it to 0)
        self.label = QLabel("Drag and drop or click to add evidence")
        self.label.setAlignment(Qt.AlignBottom)
        layout.addWidget(self.label)

        self.setLayout(layout)
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

def get_current_timestamp(timestamp=None):
    if timestamp is None:
        timestamp = QDateTime.currentDateTime().toString('yyyy-MM-dd:hh:mm:ss.zzz')
    else:
        timestamp = QDateTime.fromString(timestamp, 'yyyy-MM-dd:hh:mm').toString('yyyy-MM-dd:hh:mm:ss.zzz')
    return f"{timestamp}"

def auditme(case_directory, message):
    audit_log_path = os.path.join(case_directory, "audit.log")
    if not os.path.isfile(audit_log_path):
        with open(audit_log_path, 'w+') as f:
            pass  # create empty file
    with open(audit_log_path, 'a') as f:
        f.write(get_current_timestamp() + message + "\n")


