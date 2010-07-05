<?php
/**
 * $Horde: horde/config/mime_drivers.php.dist,v 1.97.6.14 2009-11-24 19:53:30 slusarz Exp $
 *
 * Decide which output drivers you want to activate for all Horde
 * applications. Individual Horde applications can override these settings
 * in their config/mime_drivers.php files.
 *
 * The available drivers are:
 * --------------------------
 * audio          Audio files
 * css            CSS Styles
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
 * rtf            RTF documents via unrtf
 * security       Secure multiparts (RFC 1847)
 * simple         Output text without modification
 * smil           SMIL documents
 * srchighlite    Source Highlight
 * tgz            Tarballs, including gzipped ones
 * tnef           MS-TNEF attachments
 * vcard          vCards
 * webcpp         Web C Plus Plus
 * wordperfect    WordPerfect documents via wpd2html
 * zip            Zip files
 */
$mime_drivers_map['horde']['registered'] = array(
    'audio',
    'css',
    'enriched',
    'html',
    'images',
    'ooo',
    'pdf',
    'php',
    'plain',
    'rar',
    'report',
    'rfc822',
    'richtext',
    'security',
    'simple',
    'smil',
    'tgz',
    'tnef',
    'vcard',
    'zip',
    /* The following mime drivers require external applications to be
     * installed and are disabled by default. */
    // 'deb',
    // 'enscript',
    // 'msword',
    // 'msexcel',
    // 'mspowerpoint',
    // 'rpm',
    // 'rtf',
    // 'srchighlite',
    // 'webcpp',
    // 'wordperfect',
);


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
    'default'                       => 'text.png',
    'message/*'                     => 'mail.png',
    'unknown/*'                     => 'binary.png',
    'video/*'                       => 'video.png',
    'application/pgp-signature'     => 'encryption.png',
    'application/x-pkcs7-signature' => 'encryption.png',
    'application/octet-stream'      => 'binary.png'
);


/**
 * Default text driver settings
 */
$mime_drivers['horde']['simple'] = array(
    'inline' => false,
    'handles' => array(
        'text/*'
    ),
    'icons' => array(
        'default' => 'text.png'
    )
);


/**
 * Plain text driver settings
 */
$mime_drivers['horde']['plain'] = array(
    'inline' => true,
    'handles' => array(
        'text/plain'
    ),
    'icons' => array(
        'default' => 'text.png'
    )
);


/**
 * Default audio driver settings
 */
$mime_drivers['horde']['audio'] = array(
    'inline' => false,
    'handles' => array(
        'audio/*'
    ),
    'icons' => array(
        'default' => 'audio.png'
    )
);


/**
 * Default smil driver settings
 */
$mime_drivers['horde']['smil'] = array(
    'inline' => true,
    'handles' => array(
        'application/smil'
    ),
    'icons' => array(
        'default' => 'video.png'
    )
);


/**
 * PHP driver settings
 */
$mime_drivers['horde']['php'] = array(
    'inline' => true,
    'handles' => array(
        'application/x-php', 'x-extension/phps', 'x-extension/php3s',
        'application/x-httpd-php', 'application/x-httpd-php3',
        'application/x-httpd-phps'
    ),
    'icons' => array(
        'default' => 'php.png'
    )
);


/**
 * CSS driver settings
 */
$mime_drivers['horde']['css'] = array(
    'inline' => true,
    'handles' => array(
        'text/css', 'x-extension/css'
    ),
    'icons' => array(
        'default' => 'html.png'
    )
);


/**
 * HTML text driver settings
 */
$mime_drivers['horde']['html'] = array(
    // NOTE: Inline HTML viewing is DISABLED by default.
    'inline' => false,
    'handles' => array(
        'text/html'
    ),
    'icons' => array(
        'default' => 'html.png'
    ),
    // Check for phishing exploits?
    'phishing_check' => true
);


/**
 * Enriched text driver settings
 */
$mime_drivers['horde']['enriched'] = array(
    'inline' => true,
    'handles' => array(
        'text/enriched'
    ),
    'icons' => array(
        'default' => 'text.png'
    )
);


/**
 * Richtext text driver settings
 */
$mime_drivers['horde']['richtext'] = array(
    'inline' => true,
    'handles' => array(
        'text/richtext'
    ),
    'icons' => array(
        'default' => 'text.png'
    )
);


/**
 * Web C Plus Plus driver settings
 * http://webcpp.sourceforge.net/
 */
$mime_drivers['horde']['webcpp'] = array(
    'location' => '/usr/bin/webcpp',
    'inline' => true,
    'handles' => array(
        'text/xml', 'text/sgml', 'application/xml', 'application/x-sh',
        'application/x-javascript', 'application/x-tcl', 'x-extension/asm',
        'application/x-asp', 'x-extension/bas', 'x-extension/cs',
        'text/x-csrc', 'x-extension/rc', 'text/x-c++src', 'text/x-c++src',
        'text/x-c++src', 'text/x-chdr', 'x-extension/bat', 'text/x-fortran',
        'x-extension/f77', 'x-extension/f90', 'x-extension/for',
        'x-extension/ftn', 'text/x-java', 'application/x-javascript',
        'text/sgml', 'text/xml', 'text/x-pascal', 'application/x-cgi',
        'application/x-perl', 'application/x-python', 'text/x-sql',
        'text/x-tcl', 'application/x-shellscript', 'x-extension/vhd',
        'x-extension/vhdl'
    ),
    'icons' => array(
        'default'                  => 'text.png',
        'text/xml'                 => 'xml.png',
        'text/x-csrc'              => 'source-c.png',
        'text/x-chdr'              => 'source-h.png',
        'text/x-java'              => 'source-java.png',
        'application/x-javascript' => 'script-js.png'
    )
);


