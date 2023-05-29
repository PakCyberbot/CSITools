import sys, argparse, os, subprocess, json, shutil, platform, wmi, psutil, time
from PyQt5.QtWidgets import QApplication, QWidget, QFileDialog, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QPlainTextEdit, QStatusBar, QInputDialog, QWizard, QWizardPage, QLineEdit, QFormLayout, QDialog, QSizePolicy, QProgressDialog
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFocusEvent, QIcon
import sharedfunctions
import ctypes, win32api
myappid = 'mycompany.myproduct.subproduct.version'
ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)

class ConfigMe():

    def __init__(self, case, computer_name, hw_file, cnotes, audit_file):
        self.case = case
        self.computer_name = computer_name
        self.hw_file = hw_file
        self.cnotes = cnotes
        self.audit_file = audit_file

    def run_hwinfo(self, computer_name, sudo_password):
        progress = QProgressDialog("Running Hardware Information...", None, 0, 7, None)
        progress.setWindowModality(Qt.WindowModal)
        progress.setWindowTitle("Gathering Data")
        progress.setLabelText("Running Hardware Information...")
        progress.show()
        i = 0
        progress.setValue(i)
        os.makedirs(os.path.dirname(self.hw_file), exist_ok=True)
        with open(self.hw_file, "w") as f:
        
            # System information
            c = wmi.WMI()
            system = c.Win32_ComputerSystem()[0]
            operating_system  = c.Win32_OperatingSystem()[0]
            bios = c.Win32_BIOS()[0]
            processor = c.Win32_Processor()[0]
            disks = c.Win32_LogicalDisk()
            memory = c.Win32_PhysicalMemory()
            data = {
                "system": {
                    "manufacturer": system.Manufacturer,
                    "model": system.Model,
                    "serial_number": system.Name,
                    "bios_version": bios.Version,
                    "processor": processor.Name,
                    # "memory": str(sum([m.Capacity for m in memory]) // (1024 ** 3)), # <-- Add closing parenthesis here
                    "operating_system": operating_system.Caption,
                    "os_architecture": operating_system.OSArchitecture,
                    "os_version": operating_system.Version,
                },
                "disks": [
                    {
                        "drive_letter": disk.Caption,
                        "file_system": disk.FileSystem,
                        # "size": disk.Size // (1024 ** 3), # convert to GB
                        # "free_space": disk.FreeSpace // (1024 ** 3), # convert to GB
                    }
                    for disk in disks
                ],
            }
            i += 1
            progress.setLabelText("Getting hardware information...")
            self.audit_me("Getting user accounts...")
            aduseraccounts = c.Win32_UserAccount()
            data["User Accounts"] = [
                {
                    "name": user.Name,
                    "full_name": user.FullName,
                    "disabled": user.Disabled,
                    "lockout": user.Lockout,
                    "password_changeable": user.PasswordChangeable,
                    "password_expires": user.PasswordExpires,
                    "password_required": user.PasswordRequired
                }
                for user in aduseraccounts
            ]
            i += 1
            progress.setValue(i)
            progress.setLabelText("Getting network information...") 
            self.audit_me("Getting network information...")
            network_adapters = c.Win32_NetworkAdapterConfiguration(IPEnabled=True)
            data["network"] = [
                {
                    "name": adapter.Caption,
                    "mac_address": adapter.MACAddress,
                    "ip_address": adapter.IPAddress[0] if adapter.IPAddress else None,
                    "subnet_mask": adapter.IPSubnet[0] if adapter.IPSubnet else None,
                    "default_gateway": adapter.DefaultIPGateway[0] if adapter.DefaultIPGateway else None,
                    "dns_servers": adapter.DNSServerSearchOrder if adapter.DNSServerSearchOrder else None,
                }
                for adapter in network_adapters
            ]
            i += 1
            progress.setValue(i)
            progress.setLabelText("Getting running processes...") 
            self.audit_me("Getting running processes...")
            processes = c.Win32_Process()
            data["processes"] = [
                {
                    "name": process.Name,
                    "process_id": process.ProcessId,
                    "thread_count": process.ThreadCount,
                    "priority": process.Priority,
                    # "working_set_size": process.WorkingSetSize // (1024 ** 2), # convert to MB
                }
                for process in processes
            ]
            i += 1
            progress.setValue(i)
            progress.setLabelText("Getting Services...") 
            self.audit_me("Getting Services...")
            services = c.Win32_Service()
            data["Services"] = [
                {
                    "name": service.Name,
                    "display_name": service.DisplayName,
                    "state": service.State,
                    "start_mode": service.StartMode,
                    "process_id": service.ProcessId,
                }
                for service in services
            ]
            i += 1
            progress.setValue(i)
            progress.setLabelText("Getting Scheduled Jobs...")            
            self.audit_me("Getting Scheduled Jobs...")
            jobs = c.Win32_ScheduledJob()
            data["scheduled jobs"] = [
                {
                    "name": job.Name,
                    "command": job.Command,
                    "run_as_user": job.RunAsUser,
                    "status": job.Status,
                    "next_run_time": job.NextRunTime,
                    "last_run_time": job.LastRunTime,
                    "priority": job.Priority,
                    "job_id": job.JobId,
                    "owner": job.Owner,
                    "parameters": job.Parameters
                }
                for job in jobs
            ]
            i += 1
            progress.setValue(i)
            progress.setLabelText("Done...") 
            self.audit_me("Finished stage 1...")
            json.dump(data, f, indent=4)
        progress.close()
    
    def priv_copy(self, source, dest, sudo_password):
        print("priv_copy")
        if not os.path.exists(source):
            print(f"Error: Source file/directory '{source}' does not exist")
            return
        if not os.access(source, os.R_OK):
            print(f"Error: You do not have permission to access source file/directory '{source}'")
            return
        if not os.path.exists(dest):
            print(f"Error: Destination directory '{dest}' does not exist")
            return
        if not os.access(dest, os.W_OK):
            print(f"Error: You do not have permission to write to destination directory '{dest}'")
            return

        print("Copying...")
        result = shutil.copytree(source, dest)
        print(f"Copy complete. Result: {result}")
        return result

    def open_folder(folder_path):
        os.startfile(folder_path.replace("/", "\\"))
        system = platform.system()       

    def sudo_chown(self, dest, sudo_password):
        username = os.getlogin()
        print("sudo_chown")
        # command = f"echo '{sudo_password}' | sudo -S chown -R {username}:{username} {dest}"
        # process = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stdin=subprocess.PIPE, stderr=subprocess.PIPE)
        # stdout, stderr = process.communicate()
        # command = f"ls -la -R {dest}"
        # process = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stdin=subprocess.PIPE, stderr=subprocess.PIPE)
        # stdout, stderr = process.communicate()
        # if stdout:
        #     output = stdout.decode("utf-8")
        # else:
        #     output = stderr.decode("utf-8")
        # return output

    def pick_folder(self, sudo_password):
        dialog = QFileDialog()
        dialog.setDirectory("/")
        dialog.setFileMode(QFileDialog.DirectoryOnly)
        if dialog.exec_():
            drive = str(dialog.selectedFiles()[0])
        else:
            self.update_case_notes("Cancelled Data Capture")        
        # if sudo_password == "":
        #     sudo_password, ok_pressed = QInputDialog.getText(None, "Sudo Password", "Please enter your sudo password:", QLineEdit.Password)
        #     if not ok_pressed or not sudo_password:
        #         self.update_case_notes("No password entered.  Canceling")
        #         return None    
        # return drive
                
    def audit_me(self, message):
        with open(self.audit_file, "a+") as f:
            f.write(message + "\n")
        return message       
             
    def run_write_blocker(self, case, computer_name):
        self.audit_me("Running Write Blocker")
        print("wb")
        prog_path = os.path.join(os.getcwd(), "csi_write_blocker.exe")
        process = subprocess.Popen([prog_path, "--case", self.case], stderr=subprocess.PIPE)
        result = process.wait()
        if result == 0:
            self.audit_me("Write blocker started successfully.")
        else:
            error_output = process.stderr.read().decode('utf-8').strip()
            self.audit_me(f"Failed to start write blocker. Error: {error_output}")

    def run_gallery_view(self, case, computer_name):
        self.audit_me("Running Forensic Gallery Viewer")
        prog_path = os.path.join(os.getcwd(), "csi_forensic_gallery_view.exe")
        process = subprocess.Popen([prog_path, "--case", self.case, "--computer_name", self.computer_name])
        result = process.wait()
        if result == 0:
            self.audit_me("Write blocker started successfully.")
        else:
            error_output = process.stderr.read().decode('utf-8').strip()
            self.audit_me(f"Failed to start write blocker. Error: {error_output}")                       

