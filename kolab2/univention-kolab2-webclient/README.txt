Current logic for Kolab upstream package patches expained:
==========================================================

The script debian/upstream-pkgs.sh takes the following steps to obtain
current Kolab tarballs:
## 1. checkout current kolab pear and php-kolab from kolab CVS
## 2. look for package.info files in the pear and php-kolab directories
## 3. download upstream tarballs (from sourceurl in package.info), usually:
   * http://pear.php.net/						for php tarballs
   * http://pear.horde.org/						for Kolab_* tarballs
   * http://files.kolab.org/incoming/wrobel/	for Horde_* tarballs
## 4. apply all patches from kolab CVS for the repective package 
## 5. write the final tarballs to 'kolab-php-lib' directory

Beware: the current script pulls CVS HEAD, maybe kolab_2_2_branch or kolab-server-2-2-3 would be better.

Then debian/rules should operate on the basis of the tarballs in 'kolab-php-lib'.


Interesting from the point of OEM configuration adjustments:
============================================================
kolab-upstream/server/pear/Horde_Framework/patches/Horde_Framework-0.0.2dev20091215/t_horde_HK__MP_ConfdStyleConfigurationOverride.diff
http://bugs.horde.org/ticket/8172

