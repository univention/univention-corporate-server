#!/bin/sh
# $Horde: horde/scripts/update_horde.sh,v 1.2 2002/07/08 23:46:42 chuck Exp $
#
# update_horde.sh - Marcus I. Ryan <marcus@riboflavin.net>
#
# I wrote this script for me, so there isn't really much documentation.
# I'll explain the few things that come to mind:
#
# Summary: This script facilitates the updating and/or installation of horde
# and its applications.
# * Create a temporary directory to hold a new install
# * Make a patch file of the various *.dist files and their non-dist versions
# * Copy the existing install or download fresh from CVS
# * Apply the patch made earlier
# * Make a backup of the existing install
# * Make the new download the current install
#
# Options/Variables:
# NUM_SLASHES - Since I'm too lazy to code a better way, this is the number
#               of slashes to remove from the path to make the patch work
#               relative to the temporary directory.
# NUM_BACKUPS - How many backups do we want to keep?
# WEBDIR      - The actual install directory (this is the live version)
# BACKUPDIR   - Where do we want to keep the backups
# TMPDIR      - Where do we build the new version to install
# RELEASES    - A list of the various "releases" we've defined
# <rel>_dir   - The name of the "horde" dir (usually horde) for release <rel>
# <rel>_ver   - A list of the various CVS distributions for realease <ver>
#               and the CVS branches to download.  See examples.
#
# WARNING: I do not currently have it set up to check if a patch fails 
#          completely.  This is not usually a problem, but if a *.dist file
#          is drastically updated it has been known to cause problems.
#          If you use this script, please keep an eye out for this.  That
#          said, I updated both my installs (release and head) with it
#          over 50 times before I finally had a problem.

trim () {
  echo $@
}

######## CONFIGURATION ########

### MISC. OPTIONS ###
NUM_SLASHES=4
NUM_BACKUPS=5

### DIRECTORIES ###
WEBDIR=/usr/local/www
BACKUPDIR=/usr/local/src
TMPDIR=/usr/local/src

### RELEASES ###
RELEASES="release head"

# For each release, we need _dir and _ver settings

#This is the "array" of applications and versions to get
release_dir=horde
release_ver="
        horde-RELENG_2
	imp-RELENG_3
	turba-RELENG_1
	kronolith-RELENG_1
	nag-RELENG_1
	mnemo-RELENG_1
"
release_ver=`trim ${release_ver}`

head_dir=horde.head
head_ver="
        horde-HEAD
	imp-HEAD
	turba-HEAD
	gollem-HEAD
	kronolith-HEAD
	jonah-HEAD
	troll-HEAD
	nag-HEAD
	nic-HEAD
        mnemo-HEAD
	passwd-HEAD
	sam-HEAD
"
head_ver=`trim ${head_ver}`

######## MAIN CODE ########

APPVER=$head_ver
HORDEDIR=$head_dir

# check to see if any command line args are specified
for arg in $*
do
  name=${arg%%=*}
  name=${name##--}
  value=${arg##*=}
  if [ "$name" = "release" ]; then
    APPVER=`eval echo '$'$value'_ver'`
    HORDEDIR=`eval echo '$'$value'_dir'`
    if [ "$APPVER" = "" -o "$HORDEDIR" = "" ]; then
      echo "ERROR: No settings for release $value"
    fi
    continue
  fi
  echo "Unknown option $arg ('$name' = '$value')"
  exit 1
done

echo "Verifying distribution list"
if [ ! "${APPVER%%[- ]*}" = "horde" ]; then
  echo "  horde MUST be the first item in the APPVER list!"
  exit 1
fi

echo "Determining temporary directory..."
EXISTS=`ls -d ${TMPDIR}/${HORDEDIR}.TMP.[0-9]* | head -1`
TMPDIR="${TMPDIR}/${HORDEDIR}.TMP.$$"

if [ ! -z ${EXISTS} ]; then
  echo "  Found an existing (aborted?) update of horde (${EXISTS})."
  read -p "  Should I use it? [Yes]" USE_EXISTING
  case ${USE_EXISTING} in
  [Nn]|[Nn][Oo])
    read -p "  Should I delete ${EXISTS}? [Yes]" DELETE_EXISTING
    case ${DELETE_EXISTING} in
    [Nn]|[Nn][Oo])
      echo "    Not deleting ${EXISTS}"
      ;;
    *)
      echo "    Deleting ${EXISTS}"
      rm -rf ${EXISTS}
      ;;
    esac
    ;;
  *)
    TMPDIR=${EXISTS}
    ;;
  esac
  unset USE_EXISTING
fi
if [ -e ${TMPDIR} ]; then
  echo "  Using ${TMPDIR}"
else
  echo "  Creating new directory ${TMPDIR}"
  mkdir ${TMPDIR}
  if [ ! -e ${TMPDIR} ]; then
    echo "ERROR: Couldn't create ${TMPDIR}"
    exit 1
  fi
