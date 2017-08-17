def test_manual_screenshots():
	pass
#language=${language}
#case $language in
#    de)
#    	vm_name=installer_test_manual-screenshots_de
#        echo 10.200.13.80 > IP
#        script_name=90_manual_screenshots-de.py
#        ;;
#    en)
#        vm_name=installer_test_manual-screenshots_en
#        echo 10.200.13.81 > IP
#        script_name=90_manual_screenshots-en.py
#        ;;
#    *)
#        echo "No valid language has been chosen."
#        exit 1
#        ;;
#esac
#
#python installer_test/create-vm --name $vm_name --server $KVM_BUILD_SERVER --ucs-iso /mnt/omar/vmwares/kvm/iso/iso-tests/ucs_4.2-0-latest-amd64.iso --resultfile resultfile
#python installer_test/$script_name --ip $(cat IP) --dump-dir screen_dumps $(python installer_test/resultfile_to_vnc_connection resultfile)
#
#bash installer_test/move_and_add_shadows_to_screenshots.sh
#tar --remove-files -zcf manual_installer_screenshots.tar.gz manual
#
