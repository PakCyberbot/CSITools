import os
import sys
import json
import subprocess
import threading
from PySide2.QtCore import QThread, Signal, QUrl, Qt, QSize
from PySide2.QtGui import QIcon, QPixmap
from PySide2.QtWidgets import QApplication, QWidget, QMainWindow, QVBoxLayout, QHBoxLayout, QPushButton, QStatusBar, QLabel, QPlainTextEdit, QScrollArea
from PySide2.QtWebEngineWidgets import QWebEngineView
from urllib.parse import quote_plus
from sharedfunctions import auditme, get_current_timestamp, WhatIsMyIP, WhatIsMyTorIP, CSIIPLocation, TorCheck, CSI_TorVPN

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

csitoolname = "CSI: What is My IP?"
case_directory = cases_folder
current_dir = os.getcwd()  # Get the current working directory
notes_file_path = os.path.join(case_directory, "External_Network.txt")
icon = "Images/CSI-TorVPN-Icon.png"

if not os.path.isfile(notes_file_path):
    with open(notes_file_path, 'a+') as f:
        f.write("External IP Address Information:\n" + get_current_timestamp() + "\n\n")


def format_dict_to_str(dict_obj):
    return '\n'.join([f'{k}: {v}' for k, v in dict_obj.items()])


class Worker(QThread):
    data_fetched = Signal(str, dict)

    def __init__(self, main_window, ip_fetcher, location_fetcher, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.main_window = main_window
        self.ip_fetcher = ip_fetcher
        self.location_fetcher = location_fetcher

    def run(self):
        ip, istor = self.ip_fetcher()
        ip_info = self.location_fetcher(ip, istor)
        if ip_info is not None:
            self.data_fetched.emit(ip, ip_info)
        else:
            print("Failed to fetch IP info.")

class StartCSITorVPNThread(QThread):
    torvpn_started = Signal()

    def run(self):
        try:
            subprocess.run(["CSI_TorVPN"], check=True)
        except subprocess.CalledProcessError:
            print("CSI_TorVPN exited with a non-zero status")
        except Exception as e:
            print(f"An error occurred: {str(e)}")
        finally:
            self.torvpn_started.emit()

class BaseCSIApplication(QApplication):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)


