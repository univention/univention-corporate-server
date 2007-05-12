#!/bin/sh
#
# Univention Installer
#  main script for the installation process
#
# Copyright (C) 2004, 2005, 2006 Univention GmbH
#
# http://www.univention.de/
#
# All rights reserved.
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License version 2 as
# published by the Free Software Foundation.
#
# Binary versions of this file provided by Univention to you as
# well as other copyrighted, protected or trademarked materials like
# Logos, graphics, fonts, specific documentations and configurations,
# cryptographic keys etc. are subject to a license agreement between
# you and Univention.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA

# GLOBAL
ROOT_DEVICE=""
ROOT_DEVICE_FS=""
SWAP_DEVICE=""
BOOT_DEVICE=""
CDROM_DEVICES=""

if [ -z "$SOURCE_MOUNT_CMD" ]; then
	SOURCE_MOUNT_CMD="mount /cdrom"
fi
if [ -z "$USE_NO_LOG" ]; then
	LOG=" 2>&1 | tee -a /.log"
else
	LOG=""
fi

CHROOT_SCRIPT=/instmnt/.shell_script
#LOG=""
PIPE="yes yes '' |"

source /tmp/installation_profile
source /lib/univention-installer/disks.sh

# FIXME
# TODO: save mbr

echo -n "Searching root partition: " >>/instmnt/.log
echo -n "Searching root partition: "
# Mount / partitions
for i in $devices; do
	device=`echo /$i | sed -e 's/_/\//g'`
	 device_type=`echo ${!i} | awk '{print $1}'`
   device_format=`echo ${!i} | awk '{print $2}'`
	   device_fs=`echo ${!i} | awk '{print $3}'`
	device_start=`echo ${!i} | awk '{print $4}'`
	  device_end=`echo ${!i} | awk '{print $5}'`
	   device_mp=`echo ${!i} | awk '{print $6}'`
	if [ ! -z "$device_fs" ]; then
		if [ "$device_mp" = '/' ]; then
			ROOT_DEVICE=$device
			ROOT_DEVICE_FS=$device_fs
			mount -t $device_fs $device /instmnt
		fi
	fi
done

if [ -z "$ROOT_DEVICE" ]; then
	echo " not found"
	echo " not found" >>/instmnt/.log
	exit
fi
echo "$ROOT_DEVICE" >>/instmnt/.log
echo "$ROOT_DEVICE"
echo "" >>/instmnt.log
echo ""
echo -n "Mounting Partitions: " >>/instmnt/.log
echo -n "Mounting Partitions: "

# Mount /xxx partitions
for i in $devices; do
	device=`echo /$i | sed -e 's/_/\//g'`
	 device_type=`echo ${!i} | awk '{print $1}'`
   device_format=`echo ${!i} | awk '{print $2}'`
	   device_fs=`echo ${!i} | awk '{print $3}'`
	device_start=`echo ${!i} | awk '{print $4}'`
	  device_end=`echo ${!i} | awk '{print $5}'`
	   device_mp=`echo ${!i} | awk '{print $6}'`
	if [ -n "$device_fs" ]; then
		if [ "$device_fs" == "linux-swap" ]; then
			swapon $device
			SWAP_DEVICE=$device
			echo -n "$device " >>/instmnt/.log
			echo -n "$device "
		elif [ -z "$device_mp" ]; then
			continue;
		elif [ "$device_mp" = '/' ]; then
			continue;
		elif [ "$device_mp" = 'unknown' ]; then
			continue;
		elif [ "$device_fs" = 'unknown' ]; then
			continue;
		elif [ "$device_fs" = 'None' -o "$device_fs" = "none" ]; then
			continue;
		elif [ "$device_mp" = 'None' -o "$device_mp" = "none" ]; then
			continue;
		elif [ "$device_mp" = "/boot" ]; then
			BOOT_DEVICE=$device
			mkdir -p /instmnt/$device_mp
			mount -t $device_fs $device /instmnt/$device_mp
			echo -n "$device " >>/instmnt/.log
			echo -n "$device "
		else
			mkdir -p /instmnt/$device_mp
			mount -t $device_fs $device /instmnt/$device_mp
			echo -n "$device " >>/instmnt/.log
			echo -n "$device "
		fi
	fi
done
echo "" >>/instmnt/.log
echo ""

mkdir -p /instmnt/tmp

echo "Installing univention basesystem " >>/instmnt/.log
echo "Installing univention basesystem "
# Installing univention base system
if [ -z "$USE_NO_LOG" ]; then
	debootstrap --arch i386 --exclude="pcmcia-cs" univention /instmnt/ file:/mnt/packages 2>&1 | tee -a /instmnt/.log
else
	debootstrap --arch i386 --exclude="pcmcia-cs" univention /instmnt/ file:/mnt/packages
fi

echo "Creating configuration files" >>/instmnt/.log
echo "Creating configuration files"
touch /instmnt/etc/mtab

cp /mnt/conf/sources.list /instmnt/etc/apt/sources.list
chmod 644 /instmnt/etc/apt/sources.list

if [ "$ROOT_DEVICE_FS" = "xfs" ]; then
	ROOT_DEVICE_OPTIONS="defaults"
else
	ROOT_DEVICE_OPTIONS="errors=remount-ro"
fi
cat /mnt/conf/fstab.template  | sed -e "s|@%@ROOT_DEVICE@%@|$ROOT_DEVICE|"      |
								sed -e "s|@%@ROOT_FILESYSTEM@%@|$ROOT_DEVICE_FS|" |
								sed -e "s|@%@ROOT_DEVICE_OPTIONS@%@|$ROOT_DEVICE_OPTIONS|" >/instmnt/etc/fstab