/**
 * Source-Highlight driver settings
 * http://www.gnu.org/software/src-highlite/
 */
$mime_drivers['horde']['srchighlite'] = array(
    'location' => '/usr/bin/source-highlight',
    'inline' => true,
    'handles' => array(
        'text/x-csrc', 'text/x-c++src', 'text/x-java', 'application/x-perl',
        'application/x-python', 'text/x-c++src', 'text/cpp'
    ),
    'icons' => array(
        'default'       => 'text.png',
        'text/x-csrc'   => 'source-c.png',
        'text/x-c++src' => 'source-c.png',
        'text/cpp'      => 'source-c.png',
        'text/x-java'   => 'source-java.png'
    )
);


/**
 * GNU Enscript driver settings
 */
$mime_drivers['horde']['enscript'] = array(
    'location' => '/usr/bin/enscript',
    'inline' => true,
    'handles' => array(
        'application/x-cgi', 'application/x-shellscript',
        'application/x-javascript', 'application/x-perl', 'application/xml',
        'text/xml', 'text/diff', 'text/x-diff', 'text/x-patch', 'text/x-csrc',
        'x-extension/cs', 'text/x-java', 'text/x-chdr', 'text/x-c++src',
        'text/x-c++hdr', 'x-extension/vhd', 'x-extension/vhdl', 'text/x-sql',
        'x-extension/vb', 'x-extension/vba', 'text/x-emacs-lisp', 'text/x-tex'
    ),
    'icons' => array(
        'default'                  => 'text.png',
        'text/xml'                 => 'xml.png',
        'application/xml'          => 'xml.png',
        'text/x-csrc'              => 'source-c.png',
        'text/x-chdr'              => 'source-h.png',
        'text/x-java'              => 'source-java.png',
        'application/x-javascript' => 'script-js.png'
    )
);


/**
 * Tar driver settings
 * To access gzipped files, the zlib library must have been built into PHP
 * (with the --with-zlib option).
 */
$mime_drivers['horde']['tgz'] = array(
    'inline' => true,
    'handles' => array(
        'application/x-compressed-tar', 'application/x-tar',
        'application/x-tgz', 'application/x-gzip', 'application/x-gtar',
        'application/gzip', 'application/x-gzip-compressed'
    ),
    'icons' => array(
        'default' => 'compressed.png'
    )
);


/**
 * Zip file driver settings
 */
$mime_drivers['horde']['zip'] = array(
    'inline' => true,
    'handles' => array(
        'application/zip', 'application/x-compressed',
        'application/x-zip-compressed'
    ),
    'icons' => array(
        'default' => 'compressed.png'
    )
);


/**
 * RAR archive driver settings
 */
$mime_drivers['horde']['rar'] = array(
    'inline' => true,
    'handles' => array(
        'application/x-rar', 'application/x-rar-compressed'
    ),
    'icons' => array(
        'default' => 'compressed.png'
    )
);


/**
 * MS Word driver settings
 * This driver requires wvWare to be installed.
 * wvWare homepage: http://wvware.sourceforge.net/
 *
 * The 'location' entry should point to the 'wvHtml' program, NOT the
 * 'wvWare' program.
 *
 * Embedded images in Word documents need extra configuration. See 
 * http://wiki.horde.org/GraphicswvHtml 
 */
$mime_drivers['horde']['msword'] = array(
    'location' => '/usr/bin/wvHtml',
    'inline' => false,
    'handles' => array(
        'application/vnd.ms-word', 'application/msword'
    ),
    'icons' => array(
        'default' => 'msword.png'
    )
);


/**
 * MS Excel driver settings
 * This driver requires xlhtml to be installed.
 * xlhtml homepage: http://chicago.sourceforge.net/xlhtml/
 */
$mime_drivers['horde']['msexcel'] = array(
    'location' => '/usr/local/bin/xlhtml',
    'inline' => false,
    'handles' => array(
        'application/vnd.ms-excel', 'application/msexcel',
        'application/x-msexcel'
    ),
    'icons' => array(
        'default' => 'msexcel.png'
    )
);


/**
 * MS Powerpoint driver settings
 * This driver requires ppthtml, included with xlhtml, to be installed.
 * xlhtml homepage: http://chicago.sourceforge.net/xlhtml/
 */
$mime_drivers['horde']['mspowerpoint'] = array(
    'location' => '/usr/local/bin/ppthtml',
    'inline' => false,
    'handles' => array(
        'application/vnd.ms-powerpoint', 'application/mspowerpoint'
    ),
    'icons' => array(
        'default' => 'mspowerpoint.png'
    )
);