class BaseCSIWidget(QWidget):
    def __init__(self, main_window, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.main_window = main_window
        self.main_window.update_status(f"Starting workers for data capture")

        self.clearnet_worker = Worker(main_window, WhatIsMyIP, CSIIPLocation)
        self.clearnet_worker.data_fetched.connect(self.update_clearnet_ip_label)
        self.clearnet_worker.start()

        self.tor_worker = Worker(main_window, WhatIsMyTorIP, CSIIPLocation)
        self.tor_worker.data_fetched.connect(self.update_tor_ip_label)
        self.tor_worker.start()

        self.setWindowTitle(f"{csitoolname}")
        self.setWindowIcon(QIcon(icon))

        self.main_layout = QHBoxLayout()  # Use QHBoxLayout for controlled width layout

        self.cmd_widget = QWidget()  # Create a QWidget
        self.cmd_layout = QVBoxLayout()  # Set QVBoxLayout
        self.cmd_widget.setFixedWidth(300)  # Set fixed width on widget
        self.cmd_widget.setLayout(self.cmd_layout)  # Set layout to the widget

        scroll_area = QScrollArea()  # Create a scroll area widget
        scroll_widget = QWidget()  # Create a widget to hold the scrollable contents
        self.scroll_layout = QVBoxLayout(scroll_widget)  # Set QVBoxLayout for the scrollable contents

        # IP address and geolocation data

        self.clearnet_label = QLabel("<b>Clearnet IP:</b>")
        self.scroll_layout.addWidget(self.clearnet_label)

        self.clearnet_info_label = QLabel("{clearnetipinfo}")
        self.scroll_layout.addWidget(self.clearnet_info_label)

        self.tor_label = QLabel("<b>Tor Darknet IP:</b>")
        self.scroll_layout.addWidget(self.tor_label)
        self.tor_ip_label = QLabel("{Torip}")
        self.scroll_layout.addWidget(self.tor_ip_label)

        scroll_area.setWidgetResizable(True)  # Allow the scroll area to resize its content widget
        scroll_area.setWidget(scroll_widget)  # Set the scrollable contents to the scroll area
        self.cmd_layout.addWidget(scroll_area)  # Add the scroll area to the cmd_layout
        # End Command Layout

        # View layout
        self.image_widget = QWidget()
        self.image_layout = QVBoxLayout()
        self.image_widget.setLayout(self.image_layout)

        self.browser_view = QWebEngineView()
        self.image_layout.addWidget(self.browser_view)
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

        self.sl2_button1 = QPushButton("New Tor Identity")
        self.sl2_button1.setProperty("button_state", False)
        self.sl2_button1.setIcon(QIcon(QPixmap("Images/CSI-TorVPN-Logo.png")))
        self.sl2_button1.setIconSize(QSize(300, 35))
        self.sl2_button1.setToolTip("Do Something")
        self.sl2_button1.clicked.connect(self.new_tor_identity)
        self.sl2.addWidget(self.sl2_button1)

        self.sl2_button2 = QPushButton("Start CSI TorVPN")
        self.sl2_button2.setProperty("button_state", False)
        self.sl2_button2.setIcon(QIcon(QPixmap("Images/CSI-TorVPN-Logo.png")))
        self.sl2_button2.setIconSize(QSize(300, 35))
        self.sl2_button2.setToolTip(
            "CSI TorVPN will push all your traffic through the Tor Proxy.  This minimizes the possibility of location leaks and protects like a VPN, but better."
        )
        self.sl2_button2.clicked.connect(self.start_csi_torvpn)
        self.sl2.addWidget(self.sl2_button2)

        self.close_button = QPushButton()
        self.close_button.setIcon(QIcon(QPixmap("Images/exit-csit.ico")))
        self.close_button.setIconSize(QSize(300, 35))
        self.close_button.setToolTip("Save and Close Tool.")
        self.close_button.clicked.connect(self.save_case_notes)
        self.sl2.addWidget(self.close_button)

    def update_tor_ip_label(self, Torip, Toripinfo):
        # Store Toripinfo data with prefix
        Toripinfo_data = {}
        for key, value in Toripinfo.items():
            new_key = f"Toripinfo_{key}"
            Toripinfo_data[new_key] = value

        # Strip out the prefix from dictionary keys
        Toripinfo_data = {key.split('_')[1]: value for key, value in Toripinfo_data.items()}

        # Update the labels with the stored data
        self.tor_ip_label.setText(Torip)
        self.tor_ip_label.setText(format_dict_to_str(Toripinfo_data))
        self.main_window.update_status(f"Tor proxy is now {Torip}")

        # Update the case notes
        self.case_notes_edit.appendPlainText(
            get_current_timestamp()
            + f"\nTor Proxy IP Address: {Torip}\n{Toripinfo_data.get('org', '')}\n{Toripinfo_data.get('city', '')}, {Toripinfo_data.get('region', '')}\n"
        )

    def update_clearnet_ip_label(self, clearnetip, clearnetipinfo):
        # Store clearnetipinfo data with prefix
        clearnetipinfo_data = {}
        for key, value in clearnetipinfo.items():
            new_key = f"clearnetipinfo_{key}"
            clearnetipinfo_data[new_key] = value

        # Strip out the prefix from dictionary keys
        clearnetipinfo_data = {key.split('_')[1]: value for key, value in clearnetipinfo_data.items()}

        self.clearnet_info_label.setText(format_dict_to_str(clearnetipinfo_data))

        self.main_window.update_status(f"Updating map view")

        # Show clearnet IP location on OpenStreetMap
        if 'latitude' in clearnetipinfo_data and 'longitude' in clearnetipinfo_data:
            latitude = clearnetipinfo_data['latitude']
            longitude = clearnetipinfo_data['longitude']
            self.show_clearnet_location_on_map(latitude, longitude)

        # Update the case notes
        self.case_notes_edit.appendPlainText(
            get_current_timestamp()
            + f"\nClearnet IP Address: {clearnetip}\n{clearnetipinfo_data.get('org', '')}\n{clearnetipinfo_data.get('city', '')},     {clearnetipinfo_data.get('region', '')}\n"
        )

    def show_clearnet_location_on_map(self, latitude, longitude):
        url = f"https://www.openstreetmap.org/?mlat={latitude}&mlon={longitude}#map=10/{latitude}/{longitude}"
        self.browser_view.load(QUrl(url))
        self.main_window.update_status(f"Map view opened")

    def new_tor_identity(self):
        self.case_notes_edit.appendPlainText(get_current_timestamp() + f"\nNew Tor identity requested")
        self.main_window.update_status("Requesting new Tor identity")
        TorCheck("newnym")
        new_tor_ip = WhatIsMyTorIP()
        self.main_window.update_status(f"New Tor IP address is: {new_tor_ip}")
        print(new_tor_ip)
        self.tor_worker = Worker(main_window, WhatIsMyTorIP, CSIIPLocation)
        self.tor_worker.data_fetched.connect(self.update_tor_ip_label)
        self.tor_worker.start()  # Start the worker thread
    def start_csi_torvpn(self):
        self.main_window.update_status(f"Starting the CSI TorVPN...")
        self.csi_torvpn_thread = StartCSITorVPNThread()
        self.csi_torvpn_thread.torvpn_started.connect(self.on_torvpn_started)
        self.csi_torvpn_thread.start()

    def on_torvpn_started(self):
        self.main_window.update_status(f"CSI TorVPN started successfully.")
        self.main_window.update_status(f"Sending the workers to get data...")

        try:
            self.clearnet_worker = Worker(main_window, WhatIsMyIP, CSIIPLocation)
            self.clearnet_worker.data_fetched.connect(self.update_clearnet_ip_label)
            self.clearnet_worker.start()
        except Exception as e:
            print(f"An error occurred when starting clearnet_worker: {str(e)}")

        try:
            self.tor_worker = Worker(main_window, WhatIsMyTorIP, CSIIPLocation)
            self.tor_worker.data_fetched.connect(self.update_tor_ip_label)
            self.tor_worker.start()
        except Exception as e:
            print(f"An error occurred when starting tor_worker: {str(e)}")

        self.main_window.update_status(f"Verify location settings. Please be patient, this can take time...")

    def save_case_notes(self):
        current_timestamp = get_current_timestamp()
        auditme(case_directory, f"{current_timestamp}: Saving Case Notes and Exiting {csitoolname}")
        case_notes_content = self.case_notes_edit.toPlainText()
        with open(notes_file_path, "w") as f:
            f.write(case_notes_content)
        self.main_window.close()

    def adjust_image_label_size(self):
        window_width = self.image_widget.width() - 50
        self.image_label.setFixedWidth(window_width)
        scroll_width2 = self.scroll_area2.width()
        scroll_content_width2 = self.scroll_content_widget2.width()
        scroll_content_offset2 = (scroll_width2 - scroll_content_width2) // 2
        self.scroll_area2.horizontalScrollBar().setValue(scroll_content_offset2)


class CSIMainWindow(QMainWindow):
    def __init__(self, case_directory, window_title, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.case_directory = case_directory
        self.setWindowTitle(f"{window_title}")
        self.setWindowIcon(QIcon(icon))
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.application = None

    def set_application(self, application):
        self.application = application

    def update_status(self, message):
        self.status_bar.showMessage(message)


if __name__ == "__main__":
    app = BaseCSIApplication([sys.argv[0], '--no-sandbox'])  # Corrected line
    main_window = CSIMainWindow(case_directory, csitoolname)
    widget = BaseCSIWidget(main_window, main_window)  # Pass main_window as an argument
    main_window.setCentralWidget(widget)
    main_window.setGeometry(100, 100, 1368, 768)
    main_window.set_application(app)
    main_window.show()
    sys.exit(app.exec_())