for i in $devices; do
	device=`echo /$i | sed -e 's/_/\//g'`
	 device_type=`echo ${!i} | awk '{print $1}'`
	   device_fs=`echo ${!i} | awk '{print $3}'`
	device_start=`echo ${!i} | awk '{print $4}'`
	  device_end=`echo ${!i} | awk '{print $5}'`
	   device_mp=`echo ${!i} | awk '{print $6}'`
	if [ -n "$device_fs" ]; then
		if [ -z "$device_mp" ]; then
			if [ "$device_fs" = "linux-swap" ]; then
				echo "$device   none        swap    sw          0   0">>/instmnt/etc/fstab
			fi
			continue;
		elif [ -z "$device_fs" ]; then
			continue;
		elif [ "$device_mp" = '/' ]; then
			continue;
		elif [ "$device_fs" = "linux-swap" ]; then
			echo "$device   none        swap    sw          0   0">>/instmnt/etc/fstab
		elif [ "$device_mp" = "unknown" ]; then
			echo -n ""
		elif [ "$device_fs" = "unknown" ]; then
			echo -n ""
		elif [ "$device_fs" = 'None' -o "$device_fs" = "none" ]; then
			continue
		elif [ "$device_mp" = 'None' -o "$device_mp" = "none" ]; then
			continue;
		else
			echo "$device $device_mp $device_fs defaults 0 1" >>/instmnt/etc/fstab
		fi
	fi
done

for i in /proc/ide/ide*; do
	for j in $i/hd*; do
		a=`cat $j/media| grep -i cdrom`
		if ! test -z "$a"; then
			CDROM_DEVICES="$CDROM_DEVICES `echo $j | cut -d/ -f5`"
		fi
	done
done

echo "/dev/fd0  /floppy     vfat    user,noauto             0       0" >>/instmnt/etc/fstab
j=""
if [ ! -z "$CDROM_DEVICES" ]; then
	for i in $CDROM_DEVICES; do
		echo "/dev/$i  /cdrom$j     auto    user,noauto             0       0" >>/instmnt/etc/fstab
		mkdir /cdrom$j
		if [ -z $j ]; then j=1; else j=$(($j+1)); fi
	done
else
	echo "/dev/sr0  /cdrom     auto    user,noauto             0       0" >>/instmnt/etc/fstab
fi

cp /mnt/conf/debconf.conf /instmnt/etc/debconf.conf
cp /mnt/conf/mydb.dat /instmnt/var/cache/debconf/mydb.dat
chmod 644 /instmnt/var/cache/debconf/mydb.dat

cp /mnt/conf/sources.list /instmnt/etc/apt/sources.list
chmod 644 /instmnt/etc/apt/sources.list

LILO_BOOT_DEVICE=`get_device_disk $ROOT_DEVICE`

echo "#!/bin/sh "                                                                    >$CHROOT_SCRIPT
echo "mount -a"                                                     >>$CHROOT_SCRIPT
echo "$SOURCE_MOUNT_CMD"                                                     >>$CHROOT_SCRIPT
echo "shadowconfig on $LOG"                                                         >>$CHROOT_SCRIPT
echo "echo -n \"Setting root password \" "                            >>$CHROOT_SCRIPT
echo "usermod -p `mkpasswd $root_password` root"                                        >>$CHROOT_SCRIPT
echo "mount proc /proc -t proc"                                                     >>$CHROOT_SCRIPT
echo "#create parport devices"														>>$CHROOT_SCRIPT
echo "cd /dev"														>>$CHROOT_SCRIPT
echo "./MAKEDEV parport"														>>$CHROOT_SCRIPT
echo "cd -"														>>$CHROOT_SCRIPT

echo "export DEBIAN_FRONTEND=noninteractive"                                        >>$CHROOT_SCRIPT

echo "loadkeys $keymap $LOG"                                                          >>$CHROOT_SCRIPT
echo "syslogd $LOG"                                                          >>$CHROOT_SCRIPT
echo "tail -f /var/log/syslog >/dev/tty3 2>&1 & $LOG"                                                          >>$CHROOT_SCRIPT

echo "mkdir -p /var/log/univention "                                                          >>$CHROOT_SCRIPT
echo "touch /var/log/univention/join.log $LOG"                                                          >>$CHROOT_SCRIPT
echo "chmod 600 /var/log/univention/join.log $LOG"                                                          >>$CHROOT_SCRIPT
echo "tail -f /var/log/syslog >/dev/tty3 2>&1 & $LOG"                                                          >>$CHROOT_SCRIPT
echo "tail -f /var/log/univention/join.log >/dev/tty4 2>&1 & $LOG"                                                          >>$CHROOT_SCRIPT

