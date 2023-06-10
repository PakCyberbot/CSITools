import functools
from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtWidgets import QInputDialog, QLineEdit, QMessageBox, QLabel, QVBoxLayout, QDialog, QPushButton, QHBoxLayout, QSpinBox, QCheckBox
from PyQt5.QtCore import Qt
import json, sys
import os, subprocess

# libs for encrypting APIKeys
import base64
from cryptography.fernet import Fernet, InvalidToken
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

# from sharedfunctions import encrypt, decrypt, genKey, csitools_dir
import qdarktheme

# Global var and function ###########
enc_key=''
title_icon="CSI_logo.ico"
csitools_dir='/opt/csitools/'
# You can add new tools_support and write their implementation in the Ui_MainWindow.save_api_data &  Ui_MainWindow.wipe_data 
tools_support=["OSINT-Search", "Recon-NG", "Spiderfoot", "theHarvester", "CSI UserSearch"]


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
#---------------------

def show_message_box(title, message, icon=QMessageBox.Information, buttons=QMessageBox.Ok):
    
    msg_box = QMessageBox()
    msg_box.setWindowTitle(title)
    msg_box.setWindowIcon(QtGui.QIcon(title_icon))
    msg_box.setText(message)
    msg_box.setIcon(icon)
    msg_box.setStandardButtons(buttons)
    result = msg_box.exec_()
    return result
    
###################################### 
# Setting up Table with API Data
class TableModel(QtCore.QAbstractTableModel):
    def __init__(self, data):
        super(TableModel, self).__init__()
        self._data = data
        self.header_labels = ["Name", "API Keys", "Tools Supported"]  # New header names

    def data(self, index, role):
        if role == Qt.DisplayRole:
            try:
                if type(self._data[index.row()][index.column()]) == list:
                    return ", ".join(self._data[index.row()][index.column()])
                else:
                    return self._data[index.row()][index.column()]
            except IndexError:
                return ''
        
    
    def setData(self, index, value, role):
        if role == QtCore.Qt.EditRole:
            row = index.row()
            column = index.column()
            
            # Preserve the existing data for other columns
            if column != 1:
                return False
            if not value:
                return False
            
            self._data[row][column] = value
            self.dataChanged.emit(index, index)  # Emit signal for data change
            return True
        
    def rowCount(self, index):
        return len(self._data)

    def columnCount(self, index):
        return len(self._data[0])
    
    def headerData(self, section, orientation, role):
        if role == QtCore.Qt.DisplayRole and orientation == QtCore.Qt.Horizontal:
            if section < len(self.header_labels):
                return self.header_labels[section]
        return super(TableModel, self).headerData(section, orientation, role)

    def flags(self, index):
        if index.column() == 1:  # Column 2
            return QtCore.Qt.ItemIsEditable | QtCore.Qt.ItemIsSelectable | QtCore.Qt.ItemIsEnabled
        return super(TableModel, self).flags(index)

