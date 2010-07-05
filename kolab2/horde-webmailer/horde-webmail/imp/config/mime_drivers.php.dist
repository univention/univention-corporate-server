<?php
/**
 * $Horde: imp/config/mime_drivers.php.dist,v 1.35.10.7 2009-06-20 21:37:43 jan Exp $
 *
 * Decide which output drivers you want to activate for the IMP application.
 * Settings in this file override settings in horde/config/mime_drivers.php.
 *
 * Additional settings for IMP:
 * + If you want to limit the display of message data inline for large
 *   messages of a certain type, add a 'limit_inline_size' parameter to the
 *   desired mime type to the maximum size of the displayed message in bytes
 *   (see example under text/plain below).  If set, the user will only be able
 *   to download the part.  Don't set the parameter, or set to 0, to disable
 *   this check.
 *
 * The available drivers are:
 * --------------------------
 * alternative    multipart/alternative parts
 * appledouble    multipart/appledouble parts
 * enriched       Enriched text messages
 * html           HTML messages
 * images         Attached images inline
 * itip           iCalendar Transport-Independent Interoperability Protocol
 * multipart      All other multipart/* messages
 * notification   Notification messages
 * partial        message/partial parts
 * pdf            Portable Document Format (PDF) files
 * pgp            PGP signed/encrypted messages
 * pkcs7          S/MIME signed/encrypted messages
 * plain          URL syntax highlighting for text/plain parts
 * related        multipart/related parts
 * rfc822         Digested messages
 * status         Mail delivery status messages
 * tnef           MS-TNEF attachments
 * zip            ZIP attachments
 */
$mime_drivers_map['imp']['registered'] = array(
    'alternative', 'appledouble', 'enriched', 'html', 'images', 'itip',
    'multipart', 'notification', 'partial', 'pdf', 'pgp', 'pkcs7', 'plain',
    'related', 'rfc822', 'smil', 'status', 'tnef', 'zip'
);

/**
 * If you want to specifically override any MIME type to be handled by
 * a specific driver, then enter it here.  Normally, this is safe to
 * leave, but it's useful when multiple drivers handle the same MIME
 * type, and you want to specify exactly which one should handle it.
 */
$mime_drivers_map['imp']['overrides'] = array();

/**
 * Driver specific settings. See horde/config/mime_drivers.php for
 * the format.
 */

/**
 * Text driver settings
 */
$mime_drivers['imp']['plain'] = array(
    'inline' => true,
    'handles' => array('text/plain', 'text/rfc822-headers', 'application/pgp'),
    /* If you want to scan ALL incoming messages for UUencoded data, set the
     * following to true. This is very performance intensive and can take a
     * long time for large messages. It is not recommended and is disabled by
     * default. */
    'uuencode' => false,
    /* If you want to limit the display of message data inline for large
     * messages, set the maximum size of the displayed message here (in
     * bytes).  If exceeded, the user will only be able to download the part.
     * Set to 0 to disable this check. */
    'limit_inline_size' => 1048576
);

/**
 * HTML driver settings
 */
$mime_drivers['imp']['html'] = array(
    'inline' => false,
    'handles' => array(
        'text/html'
    ),
    'icons' => array(
        'default' => 'html.png'
    ),
    /* If you don't want to display the link to open the HTML content in a
     * separate window, set the following to false. */
    'external' => true,
    /* Run 'tidy' on all HTML output? This requires at least version 2.0 of the
     * PECL 'tidy' extension to be installed on your system. */
    'tidy' => false,
    /* Check for phishing exploits? */
    'phishing_check' => true
);

/**
 * Default smil driver settings
 */
$mime_drivers['imp']['smil'] = array(
    'inline' => true,
    'handles' => array(
        'application/smil'
    )
);

/**
 * Image driver settings
 */
$mime_drivers['imp']['images'] = array(
    'inline' => true,
    'handles' => array(
        'image/*'
    ),
    'icons' => array(
        'default' => 'image.png'
    ),
    /* Display thumbnails for all images, not just large images? */
    'allthumbs' => true
);

/**
 * Enriched text driver settings
 */
