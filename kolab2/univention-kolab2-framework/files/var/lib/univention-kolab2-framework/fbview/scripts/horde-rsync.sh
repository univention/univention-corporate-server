#!/bin/sh
#
#  $Horde: horde/scripts/horde-rsync.sh,v 2.11 2001/12/03 07:50:24 jon Exp $
#
#  This script performs a checkout from the horde CVS tree at horde.org
#
#  [ Edit the following values to suit your local environment ]

# The path to the basedirectory for your horde checkout                        
BASEDIR="${HOME}/horde"

# The path to your CVSROOT:
export CVSROOT="${BASEDIR}/rsync"

# The path in which to put the retrieved Horde files:
HORDE_DIR="${BASEDIR}/cvs"

# The absolute path to your rsync binary:
export RSYNC="/usr/local/bin/rsync"

# The absolute path to your cvs binary:
export CVSCOMMAND="/usr/bin/cvs"

# The modules which you'd like to retrieve:
DEFAULT_MODULE_LIST="imp kronolith turba jonah babel nag troll whups"

# The default label from which to checkout
DEFAULT_LABEL=HEAD

# The default type of action that should be done
DEFAULT_ACTION=update


#  -[ NOTHING ELSE SHOULD NEED TO BE EDITED BELOW THIS LINE ]-

# Arguments that you wish to pass on to cvs
#CVS_ARGS="-q"

# Arguments that you wish to pass on to rsync
RSYNC_ARGS="-av --delete"

# The rsync server/repository from which to "checkout"
RSYNC_DIR="rsync.horde.org::horde-cvs/"

# Make sure that the CVSROOT and HORDE_DIR directories exist
mkdir -p "$CVSROOT" "$HORDE_DIR"

# Some useful vars
MYNAME=`basename $0`
CWD=`pwd`

while [ $# -gt 0 ]; do
    case "${1}" in
        --with-modules=*)
            # Set the comma module list
            COMMA_MODULES=$(echo $1 | sed 's|.*=||')
            # Transform this to the module list
            MODULE_LIST="$(echo $COMMA_MODULES | tr ',' ' ')"
            shift
            ;;
        --type=*)
            # Set the type of action
            ACTION=$(echo $1 | sed 's|.*=||')
            shift
            ;;
        --label=*)
            # Set the label from which to checkout
            LABEL=$(echo $1 | sed 's|.*=||')
            shift
            ;;
        --h*|-h*)
            echo "Usage: $MYNAME {--with-modules=[module[,module]*]|--type=[checkout|update]|--label=[\"\"|[label]]" 1>&2
            exit 2
            ;;
    esac
done

# Check if all the needed vars have been set
MODULE_LIST="${MODULE_LIST:-$DEFAULT_MODULE_LIST}"
COMMA_MODULES=${COMMA_MODULES:-$(echo $DEFAULT_MODULE_LIST | tr ' ' ',')}
ACTION=${ACTION:-$DEFAULT_ACTION}
LABEL=${LABEL:-$DEFAULT_LABEL}

# Append the action to the cvs arguments
CVS_ARGS="${CVS_ARGS} -d $CVSROOT ${ACTION}"

# Buildup the list of to-be excluded files
RSYNC_EXCLUDES="CVSROOT/config*"

RSYNC_EXCLUDE=""
for exclude in $RSYNC_EXCLUDES ; do
    RSYNC_EXCLUDE="${RSYNC_EXCLUDE} --exclude=${exclude}"
done

# Sync up our repository with the main repository
echo "rsync'ing with $RSYNC_DIR..."

$RSYNC $RSYNC_EXCLUDE $RSYNC_ARGS $RSYNC_DIR $CVSROOT

# Checkout the main Horde module
cd `dirname $HORDE_DIR`

echo "Doing $CVS_ACTION from $LABEL in main Horde module..."

$CVSCOMMAND $CVS_ARGS -r $LABEL horde
cd $HORDE_DIR

# Check out each of the other modules specified
for MODULE in $MODULE_LIST; do
    echo "Doing $ACTION from $LABEL in $MODULE module..."
    echo $CVSCOMMAND $CVS_ARGS -r $LABEL $MODULE
    $CVSCOMMAND $CVS_ARGS -r $LABEL $MODULE
done

# Put the user back where they came from
cd $CWD
