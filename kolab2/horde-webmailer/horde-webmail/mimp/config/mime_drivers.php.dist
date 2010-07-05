<?php
/**
 * $Horde: mimp/config/mime_drivers.php.dist,v 1.5.2.2 2008-07-19 21:11:56 slusarz Exp $
 *
 * Decide which output drivers you want to activate for the MIMP application.
 * Settings in this file override settings in horde/config/mime_drivers.php.
 *
 * The available drivers are:
 * --------------------------
 * alternative    multipart/alternative parts
 * html           Conversion of HTML to basic text/plain
 * multipart      All other multipart/* messages
 * plain          text/plain parts
 * related        multipart/related parts
 * status         Mail delivery status messages
 */
$mime_drivers_map['mimp']['registered'] = array(
    'alternative', 'html', 'multipart', 'plain', 'related', 'status'
);

/**
 * If you want to specifically override any MIME type to be handled by
 * a specific driver, then enter it here.  Normally, this is safe to
 * leave, but it's useful when multiple drivers handle the same MIME
 * type, and you want to specify exactly which one should handle it.
 */
$mime_drivers_map['mimp']['overrides'] = array();

/**
 * Driver specific settings. See horde/config/mime_drivers.php for
 * the format.
 */

/**
 * Text driver settings.
 */
$mime_drivers['mimp']['plain'] = array(
    'inline' => true,
    'handles' => array(
        'text/plain', 'text/rfc822-headers'
    )
);


/**
 * HTML driver settings.
 */
$mime_drivers['mimp']['html'] = array(
    'inline' => true,
    'handles' => array(
        'text/html', 'text/enriched'
    ),
    /* Check for phishing exploits? */
    'phishing_check' => true
);


/**
 * Delivery Status messages settings
 */
$mime_drivers['mimp']['status'] = array(
    'inline' => true,
    'handles' => array(
        'message/delivery-status'
    )
);


/**
 * multipart/alternative settings
 * YOU SHOULD NOT NORMALLY ALTER THIS SETTING.
 */
$mime_drivers['mimp']['alternative'] = array(
    'inline' => true,
    'handles' => array(
        'multipart/alternative'
    )
);


/**
 * multipart/related settings
 * YOU SHOULD NOT NORMALLY ALTER THIS SETTING.
 */
$mime_drivers['mimp']['related'] = array(
    'inline' => true,
    'handles' => array(
        'multipart/related'
    )
);


/**
 * All other multipart/* messages
 * YOU SHOULD NOT NORMALLY ALTER THIS SETTING.
 */
$mime_drivers['mimp']['multipart'] = array(
    'inline' => true,
    'handles' => array(
        'multipart/*'
    )
);
