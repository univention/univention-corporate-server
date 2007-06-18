<?php
/**
 * $Horde: horde/config/mime_drivers.php.dist,v 1.92 2004/04/12 22:49:22 slusarz Exp $
 *
 * Decide which output drivers you want to activate for all Horde
 * applications. Individual Horde applications can override these settings
 * in their config/mime_drivers.php files.
 *
 * The available drivers are:
 * --------------------------
 * deb            Debian packages
 * enriched       Enriched text format
 * enscript       GNU enscript
 * html           HTML data
 * images         Image files
 * msword         Microsoft Word files via wvHtml
 * msexcel        Microsoft Excel files via xlhtml
 * mspowerpoint   Microsoft Powerpoint files via ppthtml
 * ooo            OpenOffice.org/StarOffice Documents
 * pdf            Portable Document Format (PDF) files
 * php            The internal PHP4 syntax highlighting engine
 * plain          Return text, with links made clickable and other HTML
 *                filtered out
 * rar            RAR archives
 * report         Report messages (RFC 3452)
 * rfc822         Digested messages (RFC 2046 [5.2.1])
 * richtext       Richtext text format (RFC 1341 [7.1.3])
 * rpm            RPM packages
 * security       Secure multiparts (RFC 1847)
 * srchighlite    Source Highlight
 * tgz            Tarballs, including gzipped ones
 * tnef           MS-TNEF attachments
 * vcard          vCards
 * webcpp         Web C Plus Plus
 * zip            Zip files
 */
$mime_drivers_map['horde']['registered'] = array(
    'deb', 'enriched', 'enscript', 'html', 'images', 'msword', 'msexcel',
    'mspowerpoint', 'ooo', 'pdf', 'php', 'plain', 'rar', 'report',
    'richtext', 'rpm', 'security', 'srchighlite', 'tgz', 'tnef', 'vcard',
    'webcpp', 'zip');


/**
 * If you want to specifically override any MIME type to be handled by
 * a specific driver, then enter it here.  Normally, this is safe to
 * leave, but it's useful when multiple drivers handle the same MIME
 * type, and you want to specify exactly which one should handle it.
 */
$mime_drivers_map['horde']['overrides'] = array();


/**
 * Driver specific settings. Here, you have to configure each driver
 * which you chose to activate above. Default settings have been
 * filled in for them, and if you haven't activated it, then just
 * leave it as it is - it won't get loaded.
 *
 * The 'handles' setting below shouldn't be changed in most
 * circumstances. It registers a set of MIME type that the driver can
 * handle. The 'x-extension' MIME type is a special one to Horde that
 * maps a file extension to a MIME type. It's useful when you know
 * that all files ending in '.c' are C files, for example. You can set
 * the MIME subtype to '*' to match all possible subtypes
 * (i.e. 'image/*').
 *
 * The 'icons' entry is for the driver to register various icons for
 * the MIME types it handles. The array consists of a 'default' icon
 * for that driver, and can also include specific MIME-types which can
 * have their own icons. You can set the MIME subtype to '*' to match
 * all possible subtypes (i.e. 'image/*').
 */

/**
 * Default driver settings
 */
$mime_drivers['horde']['default']['icons'] = array(
    'default'                       => 'text.gif',
    'audio/*'                       => 'audio.gif',
    'message/*'                     => 'mail.gif',
    'unknown/*'                     => 'binary.gif',
    'video/*'                       => 'video.gif',
    'application/pgp-signature'     => 'encryption.gif',
    'application/x-pkcs7-signature' => 'encryption.gif',
    'application/octet-stream'      => 'binary.gif');


/**
 * Plain text driver settings
 */
$mime_drivers['horde']['plain']['handles'] = array(
    'text/*');
$mime_drivers['horde']['plain']['icons'] = array(
    'default' => 'text.gif');


/**
 * PHP driver settings
 */
$mime_drivers['horde']['php']['handles'] = array(
    'application/x-php', 'x-extension/phps',
    'x-extension/php3s', 'application/x-httpd-php',
    'application/x-httpd-php3', 'application/x-httpd-phps');
$mime_drivers['horde']['php']['icons'] = array(
    'default' => 'php.gif');


/**
 * Enriched text driver settings
 */