echo "apt-get clean $LOG"                                                           >>$CHROOT_SCRIPT
echo "apt-get update $LOG"                                                          >>$CHROOT_SCRIPT
installBaseConfig ()
{
    installPackage "univention-baseconfig"

    echo "univention-baseconfig set domainname=$domainname $LOG"									>>$CHROOT_SCRIPT
    echo "univention-baseconfig set hostname=$hostname $LOG"										>>$CHROOT_SCRIPT
	echo "hostname $hostname $LOG"																	>>$CHROOT_SCRIPT
	if [ -n "$nameserver_1" ]; then
		echo "univention-baseconfig set nameserver1=$nameserver_1 $LOG"							>>$CHROOT_SCRIPT
	fi
	if [ -n "$nameserver_2" ]; then
		echo "univention-baseconfig set nameserver2=$nameserver_2 $LOG"							>>$CHROOT_SCRIPT
	fi
	if [ -n "$nameserver_3" ]; then
		echo "univention-baseconfig set nameserver3=$nameserver_3 $LOG"							>>$CHROOT_SCRIPT
	fi

	if [ -n "$dns_forwarder_1" ]; then
		echo "univention-baseconfig set dns/forwarder1=$dns_forwarder_1 $LOG"							>>$CHROOT_SCRIPT
	fi
	if [ -n "$dns_forwarder_2" ]; then
		echo "univention-baseconfig set dns/forwarder2=$dns_forwarder_2 $LOG"							>>$CHROOT_SCRIPT
	fi
	if [ -n "$dns_forwarder_3" ]; then
		echo "univention-baseconfig set dns/forwarder3=$dns_forwarder_3 $LOG"							>>$CHROOT_SCRIPT
	fi


    WINDOWS_DOMAIN=`echo $domainname | sed -e "s/\..*//"`
	if [ -n "$eth0_type" -a "$eth0_type" = "dynamic" ]; then
		echo "univention-baseconfig set interfaces/eth0/type=dhcp $LOG" >>$CHROOT_SCRIPT
	fi

	if [ -n "$eth0_ip" ]; then
		echo "univention-baseconfig set interfaces/eth0/address=$eth0_ip $LOG"							>>$CHROOT_SCRIPT
		echo "univention-baseconfig set interfaces/eth0/network=$eth0_network $LOG"						>>$CHROOT_SCRIPT
		echo "univention-baseconfig set interfaces/eth0/netmask=$eth0_netmask $LOG"						>>$CHROOT_SCRIPT
		echo "univention-baseconfig set interfaces/eth0/broadcast=$eth0_broadcast $LOG"					>>$CHROOT_SCRIPT
	fi

	if [ -n "$use_external_nameserver" -a "$use_external_nameserver" = "true" ]; then
		echo "univention-baseconfig set nameserver/external=true $LOG"							>>$CHROOT_SCRIPT
	else
		echo "univention-baseconfig set nameserver/external=false $LOG"							>>$CHROOT_SCRIPT
	fi

	if [ -n "$eth0_0_ip" ]; then
		echo "univention-baseconfig set interfaces/eth0_0/address=$eth0_0_ip $LOG"							>>$CHROOT_SCRIPT
		echo "univention-baseconfig set interfaces/eth0_0/network=$eth0_0_network $LOG"						>>$CHROOT_SCRIPT
		echo "univention-baseconfig set interfaces/eth0_0/netmask=$eth0_0_netmask $LOG"						>>$CHROOT_SCRIPT
		echo "univention-baseconfig set interfaces/eth0_0/broadcast=$eth0_0_broadcast $LOG"					>>$CHROOT_SCRIPT
		if [ -n "$eth0_0_gateway" ]; then
			echo "univention-baseconfig set interfaces/eth0_0/gateway=$eth0_0_gateway $LOG"					>>$CHROOT_SCRIPT
		fi
	fi
	if [ -n "$eth1_ip" ]; then
		echo "univention-baseconfig set interfaces/eth1/address=$eth1_ip $LOG"						>>$CHROOT_SCRIPT
	fi
	if [ -n "$eth1_network" ]; then
		echo "univention-baseconfig set interfaces/eth1/network=$eth1_network $LOG"					>>$CHROOT_SCRIPT
	fi
	if [ -n "$eth1_netmask" ]; then
		echo "univention-baseconfig set interfaces/eth1/netmask=$eth1_netmask $LOG"					>>$CHROOT_SCRIPT
	fi
	if [ -n "$eth1_broadcast" ]; then
		echo "univention-baseconfig set interfaces/eth1/broadcast=$eth1_broadcast $LOG"				>>$CHROOT_SCRIPT
	fi
	if [ -n "$eth2_ip" ]; then
		echo "univention-baseconfig set interfaces/eth2/address=$eth2_ip $LOG"						>>$CHROOT_SCRIPT
	fi
	if [ -n "$eth2_network" ]; then
		echo "univention-baseconfig set interfaces/eth2/network=$eth2_network $LOG"					>>$CHROOT_SCRIPT
	fi
	if [ -n "$eth2_netmask" ]; then
		echo "univention-baseconfig set interfaces/eth2/netmask=$eth2_netmask $LOG"					>>$CHROOT_SCRIPT
	fi
	if [ -n "$eth2_broadcast" ]; then
		echo "univention-baseconfig set interfaces/eth2/broadcast=$eth2_broadcast $LOG"				>>$CHROOT_SCRIPT
	fi
	if [ -n "$eth3_ip" ]; then
		echo "univention-baseconfig set interfaces/eth3/address=$eth3_ip $LOG"						>>$CHROOT_SCRIPT
	fi
	if [ -n "$eth3_network" ]; then
		echo "univention-baseconfig set interfaces/eth3/network=$eth3_network $LOG"					>>$CHROOT_SCRIPT
	fi
	if [ -n "$eth3_netmask" ]; then
		echo "univention-baseconfig set interfaces/eth3/netmask=$eth3_netmask $LOG"					>>$CHROOT_SCRIPT
	fi
	if [ -n "$eth3_broadcast" ]; then
		echo "univention-baseconfig set interfaces/eth3/broadcast=$eth3_broadcast $LOG"				>>$CHROOT_SCRIPT
	fi

	if [ -n "$gateway" ]; then
		echo "univention-baseconfig set gateway=$gateway $LOG"										>>$CHROOT_SCRIPT
	fi
	if [ -n "$create_home_share" -a "$create_home_share" = "true" ]; then
		echo "univention-baseconfig set create/home/share=true $LOG"										>>$CHROOT_SCRIPT
	fi
	if [ -n "$system_role" ]; then
		server_role="$system_role"
	fi
	if [ -n "$ldap_position" ]; then
		echo "univention-baseconfig set ldap/position="$ldap_position" $LOG"										>>$CHROOT_SCRIPT
	fi

	if [ -n "$server_role" ]; then
		if [ $server_role = "DomainController_Slave" ]
		then
			echo "univention-baseconfig set server/role=domaincontroller_slave $LOG"					>>$CHROOT_SCRIPT
			if [ -n "$domain_controller_ip" ]; then
				echo "univention-baseconfig set ldap/master/ip=$domain_controller_ip $LOG"				>>$CHROOT_SCRIPT
			fi
			if [ -n "$ldap_base" ]; then
				echo "univention-baseconfig set ldap/base=\"$ldap_base\" $LOG"									>>$CHROOT_SCRIPT
			fi
		elif [ $server_role = "MemberServer" ]
		then
			if [ -n "$domain_controller_ip" ]; then
				echo "univention-baseconfig set ldap/master/ip=$domain_controller_ip $LOG"				>>$CHROOT_SCRIPT
			fi
			if [ -n "$ldap_base" ]; then
				echo "univention-baseconfig set ldap/base=\"$ldap_base\" $LOG"									>>$CHROOT_SCRIPT
			fi
			echo "univention-baseconfig set server/role=memberserver $lOG"								>>$CHROOT_SCRIPT
		elif [ $server_role = "FatClient" ]
		then
			if [ -n "$domain_controller_ip" ]; then
				echo "univention-baseconfig set ldap/master/ip=$domain_controller_ip $LOG"				>>$CHROOT_SCRIPT
			fi
			if [ -n "$ldap_base" ]; then
				echo "univention-baseconfig set ldap/base=\"$ldap_base\" $LOG"									>>$CHROOT_SCRIPT
			fi
			echo "univention-baseconfig set server/role=fatclient $lOG"								>>$CHROOT_SCRIPT
		elif [ $server_role = "MobileClient" ]
		then
			if [ -n "$domain_controller_ip" ]; then
				echo "univention-baseconfig set ldap/master/ip=$domain_controller_ip $LOG"				>>$CHROOT_SCRIPT
			fi
			if [ -n "$ldap_base" ]; then
				echo "univention-baseconfig set ldap/base=\"$ldap_base\" $LOG"									>>$CHROOT_SCRIPT
			fi
			echo "univention-baseconfig set server/role=mobileclient $lOG"								>>$CHROOT_SCRIPT
		elif [ $server_role = "DomainController_Backup" ]
		then
			if [ -n "$domain_controller_ip" ]; then
				echo "univention-baseconfig set ldap/master/ip=$domain_controller_ip $LOG"				>>$CHROOT_SCRIPT
			fi
			echo "univention-baseconfig set server/role=domaincontroller_backup $LOG"					>>$CHROOT_SCRIPT
			if [ -n "$ldap_base" ]; then
				echo "univention-baseconfig set ldap/base=\"$ldap_base\" $LOG"									>>$CHROOT_SCRIPT
			fi
		elif [ $server_role = "DomainController_Master" ];
		then
			if [ -n "$ldap_base" ]; then
				echo "univention-baseconfig set ldap/base=\"$ldap_base\" $LOG"									>>$CHROOT_SCRIPT
			fi
			echo "univention-baseconfig set ldap/server/ip=$eth0_ip $LOG"								>>$CHROOT_SCRIPT
			echo "univention-baseconfig set ldap/server/name=$hostname.$domainname $LOG"				>>$CHROOT_SCRIPT
			echo "univention-baseconfig set ldap/master=$hostname.$domainname $LOG"						>>$CHROOT_SCRIPT
			echo "univention-baseconfig set kerberos/adminserver=$hostname.$domainname $LOG"			>>$CHROOT_SCRIPT
			echo "univention-baseconfig set server/role=domaincontroller_master"						>>$CHROOT_SCRIPT
		fi
    fi

    echo "univention-baseconfig set windows/domain=$WINDOWS_DOMAIN $LOG"							>>$CHROOT_SCRIPT
    echo "univention-baseconfig set locale=$locales $LOG"											>>$CHROOT_SCRIPT
    echo "echo \"$timezone\" >/etc/timezone $LOG"											>>$CHROOT_SCRIPT
	echo "cp -v /usr/share/keymaps/i386/*/$keymap.kmap.gz /etc/console/boottime.kmap.gz $LOG"  >>$CHROOT_SCRIPT
	if [ -n "$server_role" ]; then
		if [ $server_role = "DomainController_Master" ]; then
			echo "univention-baseconfig set ldap/server/type=master $LOG"								>>$CHROOT_SCRIPT
		elif [ $server_role = "DomainController_Slave" ]; then
			echo "univention-baseconfig set ldap/server/type=slave $LOG"								>>$CHROOT_SCRIPT
		fi
	fi
	#cat /mnt/conf/lilo.conf.template | sed "s|@%@BOOT_DEVICE@%@|$LILO_BOOT_DEVICE|;s|@%@ROOT_DEVICE@%@|$ROOT_DEVICE|" > /instmnt/etc/lilo.conf
	echo "univention-baseconfig set lilo/boot=$LILO_BOOT_DEVICE $LOG"							>>$CHROOT_SCRIPT
	echo "univention-baseconfig set lilo/root=$ROOT_DEVICE $LOG"							>>$CHROOT_SCRIPT

    echo "univention-baseconfig commit $LOG"                                            >>$CHROOT_SCRIPT


	#SSL Preferences
	if [ -n "$ssl_country" ]; then
		echo "univention-baseconfig set ssl/country=\"$ssl_country\"" >>$CHROOT_SCRIPT
	fi
	if [ -n "$ssl_state" ]; then
		echo "univention-baseconfig set ssl/state=\"$ssl_state\"" >>$CHROOT_SCRIPT
	fi
	if [ -n "$ssl_locality" ]; then
		echo "univention-baseconfig set ssl/locality=\"$ssl_locality\"" >>$CHROOT_SCRIPT
	fi
	if [ -n "$ssl_organization" ]; then
		echo "univention-baseconfig set ssl/organization=\"$ssl_organization\"" >>$CHROOT_SCRIPT
	fi
	if [ -n "$ssl_organizationalunit" ]; then
		echo "univention-baseconfig set ssl/organizationalunit=\"$ssl_organizationalunit\"" >>$CHROOT_SCRIPT
	fi
	if [ -n "$ssl_common" ]; then
		echo "univention-baseconfig set ssl/common=\"$ssl_common\"" >>$CHROOT_SCRIPT
	fi
	if [ -n "$ssl_email" ]; then
		echo "univention-baseconfig set ssl/email=$ssl_email" >>$CHROOT_SCRIPT
	fi


    echo "hostname $hostname $LOG"                                                    >>$CHROOT_SCRIPT
    echo "apt-get update $LOG"                                                          >>$CHROOT_SCRIPT
    echo "$PIPE apt-get -u upgrade $LOG"                                                >>$CHROOT_SCRIPT
}

