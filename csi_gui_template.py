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
import time
import webbrowser
import requests
import os
import sys
import multiprocessing
from concurrent.futures import ProcessPoolExecutor
import platform
import argparse
from PyQt5.QtWidgets import QApplication, QWidget, QMainWindow, QVBoxLayout, QHBoxLayout, QPushButton, QStatusBar, QLabel, QTextEdit, QPlainTextEdit, QLineEdit, QInputDialog, QCheckBox, QScrollArea
from PyQt5.QtCore import QTimer, Qt, QSize
from PyQt5.QtGui import QIcon, QPixmap
from sharedfunctions import auditme, get_current_timestamp, cases_folder, create_case_folder
import argparse
import json
import shutil
from urllib.parse import urlparse
from bs4 import BeautifulSoup

csitoolname = "Tool Name Goes Here"
icon = "CSI-Icon.ico"

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
var3 = args.var3
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
timestamp = get_current_timestamp()
auditme(case_directory, f"{timestamp}: Opening {csitoolname}")
notes_file_path = os.path.join(case_directory, "notes.txt")
var1 = "var1"
var2= "var2"

class BaseCSIApplication(QApplication):
    """Base CSI application class with common functionalities.
    This class is primarily used as the main application class.
    It provides functionalities that are relevant to the application as a whole.
    """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