$mime_drivers['imp']['enriched'] = array(
    'inline' => true,
    'handles' => array(
        'text/enriched'
    ),
    'icons' => array(
        'default' => 'text.png'
    )
);

/**
 * PDF settings
 */
$mime_drivers['imp']['pdf'] = array(
    'inline' => false,
    'handles' => array(
        'application/pdf', 'image/pdf'
    ),
    'icons' => array(
        'default' => 'pdf.png'
    )
);

/**
 * PGP settings
 */
$mime_drivers['imp']['pgp'] = array(
    'inline' => true,
    'handles' => array(
        'application/pgp-encrypted', 'application/pgp-keys',
        'application/pgp-signature'
    ),
    'icons' => array(
        'default' => 'encryption.png'
    ),
    /* Turn background green or red depending on whether a signature could
     * be verified? */
    'highlight' => true
);

/**
 * PKCS7 settings (S/MIME)
 */
$mime_drivers['imp']['pkcs7'] = array(
    'inline' => true,
    'handles' => array(
        'application/x-pkcs7-signature', 'application/x-pkcs7-mime',
        'application/pkcs7-signature', 'application/pkcs7-mime'
    ),
    'icons' => array(
        'default' => 'encryption.png'
    ),
    /* Turn background green or red depending on whether a signature could
     * be verified? */
    'highlight' => true
);

/**
 * Digest message (message/rfc822) settings
 */
$mime_drivers['imp']['rfc822'] = array(
    'inline' => false,
    'handles' => array(
        'message/rfc822'
    ),
    'icons' => array(
        'default' => 'mail.png'
    )
);

/**
 * Zip File Attachments settings
 */
$mime_drivers['imp']['zip'] = array(
    'inline' => false,
    'handles' => array(
        'application/zip', 'application/x-compressed',
        'application/x-zip-compressed'
    ),
    'icons' => array(
        'default' => 'compressed.png'
    )
);

/**
 * Delivery Status messages settings
 */
$mime_drivers['imp']['status'] = array(
    'inline' => true,
    'handles' => array(
        'message/delivery-status'
    )
);

/**
 * Disposition Notification message settings
 */
$mime_drivers['imp']['notification'] = array(
    'inline' => true,
    'handles' => array(
        'message/disposition-notification'
    )
);

/**
 * multipart/appledouble settings
 */
$mime_drivers['imp']['appledouble'] = array(
    'inline' => true,
    'handles' => array(
        'multipart/appledouble'
    )
);

/**
 * iCalendar Transport-Independent Interoperability Protocol
 */
$mime_drivers['imp']['itip'] = array(
    'inline' => true,
    'handles' => array(
        'text/calendar', 'text/x-vcalendar'
    ),
    'icons' => array(
        'default' => 'itip.png'
    )
);

/**
 * multipart/alternative settings
 * YOU SHOULD NOT NORMALLY ALTER THIS SETTING.
 */
$mime_drivers['imp']['alternative'] = array(
    'inline' => true,
    'handles' => array(
        'multipart/alternative'
    )
);

/**
 * multipart/related settings
 * YOU SHOULD NOT NORMALLY ALTER THIS SETTING.
 */
$mime_drivers['imp']['related'] = array(
    'inline' => true,
    'handles' => array(
        'multipart/related'
    ),
    'icons' => array(
        'default' => 'html.png'
    )
);

/**
 * message/partial settings
 * YOU SHOULD NOT NORMALLY ALTER THIS SETTING.
 */
$mime_drivers['imp']['partial'] = array(
    'inline' => true,
    'handles' => array(
        'message/partial'
    )
);

/**
 * All other multipart/* messages
 * YOU SHOULD NOT NORMALLY ALTER THIS SETTING.
 */
$mime_drivers['imp']['multipart'] = array(
    'inline' => true,
    'handles' => array(
        'multipart/*'
    )
);

/**
 * MS-TNEF Attachment (application/ms-tnef) settings
 * YOU SHOULD NOT NORMALLY ALTER THIS SETTING.
 */
$mime_drivers['imp']['tnef'] = array(
    'inline' => false,
    'handles' => array(
        'application/ms-tnef'
    ),
    'icons' => array(
        'default' => 'binary.png'
    )
);