installPackage ()
{
	echo "echo \"Installing $1 \">>/.log" >>$CHROOT_SCRIPT
	echo "echo \"Installing $1 \"" >>$CHROOT_SCRIPT
	echo "$PIPE apt-get install $1 $LOG"                                          >>$CHROOT_SCRIPT
	echo "$PIPE dpkg --configure -a $LOG" >>$CHROOT_SCRIPT
}

installBaseConfig

for i in $preinst_hook; do
	if [ -e "/mnt/script/$i" ]; then
		mkdir -p /instmnt/etc/univention/preinst
		cp "/mnt/script/$i" /instmnt/etc/univention/preinst/
		chmod 700 "/instmnt/etc/univention/preinst/$i"
		echo "/etc/univention/preinst/$i" >>$CHROOT_SCRIPT
	fi
done

res=`grep "acpi=off" /proc/cmdline`
if [ -n "$res" ]; then
	echo "univention-baseconfig set lilo/append/acpi=off $LOG"							>>$CHROOT_SCRIPT
fi

echo "$PIPE apt-get install initrd-tools $LOG"                                      >>$CHROOT_SCRIPT

LOADED_MODULES=`/sbin/lsmod | awk '{print $1}' | grep -v ^Module`
if [ ! -z "$LOADED_MODULES" ]
then
    for i in $LOADED_MODULES
    do
		if [ -e /mnt/conf/modules_ignore ]; then
			grep ^$i /mnt/conf/modules_ignore >/dev/null 2>&1
			if [ $? != 0 ]; then
				echo "echo $i >>/etc/mkinitrd/modules"                                      >>$CHROOT_SCRIPT
			fi
		else
			echo "echo $i >>/etc/mkinitrd/modules"                                      >>$CHROOT_SCRIPT
		fi
		if [ -z "$module" ]; then
			module="$i"
		else
			module="$module;$i"
		fi
    done
