import sys, json
import os
import shutil
from PyQt5.QtWidgets import QApplication, QWizard, QFileDialog
from PyQt5 import QtCore, QtGui, QtWidgets
from CSIConfig import *

class Ui_QWizard(object):
    def setupUi(self, Wizard):
        Wizard.setObjectName("Wizard")
        Wizard.resize(684, 400)
        icon = QtGui.QIcon()
        icon.addPixmap(QtGui.QPixmap("Images/CSI-Icon.png"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        Wizard.setWindowIcon(icon)
        font = QtGui.QFont()
        font.setPointSize(8)
        self.wizardPage1 = QtWidgets.QWizardPage()
        self.wizardPage1.setObjectName("wizardPage1")
        self.gridLayout = QtWidgets.QGridLayout(self.wizardPage1)
        self.gridLayout.setObjectName("gridLayout")
        
        self.alogol = QtWidgets.QLabel(self.wizardPage1)
        self.alogol.setTextFormat(QtCore.Qt.PlainText)
        self.alogol.setObjectName("alogol")
        self.gridLayout.addWidget(self.alogol, 6, 4, 1, 1)
        self.alogo = CustomGraphicsView(self.wizardPage1)
        self.alogo.setObjectName("alogo")
        self.gridLayout.addWidget(self.alogo, 7, 4, 8, 1)
        self.alogodl = QtWidgets.QLabel(self.wizardPage1)
        self.alogodl.setTextFormat(QtCore.Qt.PlainText)
        self.alogodl.setObjectName("alogodl")
        self.gridLayout.addWidget(self.alogodl, 15, 4, 1, 1)

        self.acasesl = QtWidgets.QLabel(self.wizardPage1)
        self.acasesl.setTextFormat(QtCore.Qt.PlainText)
        self.acasesl.setObjectName("acasesl")
        self.gridLayout.addWidget(self.acasesl, 6, 0, 1, 1)
        self.acases = QtWidgets.QLineEdit(self.wizardPage1)
        self.acases.setObjectName("acases")
        self.gridLayout.addWidget(self.acases, 6, 1, 1, 3)

        self.aagencyl = QtWidgets.QLabel(self.wizardPage1)
        self.aagencyl.setTextFormat(QtCore.Qt.PlainText)
        self.aagencyl.setObjectName("aagencyl")
        self.gridLayout.addWidget(self.aagencyl, 7, 0, 1, 1) 
        self.aagency = QtWidgets.QLineEdit(self.wizardPage1)
        self.aagency.setObjectName("aagency")
        self.gridLayout.addWidget(self.aagency, 7, 1, 1, 3)
        
        self.aunitl = QtWidgets.QLabel(self.wizardPage1)
        self.aunitl.setTextFormat(QtCore.Qt.PlainText)
        self.aunitl.setObjectName("aunitl")
        self.gridLayout.addWidget(self.aunitl, 8, 0, 1, 1)
        self.aunit = QtWidgets.QLineEdit(self.wizardPage1)
        self.aunit.setObjectName("aunit")
        self.gridLayout.addWidget(self.aunit, 8, 1, 1, 3)    

        self.aaddressl = QtWidgets.QLabel(self.wizardPage1)
        self.aaddressl.setTextFormat(QtCore.Qt.PlainText)
        self.aaddressl.setObjectName("aaddressl")
        self.gridLayout.addWidget(self.aaddressl, 9, 0, 1, 1)
        self.aaddress = QtWidgets.QLineEdit(self.wizardPage1)
        self.aaddress.setObjectName("aaddress")
        self.gridLayout.addWidget(self.aaddress, 9, 1, 1, 3)
        
        self.acityl = QtWidgets.QLabel(self.wizardPage1)
        self.acityl.setTextFormat(QtCore.Qt.PlainText)
        self.acityl.setObjectName("acityl")
        self.gridLayout.addWidget(self.acityl, 10, 0, 1, 1)
        self.acity = QtWidgets.QLineEdit(self.wizardPage1)
        self.acity.setObjectName("acity")
        self.gridLayout.addWidget(self.acity, 10, 1, 1, 3)
        
        self.astatel = QtWidgets.QLabel(self.wizardPage1)
        self.astatel.setTextFormat(QtCore.Qt.PlainText)
        self.astatel.setObjectName("astatel")
        self.gridLayout.addWidget(self.astatel, 11, 0, 1, 1)
        self.astate = QtWidgets.QLineEdit(self.wizardPage1)
        self.astate.setObjectName("astate")
        self.gridLayout.addWidget(self.astate, 11, 1, 1, 1)
        
        self.azipl = QtWidgets.QLabel(self.wizardPage1)
        self.azipl.setTextFormat(QtCore.Qt.PlainText)
        self.azipl.setObjectName("azipl")
        self.gridLayout.addWidget(self.azipl, 11, 2, 1, 1)
        self.azip = QtWidgets.QLineEdit(self.wizardPage1)
        self.azip.setObjectName("azip")
        self.gridLayout.addWidget(self.azip, 11, 3, 1, 1)
        
        self.acountryl = QtWidgets.QLabel(self.wizardPage1)
        self.acountryl.setTextFormat(QtCore.Qt.PlainText)
        self.acountryl.setObjectName("acountryl")
        self.gridLayout.addWidget(self.acountryl, 12, 0, 1, 1)
        self.acountry = QtWidgets.QLineEdit(self.wizardPage1)
        self.acountry.setObjectName("acountry")
        self.gridLayout.addWidget(self.acountry, 12, 1, 1, 3)
        
        self.aphonel = QtWidgets.QLabel(self.wizardPage1)
        self.aphonel.setTextFormat(QtCore.Qt.PlainText)
        self.aphonel.setObjectName("aphonel")
        self.gridLayout.addWidget(self.aphonel, 13, 0, 1, 1)
        self.aphone = QtWidgets.QLineEdit(self.wizardPage1)
        self.aphone.setObjectName("aphone")
        self.gridLayout.addWidget(self.aphone, 13, 1, 1, 3)
        
        self.aemaill = QtWidgets.QLabel(self.wizardPage1)
        self.aemaill.setTextFormat(QtCore.Qt.PlainText)
        self.aemaill.setObjectName("aemaill")
        self.gridLayout.addWidget(self.aemaill, 14, 0, 1, 1)
        self.aemail = QtWidgets.QLineEdit(self.wizardPage1)
        self.aemail.setObjectName("aemail")
        self.gridLayout.addWidget(self.aemail, 14, 1, 1, 3)
        
        self.awebl = QtWidgets.QLabel(self.wizardPage1)
        self.awebl.setTextFormat(QtCore.Qt.PlainText)
        self.awebl.setObjectName("awebl")
        self.gridLayout.addWidget(self.awebl, 15, 0, 1, 1)
        self.awebsite = QtWidgets.QLineEdit(self.wizardPage1)
        self.awebsite.setObjectName("awebsite")
        self.gridLayout.addWidget(self.awebsite, 15, 1, 1, 3)
        Wizard.addPage(self.wizardPage1)

        self.retranslateUi(Wizard)
        QtCore.QMetaObject.connectSlotsByName(Wizard)
        Wizard.setTabOrder(self.acases, self.aagency)
        Wizard.setTabOrder(self.aagency, self.aunit)
        Wizard.setTabOrder(self.aunit, self.aaddress)
        Wizard.setTabOrder(self.aaddress, self.acity)
        Wizard.setTabOrder(self.acity, self.astate)
        Wizard.setTabOrder(self.astate, self.azip)
        Wizard.setTabOrder(self.azip, self.acountry)
        Wizard.setTabOrder(self.acountry, self.aphone)
        Wizard.setTabOrder(self.aphone, self.aemail)
        Wizard.setTabOrder(self.aemail, self.awebsite)
        Wizard.setTabOrder(self.awebsite, self.alogo)
        Wizard.finished.connect(self.save_data)

    def retranslateUi(self, Wizard):
        _translate = QtCore.QCoreApplication.translate
        Wizard.setWindowTitle(_translate("Wizard", "Fill in your organization's information"))
        self.acasesl.setText(_translate("Wizard", "Cases Folder"))
        self.aagencyl.setText(_translate("Wizard", "Agency Name"))
        self.alogol.setText(_translate("Wizard", "Agency Logo"))
        self.alogodl.setText(_translate("Wizard", "Drag-n-Drop your logo into the box"))
        self.aunitl.setText(_translate("Wizard", "Unit Name"))
        self.aaddressl.setText(_translate("Wizard", "Address"))
        self.acityl.setText(_translate("Wizard", "City"))
        self.astatel.setText(_translate("Wizard", "State"))
        self.azipl.setText(_translate("Wizard", "Zip"))
        self.acountryl.setText(_translate("Wizard", "Country"))
        self.aphonel.setText(_translate("Wizard", "Phone Number"))
        self.aemaill.setText(_translate("Wizard", "Email"))
        self.awebl.setText(_translate("Wizard", "Website"))
       
    def save_data(self):
        adata = {
            "cases_folder": self.acases.text(),
            "agency_name": self.aagency.text(),
            "unit_name": self.aunit.text(),
            "address": self.aaddress.text(),
            "city": self.acity.text(),
            "state": self.astate.text(),
            "zip": self.azip.text(),
            "country": self.acountry.text(),
            "phone_number": self.aphone.text(),
            "email": self.aemail.text(),
            "website": self.awebsite.text()
        }
        with open('agency_data.json', 'w') as f:
            json.dump(adata, f)

def load_data():
    if os.path.exists("agency_data.json"):
        with open("agency_data.json", "r") as file:
            data = json.load(file)
            ui.aagency.setText(data.get("agency_name", ""))
            ui.aunit.setText(data.get("unit_name", ""))
            ui.aaddress.setText(data.get("address", ""))
            ui.acity.setText(data.get("city", ""))
            ui.astate.setText(data.get("state", ""))
            ui.azip.setText(data.get("zip", ""))
            ui.acountry.setText(data.get("country", ""))
            ui.aphone.setText(data.get("phone_number", ""))
            ui.aemail.setText(data.get("email", ""))
            ui.awebsite.setText(data.get("website", ""))
            ui.acases.setText(data.get("cases_folder", ""))
            logo_path = os.path.join("Images", "agencylogo.png")
            if os.path.exists(logo_path):
                pixmap = QtGui.QPixmap(logo_path)
                scaled_pixmap = pixmap.scaled(ui.alogo.size(), QtCore.Qt.KeepAspectRatio, QtCore.Qt.SmoothTransformation)
                ui.alogo.scene().clear()
                ui.alogo.scene().addPixmap(scaled_pixmap)
                ui.alogo.setScene(ui.alogo.scene())
       
class CustomQWizard(QWizard):
    def __init__(self, parent=None):
        super().__init__(parent)

    def closeEvent(self, event):
        case_name = ui.lineEdit.text()
        print(case_name)
        super().closeEvent(event)

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

