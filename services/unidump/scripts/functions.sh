# 	$Id: functions.sh,v 1.4 2003/11/04 11:06:55 thorsten Exp $	

true=1
false=
pwd=`pwd`

PATH=$PATH:$pwd

error() {
    # usage: error <message>
    local myself=`basename $0`
    echo -e "$myself: $*" >&2
}

warning() {
    # usage: warning <message>
    error "(warning) $*"
}

error_exit() {
    # usage: error_exit <message>
    error "$*"
    exit 1
}

regexp_match() {
    # usage: regexp_match <arg1> <arg2>
    [ "$#" = "2" ] || error_exit "usage: regexp_match <arg1> <arg2>"
#    expr "$1" : "$2" > /dev/null
    local rc=`echo $1 | sed -n "\\%$2% ="`
    if [ "X$rc" != "X" ]; then
	return 0;
    else
	return 1;
    fi
}

is_empty() {
    # usage: is_empty <string>
    [ "$#" = "1" ] || error_exit "usage: is_empty <string>"
    test "X$1" = "X"
    return $?
}

is_equal() {
    # usage: is_equal <string1> <string2>
    [ "$#" = "2" ] || error_exit "usage: is_equal <string1> <string2>"
    test "$1" = "$2"
    return $?
}

yesno() {
    # usage: yesno <prompt> <y|n>
    # return 0 for yes, 1 for no, -1 for bad argument
    [ "$#" = "2" ] || error_exit "usage: yesno <prompt> <y|n>"
    local prompt="$1"
    local default="${2:-n}"
    local rc="-1"
    local answer
    case $default in
	[yYjJ]|yes) prompt="$prompt [Yn]"; rc=0;;
	[nN]|no)    prompt="$prompt [yN]"; rc=1;;
	*)          
	    echo "yesno: bad arguments:" "$@" >&2
	    echo "usage: yesno <prompt> <y|n>" >&2
	    return $rc
	    ;;
    esac
    while :; do
	echo -n "$prompt: " >&2
	read answer
	case $answer in
	[yYjJ]|yes) rc=0; return $rc;;
	[nN]|no)    rc=1; return $rc;;
	'')         return $rc;;
	esac
    done
}

yesno_exec() {
    # usage: yesno_exec <prompt> <y|n> <command> [args ...]
    [ "$#" -ge "3" ] || error_exit \
	"usage: yesno_exec <prompt> <y|n> <command> [args ...]"
    local prompt="$1"
    local default="$2"
    shift 2
    if yesno "$prompt" "$default"
    then
	"$@"
    fi
}


yesno_for_list() {
    # usage: yesno_for_list <prompt> <y|n> <list>
    [ "$#" -ge "2" ] || error_exit \
	"usage: yesno_for_list <prompt> <y|n> <list>"
    local prompt="$1"
    local default="$2"
    local list
    shift 2
    while [ "X$1" != "X" ]; do
	if yesno "$prompt $1" "$default"; then
	    list="$list $1"
	fi
	shift
    done
    echo $list
}

prompt() {
    # usage: prompt <question> <default>
    [ "$#" = "2" ] || error_exit "usage: prompt <question> <default>"
    local prompt="$1"
    local default="$2"
    local answer
    shift 2
    echo -n "$prompt [$default]: " >&2
    read answer
    case "$answer" in
	'') answer="$default";;
    esac
    echo "$answer"
}

ask_for_tape() {
    # usage: ask_for_tape <tapedevice> <blocksize> <tapelabel> <tapeid>
    [ "$#" = "4" ] || error_exit \
	"usage: ask_for_tape <tapedevice> <blocksize> <tapelabel> <tapeid>"
    local device=$1
    local bs=$2
    local label=$3;
    local id=$4;
    local file;
    while :; do
	prompt "please insert tape $id (label ${label})" \
	    "<return>" > /dev/null;
	mt -f $device rewind;
	file=`dd if=$device bs=$bs count=1 | file -b -m $pwd/magic -`;
	if echo $file | grep -q $label; then
	    break;
	else
	    echo "Sorry, I found a wrong tape in drive:"
	    echo $file
	    echo
	fi
    done
}


