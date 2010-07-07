Current logic for Kolab upstream package patches expained:
==========================================================

The script debian/upstream-pkgs.sh takes the following steps to obtain
a current horde-webmail / kolab-webclient tarball:

## 1. checkout current kolab-webclient from kolab CVS into kolab-upstream/
## 2. look for OpenPKG .spec files in the kolab-webclient subdirectories
## 3. download upstream tarballs from http://ftp.horde.org/pub/ into horde-upstream/

the next steps are done in debian/prepare_horde-webmailer.sh and could be calld from debian/rules "prepare":

## 4. untar the horde-upstream/ packages
## 5. apply all patches from kolab-upstream/ to the repective module and move to the horde-webmail/ subdirectory
## 6. copy static Kolab config files and sub-files into target dirs
## 7. copy php.dist files where necessary
## 7.b patch the relative into an absolute path, necessary for the /etc/horde setup
## Hook templates not considered yet : hooks/horde-3.3.6/hook-delete_webmail_user.php
## 8. move usr/share/horde3/horde/* to usr/share/horde3/
## 9. generate Config sub-files from Kolab Templates for manual inspection  -- no enabled yet
## 10. build new horde-webmail.tar.gz


Beware: the current script pulls CVS HEAD, maybe kolab_2_2_branch or
        kolab-server-2-2-x (x>4) would be better.

Then debian/rules should operate on the basis of the code in 'horde-webmail.tar.gz'.

Note: the Kolab patches turn horde-webmail into kolab-webclient and make use
      of a couple of PEAR und php-kolab packages -- with their own share of
      Kolab patches. Tradtitionally these are shipped as part of the
      Univention Debian-Package univention-kolab2-webclient.

Kolab changed the method for OEM configuration adjustments:
===========================================================
univention-kolab2-webclient/kolab-upstream/server/pear/Horde_Framework/patches/Horde_Framework-0.0.2dev20091215/t_horde_HK__MP_ConfdStyleConfigurationOverride.diff ( http://bugs.horde.org/ticket/8172 )
Horde_Framework itself is not installed since it collides with server/kolab-webclient/horde included in the horde-webmailer debian package.
Since this patch has not made it yet into server/kolab-webclient/horde, it is copied into horde-webmailer/debian/patches.

## The upstream Horde packages now also make use of sub-files:
# horde-webmail/config/registry.d/README explains:
This directory can hold registry configuration snippets. Any PHP file (*.php)
is read; all other files are ignored and so are for information only. Snippets
can contain anything that would go in registry.php - one or more applications,
tree blocks, conditionals, etc.

Scripts that install or update files in this directory should always touch()
the registry.d directory after completion to ensure that its modification time
has changed; that way Horde will know to drop any cached configuration
information.

## The new upstream Horde packages ship conf.php etc. only as .php.dist
* horde-upstream/horde-3.3.6.tar.gz
* horde-upstream/kronolith-h3-2.3.3.tar.gz
* ...

## Kolab configuration files are shiped in three forms:
# 1. static Horde php.dist files that are installed as .php to provide "something"
# 2. static Kolab config files and subfiles
shell# ls kolab-upstream/server/kolab-webclient/*/configuration/*/*.php
kolab-upstream/server/kolab-webclient/horde/configuration/horde-3.3.6/conf.php
kolab-upstream/server/kolab-webclient/horde/configuration/horde-3.3.6/10-kolab_conf_base.php
kolab-upstream/server/kolab-webclient/horde/configuration/horde-3.3.6/10-kolab_hooks_base.php
kolab-upstream/server/kolab-webclient/horde/configuration/horde-3.3.6/10-kolab_prefs_base.php
kolab-upstream/server/kolab-webclient/dimp/configuration/dimp-1.1.4/conf.php
kolab-upstream/server/kolab-webclient/dimp/configuration/dimp-1.1.4/10-kolab_menu_base.php
kolab-upstream/server/kolab-webclient/dimp/configuration/dimp-1.1.4/10-kolab_servers_base.php
kolab-upstream/server/kolab-webclient/imp/configuration/imp-4.3.6/conf.php
kolab-upstream/server/kolab-webclient/imp/configuration/imp-4.3.6/10-kolab_conf_base.php
kolab-upstream/server/kolab-webclient/imp/configuration/imp-4.3.6/10-kolab_hooks_base.php
kolab-upstream/server/kolab-webclient/imp/configuration/imp-4.3.6/10-kolab_servers_base.php
kolab-upstream/server/kolab-webclient/imp/configuration/imp-4.3.6/11-kolab_conf_imp.php
kolab-upstream/server/kolab-webclient/ingo/configuration/ingo-1.2.3/conf.php
kolab-upstream/server/kolab-webclient/ingo/configuration/ingo-1.2.3/10-kolab_backends_base.php
kolab-upstream/server/kolab-webclient/ingo/configuration/ingo-1.2.3/10-kolab_conf_base.php
kolab-upstream/server/kolab-webclient/kronolith/configuration/kronolith-2.3.3/conf.php
kolab-upstream/server/kolab-webclient/kronolith/configuration/kronolith-2.3.3/10-kolab_conf_base.php
kolab-upstream/server/kolab-webclient/mimp/configuration/mimp-1.1.3/conf.php
kolab-upstream/server/kolab-webclient/mnemo/configuration/mnemo-2.2.3/conf.php
kolab-upstream/server/kolab-webclient/mnemo/configuration/mnemo-2.2.3/10-kolab_conf_base.php
kolab-upstream/server/kolab-webclient/nag/configuration/nag-2.3.4/conf.php
kolab-upstream/server/kolab-webclient/nag/configuration/nag-2.3.4/10-kolab_conf_base.php
kolab-upstream/server/kolab-webclient/turba/configuration/turba-2.3.3/conf.php
kolab-upstream/server/kolab-webclient/turba/configuration/turba-2.3.3/10-kolab_conf_base.php
kolab-upstream/server/kolab-webclient/turba/configuration/turba-2.3.3/10-kolab_sources_base.php
# 3. Kolab templates for Installation with kolabconf
#    these are not considered yet and their core settings
#    should be provided by UCR templates in univention-kolab2-webclient
shell# ls kolab-upstream/server/kolab-webclient/*/templates/*/*.template
