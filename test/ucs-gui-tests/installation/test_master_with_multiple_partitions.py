def test_master_with_multiple_partitions():
	pass
#rm -rf screen_dumps
#mv univention installer_test
#echo 10.200.13.50 > IP
#ssh-keygen -R $(cat IP)
#
#mkdir screen_dumps
#python installer_test/create-vm --name installer_test-master_multi-partition_de --server $KVM_BUILD_SERVER --ucs-iso /mnt/omar/vmwares/kvm/iso/iso-tests/ucs_4.2-0-latest-amd64.iso --resultfile resultfile
#python installer_test/01_master_multi-partition-de.py --ip $(cat IP) --dump-dir screen_dumps $(python installer_test/resultfile_to_vnc_connection resultfile)
#
#python installer_test/do_simple_vm_test.py $(cat IP)
#