fi
if [ -n "$module" ]; then
	echo "univention-baseconfig set kernel/modules=\"$module\""   						>>$CHROOT_SCRIPT
fi

echo "$PIPE apt-get install univention-initrd $LOG"                                      >>$CHROOT_SCRIPT
echo "echo \"do_initrd = Yes\" >>/etc/kernel-img.conf"                                      >>$CHROOT_SCRIPT
echo "echo \"do_bootfloppy = no\" >>/etc/kernel-img.conf"                                      >>$CHROOT_SCRIPT
echo "echo \"silent_loader = yes\" >>/etc/kernel-img.conf"                                      >>$CHROOT_SCRIPT
echo "$PIPE apt-get install univention-kernel-image $LOG"                                      >>$CHROOT_SCRIPT
echo "univention-baseconfig set version/version=$1"     >>$CHROOT_SCRIPT
echo "univention-baseconfig set version/patchlevel=$2"     >>$CHROOT_SCRIPT
echo "sleep 3"     >>$CHROOT_SCRIPT
echo "/sbin/lilo $LOG "							                                        >>$CHROOT_SCRIPT

echo "ifup lo $LOG"                                                                 >>$CHROOT_SCRIPT
if [ -n "$eth0_ip" ]; then
	echo "ifup eth0 $LOG"                                                               >>$CHROOT_SCRIPT
fi
if [ -n "$eth1_ip" ]; then
	echo "ifup eth1 $LOG"                                                               >>$CHROOT_SCRIPT
fi
if [ -n "$eth2_ip" ]; then
	echo "ifup eth2 $LOG"                                                               >>$CHROOT_SCRIPT
fi
if [ -n "$eth3_ip" ]; then
	echo "ifup eth3 $LOG"                                                               >>$CHROOT_SCRIPT