# Dialog box for editing/removing API entry
class newAPIDialog(QDialog):
    def __init__(self, mainObj, opt="remove"):
        super().__init__()
        self.mainObj = mainObj
        self.setWindowIcon(QtGui.QIcon(title_icon))
        if opt == 'add':            
            self.setWindowTitle("Add New API")
            self.addAPILabel = QLabel("Enter API Name(e.g name_api): ")
            self.addAPIInput = QLineEdit()
            self.addAPIBtn = QPushButton("Add New Entry")
            self.addAPIBtn.clicked.connect(self.create_new_entry)
        
            layout = QHBoxLayout()
            layout.addWidget(self.addAPILabel)
            layout.addWidget(self.addAPIInput)
            layout.addWidget(self.addAPIBtn)
            
            tool_layout = QVBoxLayout()
            toolLabel = QLabel("SUPPORTED BY: ")
            tool_layout.addWidget(toolLabel)
        
            self.chkbx_list = [QCheckBox() for i in range(0,len(tools_support))]
            for i, tool in enumerate(tools_support):
                self.chkbx_list[i].setText(tool)
                tool_layout.addWidget(self.chkbx_list[i])
        
        elif opt == 'remove':
            self.setWindowTitle("Remove Current API")
            self.rmAPILabel = QLabel("Enter the Entry Number:")
            self.rmAPIInput = QSpinBox()
            self.rmAPIInput.setRange(0,9999)
            self.rmAPIBtn = QPushButton("REMOVE ENTRY")
            
            self.rmAPIBtn.clicked.connect(self.remove_entry)

        
            layout = QHBoxLayout()
            layout.addWidget(self.rmAPILabel)
            layout.addWidget(self.rmAPIInput)
            layout.addWidget(self.rmAPIBtn)        
        
        main_layout = QVBoxLayout()
        main_layout.addLayout(layout)
        if opt == 'add':            
            main_layout.addLayout(tool_layout)
        self.setLayout(main_layout)

    def create_new_entry(self):
        # getting list of supported tools
        tools_sup = []
        for chkbx in self.chkbx_list:
            if chkbx.isChecked():
                tools_sup.append(chkbx.text())

        self.mainObj.api_keys_list.append([self.addAPIInput.text(),'',tools_sup])
        self.mainObj.save_api_data(f"Added {self.addAPIInput.text()} API Successfully!, Restart the program to see Changes.")
        self.close()
    
    def remove_entry(self):
        try:
            result = show_message_box("Confirmation", f"Do you want to Remove \"{self.mainObj.api_keys_list[self.rmAPIInput.value()-1][0]}\" API Entry?", QMessageBox.Question, QMessageBox.Yes | QMessageBox.No)
            if result == QMessageBox.Yes:
                del self.mainObj.api_keys_list[self.rmAPIInput.value()-1]
                self.mainObj.save_api_data(f"Removed API Successfully!")
                self.close()
        except IndexError:
            show_message_box("Error",f"You have total {len(self.mainObj.api_keys_list)} entries", QMessageBox.Warning)