class BaseCSIWidget(QWidget):
    """Base CSI widget class with common functionalities.
    
    This class is used to create individual GUI elements (widgets), which can be combined and arranged to build up your GUI.
    """

    def __init__(self, main_window, var2_var1_dict, var1, var2, var3, investigator_name, case_name, case_classification, case_priority, *args, **kwargs):
        super().__init__(*args, **kwargs)
        print(var2_var1_dict, var1, var2, var3, investigator_name, case_name, case_classification, case_priority)
        self.main_window = main_window
        self.setWindowTitle(f"{csitoolname}")
        self.setWindowIcon(QIcon(icon))

        self.main_layout = QHBoxLayout()  # Use QHBoxLayout for controlled width layout

        # Command layout
        self.cmd_widget = QWidget()  # Create a QWidget
        self.cmd_layout = QVBoxLayout()  # Set QVBoxLayout
        self.cmd_widget.setFixedWidth(400)  # Set fixed width on widget
        self.cmd_widget.setLayout(self.cmd_layout)  # Set layout to the widget
        
        # sl0 first Entry field and button layout (left side)
        self.sl0_0 = QHBoxLayout()
        self.sl0_0_button = QPushButton(f"Do something for {var3}")
        self.sl0_0.addWidget(self.sl0_0_button)
        self.sl0_0_button.clicked.connect(lambda: self.searchem(var2_var1_dict, var3))
        self.cmd_layout.addLayout(self.sl0_0)   

        self.sl0_1 = QHBoxLayout()
        self.sl0_1_entry_field = QLineEdit()
        self.sl0_1.addWidget(self.sl0_1_entry_field)
        self.sl0_1_button = QPushButton("Add Record")
        self.sl0_1.addWidget(self.sl0_1_button)
        self.sl0_1_button.clicked.connect(self.run_sl0_1_process)  # runs a subprocess through self.run_sl0_1_process below
        self.sl0_1_entry_field.returnPressed.connect(self.sl0_1_button.click)  # Connect returnPressed signal to button click slot
        self.cmd_layout.addLayout(self.sl0_1)              

        scroll_area = QScrollArea()  # Create a scroll area widget
        scroll_widget = QWidget()  # Create a widget to hold the scrollable contents
        self.scroll_layout = QVBoxLayout(scroll_widget)  # Set QVBoxLayout for the scrollable contents
        
        for var2, var1 in var2_var1_dict.items():
            line_layout = QHBoxLayout()
            line_label = QLabel(var2)
            line_label.setFixedWidth(150)
            line_checkbox = QCheckBox("Mark")          
            line_checkbox.setFixedWidth(50)
            line_button = QPushButton("Verify")
            line_button.setToolTip(var2)
            line_button.setFixedWidth(50)
            line_button.clicked.connect(lambda _, var1=var1, var2=var2, line_checkbox=line_checkbox: self.verify_var1(var1, var2, line_checkbox))
            line_button2 = QPushButton("Browser")
            line_button2.setToolTip(var1)
            line_button2.setFixedWidth(80)
            line_button2.clicked.connect(lambda _, var1=var1: self.open_with_chrome(var1))
            if os.path.exists(var2):
                line_button.setToolTip(var2)
                line_checkbox.setChecked(True)
            line_layout.addWidget(line_label)
            line_layout.addWidget(line_checkbox)
            line_layout.addWidget(line_button)
            line_layout.addWidget(line_button2)
            self.scroll_layout.addLayout(line_layout)  # Add each line_layout to the scrollable layout
        
        scroll_area.setWidgetResizable(True)  # Allow the scroll area to resize its content widget
        scroll_area.setWidget(scroll_widget)  # Set the scrollable contents to the scroll area
        self.cmd_layout.addWidget(scroll_area)  # Add the scroll area to the cmd_layout

        # End Command Layout

        # View layout
        self.image_widget = QWidget()
        self.image_layout = QVBoxLayout()
        self.image_widget.setLayout(self.image_layout)
        self.scroll_area2 = QScrollArea()
        self.scroll_area2.setWidgetResizable(True)
        
        self.scroll_content_widget2 = QWidget()
        self.scroll_layout2 = QVBoxLayout(self.scroll_content_widget2)
        self.image_label = QLabel()
        self.image_label.setAlignment(Qt.AlignCenter)
        self.image_label.setScaledContents(True)
        
        self.scroll_layout2.addWidget(self.image_label)
        self.scroll_area2.setWidget(self.scroll_content_widget2)
        self.image_layout.addWidget(self.scroll_area2)
        
        # Pre-build pixmap with default image
        default_image_path = "Images/computerforensics.png"
        default_pixmap = QPixmap(default_image_path)
        self.update_pixmap(default_pixmap)
        
        # Connect resize event to adjust the image label's size
        self.resizeEvent = lambda event: self.adjust_image_label_size()

        # End View Layout

        # Case Note layout
        self.sl2_widget = QWidget()
        self.sl2 = QVBoxLayout()
        self.case_notes_label = QLabel("Case Notes")
        self.case_notes_label.setAlignment(Qt.AlignCenter)
        self.case_notes_label.setStyleSheet("font-weight: bold;")
        self.sl2.addWidget(self.case_notes_label)
        self.case_notes_edit = QPlainTextEdit()
        self.sl2.addWidget(self.case_notes_edit)
        self.sl2_widget.setFixedWidth(300)
        self.sl2_widget.setLayout(self.sl2)

        # Add the widgets to the main layout
        self.main_layout.addWidget(self.cmd_widget)
        self.main_layout.addWidget(self.image_widget, 1)
        self.main_layout.addWidget(self.sl2_widget)

        # Set the main layout as the widget's layout
        self.setLayout(self.main_layout)

        if os.path.isfile(notes_file_path):
            with open(notes_file_path, "r") as f:
                existing_notes = f.read()
                self.case_notes_edit.setPlainText(existing_notes)

        self.sl2_button1 = QPushButton("Run Process")
        self.sl2_button1.clicked.connect(self.save_case_notes)
        self.sl2_button1.setProperty("button_state", False)
        self.sl2_button1.setIcon(QIcon(QPixmap(icon)))
        self.sl2_button1.setIconSize(QSize(300, 35))
        self.sl2_button1.setToolTip("Do Something")
        self.sl2.addWidget(self.sl2_button1)

        self.sl2_button2 = QPushButton("Run Process")
        self.sl2_button2.clicked.connect(self.save_case_notes)
        self.sl2_button2.setProperty("button_state", False)
        self.sl2_button2.setIcon(QIcon(QPixmap(icon)))
        self.sl2_button2.setIconSize(QSize(300, 35))
        self.sl2_button2.setToolTip("Do Something")
        self.sl2.addWidget(self.sl2_button2)

        self.close_button = QPushButton()
        self.close_button.setIcon(QIcon(QPixmap("Images/exit-csit.ico")))
        self.close_button.setIconSize(QSize(300, 35))
        self.close_button.setToolTip("Save and Close Tool.")
        self.close_button.clicked.connect(self.save_case_notes)
        self.sl2.addWidget(self.close_button)
        # End Case Notes Layout

    def adjust_image_label_size(self):
        window_width = self.image_widget.width() - 50
        self.image_label.setFixedWidth(window_width)
    
        # Center the image label within the scroll area
        scroll_width2 = self.scroll_area2.width()
        scroll_content_width2 = self.scroll_content_widget2.width()
        scroll_content_offset2 = (scroll_width2 - scroll_content_width2) // 2
        self.scroll_area2.horizontalScrollBar().setValue(scroll_content_offset2)

    def create_new_record_layout(self, var2, var1):
        line_layout = QHBoxLayout()
        line_label = QLabel(var2)
        line_label.setFixedWidth(150)
        line_checkbox = QCheckBox("Mark")
        line_checkbox.setFixedWidth(50)
        line_button = QPushButton("Verify")
        line_button.setToolTip(var2)
        line_button.setFixedWidth(50)
        line_button.clicked.connect(lambda _, var1=var1, var2=var2, line_checkbox=line_checkbox: self.verify_var1(var1, var2, line_checkbox))
        line_button2 = QPushButton("Browser")
        line_button2.setToolTip(var1)
        line_button2.setFixedWidth(80)
        line_button2.clicked.connect(lambda _, var1=var1: self.open_with_chrome(var1))
        if os.path.exists(var2):
            line_button.setToolTip(var2)
            line_checkbox.setChecked(True)
        line_layout.addWidget(line_label)
        line_layout.addWidget(line_checkbox)
        line_layout.addWidget(line_button)
        line_layout.addWidget(line_button2)
        return line_layout



    def searchem(self, var2_var1_dict, var3):
        var2_var1_dict2 = {}
        with open('asites.json', 'r', encoding='utf-8') as json_file:
            data = json.load(json_file)
            for site in data:
                svar1 = site.get("svar1")
                if svar1:
                    var2 = urlparse(svar1).netloc
                    if var1 not in var2_var1_dict:
                        auditme(case_directory, f"{timestamp}: {csitoolname} : Removing duplicate records")
                        var1 = svar1 + var3
                        var2_var1_dict2[var2] = var1
    
        var2_var1_dict = {var2: var1 for var2, var1 in sorted(var2_var1_dict2.items())}   
        timestamp = get_current_timestamp()
        auditme(case_directory, f"{timestamp}: {csitoolname} : Testing New records")
    
        print(var2_var1_dict)
        print(var3)
        return var2_var1_dict


    def run_sl0_1_process(self):
        var1 = self.sl0_1_entry_field.text()
        with open(filenametxt, "a") as file:
            file.write(var1 + "\n")
        parsed_var1 = urlparse(var1)
        var2 = parsed_var1.netloc
        # Create a new record for the added entry

        line_layout = self.create_new_record_layout(var2, var1)
        self.scroll_layout.addLayout(line_layout)  # Add each line_layout to the scrollable layout
        self.main_window.update_status(f"Appended '{var1}' to {filenametxt}")


    def open_with_chrome(self, var1):
        timestamp = get_current_timestamp()
        auditme(case_directory, f"{timestamp}: {csitoolname} : Opening {var1} in Chrome")
        self.main_window.update_status(f"Opening {var1} with Chrome.")
        webbrowser.get(using='google-chrome').open_new_tab(var1)

    def update_pixmap(self, pixmap):
        pixmap = pixmap.scaledToWidth(800)
        self.image_label.setPixmap(pixmap)
        
    def verify_var1(self, var1, var2, line_checkbox):
        auditme(case_directory, f"{timestamp}: {csitoolname} : something")
        #do somthing
        


    def save_case_notes(self):
        current_timestamp = get_current_timestamp()
        auditme(case_directory, f"{current_timestamp}: Saving Case Notes and Exiting {csitoolname}")
        case_notes_content = self.case_notes_edit.toPlainText()
        with open(notes_file_path, "w") as f:
            f.write(case_notes_content)
        # do more stuff if needed
        self.main_window.close()