$mime_drivers['horde']['html']['inline'] = false;
$mime_drivers['horde']['html']['handles'] = array(
    'text/html');
$mime_drivers['horde']['html']['icons'] = array(
    'default' => 'html.gif');


/**
 * Enriched text driver settings
 */
$mime_drivers['horde']['enriched']['inline'] = true;
$mime_drivers['horde']['enriched']['handles'] = array(
    'text/enriched');
$mime_drivers['horde']['enriched']['icons'] = array(
    'default' => 'text.gif');


/**
 * Richtext text driver settings
 */
$mime_drivers['horde']['richtext']['inline'] = true;
$mime_drivers['horde']['richtext']['handles'] = array(
    'text/richtext');
$mime_drivers['horde']['richtext']['icons'] = array(
    'default' => 'text.gif');


/**
 * Web C Plus Plus driver settings
 * http://webcpp.sourceforge.net/
 */
$mime_drivers['horde']['webcpp']['location'] = 'C:\Program Files\Jeffrey Bakker\webcpp\webcpp.exe';
$mime_drivers['horde']['webcpp']['inline'] = true;
$mime_drivers['horde']['webcpp']['handles'] = array(
    'text/xml', 'text/sgml', 'application/xml',
    'application/x-sh', 'application/x-javascript', 'application/x-tcl',
    'x-extension/asm', 'application/x-asp', 'x-extension/bas',
    'x-extension/cs', 'text/x-csrc', 'x-extension/rc',
    'text/x-c++src', 'text/x-c++src', 'text/x-c++src',
    'text/x-chdr', 'x-extension/bat', 'text/x-fortran',
    'x-extension/f77', 'x-extension/f90', 'x-extension/for',
    'x-extension/ftn', 'text/x-java', 'application/x-javascript',
    'text/sgml', 'text/xml', 'text/x-pascal',
    'application/x-cgi', 'application/x-perl', 'application/x-python',
    'text/x-sql', 'text/x-tcl',
    'application/x-shellscript', 'x-extension/vhd', 'x-extension/vhdl');
$mime_drivers['horde']['webcpp']['icons'] = array(
    'default'                  => 'text.gif',
    'text/xml'                 => 'xml.gif',
    'text/x-csrc'              => 'source-c.gif',
    'text/x-chdr'              => 'source-h.gif',
    'text/x-java'              => 'source-java.gif',
    'application/x-javascript' => 'script-js.gif');

/**
 * Source-Highlight driver settings
 * http://www.gnu.org/software/src-highlite/
 */
$mime_drivers['horde']['srchighlite']['location'] = 'C:\Program Files\src-highlite\bin\source-highlight.exe';
$mime_drivers['horde']['srchighlite']['inline'] = false;
$mime_drivers['horde']['srchighlite']['handles'] = array(
    'text/x-csrc', 'text/x-c++src', 'text/x-java',
    'application/x-perl', 'application/x-python', 'text/x-c++src',
    'text/cpp');
$mime_drivers['horde']['srchighlite']['icons'] = array(
    'default'                  => 'text.gif',
    'text/x-csrc'              => 'source-c.gif',
    'text/x-c++src'            => 'source-c.gif',
    'text/cpp'                 => 'source-c.gif',
    'text/x-java'              => 'source-java.gif');

/**
 * GNU Enscript driver settings
 */
$mime_drivers['horde']['enscript']['location'] = '/usr/bin/enscript';
$mime_drivers['horde']['enscript']['inline'] = false;
$mime_drivers['horde']['enscript']['handles'] = array(
    'application/x-shellscript', 'application/x-javascript',
    'application/x-perl', 'application/xml', 'text/xml',
    'text/diff', 'text/x-diff', 'text/x-patch', 'text/x-csrc',
    'x-extension/cs', 'text/x-java', 'text/x-chdr', 'text/x-c++src',
    'text/x-c++hdr', 'x-extension/vhd', 'x-extension/vhdl', 'text/x-sql',
    'x-extension/vb', 'x-extension/vba', 'text/x-emacs-lisp');
$mime_drivers['horde']['enscript']['icons'] = array(
    'default'                  => 'text.gif',
    'text/xml'                 => 'xml.gif',
    'application/xml'          => 'xml.gif',
    'text/x-csrc'              => 'source-c.gif',
    'text/x-chdr'              => 'source-h.gif',
    'text/x-java'              => 'source-java.gif',
    'application/x-javascript' => 'script-js.gif');


