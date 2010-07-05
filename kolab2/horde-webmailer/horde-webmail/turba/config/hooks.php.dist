<?php
/**
 * Turba Hooks configuration file.
 *
 * THE HOOKS PROVIDED IN THIS FILE ARE EXAMPLES ONLY.  DO NOT ENABLE THEM
 * BLINDLY IF YOU DO NOT KNOW WHAT YOU ARE DOING.  YOU HAVE TO CUSTOMIZE THEM
 * TO MATCH YOUR SPECIFIC NEEDS AND SYSTEM ENVIRONMENT.
 *
 * For more information please see the horde/config/hooks.php.dist file.
 *
 * $Horde: turba/config/hooks.php.dist,v 1.1.2.1 2007-12-20 14:34:24 jan Exp $
 */

// Here is an example _turba_hook_encode_password (and decode). encode is
// called when we store a value; decode when we display it.  Passwords should
// be MD5 encoded, but not displayed.
//
// IMPORTANT: The last parameter in these examples (&$object) is only
// passed by Turba 2.1 and later. If you are using Turba 2.0, then you
// must remove the &$object parameter.

// if (!function_exists('_turba_hook_encode_password')) {
//     function _turba_hook_encode_password($new_password, $old_password, &$contact)
//     {
//         if (is_null($new_password) || $new_password == '' ||
//             $new_password == '[Not Displayed]') {
//             return $old_password;
//         } else {
//             return md5($new_password);
//         }
//     }
//     function _turba_hook_decode_password($password, &$contact)
//     {
//         if (strstr($_SERVER['PHP_SELF'], 'editobject')) {
//             return null;
//         } else {
//             return '[Not Displayed]';
//         }
//     }
// }
