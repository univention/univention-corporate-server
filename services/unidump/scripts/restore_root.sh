#!/bin/sh
# 	$Id: restore_root.sh,v 1.7 2003/11/05 14:27:26 thorsten Exp $	

. functions.sh

root_disk=`cat rootfs.disk`
case "$root_disk" in
/dev/[hs]d[a-z]) ;;
*)
    error_exit \
    "'$root_disk' does not look like a disk device.\n" \
    "a disk device is something like '/dev/hda', '/dev/sdb', etc\n" \
    "please check if the file 'rootfs.disk' contains the correct device"
    ;;
esac

root_part=`cat rootfs.part`
case "$root_part" in
$root_disk[0-9]) ;;
*)
    error_exit \
    "'$root_part' does not look like a partition of $root_disk (your root-disk).\n" \
    "a partition device is something like '/dev/hda2', '/dev/sdb7', etc\n" \
    "please check if the file 'rootfs.part' contains the correct device"
    ;;
esac

disk_ptable=`echo "$root_disk" | sed "s@.*/@@"`.ptable
if [ -f "$disk_ptable" ]; then
    :
else
    warning \
    "partition table $disk_ptable not found.\n" \
    "if you want to crete a new partition table please use cfdisk or fdisk"
fi

mkrootfs_script="rootfs.mkfs.sh"
if [ -f "$mkrootfs_script" ]; then
    :
else
    warning \
    "Filesystem built script not found.\n" \
    "Create the rootfs by yourself using a command like this:\n" \
    "     mke2fs $root_part"
fi

restore_dir="mnt"
if [ ! -d "$restore_dir" ]; then
    if mkdir -p "$restore_dir"; then 
	:
    else
	error_exit "cannot create $restore_dir"
    fi
fi

restore_rootfs_script="rootfs.restore.sh"
if [ -f "$restore_rootfs_script" ]; then
    :
else
    warning \
    "Rootfs data restore script not found.\n" \
    "Please consult your history file (history.txt) and restore the data using native tools" 
fi

if [ -f bootfs.part ]
then
    boot_part=`cat bootfs.part`
    mkbootfs_script="bootfs.mkfs.sh"
    if [ -f "$mkbootfs_script" ]; then
	:
    else
	warning \
	    "Filesystem built script not found.\n" \
	    "Create the bootfs by yourself using a command like this:\n" \
	    "     mke2fs $boot_part"
    fi

    if [ ! -d "$restore_dir/boot" ]; then
	if mkdir -p "$restore_dir/boot"; then 
	    :
	else
	    error_exit "cannot create $restore_dir/boot"
	fi
    fi

    restore_bootfs_script="bootfs.restore.sh"
    if [ -f "$restore_bootfs_script" ]; then
	:
    else
	warning \
	    "Bootfs data restore script not found.\n" \
	    "Please consult your history file (history.txt) and restore the data using native tools" 
    fi
fi


restore_lvm_script="restore_lvm.sh";
restore_nonroot_script="restore_nonroot.sh";
restore_swap_script="restore_swap.sh";

######################################################################
######################################################################

part_rootdisk() {
    cat <<EOF >&2
+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
+++ WARNING +++ WARNING +++ WARNING +++ WARNING +++ WARNING +++ WARNING +++
+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

       THIS WILL DESTROY ALL YOUR DATA ON DISK $root_disk 
       
       PLEASE ABORT WITH ^C IF YOU DO NOT WANT TO DO THAT

+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
+++ WARNING +++ WARNING +++ WARNING +++ WARNING +++ WARNING +++ WARNING +++
+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
EOF
    if yesno \
    "Do you want to proceed and destroy all your data on $root_disk?" "n"
    then
	if [ ! -f "$disk_ptable" ]; then
	    error_exit \
	    "$disk_ptable not found, please use cfdisk or fdisk!" 
	else
	    echo
	    echo "this partition table will be written to $root_disk"
	    echo
	    cat "$disk_ptable"
	    echo
	    if yesno \
	    "Do you want to write this partition table to disk $root_disk?" "n"
	    then
		sfdisk "$root_disk" -O "$disk_ptable.old" < "$disk_ptable"
	    fi
	fi
    fi
}