fi

if [ -n "$eth0_type" -a "$eth0_type" = "dynamic" ]; then
	installPackage dhcp-client
	res=`echo $SOURCE_MOUNT_CMD | grep " nfs "`
	if [ -z "$res" ]; then
		echo "dhclient" >>$CHROOT_SCRIPT
	else
		echo "dhclient" >>$CHROOT_SCRIPT
		echo "$SOURCE_MOUNT_CMD"  >>$CHROOT_SCRIPT
		echo "mounted=\$?"  >>$CHROOT_SCRIPT
		echo "tries=0"  >>$CHROOT_SCRIPT
		echo "while [ \$mounted != 0 -a \$tries -lt 3 ]; do" >>$CHROOT_SCRIPT
			echo "sleep 10" >>$CHROOT_SCRIPT
			echo "$SOURCE_MOUNT_CMD" >>$CHROOT_SCRIPT
			echo "mounted=\$?" >>$CHROOT_SCRIPT
			echo "tries=\$((tries+1))" >>$CHROOT_SCRIPT
		echo "done" >>$CHROOT_SCRIPT
	fi
else
	res=`echo $SOURCE_MOUNT_CMD | grep " nfs "`
	if [ -n "$res" ]; then
		echo "$SOURCE_MOUNT_CMD"  >>$CHROOT_SCRIPT
		echo "mounted=\$?"  >>$CHROOT_SCRIPT
		echo "tries=0"  >>$CHROOT_SCRIPT
		echo "while [ \$mounted != 0 -a \$tries -lt 3 ]; do" >>$CHROOT_SCRIPT
			echo "sleep 10" >>$CHROOT_SCRIPT
			echo "$SOURCE_MOUNT_CMD" >>$CHROOT_SCRIPT
			echo "mounted=\$?" >>$CHROOT_SCRIPT
			echo "tries=\$((tries+1))" >>$CHROOT_SCRIPT
		echo "done" >>$CHROOT_SCRIPT
	fi

fi

installPackage univention-updater


if [ "$server_role" = "MemberServer" ]; then
	INST_PACKAGES="univention-server-member "
elif [ "$server_role" = "FatClient" ]; then
	if [ -n "$fat_client_small" ] && [ "$fat_client_small" = "True" -o "$fat_client_small" = "true" -o "$fat_client_small" = "Yes" -o "$fat_client_small" = "yes" ]; then
		INST_PACKAGES="univention-fat-client-small "
	else
		INST_PACKAGES="univention-fat-client "
	fi
elif [ "$server_role" = "MobileClient" ]; then
	INST_PACKAGES="univention-mobile-client "
elif [ "$server_role" = "DomainController_Slave" ]; then
	INST_PACKAGES="univention-server-slave "
elif [ "$server_role" = "DomainController_Backup" ]; then
	INST_PACKAGES="univention-server-backup "
elif [ "$server_role" = "DomainController_Master" ]; then
	INST_PACKAGES="univention-server-master "
fi


if [ -n "$components" ]; then
	if [ "$components" != "None" ]; then
		for i in $components; do
			if [ "$i" == "Samba" ]; then
				INST_PACKAGES="$INST_PACKAGES univention-samba "
			elif [ "$i" == "Windows-Installer" ]; then
				INST_PACKAGES="$INST_PACKAGES univention-windows-installer "
			elif [ "$i" == "DHCP" ]; then
				INST_PACKAGES="$INST_PACKAGES univention-dhcp "
			elif [ "$i" == "DNS" ]; then
				INST_PACKAGES="$INST_PACKAGES univention-bind univention-bind-proxy "
			elif [ "$i" == "ThinClient" ]; then
				INST_PACKAGES="$INST_PACKAGES univention-thin-client "
			elif [ "$i" == "X-Client" ]; then
				INST_PACKAGES="$INST_PACKAGES univention-application-server "
			elif [ "$i" == "KDE" ]; then
				INST_PACKAGES="$INST_PACKAGES univention-kde "
			elif [ "$i" == "OpenOffice.org" ]; then
				INST_PACKAGES="$INST_PACKAGES univention-ooffice "
			elif [ "$i" == "Mozilla" ]; then
				INST_PACKAGES="$INST_PACKAGES univention-mozilla univention-mozilla-german "
			elif [ "$i" == "Evolution" ]; then
				INST_PACKAGES="$INST_PACKAGES evolution "
			elif [ "$i" == "FaxClient" ]; then
				INST_PACKAGES="$INST_PACKAGES univention-fax-client "
			elif [ "$i" == "FaxServer" ]; then
				INST_PACKAGES="$INST_PACKAGES univention-fax-server "
			elif [ "$i" == "Mail" ]; then
				INST_PACKAGES="$INST_PACKAGES univention-mail-postfix univention-mail-cyrus "
			elif [ "$i" == "Proxy" ]; then
				INST_PACKAGES="$INST_PACKAGES univention-squid "
			elif [ "$i" == "Spamfilter" ]; then
				INST_PACKAGES="$INST_PACKAGES univention-spamassassin"
			elif [ "$i" == "Admin" ]; then
				INST_PACKAGES="$INST_PACKAGES univention-admin "
			elif [ "$i" == "SoftwareMonitor" ]; then
				INST_PACKAGES="$INST_PACKAGES univention-pkgdb "
			elif [ "$i" == "Backup" ]; then
				INST_PACKAGES="$INST_PACKAGES unidump "
			elif [ "$i" == "PrintServer" ]; then
				INST_PACKAGES="$INST_PACKAGES univention-printserver "
			elif [ "$i" == "PrintQuota" ]; then
				INST_PACKAGES="$INST_PACKAGES univention-printquota "
			elif [ "$i" == "X" ]; then
				INST_PACKAGES="$INST_PACKAGES univention-x-core univention-kde"
			elif [ "$i" == "NetInstaller" ]; then
				INST_PACKAGES="$INST_PACKAGES univention-net-installer"
			elif [ "$i" == "ISDN-Administration" ]; then
				INST_PACKAGES="$INST_PACKAGES univention-isdn"
			elif [ "$i" == "VNC-Server" ]; then
				INST_PACKAGES="$INST_PACKAGES vncserver"
			fi
		done
	fi