/**
 * vCard driver settings
 */
$mime_drivers['horde']['vcard'] = array(
    'handles' => array(
        'text/vcard', 'text/x-vcard', 'text/directory'
    ),
    'icons' => array(
        'default' => 'vcard.png'
    )
);


/**
 * RPM driver settings
 */
$mime_drivers['horde']['rpm'] = array(
    'location' => '/usr/bin/rpm',
    'inline' => false,
    'handles' => array(
        'application/x-rpm'
    ),
    'icons' => array(
        'default' => 'rpm.png'
    )
);


/**
 * Debian package driver settings
 */
$mime_drivers['horde']['deb'] = array(
    'location' => '/usr/bin/dpkg',
    'inline' => false,
    'handles' => array(
        'application/x-deb', 'application/x-debian-package'
    ),
    'icons' => array(
        'default' => 'deb.png'
    )
);


/**
 * Secure multiparts (RFC 1847)
 */
$mime_drivers['horde']['security'] = array(
    'inline' => true,
    'handles' => array(
        'multipart/encrypted', 'multipart/signed'
    ),
    'icons' => array(
        'default' => 'encryption.png'
    )
);


/**
 * Image settings
 */
$mime_drivers['horde']['images'] = array(
    'inline' => false,
    'handles' => array(
        'image/*'
    ),
    'icons' => array(
        'default' => 'image.png'
    )
);


/**
 * MS-TNEF Attachment (application/ms-tnef) settings
 */
$mime_drivers['horde']['tnef'] = array(
    'inline' => false,
    'handles' => array(
        'application/ms-tnef'
    ),
    'icons' => array(
        'default' => 'text.png'
    )
);


/**
 * Digest message (RFC 2046 [5.2.1]) settings
 */
$mime_drivers['horde']['rfc822'] = array(
    'inline' => false,
    'handles' => array(
        'message/rfc822', 'x-extension/eml'
    ),
    'icons' => array(
        'default' => 'mail.png'
    )
);


/**
 * Report messages (RFC 3452)
 */
$mime_drivers['horde']['report'] = array(
    'inline' => true,
    'handles' => array(
        'multipart/report'
    ),
    'icons' => array(
        'default' => 'mail.png'
    )
);


/**
 * OpenOffice.org/StarOffice settings
 */
$mime_drivers['horde']['ooo'] = array(
    'inline' => false,
    'handles' => array(
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
        'application/vnd.stardivision.writer'
    ),
    'icons' => array(
        'default'                                  => 'ooo_calc.png',
        'application/vnd.sun.xml.calc'             => 'ooo_calc.png',
        'application/vnd.stardivision.calc'        => 'ooo_calc.png',
        'application/vnd.sun.xml.calc.template'    => 'ooo_calc.png',
        'application/vnd.sun.xml.draw'             => 'ooo_draw.png',
        'application/vnd.stardivision.draw'        => 'ooo_draw.png',
        'application/vnd.sun.xml.draw.template'    => 'ooo_draw.png',
        'application/vnd.sun.xml.impress'          => 'ooo_impress.png',
        'application/vnd.stardivision.impress'     => 'ooo_impress.png',
        'application/vnd.sun.xml.impress.template' => 'ooo_impress.png',
        'application/vnd.sun.xml.math'             => 'ooo_math.png',
        'application/vnd.stardivision.math'        => 'ooo_math.png',
        'application/vnd.sun.xml.writer'           => 'ooo_writer.png',
        'application/vnd.stardivision.writer'      => 'ooo_writer.png',
        'application/vnd.sun.xml.writer.global'    => 'ooo_writer.png',
        'application/vnd.sun.xml.writer.template'  => 'ooo_writer.png'
    )
);


/**
 * Portable Document Format (PDF) files
 * YOU SHOULD NOT NORMALLY ALTER THIS SETTING.
 */
$mime_drivers['horde']['pdf'] = array(
    'inline' => false,
    'handles' => array(
        'application/pdf'
    ),
    'icons' => array(
        'default' => 'pdf.png'
    )
);


/**
 * RTF driver settings
 * This driver requires UnRTF to be installed.
 * UnRTF homepage: http://www.gnu.org/software/unrtf/unrtf.html
 */
$mime_drivers['horde']['rtf'] = array(
    'location' => '/usr/bin/unrtf',
    'inline' => false,
    'handles' => array(
        'text/rtf', 'application/rtf'
    ),
    'icons' => array(
        'default' => 'text.png'
    )
);


/**
 * WordPerfect driver settings
 * This driver requires wpd2html to be installed.
 * libwpd homepage: http://libwpd.sourceforge.net/
 */
$mime_drivers['horde']['wordperfect'] = array(
    'location' => '/usr/bin/wpd2html',
    'inline' => false,
    'handles' => array(
        'application/vnd.wordperfect', 'application/wordperf',
        'application/wordperfect', 'application/wpd', 'application/x-wpwin'
    ),
    'icons' => array(
        'default' => 'wordperfect.png'
    )
);
