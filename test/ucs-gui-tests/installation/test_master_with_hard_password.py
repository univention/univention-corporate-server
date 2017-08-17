def test_master_with_hard_password():
	pass
#rm -rf screen_dumps
#mv univention installer_test
#echo 10.200.13.30 > IP
#ssh-keygen -R $(cat IP)
#
#mkdir screen_dumps
#python installer_test/create-vm --name installer_test-master_hard_password_de --server $KVM_BUILD_SERVER --ucs-iso /mnt/omar/vmwares/kvm/iso/iso-tests/ucs_4.2-0-latest-amd64.iso --resultfile resultfile
#python installer_test/02_master_hard_password-de.py --ip $(cat IP) --dump-dir screen_dumps $(python installer_test/resultfile_to_vnc_connection resultfile)
#
# FIXME: Using a '2' instead of an '@' in the password, to work around a bug in vncdotool.
#python installer_test/do_simple_vm_test.py --password="2fooBar99Extr4L4rg3Size" $(cat IP)
#