create_rootfs() {
    cat <<EOF >&2
+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
+++ WARNING +++ WARNING +++ WARNING +++ WARNING +++ WARNING +++ WARNING +++
+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

       THIS WILL DESTROY ALL YOUR DATA ON PARTITION $root_part
       
       PLEASE ABORT WITH ^C IF YOU DO NOT WANT TO DO THAT

+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
+++ WARNING +++ WARNING +++ WARNING +++ WARNING +++ WARNING +++ WARNING +++
+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
EOF
    if yesno \
    "Do you want to proceed and destroy all your data on $root_part?" "n"
    then
	/bin/sh "$mkrootfs_script" "$root_part" || exit 1
    fi
}

create_bootfs() {
    cat <<EOF >&2
+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
+++ WARNING +++ WARNING +++ WARNING +++ WARNING +++ WARNING +++ WARNING +++
+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

       THIS WILL DESTROY ALL YOUR DATA ON PARTITION $boot_part
       
       PLEASE ABORT WITH ^C IF YOU DO NOT WANT TO DO THAT

+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
+++ WARNING +++ WARNING +++ WARNING +++ WARNING +++ WARNING +++ WARNING +++
+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
EOF
    if yesno \
    "Do you want to proceed and destroy all your data on $boot_part?" "n"
    then
	/bin/sh "$mkbootfs_script" "$boot_part" || exit 1
    fi
}


mount_rootfs() {
    if mount "$root_part" "$restore_dir"; then
	    test -e $restore_dir/lost+found && rm -rf $restore_dir/lost+found;              
    else
	error_exit "mounting $root_part on $restore_dir failed"
    fi
}

mount_bootfs() {
    if mount "$boot_part" "$restore_dir/boot"; then
	    test -e $restore_dir/boot/lost+found && rm -rf $restore_dir/boot/lost+found;      
    else
	error_exit "mounting $boot_part on $restore_dir/boot failed"
    fi
}

restore_rootfs() {
    /bin/sh "$restore_rootfs_script" "$restore_dir" || exit 2
}

restore_bootfs() {
    /bin/sh "$restore_bootfs_script" "$restore_dir/boot" || exit 2
}

save_scripts() {
    cp "functions.sh" "$restore_dir" || exit 2
    cp "magic" "$restore_dir" || exit 2
            
    if [ -f "$restore_lvm_script" ]; then
	    cp "$restore_lvm_script" "$restore_dir" || exit 2
    fi
    if [ -f "$restore_nonroot_script" ]; then
	    cp "$restore_nonroot_script" "$restore_dir" || exit 2
    fi
    if [ -f "$restore_swap_script" ]; then
        cp "$restore_swap_script" "$restore_dir" || exit 2
    fi
}

save_history() {
    cp history.txt "$restore_dir" || exit 2
#   cp history.txt "$restore_dir/var/lib/unidump" || true               # wird von restore_nonroot.sh gemacht !
}

rewrite_bootsec() {
    lilo -r "$restore_dir"
    lilo -r "$restore_dir" -R linux 1
}

reboot() {
    shutdown -r now
}

######################################################################
######################################################################

# ask if we shall restore the rootfs
if yesno "Do you want to rebuild the root-filesystem (the fs holding '/')?" "n"
then
    :
else
    exit 0
fi


# ask if we shall repart the root-disk
if yesno "Do you want to write a new partition table on disk $root_disk?" "n"
then
    part_rootdisk
fi


# ask if we shall create a new filesystem 
if yesno "Do you want to create a new filesystem on partition $root_part?" "n"
then
    create_rootfs
fi

# ask if we shall mount the target
if yesno "Do you want to mount your target filesystem $root_part on $restore_dir (necessary to restore data)?" "n"
then
    mount_rootfs
fi

# ask if we shall restore the data
if yesno "Do you want to restore the data of your root-filesystem?" "n"
then
    restore_rootfs
    save_scripts
    save_history
fi


if [ -f bootfs.part ]
then

# ask if we shall create a new filesystem 
    if yesno "Do you want to create a new filesystem on partition $boot_part?" "n"
	then
	create_bootfs
    fi

# ask if we shall mount the target
    if yesno "Do you want to mount your target filesystem $boot_part on $restore_dir/boot (necessary to restore data)?" "n"
	then
	mount_bootfs
    fi

    # ask if we shall restore the data
    if yesno "Do you want to restore the data of your boot-filesystem?" "n"
	then
	restore_bootfs
    fi
fi


# write a new bootsector
if yesno "Do you want to make the target filesystem bootable?" "n"
then
    rewrite_bootsec
fi