/**
 * Tar driver settings
 * To access gzipped files, the zlib library must have been built into PHP
 * (with the --with-zlib option).
 */
$mime_drivers['horde']['tgz']['inline'] = true;
$mime_drivers['horde']['tgz']['handles'] = array(
    'application/x-compressed-tar',
    'application/x-tar',
    'application/x-tgz',
    'application/x-gzip',
    'application/x-gtar',
    'application/gzip',
    'application/x-gzip-compressed');
$mime_drivers['horde']['tgz']['icons'] = array(
    'default' => 'compressed.gif');


/**
 * Zip file driver settings
 */
$mime_drivers['horde']['zip']['inline'] = true;
$mime_drivers['horde']['zip']['handles'] = array(
    'application/zip',
    'application/x-compressed',
    'application/x-zip-compressed');
$mime_drivers['horde']['zip']['icons'] = array(
    'default' => 'compressed.gif');


/**
 * RAR archive driver settings
 */
$mime_drivers['horde']['rar']['inline'] = true;
$mime_drivers['horde']['rar']['handles'] = array(
    'application/x-rar',
    'application/x-rar-compressed');
$mime_drivers['horde']['rar']['icons'] = array(
    'default' => 'compressed.gif');


/**
 * MS Word driver settings
 * This driver requires wvWare to be installed.
 * wvWare homepage: http://wvware.sourceforge.net/
 *
 * The 'location' entry should point to the 'wvHtml' program, NOT the
 * 'wvWare' program.
 */
$mime_drivers['horde']['msword']['location'] = '/usr/bin/wvHtml';
$mime_drivers['horde']['msword']['inline'] = false;
$mime_drivers['horde']['msword']['handles'] = array(
    'application/msword',
    'application/rtf',
    'text/rtf');
$mime_drivers['horde']['msword']['icons'] = array(
    'default' => 'msword.gif');


/**
 * MS Excel driver settings
 * This driver requires xlhtml to be installed.
 * xlhtml homepage: http://chicago.sourceforge.net/xlhtml/
 */
$mime_drivers['horde']['msexcel']['location'] = '/usr/local/bin/xlhtml';
$mime_drivers['horde']['msexcel']['inline'] = false;
$mime_drivers['horde']['msexcel']['handles'] = array(
    'application/vnd.ms-excel',
    'application/msexcel',
    'application/x-msexcel');
$mime_drivers['horde']['msexcel']['icons'] = array(
    'default' => 'msexcel.gif');


/**
 * MS Powerpoint driver settings
 * This driver requires ppthtml, included with xlhtml, to be installed.
 * xlhtml homepage: http://chicago.sourceforge.net/xlhtml/
 */
$mime_drivers['horde']['mspowerpoint']['location'] = '/usr/local/bin/ppthtml';
$mime_drivers['horde']['mspowerpoint']['inline'] = false;
$mime_drivers['horde']['mspowerpoint']['handles'] = array(
    'application/vnd.ms-powerpoint',
    'application/mspowerpoint');
$mime_drivers['horde']['mspowerpoint']['icons'] = array(
    'default' => 'mspowerpoint.gif');


/**
 * vCard driver settings
 */
$mime_drivers['horde']['vcard']['handles'] = array(
    'text/x-vcard',
    'text/x-vcalendar');
$mime_drivers['horde']['vcard']['icons'] = array(
    'default' => 'vcard.gif');


/**
 * RPM driver settings
 */
$mime_drivers['horde']['rpm']['location'] = '/usr/bin/rpm';
$mime_drivers['horde']['rpm']['inline'] = false;
$mime_drivers['horde']['rpm']['handles'] = array(
    'application/x-rpm');
$mime_drivers['horde']['rpm']['icons'] = array(
    'default' => 'rpm.gif');


/**
 * Debian package driver settings
 */
$mime_drivers['horde']['deb']['location'] = '/usr/bin/dpkg';
$mime_drivers['horde']['deb']['inline'] = false;
$mime_drivers['horde']['deb']['handles'] = array(
    'application/x-deb',
    'application/x-debian-package');
