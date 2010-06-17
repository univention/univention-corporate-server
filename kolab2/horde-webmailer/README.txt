Current logic for Kolab upstream package patches expained:
==========================================================

The script debian/upstream-pkgs.sh takes the following steps to obtain
current kolab-webclient tarballs:
## 1. checkout current kolab-webclient from kolab CVS into kolab-upstream/
## 2. look for OpenPKG .spec files in the kolab-webclient subdirectories
## 3. download upstream tarballs from http://ftp.horde.org/pub/ into horde-upstream/
## 4. untar the horde-upstream/ packages into horde-webmailer/
## 5. apply all patches from kolab-upstream/ to the repective horde-webmailer/ subdirectory 

Beware: the current script pulls CVS HEAD, maybe kolab_2_2_branch or
        kolab-server-2-2-3 would be better.

Then debian/rules should operate on the basis of the code in 'horde-webmailer'.

Note: the Kolab patches turn horde-webmailer into kolab-webclient and make use
      of a couple of PEAR und php-kolab packages -- with their own share of
      Kolab patches. Tradtitionally these are shipped as part of the
      Univention Debian-Package univention-kolab2-webclient.