fi

if [ -n "$INST_PACKAGES" ]; then
	for i in $INST_PACKAGES
	do
		installPackage $i
	done
fi

if [ -n "$extra_packages" ]; then
	for i in $extra_packages; do
		installPackage $i
	done
fi

if [ "$local_repository" = "true" -o "$local_repository" = "yes" ]; then
	echo "univention-baseconfig set local/repository=true $LOG"				>>$CHROOT_SCRIPT
else
	echo "univention-baseconfig set local/repository=false $LOG"				>>$CHROOT_SCRIPT
fi

#if [ "$LANG"x = "de"x ]
#then
echo "cp /usr/share/keymaps/i386/*/$keymap.kmap.gz /etc/console/boottime.kmap.gz"  >>$CHROOT_SCRIPT
echo "rm /etc/localtime ">>$CHROOT_SCRIPT
echo "ln -sf /usr/share/zoneinfo/$timezone /etc/localtime">>$CHROOT_SCRIPT
#fi



echo "if [ -d /var/lib/univention-ldap/ldap ]; then rm -f /var/lib/univention-ldap/ldap/*; fi" >>$CHROOT_SCRIPT

if [ "$server_role" = "DomainController_Master" ]; then
	if [ -z "$slave_join_password" ]; then
		echo "slave_join_password=\`makepasswd --chars=8\`" >>$CHROOT_SCRIPT
		echo "echo \"\$slave_join_password\"  >/etc/slave-join.secret"  >>$CHROOT_SCRIPT
	else
		echo "echo "$slave_join_password"  >/etc/slave-join.secret"  >>$CHROOT_SCRIPT
	fi
	if [ -z "$backup_join_password" ]; then
		echo "backup_join_password=\`makepasswd --chars=8\`" >>$CHROOT_SCRIPT
		echo "echo \"\$backup_join_password\" >/etc/backup-join.secret" >>$CHROOT_SCRIPT
	else
		echo "echo "$backup_join_password" >/etc/backup-join.secret" >>$CHROOT_SCRIPT
	fi
elif [ -n "$domain_controller_account" -a -n "$domain_controller_password" ]; then
	if [ -z "$auto_join" ] || [ "$auto_join" != "FALSE" -a "$auto_join" != "false" -a "$auto_join" != "False" ]; then
		echo "pwd_file=\`mktemp\`" >>$CHROOT_SCRIPT
		echo "chmod 600 \$pwd_file" >>$CHROOT_SCRIPT
		echo "echo \"$domain_controller_password\" >>\$pwd_file" >>$CHROOT_SCRIPT
		echo "/usr/share/univention-join/univention-join -dcaccount $domain_controller_account -dcpwd \$pwd_file" >>$CHROOT_SCRIPT
	fi
fi


if [ "$server_role" = "DomainController_Master" ]; then
	echo "mkdir -p /usr/share/univention-join/"													>>$CHROOT_SCRIPT
	echo "touch /usr/share/univention-join/.joined"												>>$CHROOT_SCRIPT
	echo "for i in /usr/lib/univention-install/*.inst; do echo \"Configure \`basename \$i\`\"; \$i >>/var/log/univention/join.log; done" >>$CHROOT_SCRIPT

	echo "eval \`univention-baseconfig shell\`" >>$CHROOT_SCRIPT
	echo "univention-admin users/user create --position=\"cn=users,\$ldap_base\" --option samba --set username=root --set lastname=root --set password=$root_password" >>$CHROOT_SCRIPT
	echo "univention-admin users/user create --position=\"cn=users,\$ldap_base\" --set username=Administrator --set unixhome=/home/Administrator --set lastname=Administrator --set password=$root_password --set primaryGroup=\"cn=Domain Admins,cn=groups,\$ldap_base\"" >>$CHROOT_SCRIPT

fi
if [ "$server_role" = "DomainController_Master" -o "$server_role" = "DomainController_Backup" ]; then
	echo "mkdir -p /var/lib/samba/netlogon/scripts/"													>>$CHROOT_SCRIPT
fi

if [ "$server_role" = "DomainController_Master" ]; then
	#create default network

	echo "eval \`univention-baseconfig shell\`" >>$CHROOT_SCRIPT
	echo "forwardZone=\`univention-admin dns/forward_zone list --filter zone=\$domainname | grep DN | head -1 | sed -e 's/DN: //g'\`" >>$CHROOT_SCRIPT
	echo "reverseZone=\`univention-admin dns/reverse_zone list | grep ^DN | head -1 | sed -e 's|DN: ||'\`" >>$CHROOT_SCRIPT
	echo "dhcpService=\`univention-admin dhcp/service list | grep DN | head -1 | sed -e 's/DN: //g'\`" >>$CHROOT_SCRIPT

	echo "univention-admin networks/network create --position \"cn=networks,\$ldap_base\" --set name=default --set netmask=\$interfaces_eth0_netmask --set network=\$interfaces_eth0_network --set dnsEntryZoneForward=\$forwardZone --set dnsEntryZoneReverse=\$reverseZone --set dhcpEntryZone=\$dhcpService" >>$CHROOT_SCRIPT
