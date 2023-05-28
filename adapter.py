import sys
import netifaces
import subprocess
import re
from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QRadioButton, QPushButton


class NetworkAdapterSelector(QWidget):
    def __init__(self):
        super().__init__()
        self.selected_adapter = None
        self.init_ui()


    def init_ui(self):
        self.setWindowTitle("Network Adapter Selector")

        # Create a layout
        layout = QVBoxLayout()

        # Get the list of network adapters
        adapters = self.get_network_adapters()

        # Create radio buttons for each adapter
        self.radio_buttons = []
        for adapter_name, adapter_type in adapters:
            label = f"{adapter_type}: {adapter_name}"
            radio_button = QRadioButton(label)
            self.radio_buttons.append(radio_button)
            layout.addWidget(radio_button)

        # Create a button to get the selected adapter
        button = QPushButton("Select Adapter")
        button.clicked.connect(self.get_selected_adapter)
        layout.addWidget(button)

        # Set the layout
        self.setLayout(layout)

    def get_network_adapters(self):
        adapters = []
        interfaces = netifaces.interfaces()
        for interface in interfaces:
            if interface == "lo":
                continue
            addresses = netifaces.ifaddresses(interface)
            if netifaces.AF_INET in addresses:
                adapter_type = "Wireless Connection" if self.is_wireless_adapter(interface) else "Ethernet Connection"
                if self.is_virtual_adapter(interface):
                    adapter_type = "Bridged Connection"
                adapter_name = interface
                if adapter_type == "Wireless Connection":
                    access_point = self.get_wireless_access_point(interface)
                    if access_point:
                        adapter_name = f"{adapter_name} (Connected to \"{access_point}\")"
                adapters.append((adapter_name, adapter_type))
        return adapters

    def is_wireless_adapter(self, adapter):
        try:
            output = subprocess.check_output(["iwconfig", adapter])
            output = output.decode("utf-8")
            if "ESSID" in output:
                return True
        except subprocess.CalledProcessError:
            pass
        return False

    def is_virtual_adapter(self, adapter):
        try:
            output = subprocess.check_output(["ethtool", "-i", adapter])
            output = output.decode("utf-8")
            if "driver: vboxnet" in output:
                return True
        except subprocess.CalledProcessError:
            pass
        return False

    def get_selected_adapter(self):
        selected_adapter = None
        for radio_button in self.radio_buttons:
            if radio_button.isChecked():
                # If the adapter is connected to an access point, split on " ("
                if " (" in radio_button.text():
                    selected_adapter = radio_button.text().split(": ")[1].split(" (")[0]
                else:
                    selected_adapter = radio_button.text().split(": ")[1]
                break
    
        if selected_adapter:
            if selected_adapter.startswith("w"):
                access_point = self.get_wireless_access_point(selected_adapter)
                if access_point:
                    print(selected_adapter)
                else:
                    print("Wireless adapter is not connected to an access point.")
            # Save the selected adapter as an attribute
            self.selected_adapter = selected_adapter
    
        # Close the application
        QApplication.quit()



    def get_wireless_access_point(self, adapter):
        try:
            output = subprocess.check_output(["iw", "dev", adapter, "link"])
            output = output.decode("utf-8")
            ssid_match = re.search(r"SSID:\s(.+)", output)
            if ssid_match:
                return ssid_match.group(1)
        except subprocess.CalledProcessError:
            pass
        return None


if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = NetworkAdapterSelector()
    window.show()
    sys.exit(app.exec_())
    # After the application has been closed, the selected adapter's name will be available here
    print(window.selected_adapter)


