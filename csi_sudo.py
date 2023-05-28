import sys
import subprocess
from PyQt5.QtWidgets import QApplication, QWidget, QLabel, QLineEdit, QPushButton, QVBoxLayout


class PasswordVerifier(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Password Verifier")

        # Create GUI elements
        self.password_label = QLabel("Enter sudo password:")
        self.password_input = QLineEdit()
        self.login_button = QPushButton("Log In")
        self.result_label = QLabel()

        # Set up layout
        layout = QVBoxLayout()
        layout.addWidget(self.password_label)
        layout.addWidget(self.password_input)
        layout.addWidget(self.login_button)
        layout.addWidget(self.result_label)
        self.setLayout(layout)

        # Connect button click event to function
        self.login_button.clicked.connect(self.verify_password)

    def verify_password(self):
        password = self.password_input.text()

        # Check if password is correct and user has root access
        if self.check_password(password):
            self.result_label.setText("Login successful!")
            # Additional code for actions after successful login

        else:
            self.result_label.setText("Wrong password. Please try again.")

    def check_password(self, password):
        try:
            # Run the sudo command to verify the password and check the return code
            command = ['sudo', '-k', '-S', 'ls']
            proc = subprocess.run(command, input=password.encode(), capture_output=True, text=True)
            return proc.returncode == 0

        except subprocess.CalledProcessError:
            return False

        except Exception:
            return False


if __name__ == "__main__":
    app = QApplication(sys.argv)

    window = PasswordVerifier()
    window.show()

    sys.exit(app.exec_())