fi

#TODO: postinst_hook
for i in $postinst_hook; do
	if [ -e "/mnt/script/$i" ]; then
		mkdir -p /instmnt/etc/univention/postinst
		cp "/mnt/script/$i" /instmnt/etc/univention/postinst/
		chmod 700 "/instmnt/etc/univention/postinst/$i"
		echo "/etc/univention/postinst/$i" >>$CHROOT_SCRIPT
	fi
done

echo "test -x /usr/sbin/locale-gen && /usr/sbin/locale-gen" >>$CHROOT_SCRIPT
echo "umount /cdrom" >>$CHROOT_SCRIPT

umount /mnt
chmod 500 $CHROOT_SCRIPT

#Start the Shell Script
chroot /instmnt .`echo $CHROOT_SCRIPT | sed -e "s/\/instmnt//g"`

chmod 777 /instmnt/tmp/.

. /tmp/mount_cdrom

if [ "$local_repository" = "yes" -o "$local_repository" = "true" ]; then
	echo "Copy cdrom to /var/lib/univention-server-cdrom" >>/instmnt/.log
	echo "Copy cdrom to /var/lib/univention-server-cdrom"
	mkdir -p /instmnt/var/lib/univention-server-cdrom
	cp -dpR /mnt/* /instmnt/var/lib/univention-server-cdrom/
	cp -dpR /mnt/.??* /instmnt/var/lib/univention-server-cdrom/
	if [ -e "/instmnt/var/lib/univention-server-cdrom/profiles" ]; then
		chmod -R o-rwx /instmnt/var/lib/univention-server-cdrom/profiles
	fi
	if [ -e "/instmnt/var/lib/univention-server-cdrom/internal_profiles" ]; then
		chmod -R o-rwx /instmnt/var/lib/univention-server-cdrom/internal_profiles
	fi

	cat /mnt/conf/sources.list.new | sed -e 's|http://univention-repository/univention-cdrom|file:/var/lib/univention-server-cdrom|' >/instmnt/etc/apt/sources.list

	touch /instmnt//var/lib/univention-server-cdrom/sources.list
	if [ -d "/instmnt//var/lib/univention-server-cdrom/packages" ]; then
		echo "deb http://$hostname.$domainname/univention-cdrom/packages/ ./">> /instmnt/var/lib/univention-server-cdrom/sources.list
	fi
	mkdir -p /instmnt/var/lib/univention-server-cdrom/ucs-updates
	echo "$1-$2" >>/instmnt/var/lib/univention-server-cdrom/ucs-updates/index.list
	echo "nextupdate=none" >>/instmnt/var/lib/univention-server-cdrom/ucs-updates/ucs_$1-$2.txt
	for dir in /instmnt/var/lib/univention-server-cdrom/ucs-updates/*; do
		if [ -d "$dir" ]; then
			echo "`basename $dir`" >>/instmnt/var/lib/univention-server-cdrom/ucs-updates/index.list
			echo "deb http://$hostname.$domainname/univention-cdrom/ucs-updates/`basename $dir`/ ./">> /instmnt/var/lib/univention-server-cdrom/sources.list
		fi
	done

else
	cp /mnt/conf/sources.list.new /instmnt/etc/apt/sources.list
fi

mkdir -p /instmnt/etc/univention/
cat /tmp/installation_profile | sed -e "s|root_password=.*|#root_password=''|" | sed -e "s|domain_controller_password=.*|#domain_controller_password=''|" >/instmnt/etc/univention/installation_profile
chmod 600 /instmnt/etc/univention/installation_profile
mv /instmnt/.log /instmnt/etc/univention/install.log
mv /instmnt/.shell_script /instmnt/etc/univention/installation_script.sh
chmod 600 /instmnt/etc/univention/installation_script.sh /instmnt/etc/univention/install.log

chmod -R 700 /instmnt/root
chmod 1777 /instmnt/tmp

/bin/sync
echo "#!/bin/sh" >>/instmnt/.reboot
echo "apt-get update >/dev/null 2>&1 " >>/instmnt/.reboot
echo "umount -a" >>/instmnt/.reboot

echo "echo -n \"Sending all processes the TERM signal... \"" >>/instmnt/.reboot
echo "killall5 -15" >>/instmnt/.reboot
echo "echo \"done.\"" >>/instmnt/.reboot
echo "sleep 5" >>/instmnt/.reboot
echo "echo -n \"Sending all processes the KILL signal... \"" >>/instmnt/.reboot
echo "killall5 -9" >>/instmnt/.reboot
echo "echo \"done.\"" >>/instmnt/.reboot
echo "umount -a" >>/instmnt/.reboot
chmod 700 /instmnt/.reboot

chroot /instmnt/ /.reboot
rm /instmnt/.reboot
umount /instmnt >/dev/null 2>&1
umount /mnt >/dev/null 2>&1

echo "INSTALLATION DONE" >>/instmnt/.log

if [ -n "$auto_reboot" ] && [ "$auto_reboot" = "Yes" -o "$auto_reboot" = "yes" -o "$auto_reboot" = "True" -o "$auto_reboot" = "true" ]; then
	reboot -d -f -i
fi

echo "Press enter to reboot"
read

reboot -d -f -i
