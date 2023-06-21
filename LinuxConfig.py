import sys, argparse, os, subprocess, json, shutil, platform
from PySide2.QtWidgets import QApplication, QWidget, QFileDialog, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QPlainTextEdit, QStatusBar, QInputDialog, QWizard, QWizardPage, QLineEdit, QFormLayout, QDialog, QSizePolicy
from PySide2.QtCore import Qt
from PySide2.QtGui import QFocusEvent, QIcon
import sharedfunctions

class ConfigMe():

    def __init__(self, case, computer_name, hw_file, cnotes, audit_file):
        self.case = case
        self.computer_name = computer_name
        self.hw_file = hw_file
        self.cnotes = cnotes
        self.audit_file = audit_file
        self.process_file = f"{case}/Evidence/Triage/{computer_name}/processes.json"
        output = subprocess.check_output('jc ps aux', shell=True, stderr=subprocess.STDOUT)
        if output:
            output_str = output.decode('utf-8')
            parsed_output = json.loads(output_str)
            with open(self.process_file, 'w') as file:
                json.dump(parsed_output, file, indent=4)      

    def run_hwinfo(self, computer_name, sudo_password):
        global sudo_pasword 
        os.makedirs(os.path.dirname(self.hw_file), exist_ok=True)
        if sudo_password == "":
            sudo_password, ok_pressed = QInputDialog.getText(None, "Sudo Password", "Please enter your sudo password:", QLineEdit.Password)
            if not ok_pressed or not sudo_password:
                self.audit_me("No password entered.  Canceling")
                with open(self.hw_file, "w") as f:
                    f.write("You need to run this tool with root priviledges to get hardware information.")
                return None
        with open(self.hw_file, "w") as f:
            command = f"echo '{sudo_password}' | sudo -S lshw -json"
            subprocess.run(command, stdout=f, shell=True, check=True)
     
    def process_ps_aux():
        output = subprocess.check_output('jc ps aux', shell=True, stderr=subprocess.STDOUT)
        if output:
            output_str = output.decode('utf-8')
            parsed_output = json.loads(output_str)
            with open(self.process_file, 'w') as file:
                json.dump(parsed_output, file, indent=4) 
            
    def open_folder(folder_path):
        system = platform.system()
        subprocess.run(["xdg-open", folder_path])   
    
    def priv_copy(self, source, dest, sudo_password):
        command = f"echo '{sudo_password}' | sudo -S cp -r {source} {dest}"
        process = subprocess.Popen(command, shell=True, stdin=subprocess.PIPE, stderr=subprocess.PIPE)
        stdout, stderr = process.communicate()
        if stdout:
            output = stdout.decode("utf-8")
        else:
            output = stderr.decode("utf-8")
        return output

    def sudo_chown(self, dest, sudo_password):
        username = os.getlogin()
        command = f"echo '{sudo_password}' | sudo -S chown -R {username}:{username} {dest}"
        process = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stdin=subprocess.PIPE, stderr=subprocess.PIPE)
        stdout, stderr = process.communicate()
        command = f"ls -la -R {dest}"
        process = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stdin=subprocess.PIPE, stderr=subprocess.PIPE)
        stdout, stderr = process.communicate()
        if stdout:
            output = stdout.decode("utf-8")
        else:
            output = stderr.decode("utf-8")
        return output

    def pick_folder(self, sudo_password):
        dialog = QFileDialog()
        dialog.setDirectory("/")
        dialog.setFileMode(QFileDialog.DirectoryOnly)
        if dialog.exec_():
            drive = str(dialog.selectedFiles()[0])
        else:
            self.update_case_notes("Cancelled Data Capture")        
        if sudo_password == "":
            sudo_password, ok_pressed = QInputDialog.getText(None, "Sudo Password", "Please enter your sudo password:", QLineEdit.Password)
            if not ok_pressed or not sudo_password:
                self.update_case_notes("No password entered.  Canceling")
                return None    
        return drive
                
    def audit_me(self, message):
        with open(self.audit_file, "a+") as f:
            f.write(message + "\n")
        return message
              
    def run_write_blocker(self, case, computer_name):
        self.audit_me("Running Forensic Gallery Viewer")
        print("wb")
        prog_path = os.path.join(os.getcwd(), "csi_write_blocker")
        process = subprocess.Popen([prog_path, "--case", self.case], stderr=subprocess.PIPE)

    def run_gallery_view(self, case, computer_name):
        print("Running Forensic Gallery Viewer")
        self.audit_me("Running Forensic Gallery Viewer")
        prog_path = os.path.join(os.getcwd(), "csi_forensic_gallery_view.py")
        process = subprocess.Popen(["python", prog_path, "--case", self.case, "--computer_name", self.computer_name])

