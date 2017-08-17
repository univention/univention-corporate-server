def test_master_with_different_languages():
	pass
#language=${language}
#case $language in
#    de)
#    	vm_name=installer_test_master_multi-language_de
#        echo 10.200.13.20 > IP
#        script_name=00_master-de.py
#        ;;
#    en)
#        vm_name=installer_test_master_multi-language_en
#        echo 10.200.13.21 > IP
#        script_name=00_master-en.py
#        ;;
#    fr)
#    	vm_name=installer_test_master_multi-language_fr
#        echo 10.200.13.22 > IP
#        script_name=00_master-fr.py
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
#ssh-keygen -R $(cat IP)
#python installer_test/do_simple_vm_test.py $(cat IP)
#