# MAIN Windows
class Ui_MainWindow(object):
    def setupUi(self, MainWindow):
        self.changed_values = []  # to store the changes into the file
        api_keys = {}

        MainWindow.setObjectName("MainWindow")
        MainWindow.setWindowIcon(QtGui.QIcon(title_icon))

        MainWindow.setGeometry(550,100,790, 900)    # approx center location
        MainWindow.setFixedSize(790, 900)
        
        
        #--------------- Setting up GUI elements ---------------
        self.centralwidget = QtWidgets.QWidget(MainWindow)
        self.centralwidget.setObjectName("centralwidget")
        self.Heading = QtWidgets.QLabel(self.centralwidget)
        self.Heading.setGeometry(QtCore.QRect(10, 10, 770, 30))
        font = QtGui.QFont()
        font.setFamily("Bahnschrift")
        font.setPointSize(14)
        self.Heading.setFont(font)
        self.Heading.setLayoutDirection(QtCore.Qt.LeftToRight)
        self.Heading.setAlignment(QtCore.Qt.AlignCenter)
        self.Heading.setObjectName("Heading")
        self.btns_frame = QtWidgets.QFrame(self.centralwidget)
        self.btns_frame.setGeometry(QtCore.QRect(20, 780, 750, 50))
        font = QtGui.QFont()
        font.setFamily("Arial Black")
        font.setPointSize(12)
        font.setBold(True)
        font.setWeight(75)
        # Buttons
        self.btns_frame.setFont(font)
        self.btns_frame.setFrameShape(QtWidgets.QFrame.StyledPanel)
        self.btns_frame.setFrameShadow(QtWidgets.QFrame.Raised)
        self.btns_frame.setObjectName("btns_frame")
        
        self.exitBtn = QtWidgets.QPushButton(self.btns_frame)
        self.exitBtn.setGeometry(QtCore.QRect(522, 0, 181, 51))
        self.exitBtn.setAutoDefault(False)
        self.exitBtn.setObjectName("exitBtn")
        self.exitBtn.clicked.connect(MainWindow.close)

        self.saveBtn = QtWidgets.QPushButton(self.btns_frame)
        self.saveBtn.setGeometry(QtCore.QRect(288, 0, 180, 51))
        self.saveBtn.setAutoDefault(False)
        self.saveBtn.setObjectName("saveBtn")
        self.saveBtn.clicked.connect(functools.partial(self.save_api_data,"Your API Keys saved successfully!"))

        self.wipeBtn = QtWidgets.QPushButton(self.btns_frame)
        self.wipeBtn.setGeometry(QtCore.QRect(54, 0, 180, 51))
        self.wipeBtn.setAutoDefault(False)
        self.wipeBtn.setObjectName("wipeBtn")
        self.wipeBtn.clicked.connect(self.wipe_data)
        font = QtGui.QFont()
        font.setFamily("Calibri")
        font.setPointSize(14)
        font.setBold(True)
        font.setWeight(75)


        # Table View setup
        self.APIData = QtWidgets.QTableView(self.centralwidget)
        self.APIData.setGeometry(QtCore.QRect(20, 50, 750, 700))
        self.APIData.setObjectName("APIData")
        
        decrypt(enc_key)
        with open(f"{csitools_dir}APIKeys.json") as api_file:
            api_keys = json.load(api_file)
        encrypt(enc_key)

        self.api_keys_list = [[key, value["key"],value["inTools"]] for key, value in api_keys.items()]

        self.model = TableModel(self.api_keys_list)
        self.APIData.setModel(self.model)
        self.APIData.setColumnWidth(0,150)
        self.APIData.setColumnWidth(1,300)
        self.APIData.setColumnWidth(2,200)
        self.APIData.horizontalHeader().setStretchLastSection(True)

        self.model.dataChanged.connect(self.on_data_changed)  # Connect dataChanged signal to slot

        MainWindow.setCentralWidget(self.centralwidget)

        #------------ MENU BAR ------------
        
        self.menubar = QtWidgets.QMenuBar(MainWindow)
        self.menubar.setGeometry(QtCore.QRect(0, 0, 480, 26))
        self.menubar.setObjectName("menubar")
        
        self.menuEdit_API_Data = QtWidgets.QMenu(self.menubar)
        self.menuEdit_API_Data.setObjectName("menuEdit_API_Data")
        self.menuThemes = QtWidgets.QMenu(self.menubar)
        self.menuThemes.setObjectName("menuThemes")

        MainWindow.setMenuBar(self.menubar)
        self.statusbar = QtWidgets.QStatusBar(MainWindow)
        self.statusbar.setObjectName("statusbar")
        MainWindow.setStatusBar(self.statusbar)
        self.actionAdd_New_Entry = QtWidgets.QAction(MainWindow)
        self.actionAdd_New_Entry.setObjectName("actionAdd_New_Entry")
        self.actionRemove_Entry = QtWidgets.QAction(MainWindow)
        self.actionRemove_Entry.setObjectName("actionRemove_Entry")
        self.menuEdit_API_Data.addAction(self.actionAdd_New_Entry)
        self.menuEdit_API_Data.addAction(self.actionRemove_Entry)

        self.actionDark_Theme = QtWidgets.QAction(MainWindow)
        self.actionDark_Theme.setObjectName("actionDark_Theme")
        self.actionLight_Theme = QtWidgets.QAction(MainWindow)
        self.actionLight_Theme.setObjectName("actionLight_Theme")
        self.menuThemes.addAction(self.actionDark_Theme)
        self.menuThemes.addAction(self.actionLight_Theme)

        self.menubar.addAction(self.menuEdit_API_Data.menuAction())
        self.menubar.addAction(self.menuThemes.menuAction())

        self.actionAdd_New_Entry.triggered.connect(self.add_APIentry)
        self.actionRemove_Entry.triggered.connect(self.rm_APIentry)

        self.actionLight_Theme.triggered.connect(functools.partial(self.change_theme,"light"))
        self.actionDark_Theme.triggered.connect(functools.partial(self.change_theme,"dark"))

        self.retranslateUi(MainWindow)
        QtCore.QMetaObject.connectSlotsByName(MainWindow)

    def retranslateUi(self, MainWindow):
        _translate = QtCore.QCoreApplication.translate
        MainWindow.setWindowTitle(_translate("MainWindow", "CSI Linux API Keys Management tool"))
        self.Heading.setText(_translate("MainWindow", "CSI Linux API Manager"))
        self.exitBtn.setText(_translate("MainWindow", "EXIT"))
        self.saveBtn.setText(_translate("MainWindow", "SAVE"))
        self.wipeBtn.setText(_translate("MainWindow", "WIPE DATA"))

        self.menuEdit_API_Data.setTitle(_translate("MainWindow", "Edit API Data"))
        self.actionAdd_New_Entry.setText(_translate("MainWindow", "Add New Entry"))
        self.actionAdd_New_Entry.setStatusTip(_translate("MainWindow", "Adds new entry in the API Data"))
        self.actionAdd_New_Entry.setShortcut(_translate("MainWindow", "Ctrl+A"))
        self.actionRemove_Entry.setText(_translate("MainWindow", "Remove Entry"))
        self.actionRemove_Entry.setStatusTip(_translate("MainWindow", "Removes by entry number from table."))
        self.actionRemove_Entry.setShortcut(_translate("MainWindow", "Ctrl+R"))

        self.menuThemes.setTitle(_translate("MainWindow", "Themes"))
        self.actionDark_Theme.setText(_translate("MainWindow", "Dark Theme"))
        self.actionLight_Theme.setText(_translate("MainWindow", "Light Theme"))

    #----------- ACTIONS  -----------
    def on_data_changed(self, top_left, bottom_right):
        for row in range(top_left.row(), bottom_right.row() + 1):
            for column in range(top_left.column(), bottom_right.column() + 1):
                index = self.model.index(row, column)
                value = self.model.data(index, QtCore.Qt.DisplayRole)
                self.changed_values.append((row, column, value))

    def save_api_data(self, text):
        for i,j,keys in self.changed_values:
            self.api_keys_list[i][j] = keys

        update_api_keys = {item[0]: {"key":item[1],"inTools":item[2]} for item in self.api_keys_list}
        decrypt(enc_key)
        with open(f"{csitools_dir}APIKeys.json","w") as api_file:
            json.dump(update_api_keys,api_file)
        encrypt(enc_key)
        
        #-------- Adding API keys in supported tools ----------------
        try:
            for api in self.api_keys_list:
                # api[0]=name, api[1]=key, api[2]=inTools

                if 'Recon-NG' in api[2]:    
                    subprocess.run(["sqlite3", "/home/csi/.recon-ng/keys.db", f'UPDATE keys SET Value = "{api[1]}" WHERE name="{api[0]}";'])
                if 'hades' in api[0]:  
                    subprocess.run(["sed", "-i", "s/atiikey=''/atiikey='$key'/g", "/opt/csitools/ProjectHades"])
                if 'Spiderfoot' in api[2]:
                    #improve it more
                    search_term = api[0]    # e.g. shodan_api = [shodan,api]  to search into spiderfoot config
                    # Using regex for finding the api name dynamically.
                    subprocess.run(["sed", "-i", "-E", f"s/(^sfp.*{search_term[0]}.*{search_term[1]}.*=)(key value)?/\\1{api[1]}/", "/opt/csitools/SpiderFoot.cfg"])
        
        except Exception as e:
            print("Got error during adding API data to supported tools!")
            print(e)
                
        
        show_message_box("Success",text)

    def wipe_data(self):
        result = show_message_box("Confirmation", "Do you want to proceed?", QMessageBox.Question, QMessageBox.Yes | QMessageBox.No)
        if result == QMessageBox.Yes:
            empty_api_keys = {item[0]: {"key":'',"inTools":item[2]} for item in self.api_keys_list}
            decrypt(enc_key)
            with open(f"{csitools_dir}APIKeys.json","w") as api_file:
                json.dump(empty_api_keys,api_file)
            encrypt(enc_key)
            try:
                # Wiping data from supported tools using bash commands for better readability
                subprocess.run(["cp", "/opt/theHarvester/api-backup","/opt/theHarvester/api-keys.yaml"])
                subprocess.run(["cp", "/opt/OSINT-Search/osintSearch.config.back", "/opt/OSINT-Search/osintSearch.config.ini"])
                subprocess.run(["cp", "/opt/csitools/SpiderFoot.empty", "/opt/csitools/SpiderFoot.cfg"])
                for api in self.api_keys_list:  # api[0], first entry is name
                    if 'Recon-NG' in api[2]:
                        subprocess.run(["sqlite3", "/home/csi/.recon-ng/keys.db", f'UPDATE keys SET Value = "" WHERE name="{api[0]}";'])
            except Exception as e:
                print("Got error during wiping API data from supported tools!")
                print(e)

            show_message_box("Success","Data Removed From APIKeys, Recon-NG, theHarvester, OSINT-Search and SpiderFoot Successfully!",QMessageBox.Information)

            self.setupUi(MainWindow)
        
    
    def add_APIentry(self):
        dialog = newAPIDialog(self,"add")
        dialog.exec_()
        dialog.finished.connect(self.dialog_finished)
    
    def rm_APIentry(self):
        dialog = newAPIDialog(self,"remove")
        dialog.exec_()
        dialog.finished.connect(self.dialog_finished)

    def dialog_finished(self, result):
        print("reached here")
        self.setupUi(MainWindow)
    
    def change_theme(self, mode):
        if mode == 'dark':
            os.environ['CSI_DARK'] = 'enable'
            qdarktheme.setup_theme()
        else:
            os.environ['CSI_DARK'] = 'disable'
            qdarktheme.setup_theme("light")