fi

echo "Creating config patch file from existing horde"
if [ -e ${TMPDIR}/update.patch ]; then
  read -p "  This directory includes a patch. Use it? [Yes]" USE_EXISTING
  case ${USE_EXISTING} in
  [Nn]|[Nn][Oo])
    echo "  Clearing existing update.patch"
    rm -f ${TMPDIR}/update.patch || exit 1
    ;;
  esac
  unset USE_EXISTING
fi
if [ ! -e ${TMPDIR}/update.patch ]; then
  if [ ! -e ${WEBDIR}/${HORDEDIR} ]; then
    echo "  No existing horde distribution found.  Can't create patch."
  else
    read -p "  Do you want to create a patch from the existing install? [Yes]" MAKE_PATCH
    case ${MAKE_PATCH} in
    [Nn]|[Nn][Oo])
      echo "  Not creating a patch"
      ;;
    *)
      echo "  Creating patch...this could take a bit..."
      find ${WEBDIR}/${HORDEDIR} -type f -name \*.dist -print \
       | perl -ne 's/\.dist[\r\n]*//; print "$_.dist\n$_\n";' \
       | xargs -n 2 diff -u > ${TMPDIR}/update.patch
      ;;
    esac
    unset MAKE_PATCH
  fi
fi

if [ -e "${WEBDIR}/${HORDEDIR}" ]; then
  read -p "Do you want to fetch new (N) or update (U)? [U] " FETCH_NEW
else
  FETCH_NEW=new
fi

case ${FETCH_NEW} in
  [Nn]|[Nn][Ee][Ww])
    for APP in ${APPVER}
    {
      app=${APP%%-*}
      rel=${APP##*-}
      if [ ${app} = ${APP} ]; then
        echo "  No release specified...assuming HEAD"
        rel=HEAD
      fi

      case ${app} in
        horde)
          APPDIR=${TMPDIR}
          EXISTDIR="${TMPDIR}/${HORDEDIR}"
          ;;
        *)
          APPDIR=${TMPDIR}/${HORDEDIR}
          EXISTDIR="${TMPDIR}/${HORDEDIR}/${app}"
          ;;
      esac

      if [ -e $EXISTDIR ]; then
        case ${REGET} in
        [Aa]|[Aa][Ll][Ll])
          echo "  Removing existing ${APPDIR}/${app}...";
          rm -rf ${APPDIR}/${app}
          echo "  Retrieving ${app} $rel..."
          cd ${APPDIR}
          cvs -Q -z3 -d :pserver:cvsread@anoncvs.horde.org:/repository co \
           -r $rel ${app}
          ;;
        [Nn][Oo][Nn][Ee])
          REGET="NONE"
          echo "  Using existing ${APPDIR}/${app}"
          ;;
        *)
          echo "  ${app} exists. Should I get ${app} anyway?"
          if [ "${app}" = "horde" ]; then
            echo "  NOTE: regetting horde does not clear out any existing files"
          fi
          read -p "   [Y]es/[N]o/[A]ll/None (default None): " REGET
          case ${REGET} in
          [Yy]|[Yy][Ee][Ss]|[Aa]|[Aa][Ll][Ll])
            echo "  Removing existing ${APPDIR}/${app}...";
            rm -rf ${APPDIR}/${app}
            echo "  Retrieving ${app} $rel..."
            cd ${APPDIR}
            cvs -Q -z3 -d :pserver:cvsread@anoncvs.horde.org:/repository co \
             -r $rel ${app}
            ;;
          [Nn]|[Nn][Oo])
            echo "  Using existing ${APPDIR}/${app}"
            ;;
          *)
            echo "  Using existing ${APPDIR}/${app}"
            REGET=NONE
            ;;
          esac
          ;;
        esac
      else
        echo -n "  Retrieving ${app} $rel..."
        cd ${APPDIR}
        cvs -Q -z3 -d :pserver:cvsread@anoncvs.horde.org:/repository co \
         -r $rel ${app}
	echo "done"
      fi
      if [ "$app" = "horde" -a "$HORDEDIR" != "horde" ]; then
	echo "  Moving ${TMPDIR}/horde to ${TMPDIR}/${HORDEDIR}"
        mv ${TMPDIR}/horde ${TMPDIR}/${HORDEDIR}
      fi
    }
    ;;
  *)
    mkdir ${TMPDIR}/${HORDEDIR}
    cp -Rpf ${WEBDIR}/${HORDEDIR}/* ${TMPDIR}/${HORDEDIR}
    cd ${TMPDIR}/${HORDEDIR}
    cvs update -PdC
    ;;
esac

echo "Putting default config files in place..."
if [ -e ${TMPDIR}/${HORDEDIR}/config/conf.php ]; then
  echo "  I have found some configuration files already in place."
  echo "  If you are updating an existing installation this is normal."
  echo "  NOTE: If some have been copied and others not, horde will be broken."
  read -p "   Should I copy .dist files anyway? [Yes] " USE_EXISTING
  #The phrasing of the question means USE_EXISTING from the read is backwards
  # but it seems better to confuse the programmer than the user...
  case ${USE_EXISTING} in
   [Nn]|[Nn][Oo])
    USE_EXISTING=YES
    ;;
  *)
    USE_EXISTING=NO
    ;;
  esac
fi
if [ "${USE_EXISTING:=NO}" = "NO" ]; then
  echo "  Copying *.dist files..."
  find ${TMPDIR}/${HORDEDIR} -type f -name \*.dist -print \
   | perl -ne 'print "$_"; s/\.dist//; print "$_"' \
   | xargs -n 2 cp
fi

echo "Applying patch..."
echo "  Clearing out any old reject files..."
find ${TMPDIR} -name \*.rej -type f -exec rm {} \; -print

if [ ! -e ${TMPDIR}/update.patch ]; then
  echo "  I can't seem to find the patch file ${TMPDIR}/update.patch!"
  read -p "  Do you want me to load all config files in $EDITOR? [No]" EDIT
  case ${EDIT} in
  [Yy]|[Yy][Ee][Ss])
    find ${TMPDIR}/${HORDEDIR} -type f -name \*.dist \
     | perl -ne 's/\.dist[\r\n]*//; print "$_\n";' \
     | xargs -n 2 echo $EDITOR > ${TMPDIR}/edit.sh
    sh ${TMPDIR}/edit.sh
    rm ${TMPDIR}/edit.sh
    ;;
  *)
    echo "  WARNING: You need to change the config files later!"
    ;;
  esac
