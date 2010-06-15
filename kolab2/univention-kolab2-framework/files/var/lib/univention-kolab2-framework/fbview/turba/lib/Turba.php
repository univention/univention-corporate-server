<?php
/**
 * Turba Base Class.
 *
 * $Horde: turba/lib/Turba.php,v 1.48 2004/04/07 14:43:52 chuck Exp $
 *
 * @author  Chuck Hagenbuch <chuck@horde.org>
 * @author  Jon Parise <jon@horde.org>
 * @version $Revision: 1.1.2.1 $
 * @package Turba
 */
class Turba {

    /**
     * Split a GUID into source and contactId parts.
     *
     * @param string $guid  The GUID.
     *
     * @return array  array($source, $contactId)
     */
    function splitGUID($guid)
    {
        $pieces = explode(':', $guid);

        /* Make sure this is a Turba GUID. */
        if ($pieces[0] != 'turba') {
            return array(false, false);
        }

        /* Strip off the turba entry. */
        array_shift($pieces);

        /* The contact id is the last entry in the array. */
        $contactId = array_pop($pieces);

        /* The source id is everything else. */
        $source = implode(':', $pieces);

        return array($source, $contactId);
    }

    function formatEmailAddresses($data, &$ob)
    {
        require_once 'Horde/MIME.php';

        $email_vals = explode(',', $data);
        $email_values = false;
        foreach ($email_vals as $email_val) {
            $email_val = trim($email_val);

            // Format the address according to RFC822.
            $mailbox_host = explode('@', $email_val);
            if (!isset($mailbox_host[1])) {
                $mailbox_host[1] = '';
            }
            $name = $ob->getValue('name');
            $address = MIME::rfc822WriteAddress($mailbox_host[0], $mailbox_host[1], $name);

            // Get rid of the trailing @ (when no host is included in
            // the email address).
            $address = str_replace('@>', '>', $address);
            $mail_link = $GLOBALS['registry']->call('mail/compose', array(array('to' => addslashes($address))));
            if (is_a($mail_link, 'PEAR_Error')) {
                $mail_link = 'mailto:' . urlencode($address);
            }

            $email_value = Horde::link($mail_link, $email_val) . htmlspecialchars($email_val) . '</a>';
            if ($email_values) {
                $email_values .= ', ' . $email_value;
            } else {
                $email_values = $email_value;
            }
        }

        return $email_values;
    }

    function string2Columns($string)
    {
        $ret = array();
        $lines = explode("\n", $string);
        foreach ($lines as $line) {
            $line = trim($line);
            if (!empty($line)) {
                $columns = explode("\t", $line);
                if (count($columns) > 1) {
                    $source = array_splice($columns, 0, 1);
                    $ret[$source[0]] = $columns;
                }
            }
        }

        return $ret;
    }

    /**
     * Returns a best guess at the lastname in a string.
     *
     * @param $name     String contain the full name.
     *
     * @return          String containing the last name.
     */
    function guessLastname($name)
    {
        $name = trim(preg_replace('|\s|', ' ', $name));
        if (!empty($name)) {
            /* Assume that last names are always before any commas. */
            if (is_int(strpos($name, ','))) {
                $name = String::substr($name, 0, strpos($name, ','));
            }

            /* Take out anything in parentheses. */
            $name = trim(preg_replace('|\(.*\)|', '', $name));

            $namelist = explode(' ', $name);
            $name = $namelist[($nameindex = (count($namelist) - 1))];

            while (String::length($name) < 5 &&
                   strspn($name[(String::length($name) - 1)], '.:-') &&
                   !empty($namelist[($nameindex - 1)])) {
                $nameindex--;
                $name = $namelist[$nameindex];
            }
        }
        return $name;
    }

    /**
     * Formats the name according to the user's preference.
     *
     * @param object Turba_Object $ob  The object to get a name from.
     *
     * @return string  The formatted name, either "Firstname Lastname"
     *                 or "Lastname, Firstname" depending on the user's
     *                 preference.
     */
    function formatName($ob)
    {
        global $prefs;

        /* See if we have the name fields split out explicitly. */
        if ($ob->hasValue('firstname') && $ob->hasValue('lastname')) {
            if ($prefs->getValue('name_format') == 'last_first') {
                return $ob->getValue('lastname') . ', ' . $ob->getValue('firstname');
            } else {
                return $ob->getValue('firstname') . ' ' . $ob->getValue('lastname');
            }
        } else {
            /* One field, we'll have to guess. */
            $format = $prefs->getValue('name_format');
            $name = $ob->getValue('name');
            $lastname = Turba::guessLastname($name);
            if ($format == 'last_first' &&
                !is_int(strpos($name, ',')) &&
                String::length($name) > String::length($lastname)) {
                $name = preg_replace("|\s+$lastname|", '', $name);
                $name = $lastname . ', ' . $name;
            }
            if ($format == 'first_last' &&
                is_int(strpos($name, ',')) &&
                String::length($name) > String::length($lastname)) {
                $name = preg_replace("|$lastname,\s*|", '', $name);
                $name = $name . ' ' . $lastname;
            }
            return $name;
        }
    }

    /**
     * Checks if a user has the specified permissions on the passed-in
     * object.
     *
     * @param array $in        The data to check on.
     * @param string $filter   What are we checking for.
     * @param int $permission  What permission to check for.
     *
     * @return array           An array containing the criteria.
     */
    function checkPermissions($in, $filter, $permission = PERMS_READ)
    {
        $userID = Auth::getAuth();
        $admin = Auth::isAdmin();

        switch ($filter) {
        case 'object':
            if ($admin || in_array($userID, $in->source->admin)) {
                return true;
            }

            switch ($permission) {
            case PERMS_SHOW:
            case PERMS_READ:
                if ($in->source->public ||
                    ($in->hasValue('__owner') &&
                     $in->getValue('__owner') == $userID)) {
                    return true;
                }
                break;

            case PERMS_EDIT:
            case PERMS_DELETE:
                /* Find out if this is a case that the object is
                 * editable. */
                if (!$in->source->readonly &&
                    $in->hasValue('__owner') &&
                    $in->getValue('__owner') == $userID) {
                    return true;
                }
                return false;
                break;
            }
            break;

        default:
            return true;
        }

        return false;
    }

    function permissionsFilter($in, $filter, $permission = PERMS_READ)
    {
        global $perms;

        $out = array();
        $userID = Auth::getAuth();
        $admin = Auth::isAdmin();

        switch ($filter) {
        case 'source':
            if ($admin) {
                return $in;
            }

            foreach ($in as $sourceID => $name) {
                $sourceTag = 'turba:sources:' . $sourceID;
                if (!$perms->exists($sourceTag) || $perms->hasPermission($sourceTag, $userID, $permission)) {
                    $out[$sourceID] = $name;
                }
            }
            break;

        default:
            $out = $in;
        }

        return $out;
    }

    function menu()
    {
        global $conf, $registry, $notification;
        require_once 'Horde/Menu.php';
        require TURBA_TEMPLATES . '/menu/menu.inc';

        $notification->notify(array('listeners' => 'status'));

        /* Include the JavaScript for the help system. */
        Help::javascript();
    }

}