if __name__ == "__main__":
    
    app = QtWidgets.QApplication(sys.argv)
    if os.environ.get("CSI_DARK") == 'enable':
        qdarktheme.setup_theme()
    else:
        qdarktheme.setup_theme("light")

    # Just to set the Icon on the password input
    MainWindow = QtWidgets.QMainWindow()
    MainWindow.setWindowIcon(QtGui.QIcon(title_icon))
    MainWindow.setGeometry(550,100,790, 900)    # approx center location

    # Creating encrypted APIKeys by setting up new password
    if os.path.isfile(f"{csitools_dir}APIKeys.json"):
        new_password, ok = QInputDialog.getText(MainWindow, "Set New Password", "Enter a New Password:", QLineEdit.Password)
        if ok:
            confirm_password, ok = QInputDialog.getText(MainWindow, "Set New Password", "ReEnter the Password:", QLineEdit.Password)
            if ok:
                if new_password != '' and new_password == confirm_password :
                    encrypt(genKey(new_password))
                    show_message_box("Success","Password Set Successfully!",QMessageBox.Information)
                    enc_key=genKey(new_password)
                else:
                    msg_box = QMessageBox()
                    show_message_box("Error","Password Confirmation Failed!",QMessageBox.Warning)
                    exit()
            else:
                exit()
        else:
            exit()
    # Decrypting the APIKeys encrypted file, if it is present
    else:
        decrypt_password, ok = QInputDialog.getText(MainWindow, "Password to Decrypt", "Enter Password to decrypt the API Keys File:", QLineEdit.Password)
        if ok:
            if decrypt(genKey(decrypt_password)):
                # No need to show success message if password is correct just open directly
                # show_message_box("Success","Decrypted APIKeys file Successfully!",QMessageBox.Information)
                # Encrypt the file immediately after using the decrypted content to avoid any loopholes.
                encrypt(genKey(decrypt_password))
                enc_key=genKey(decrypt_password)
            else:
                show_message_box("Error","Failed to Decrypt With this Password!",QMessageBox.Warning)
                exit()
            
    # Again declaring to set the location to center
    MainWindow = QtWidgets.QMainWindow()

    ui = Ui_MainWindow()
    ui.setupUi(MainWindow)
    MainWindow.show()

    sys.exit(app.exec_())
