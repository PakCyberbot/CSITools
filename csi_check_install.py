import subprocess
import sys

def check_install_debian(package_name):
    try:
        subprocess.check_call(["dpkg", "-s", package_name], stdout=subprocess.DEVNULL)
    except subprocess.CalledProcessError:
        print(f"Installing {package_name} on Debian-based system...")
        subprocess.call(["sudo", "apt-get", "install", "-y", package_name])

def check_install_arch(package_name):
    try:
        subprocess.check_call(["pacman", "-Qi", package_name], stdout=subprocess.DEVNULL)
    except subprocess.CalledProcessError:
        print(f"Installing {package_name} on Arch-based system...")
        subprocess.call(["sudo", "pacman", "-S", "--noconfirm", package_name])

def check_install_redhat(package_name):
    try:
        subprocess.check_call(["rpm", "-q", package_name], stdout=subprocess.DEVNULL)
    except subprocess.CalledProcessError:
        print(f"Installing {package_name} on RedHat-based system...")
        subprocess.call(["sudo", "dnf", "install", "-y", package_name])

def install_package(package_name):
    try:
        with open("/etc/os-release") as f:
            os_info = f.read()

        success = False
        if "Debian" in os_info or "Ubuntu" in os_info:
            success = check_install_debian(package_name)
        elif "Arch" in os_info or "Manjaro" in os_info:
            success = check_install_arch(package_name)
        elif "Red Hat" in os_info or "Fedora" in os_info or "CentOS" in os_info:
            success = check_install_redhat(package_name)
        else:
            print("Unsupported Linux distribution.")
            return False

        return success
    except Exception as e:
        print(f"Error: {e}")
        return False

def main():
    package_name = "example_package"  # Replace with the desired package name

    try:
        with open("/etc/os-release") as f:
            os_info = f.read()

        if "Debian" in os_info or "Ubuntu" in os_info:
            check_install_debian(package_name)
        elif "Arch" in os_info or "Manjaro" in os_info:
            check_install_arch(package_name)
        elif "Red Hat" in os_info or "Fedora" in os_info or "CentOS" in os_info:
            check_install_redhat(package_name)
        else:
            print("Unsupported Linux distribution.")
            sys.exit(1)
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()