class CSIMainWindow(QMainWindow):
    """The main window class for the CSI application."""

    def __init__(self, case_directory, window_title, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.case_directory = case_directory
        self.setWindowTitle(f"{window_title} : Case: {case_name} - {case_classification} Priority:{case_priority}")
        self.setWindowIcon(QIcon(icon))
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.application = None

    def set_application(self, application):
        """Set the application instance."""
        self.application = application

    def update_status(self, message):
        """Update the status bar with the given message."""
        self.status_bar.showMessage(message)  
        
def run_script(evidence_dir):
    filenametxt = os.path.join(evidence_dir, f'File_to_list_on_left.txt')
    with open(filenametxt, 'r') as f:
        lines = f.readlines()

    lines = sorted(list(set(lines)))
    var2_var1_dict = {}

    for line in lines:
        var1 = line.strip()
        var2 = urlparse(var1).netloc
        var2_var1_dict[var2] = var1

    timestamp = get_current_timestamp()
    auditme(case_directory, f"{timestamp}: {csitoolname} - Removing duplicate records")

    return var2_var1_dict


if __name__ == "__main__":
    app = BaseCSIApplication(sys.argv)
 
    if var3 is None:
        var3, ok = QInputDialog.getText(None, "Var3", "Enter the the Var3 value here:", QLineEdit.Normal, "")
        if not var3 == '':
            sys.exit(1) 
            
    evidence_dir = os.path.join(case_directory, f"Evidence/Online/Folder")    # Change "Folder" to the appropriate evidence sub-folder
    os.makedirs(evidence_dir, exist_ok=True)                                  # If the "Folder" doesn't exist, create it
    filenametxt = os.path.join(evidence_dir, f'File_to_list_on_left.txt')     # File to build the left list from if you use it.
    if not os.path.exists(filenametxt):
        with open(filenametxt, 'w') as file:
            # Optional: Add initial content to the file if desired
            file.write("")
`        
    # Create the main window
    main_window = CSIMainWindow(case_directory, csitoolname)
    
    # Create the base CSI widget and set it as the central widget in the main window
    var2_var1_dict = run_script(evidence_dir)
    widget = BaseCSIWidget(main_window, var2_var1_dict, var1, var2, var3, investigator_name, case_name, case_classification, case_priority)
    main_window.setCentralWidget(widget)
    main_window.setGeometry(100, 100, 1650, 800)
    main_window.set_application(app)
    
    # Show the main window
    main_window.show()
    
    # Start the application event loop
    sys.exit(app.exec_())