else
  if [ "${USE_EXISTING}" = "YES" ]; then
    echo "  We kept the modified configuration files."
    read -p "  Should we still apply the patch? [No] " PATCH
    case ${PATCH} in
    [Yy]|[Yy][Ee][Ss])
      PATCH=YES
      ;;
    *)
      PATCH=NO
      ;;
    esac
  fi

  if [ "${PATCH:=YES}" = "YES" ]; then
    echo "  running patch"
    cd ${TMPDIR}
    if [ `patch -f -p${NUM_SLASHES} -s < ${TMPDIR}/update.patch` ]; then
      echo "  Patch applied successfully"
    else
      find ${TMPDIR}/${HORDEDIR} -type f -name \*.rej \
       | perl -ne 's/\.rej[\r\n]*//; print "$_.rej\n$_\n"; ' \
       | xargs -n 2 echo $EDITOR > ${TMPDIR}/edit.sh
      sh ${TMPDIR}/edit.sh
      rm ${TMPDIR}/edit.sh
    fi
  fi
fi

read -p "Are you ready to put the new CVS into production? [Yes]" PROD
case ${PROD} in
[Nn]|[Nn][Oo])
  echo "${TMPDIR} has not been put in production."
  ;;
*)
  if [ -e ${WEBDIR}/${HORDEDIR} ]; then
    i=1
    while [ ${i} != ${NUM_BACKUPS} ]
    do
      if [ ! -e ${BACKUPDIR}/${HORDEDIR}.${i} ]; then
        break;
      fi
      i=$((${i}+1))
    done

    if [ ${i} = ${NUM_BACKUPS} ] && [ -e ${BACKUPDIR}/${HORDEDIR}.${i} ]; then
      echo "  Removing oldest backup directory (${BACKUPDIR}/${HORDEDIR}.${i})"
      rm -rf ${BACKUPDIR}/${HORDEDIR}.${i} || exit 1
    fi

    while [ ${i} != 1 ]
    do
      echo "  Moving ${BACKUPDIR}/${HORDEDIR}.$((${i}-1)) to ${BACKUPDIR}/${HORDEDIR}.${i}"
      mv ${BACKUPDIR}/${HORDEDIR}.$((${i}-1)) ${BACKUPDIR}/${HORDEDIR}.${i} || exit 1
      i=$((${i}-1))
    done

    echo "  Moving ${WEBDIR}/${HORDEDIR} to ${BACKUPDIR}/${HORDEDIR}.1"
    mv ${WEBDIR}/${HORDEDIR} ${BACKUPDIR}/${HORDEDIR}.1 || exit 1

    echo "  Moving ${TMPDIR}/${HORDEDIR} ${WEBDIR}/${HORDEDIR}"
    mv ${TMPDIR}/${HORDEDIR} ${WEBDIR}/${HORDEDIR} || exit 1

    echo "  Removing ${TMPDIR}"
    rm -rf ${TMPDIR}

    echo "New CVS horde is now in production!"
  else
    echo "${WEBDIR}/${HORDEDIR} does not exist.  Copying ${TMPDIR}/${HORDEDIR} to ${WEBDIR}/${HORDEDIR}"
    cp ${TMPDIR}/${HORDEDIR} ${WEBDIR}/${HORDEDIR}
  fi
  ;;
esac
