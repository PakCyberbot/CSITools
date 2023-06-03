import sys
import os
import shutil
from PyQt5.QtWidgets import QApplication, QWizard, QFileDialog
from PyQt5 import QtCore, QtGui, QtWidgets
import json
import sharedfunctions

class Ui_QWizard(object):
    def __init__(self):
        self.font = QtGui.QFont()
        self.font.setPointSize(8)

    def setupUi(self, Wizard):
        Wizard.setObjectName("Wizard")
        Wizard.resize(684, 200)
        icon = QtGui.QIcon()
        icon.addPixmap(QtGui.QPixmap("Images/CSI-Icon.png"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        Wizard.setWindowIcon(icon)

        self.wizardPage1 = QtWidgets.QWizardPage()
        self.wizardPage1.setObjectName("wizardPage1")
        self.gridLayout = QtWidgets.QGridLayout(self.wizardPage1)
        self.gridLayout.setObjectName("gridLayout")

        self.create_label(self.gridLayout, "Case Name", 0, 0)
        self.lineEdit = self.create_line_edit(self.gridLayout, 0, 1, 1, 3)

        self.create_label(self.gridLayout, "Investigator Name", 1, 0)
        self.lineEdit_2 = self.create_line_edit(self.gridLayout, 1, 1, 1, 3)

        self.calendarWidget = QtWidgets.QCalendarWidget(self.wizardPage1)
        self.calendarWidget.setFont(self.font)  # Set the desired font and point size
        self.calendarWidget.setObjectName("calendarWidget")
        self.gridLayout.addWidget(self.calendarWidget, 0, 4, 5, 1)

        self.create_label(self.gridLayout, "Case Type", 2, 0)
        self.lineEdit_3 = self.create_line_edit(self.gridLayout, 2, 1, 1, 3)

        self.create_label(self.gridLayout, "Case Priority", 3, 0)
        self.priorityme = self.create_combobox(self.gridLayout, 3, 1, 1, 3, ["Informational", "Low", "Medium", "High", "Critical"])

        self.create_label(self.gridLayout, "Case Classification", 4, 0)
        self.classme = self.create_combobox(self.gridLayout, 4, 1, 1, 3, ["Sensitive But Unclassified // SBU", "Confidential // C", "For Official Use Only // FOUO", "Secret // S", "Top Secret // TS"])

        self.line = QtWidgets.QFrame(self.wizardPage1)

        Wizard.addPage(self.wizardPage1)

        self.retranslateUi(Wizard)
        self.setup_connections(Wizard)
        QtCore.QMetaObject.connectSlotsByName(Wizard)
        Wizard.setTabOrder(self.lineEdit, self.lineEdit_2)
        Wizard.setTabOrder(self.lineEdit_2, self.lineEdit_3)
        Wizard.setTabOrder(self.lineEdit_3, self.priorityme)
        Wizard.setTabOrder(self.priorityme, self.classme)
        Wizard.setTabOrder(self.classme, self.calendarWidget)

    def create_label(self, layout, text, row, column):
        label = QtWidgets.QLabel(self.wizardPage1)
        label.setTextFormat(QtCore.Qt.PlainText)
        label.setObjectName(f"label_{row}_{column}")
        label.setText(text)
        layout.addWidget(label, row, column, 1, 1)
        return label

    def create_line_edit(self, layout, row, column, rowspan, colspan):
        line_edit = QtWidgets.QLineEdit(self.wizardPage1)
        line_edit.setObjectName(f"lineEdit_{row}_{column}")
        layout.addWidget(line_edit, row, column, rowspan, colspan)
        return line_edit

    def create_combobox(self, layout, row, column, rowspan, colspan, items):
        combobox = QtWidgets.QComboBox(self.wizardPage1)
        combobox.setObjectName(f"combobox_{row}_{column}")
        combobox.addItems(items)
        layout.addWidget(combobox, row, column, rowspan, colspan)
        return combobox

    def retranslateUi(self, Wizard):
        _translate = QtCore.QCoreApplication.translate
        Wizard.setWindowTitle(_translate("Wizard", "Starting a Case"))

    def save_data(self):

        case_name = self.lineEdit.text()
    
        cdata = {
            "case_name": case_name,
            "investigator_name": self.lineEdit_2.text(),
            "case_type": self.lineEdit_3.text(),
            "case_priority": self.priorityme.currentText(),
            "case_classification": self.classme.currentText(),
            "case_date": self.calendarWidget.selectedDate().toString("yyyy-MM-dd")
        }
        case_directory = create_case_folder(case_name, cases_folder)
        json_path = os.path.join(case_directory, "case_data.json")
        with open(json_path, 'w') as f:
            json.dump(cdata, f)
        print(case_directory)

    def setup_connections(self, wizard):
        wizard.button(QWizard.FinishButton).clicked.connect(self.save_data)

def create_case_folder(case, cases_folder):
    timestamp = sharedfunctions.get_current_timestamp()
    case_directory = os.path.join(cases_folder, case)
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

    # Create audit log and history files
    audit_log_path = os.path.join(case_directory, "audit.log")
    if not os.path.isfile(audit_log_path):
        with open(audit_log_path, 'w+') as f:
            f.write(sharedfunctions.get_current_timestamp() + " Audit log created.\n")

    history_file_path = os.path.join(case_directory, "history.txt")

    if not os.path.isfile(history_file_path):
        with open(history_file_path, 'w+') as f:
            f.write(sharedfunctions.get_current_timestamp() + " History file created.\n")

    notes_file_path = os.path.join(case_directory, "notes.txt")
    with open(notes_file_path, 'w+') as f:
        f.write("Case notes for Digital Forensics Investigation:\n" + sharedfunctions.get_current_timestamp() + "\n\n")
        pass  # create empty file

    with open(audit_log_path, 'a') as f:
        f.write(sharedfunctions.get_current_timestamp() + " Created case folder structure.\n")
        
    return case_directory

def load_data():
    global cases_folder
    if os.path.exists("agency_data.json"):
        with open("agency_data.json", "r") as file:
            data = json.load(file)
            cases_folder = data.get("cases_folder", "")
            logo_path = os.path.join("Images", "agencylogo.png")

class CustomQWizard(QWizard):
    def __init__(self, parent=None):
        super().__init__(parent)

class CustomGraphicsView(QtWidgets.QGraphicsView):
    def __init__(self, parent=None):
        super(CustomGraphicsView, self).__init__(parent)
        self.setScene(QtWidgets.QGraphicsScene(self))

    def mousePressEvent(self, event):
        if event.button() == QtCore.Qt.LeftButton:
            self.open_image()

    def open_image(self):
        options = QFileDialog.Options()
        options |= QFileDialog.ReadOnly
        file_name, _ = QFileDialog.getOpenFileName(self, "Open Image", "", "Images (*.png *.xpm *.jpg *.bmp);;All Files (*)", options=options)

        if file_name:
            dest_path = os.path.join("Images", "agencylogo.png")
            shutil.copyfile(file_name, dest_path)
            # Display the copied and scaled image in the QGraphicsView
            pixmap = QtGui.QPixmap(dest_path)
            scaled_pixmap = pixmap.scaled(self.size(), QtCore.Qt.KeepAspectRatio, QtCore.Qt.SmoothTransformation)
            self.scene().clear()
            self.scene().addPixmap(scaled_pixmap)
            self.setScene(self.scene())

app = QApplication(sys.argv)
QWizard = CustomQWizard()
ui = Ui_QWizard()
ui.setupUi(QWizard)
load_data()
QWizard.show()
sys.exit(app.exec_())

