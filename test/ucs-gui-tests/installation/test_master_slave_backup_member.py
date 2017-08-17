def master_slave_backup_member():
	pass
#rm -rf screen_dumps
#mv univention installer_test
#echo 10.200.13.60 > IP_MASTER
#echo 10.200.13.61 > IP_SLAVE
#echo 10.200.13.62 > IP_BACKUP
#echo 10.200.13.63 > IP_MEMBER
#ssh-keygen -R $(cat IP_MASTER)
#ssh-keygen -R $(cat IP_SLAVE)
#ssh-keygen -R $(cat IP_BACKUP)
#ssh-keygen -R $(cat IP_MEMBER)
#
#mkdir -p screen_dumps/master
#python installer_test/create-vm --name installer_test-large_master_de --server $KVM_BUILD_SERVER --ucs-iso /mnt/omar/vmwares/kvm/iso/iso-tests/ucs_4.2-0-latest-amd64.iso --resultfile resultfile_master
#python installer_test/00_master-de.py --ip $(cat IP_MASTER) --dump-dir screen_dumps/master $(python installer_test/resultfile_to_vnc_connection resultfile_master)
#
#mkdir -p screen_dumps/slave
#python installer_test/create-vm --name installer_test-large_slave_de --server $KVM_BUILD_SERVER --ucs-iso /mnt/omar/vmwares/kvm/iso/iso-tests/ucs_4.2-0-latest-amd64.iso --resultfile resultfile_slave
#python installer_test/10_slave-de.py --ip $(cat IP_SLAVE) --dns-server $(cat IP_MASTER) --dump-dir screen_dumps/slave $(python installer_test/resultfile_to_vnc_connection resultfile_slave)
#
#mkdir -p screen_dumps/backup
#python installer_test/create-vm --name installer_test-large_backup_de --server $KVM_BUILD_SERVER --ucs-iso /mnt/omar/vmwares/kvm/iso/iso-tests/ucs_4.2-0-latest-amd64.iso --resultfile resultfile_backup
#python installer_test/20_backup-de.py --ip $(cat IP_BACKUP) --dns-server $(cat IP_MASTER) --dump-dir screen_dumps/backup $(python installer_test/resultfile_to_vnc_connection resultfile_backup)
#
#mkdir -p screen_dumps/member
#python installer_test/create-vm --name installer_test-large_member_de --server $KVM_BUILD_SERVER --ucs-iso /mnt/omar/vmwares/kvm/iso/iso-tests/ucs_4.2-0-latest-amd64.iso --resultfile resultfile_member
#python installer_test/30_member-de.py --ip $(cat IP_MEMBER) --dns-server $(cat IP_MASTER) --dump-dir screen_dumps/member $(python installer_test/resultfile_to_vnc_connection resultfile_member)
#
#python installer_test/do_simple_vm_test.py $(cat IP_MASTER)
#python installer_test/do_simple_vm_test.py --reuse-license $(cat IP_SLAVE)
#python installer_test/do_simple_vm_test.py --reuse-license $(cat IP_BACKUP)
#python installer_test/do_simple_vm_test.py --reuse-license $(cat IP_MEMBER)
#