check_dumplabel() {
    # usage: check_dumplabel <tapedevice> <blocksize> <dumplabel>
    [ "$#" = "3" ] || error_exit \
	"usage: check_dumplabel <tapedevice> <blocksize> <dumplabel>"
    local device=$1
    local bs=$2
    local label=$3;
    local file=`dd if=$device bs=$bs count=1 | file -b -m $pwd/magic -`;
    if regexp_match "$file" "s?tar"; then
	return 0;
    fi
    if echo $file | grep -q $label; then
	return 0;
    else
	error_exit \
    "Sorry, I found a wrong dump on tape.\nShould be: $label\nIt is: $file"
    fi
}

f_restore() {
    # usage: f_restore <tapedevice> <blocksize> <dumpformat> <label> <compression> 
    [ "$#" -ge "4" ] || error_exit \
	"usage: f_restore <tapedevice> <blocksize> <dumpformat> <label> <compression> "
    local device=$1
    local bs=$2
    local format=$3
    local label=$4
    local zip=$5
    case $format in
    ext2dump|ext3dump)
	restore -r -b $((bs / 1024)) -f $device;
	;;
    xfsdump)
	case "$zip" in
	    gzip) dd if=$device bs=$bs|gzip -dc |xfsrestore -F -L "$label" -r - .;;
	    bzip2)dd if=$device bs=$bs|bzip2 -dc|xfsrestore -F -L "$label" -r - .;;
	    *)    xfsrestore -F -L "$label" -r -m -b $bs -f $device .;;
	esac
	;;
    star)
	star -x -p -k -U -xfflags -acl -H=exustar -f $device;
	;;
    gtar) 
	case "$zip" in
	    gzip|z) tar -x -z -p -k -V "$label" -f $device;;
	    bzip2)  tar -x -j -p -k -V "$label" -f $device;;
	    *)      tar -x -p -k -V "$label" -f $device;
	esac
	;;
    *)
	error_exit "unknown dump format";
	;;
    esac
}

cd_or_die() {
    # usage: cd_or_die <dir>
    [ "$#" = "1" ] || error_exit "usage: cd_or_die <dir>"
    local dir=$1
    if [ ! -d "$dir" ]; then
	mkdir -p "$dir" || error_exit "cannot create directory $dir";
    fi
    cd "$dir" || error_exit "cannot cd to directory $dir";
}



part_disk() {
    # usage: part_disk <device>
    local disk=$1
    local disk_ptable=`echo "$disk" | sed "s@.*/@@"`.ptable
    if [ -f "$disk_ptable" ]; then
    :;	
    else
	error_exit \
	"partition table $disk_ptable not found.\n" \
	"if you want to crete a new partition table please use cfdisk or fdisk"
    fi

    cat <<EOF >&2
+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
+++ WARNING +++ WARNING +++ WARNING +++ WARNING +++ WARNING +++ WARNING +++
+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

       THIS WILL DESTROY ALL YOUR DATA ON DISK $disk 
       
       PLEASE ABORT WITH ^C IF YOU DO NOT WANT TO DO THAT

+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
+++ WARNING +++ WARNING +++ WARNING +++ WARNING +++ WARNING +++ WARNING +++
+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
EOF
    if yesno \
    "Do you want to proceed and destroy all your data on $disk?" "n"
    then
	if [ ! -f "$disk_ptable" ]; then
	    error_exit \
	    "$disk_ptable not found, please use cfdisk or fdisk!" 
	else
	    echo
	    echo "this partition table will be written to $disk"
	    echo
	    cat "$disk_ptable"
	    echo
	    if yesno \
	    "Do you want to write this partition table to disk $root_disk?" "n"
	    then
		sfdisk "$disk" < "$disk_ptable"
	    fi
	fi
    fi
}

rwmount () {
# usage: rwmount;
    mount -o remount,rw /
}
