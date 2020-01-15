from debian.deb822 import Deb822
import time

installed_pkgs = {}

def update_installed_packages():
    with open('/var/lib/dpkg/status', 'r') as dpkg_status:
        for deb_obj in Deb822.iter_paragraphs(dpkg_status, ["Package", "Status"], use_apt_pkg=True):
            try:
                if deb_obj["Status"] != "install ok installed":
                    installed_pkgs.update({deb_obj["Package"] : deb_obj["Status"]})
            except KeyError:
                continue

if __name__ == "__main__":
    while(True):
        update_installed_packages()
        print "\n" + str(time.time())
        print installed_pkgs
        time.sleep(3)