$mime_drivers['horde']['deb']['icons'] = array(
    'default' => 'deb.gif');


/**
 * Secure multiparts (RFC 1847)
 */
$mime_drivers['horde']['security']['inline'] = true;
$mime_drivers['horde']['security']['handles'] = array(
    'multipart/encrypted', 'multipart/signed');
$mime_drivers['horde']['security']['icons'] = array(
    'default' => 'encryption.gif');


/**
 * Image settings
 */
$mime_drivers['horde']['images']['inline'] = false;
$mime_drivers['horde']['images']['handles'] = array(
    'image/*');
$mime_drivers['horde']['images']['icons'] = array(
    'default' => 'image.gif');


/**
 * MS-TNEF Attachment (application/ms-tnef) settings
 */
$mime_drivers['horde']['tnef']['inline'] = false;
$mime_drivers['horde']['tnef']['handles'] = array(
    'application/ms-tnef');
$mime_drivers['horde']['tnef']['icons'] = array(
    'default' => 'text.gif');


/**
 * Digest message (RFC 2046 [5.2.1]) settings
 */
$mime_drivers['horde']['rfc822']['inline'] = false;
$mime_drivers['horde']['rfc822']['handles'] = array(
    'message/rfc822');
$mime_drivers['horde']['rfc822']['icons'] = array(
    'default' => 'mail.gif');


/**
 * Report messages (RFC 3452)
 */
$mime_drivers['horde']['report']['inline'] = true;
$mime_drivers['horde']['report']['handles'] = array(
    'multipart/report');
$mime_drivers['horde']['report']['icons'] = array(
    'default' => 'mail.gif');


/**
 * OpenOffice.org/StarOffice settings
 */
$mime_drivers['horde']['ooo']['inline'] = false;
$mime_drivers['horde']['ooo']['handles'] = array(
    'application/vnd.sun.xml.calc',
    'application/vnd.sun.xml.calc.template',
    'application/vnd.sun.xml.draw',
    'application/vnd.sun.xml.draw.template',
    'application/vnd.sun.xml.impress',
    'application/vnd.sun.xml.impress.template',
    'application/vnd.sun.xml.math',
    'application/vnd.sun.xml.writer',
    'application/vnd.sun.xml.writer.global',
    'application/vnd.sun.xml.writer.template',
    'application/vnd.stardivision.calc',
    'application/vnd.stardivision.draw',
    'application/vnd.stardivision.impress',
    'application/vnd.stardivision.math',
    'application/vnd.stardivision.writer');
$mime_drivers['horde']['ooo']['icons'] = array(
    'default' => 'ooo_calc.gif',
    'application/vnd.sun.xml.calc'             => 'ooo_calc.gif',
    'application/vnd.stardivision.calc'        => 'ooo_calc.gif',
    'application/vnd.sun.xml.calc.template'    => 'ooo_calc.gif',
    'application/vnd.sun.xml.draw'             => 'ooo_draw.gif',
    'application/vnd.stardivision.draw'        => 'ooo_draw.gif',
    'application/vnd.sun.xml.draw.template'    => 'ooo_draw.gif',
    'application/vnd.sun.xml.impress'          => 'ooo_impress.gif',
    'application/vnd.stardivision.impress'     => 'ooo_impress.gif',
    'application/vnd.sun.xml.impress.template' => 'ooo_impress.gif',
    'application/vnd.sun.xml.math'             => 'ooo_math.gif',
    'application/vnd.stardivision.math'        => 'ooo_math.gif',
    'application/vnd.sun.xml.writer'           => 'ooo_writer.gif',
    'application/vnd.stardivision.writer'      => 'ooo_writer.gif',
    'application/vnd.sun.xml.writer.global'    => 'ooo_writer.gif',
    'application/vnd.sun.xml.writer.template'  => 'ooo_writer.gif');


/**
 * Portable Document Format (PDF) files
 * YOU SHOULD NOT NORMALLY ALTER THIS SETTING.
 */
$mime_drivers['horde']['pdf']['inline'] = false;
$mime_drivers['horde']['pdf']['handles'] = array(
    'application/pdf');
$mime_drivers['horde']['pdf']['icons'] = array(
    'default' => 'pdf.gif');
