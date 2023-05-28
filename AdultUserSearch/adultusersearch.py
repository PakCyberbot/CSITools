import os
import requests
import webbrowser
from PyQt5.QtWidgets import QApplication, QInputDialog, QLineEdit, QMessageBox

app = QApplication([])

def test_user(sitename, sitetest, stringtest, userfound, filename):
    print(f"[+] {sitename}: ", end="")
    response = requests.get(sitetest)
    if ((userfound == '1' and response.status_code == 200) or
       (userfound == '0' and response.status_code == 404)):
        print("Found!")
        with open(filename, 'a') as f:
            f.write(sitetest + '\n')
    else:
        print("Not Found!")

def run_script():
    case_dir, ok = QInputDialog.getText(None, "Case Directory", "Enter the case directory:", QLineEdit.Normal, "")
    if not ok or case_dir == '':
        return

    username, ok = QInputDialog.getText(None, "Username", "Enter the username to search:", QLineEdit.Normal, "")
    if not ok or username == '':
        return

    os.makedirs(case_dir, exist_ok=True)
    filename = os.path.join(case_dir, f'Adult_Account_Search_{username}.txt')
    
    sites = [
        ("Cam SITE - Chaterbate", f"https://chaturbate.com/{username}", "Page Not Found", '0'),
        ("Cam SITE - LiveJasmin", f"https://www.livejasmin.com/en/chat-html5/{username}", "404", '0'),
        ("Cam SITE - Epornercams", f"https://epornercams.com/cam/{username}", "Sorry", '0'),
        ("Cam SITE - Cam4", f"https://www.cam4.com/{username}", "not exist", '0'),
        ("Cam SITE - SpankBang", f"https://spankbang.com/live/performer/{username}", "not exist", '0'),
        ("XXX SITE User - GotPorn", f"https://www.gotporn.com/users/{username}", "404", '0'),
        ("XXX SITE User - Motherless", f"https://motherless.com/m/{username}", "damn!", '0'),
        ("XXX SITE User - PornHub", f"https://www.pornhub.com/model/{username}", "Page Not Found", '0'),
        ("XXX SITE User - SpankBang", f"https://spankbang.com/hot/{username}", "not exist", '0'),
        ("XXX SITE User - xHamster", f"https://xhamster.com/users/{username}", "Personal", '1'),
        ("XXX SITE User - xVideos", f"https://www.xvideos.com/profiles/{username}", "404", '0'),
        ("XXX SITE User - YesPornPlease", f"https://yespornplease.com/user/{username}", "Error", '0'),
        ("XXX SITE User - Yuvutu", f"http://www.yuvutu.com/{username}", "personal", '1'),
        ("XXX SITE User - WatchMyGF", f"https://www.watchmygf.me/channel/{username}/", "not found", '0'),
    ]

    for sitename, sitetest, stringtest, userfound in sites:
        test_user(sitename, sitetest, stringtest, userfound, filename)

    msgBox = QMessageBox()
    msgBox.setText("Would you like to open the findings in a browser?")
    msgBox.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
    ret = msgBox.exec_()

    if ret == QMessageBox.Yes:
        with open(filename, 'r') as f:
            for link in f:
                webbrowser.open_new_tab(link.strip())
    else:
        app.quit()

run_script()

