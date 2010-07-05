<?php
/**
 * $Horde: turba/data.php,v 1.70.4.21 2009-01-06 15:27:38 jan Exp $
 *
 * Copyright 2001-2009 The Horde Project (http://www.horde.org/)
 *
 * See the enclosed file LICENSE for license information (ASL).  If you
 * did not receive this file, see http://www.horde.org/licenses/asl.php.
 *
 * @author Jan Schneider <jan@horde.org>
 */

function _cleanup()
{
    global $import_step;
    $import_step = 1;
    return IMPORT_FILE;
}

/**
 * Remove empty attributes from attributes array.
 *
 * @param mixed $val    Value from attributes array.
 *
 * @return boolean         Boolean used by array_filter.
 */
function _emptyAttributeFilter($var)
{
    if (!is_array($var)) {
        return ($var != '');
    } else {
        foreach ($var as $v) {
            if ($v == '') {
                return false;
            }
        }
        return true;
    }
}

/**
 * Static function to make a given email address rfc822 compliant.
 *
 * @param string $address  An email address.
 * @param boolean $allow_multi  Allow multiple email addresses.
 *
 * @return string  The RFC822-formatted email address.
 */
function _getBareEmail($address, $allow_multi = false)
{
    // Empty values are still empty.
    if (!$address) {
        return $address;
    }

    require_once 'Mail/RFC822.php';
    require_once 'Horde/MIME.php';

    static $rfc822;
    if (is_null($rfc822)) {
        $rfc822 = new Mail_RFC822();
    }

    // Split multiple email addresses
    if ($allow_multi) {
        $addrs = MIME::rfc822Explode($address);
    } else {
        $addrs = array($address);
    }

    $result = array();
    foreach ($addrs as $addr) {
        $addr = trim($addr);

        if ($rfc822->validateMailbox($addr)) {
            $result[] = MIME::rfc822WriteAddress($addr->mailbox, $addr->host);
        }
    }

    return implode(', ', $result);
}

require_once dirname(__FILE__) . '/lib/base.php';
require_once 'Horde/Data.php';

if (!$conf['menu']['import_export']) {
    require TURBA_BASE . '/index.php';
    exit;
}

/* If there are absolutely no valid sources, abort. */
if (!$cfgSources) {
    $notification->push(_("No Address Books are currently available. Import and Export is disabled."), 'horde.error');
    require TURBA_TEMPLATES . '/common-header.inc';
    require TURBA_TEMPLATES . '/menu.inc';
    require $registry->get('templates', 'horde') . '/common-footer.inc';
    exit;
}

/* Importable file types. */
$file_types = array('csv'      => _("CSV"),
                    'tsv'      => _("TSV"),
                    'vcard'    => _("vCard"),
                    'mulberry' => _("Mulberry Address Book"),
                    'pine'     => _("Pine Address Book"),
                    'ldif'     => _("LDIF Address Book"));

/* Templates for the different import steps. */
$templates = array(
    IMPORT_FILE => array(TURBA_TEMPLATES . '/data/export.inc'),
    IMPORT_CSV => array($registry->get('templates', 'horde') . '/data/csvinfo.inc'),
    IMPORT_TSV => array($registry->get('templates', 'horde') . '/data/tsvinfo.inc'),
    IMPORT_MAPPED => array($registry->get('templates', 'horde') . '/data/csvmap.inc'),
    IMPORT_DATETIME => array($registry->get('templates', 'horde') . '/data/datemap.inc')
);

/* Initial values. */
$import_step = Util::getFormData('import_step', 0) + 1;
$actionID = Util::getFormData('actionID');
$next_step = IMPORT_FILE;
$app_fields = array();
$time_fields = array();
$error = false;
$outlook_mapping = array(
    'Title' => 'namePrefix',
    'First Name' => 'firstname',
    'Middle Name' => 'middlenames',
    'Last Name' => 'lastname',
    'Nickname' => 'nickname',
    'Suffix' => 'nameSuffix',
    'Company' => 'company',
    'Department' => 'department',
    'Job Title' => 'title',
    'Business Street' => 'workStreet',
    'Business City' => 'workCity',
    'Business State' => 'workProvince',
    'Business Postal Code' => 'workPostalCode',
    'Business Country' => 'workCountry',
    'Home Street' => 'homeStreet',
    'Home City' => 'homeCity',
    'Home State' => 'homeProvince',
    'Home Postal Code' => 'homePostalCode',
    'Home Country' => 'homeCountry',
    'Business Fax' => 'workFax',
    'Business Phone' => 'workPhone',
    'Home Phone' => 'homePhone',
    'Mobile Phone' => 'cellPhone',
    'Pager' => 'pager',
    'Anniversary' => 'anniversary',
    'Assistant\'s Name' => 'assistant',
    'Birthday' => 'birthday',
    'Business Address PO Box' => 'workPOBox',
    'Categories' => 'category',
    'Children' => 'children',
    'E-mail Address' => 'email',
    'Home Address PO Box' => 'homePOBox',
    'Initials' => 'initials',
    'Internet Free Busy' => 'freebusyUrl',
    'Language' => 'language',
    'Notes' => 'notes',
    'Profession' => 'role',
    'Office Location' => 'office',
    'Spouse' => 'spouse',
    'Web Page' => 'website',
);
$import_mapping = array(
    'e-mail' => 'email',
    'homeaddress' => 'homeAddress',
    'businessaddress' => 'workAddress',
    'homephone' => 'homePhone',
    'businessphone' => 'workPhone',
    'mobilephone' => 'cellPhone',
    'businessfax' => 'fax',
    'jobtitle' => 'title',
    'internetfreebusy' => 'freebusyUrl',

    // Entourage on MacOS
    'Dept' => 'department',
    'Work Street Address' => 'workStreet',
    'Work City' => 'workCity',
    'Work State' => 'workProvince',
    'Work Zip' => 'workPostalCode',
    'Work Country/Region' => 'workCountry',
    'Home Street Address' => 'homeStreet',
    'Home City' => 'homeCity',
    'Home State' => 'homeProvince',
    'Home Zip' => 'homePostalCode',
    'Home Country/Region' => 'homeCountry',
    'Work Fax' => 'workFax',
    'Work Phone 1' => 'workPhone',
    'Home Phone 1' => 'homePhone',
    'Instant Messaging 1' => 'instantMessenger',

    // Thunderbird
    'Primary Email' => 'email',
    'Fax Number' => 'fax',
    'Pager Number' => 'pager',
    'Mobile Number' => 'Mobile Phone',
    'Home Address' => 'homeStreet',
    'Home ZipCode' => 'homePostalCode',
    'Work Address' => 'workStreet',
    'Work ZipCode' => 'workPostalCode',
    'Work Country' => 'workCountry',
    'Work Phone' => 'workPhone',
    'Organization' => 'company',
    'Web Page 1' => 'website',
);
$param = array('time_fields' => $time_fields,
               'file_types'  => $file_types,
               'import_mapping' => array_merge($outlook_mapping, $import_mapping));
$import_format = Util::getFormData('import_format', '');
if ($import_format == 'mulberry' || $import_format == 'pine') {
    $import_format = 'tsv';
}
if ($actionID != 'select') {
    array_unshift($templates[IMPORT_FILE], TURBA_TEMPLATES . '/data/import.inc');
}

/* Loop through the action handlers. */
switch ($actionID) {
case 'export':
    $sources = array();
    if (Util::getFormData('selected')) {
        foreach (Util::getFormData('objectkeys') as $objectkey) {
            list($source, $key) = explode(':', $objectkey, 2);
            if (!isset($sources[$source])) {
                $sources[$source] = array();
            }
            $sources[$source][] = $key;
        }
    } else {
        $source = Util::getFormData('source');
        if (!isset($source) && !empty($cfgSources)) {
            reset($cfgSources);
            $source = key($cfgSources);
        }
        $sources[$source] = array();
    }

    $data = array();
    $contacts = array();
    $all_fields = array();
    foreach ($sources as $source => $objectkeys) {
        /* Create a Turba storage instance. */
        $driver = &Turba_Driver::singleton($source);
        if (is_a($driver, 'PEAR_Error')) {
            $notification->push(sprintf(_("Failed to access the address book: %s"), $driver->getMessage()), 'horde.error');
            $error = true;
            break;
        }

        /* Get the full, sorted contact list. */
        if (count($objectkeys)) {
            $results = &$driver->getObjects($objectkeys);
        } else {
            $results = $driver->search(array());
            if (is_a($results, 'Turba_List')) {
                $results = $results->objects;
            }
        }
        if (is_a($results, 'PEAR_Error')) {
            $notification->push(sprintf(_("Failed to search the directory: %s"), $results->getMessage()), 'horde.error');
            $error = true;
            break;
        }

        $fields = array_keys($driver->map);
        $all_fields = array_merge($all_fields, $fields);
        $params = $driver->getParams();
        foreach ($results as $ob) {
            $row = array();
            foreach ($fields as $field) {
                if (substr($field, 0, 2) != '__') {
                    $attribute = $ob->getValue($field);
                    if ($attributes[$field]['type'] == 'date') {
                        $row[$field] = strftime('%Y-%m-%d', $attribute);
                    } elseif ($attributes[$field]['type'] == 'time') {
                        $row[$field] = strftime('%R', $attribute);
                    } elseif ($attributes[$field]['type'] == 'datetime') {
                        $row[$field] = strftime('%Y-%m-%d %R', $attribute);
                    } else {
                        $row[$field] = String::convertCharset($attribute, NLS::getCharset(), $params['charset']);
                    }
                }
            }
            $data[] = $row;
        }

        $contacts = array_merge($contacts, $results);
    }
    if (!count($data)) {
        $notification->push(_("There were no addresses to export."), 'horde.message');
        $error = true;
        break;
    }

    /* Make sure that all rows have the same columns if exporting from
     * different sources. */
    if (count($sources) > 1) {
        for ($i = 0; $i < count($data); $i++) {
            foreach ($all_fields as $field) {
                if (!isset($data[$i][$field])) {
                    $data[$i][$field] = '';
                }
            }
        }
    }

    switch (Util::getFormData('exportID')) {
    case EXPORT_CSV:
        $csv = &Horde_Data::singleton('csv');
        $csv->exportFile(_("contacts.csv"), $data, true);
        exit;

    case EXPORT_OUTLOOKCSV:
        $csv = &Horde_Data::singleton('outlookcsv');
        $csv->exportFile(_("contacts.csv"), $data, true, array_flip($outlook_mapping));
        exit;

    case EXPORT_TSV:
        $tsv = &Horde_Data::singleton('tsv');
        $tsv->exportFile(_("contacts.tsv"), $data, true);
        exit;

    case EXPORT_VCARD:
        $cards = array();
        foreach ($contacts as $contact) {
            $cards[] = Turba_Driver::tovCard($contact);
        }

        $vcard = &Horde_Data::singleton('vcard');
        $vcard->exportFile(_("contacts.vcf"), $cards, true);
        exit;

    case 'ldif':
        $ldif = &Horde_Data::singleton(array('turba', 'ldif'));
        $ldif->exportFile(_("contacts.ldif"), $data, true);
        exit;
    }
    break;

case IMPORT_FILE:
    $dest = Util::getFormData('dest');
    $driver = &Turba_Driver::singleton($dest);
    if (is_a($driver, 'PEAR_Error')) {
        $notification->push(sprintf(_("Failed to access the address book: %s"), $driver->getMessage()), 'horde.error');
        $error = true;
        break;
    }

    /* Check permissions. */
    $max_contacts = Turba::getExtendedPermission($driver, 'max_contacts');
    if ($max_contacts !== true &&
        $max_contacts <= $driver->count()) {
        $message = @htmlspecialchars(sprintf(_("You are not allowed to create more than %d contacts in \"%s\"."), $max_contacts, $driver->title), ENT_COMPAT, NLS::getCharset());
        if (!empty($conf['hooks']['permsdenied'])) {
            $message = Horde::callHook('_perms_hook_denied', array('turba:max_contacts'), 'horde', $message);
        }
        $notification->push($message, 'horde.error', array('content.raw'));
        $error = true;
        break;
    }

    $_SESSION['import_data']['target'] = $dest;
    $_SESSION['import_data']['purge'] = Util::getFormData('purge');
    break;

case IMPORT_MAPPED:
case IMPORT_DATETIME:
    foreach ($cfgSources[$_SESSION['import_data']['target']]['map'] as $field => $null) {
        if (substr($field, 0, 2) != '__' && !is_array($null)) {
            if ($attributes[$field]['type'] == 'monthyear' ||
                $attributes[$field]['type'] == 'monthdayyear') {
                $time_fields[$field] = 'date';
            } elseif ($attributes[$field]['type'] == 'time') {
                $time_fields[$field] = 'time';
            }
        }
    }
    $param['time_fields'] = $time_fields;
    break;
}

if (!$error && !empty($import_format)) {
    if ($import_format == 'ldif') {
        $data = &Horde_Data::singleton(array('turba', $import_format));
    } else {
        $data = &Horde_Data::singleton($import_format);
    }
    if (is_a($data, 'PEAR_Error')) {
        $notification->push(_("This file format is not supported."), 'horde.error');
        $next_step = IMPORT_FILE;
    } else {
        $next_step = $data->nextStep($actionID, $param);
        if (is_a($next_step, 'PEAR_Error')) {
            $notification->push($next_step->getMessage(), 'horde.error');
            $next_step = $data->cleanup();
        } else {
            /* Raise warnings if some exist. */
            if (method_exists($data, 'warnings')) {
                $warnings = $data->warnings();
                if (count($warnings)) {
                    foreach ($warnings as $warning) {
                        $notification->push($warning, 'horde.warning');
                    }
                    $notification->push(_("The import can be finished despite the warnings."), 'horde.message');
                }
            }
        }
    }
}

/* We have a final result set. */
if (is_array($next_step)) {
    /* Create a category manager. */
    require_once 'Horde/Prefs/CategoryManager.php';
    $cManager = new Prefs_CategoryManager();
    $categories = $cManager->get();

    /* Create a Turba storage instance. */
    $dest = $_SESSION['import_data']['target'];
    $driver = &Turba_Driver::singleton($dest);
    if (is_a($driver, 'PEAR_Error')) {
        $notification->push(sprintf(_("Failed to access the address book: %s"), $driver->getMessage()), 'horde.error');
    } elseif (!count($next_step)) {
        $notification->push(sprintf(_("The %s file didn't contain any contacts."),
                                    $file_types[$_SESSION['import_data']['format']]), 'horde.error');
    } else {
        /* Purge old address book if requested. */
        if ($_SESSION['import_data']['purge']) {
            $result = $driver->deleteAll();
            if (is_a($result, 'PEAR_Error')) {
                $notification->push(sprintf(_("The address book could not be purged: %s"), $result->getMessage()), 'horde.error');
            } else {
                $notification->push(_("Address book successfully purged."), 'horde.success');
            }
        }

        $error = false;
        foreach ($next_step as $row) {
            if (is_a($row, 'Horde_iCalendar_vcard')) {
                $row = $driver->toHash($row);
            }

            /* Don't search for empty attributes. */
            $row = array_filter($row, '_emptyAttributeFilter');
            $result = $driver->search($row);
            if (is_a($result, 'PEAR_Error')) {
                $notification->push($result, 'horde.error');
                $error = true;
                break;
            } elseif ($result->count()) {
                $result->reset();
                $object = $result->next();
                $notification->push(sprintf(_("\"%s\" already exists and was not imported."),
                                            $object->getValue('name')), 'horde.message');
            } else {
                /* Check for, and validate, any email fields */
                foreach (array_keys($row) as $field) {
                    if ($attributes[$field]['type'] == 'email') {
                        $allow_multi = is_array($attributes[$field]['params']) &&
                            !empty($attributes[$field]['params']['allow_multi']);
                        $row[$field] = _getBareEmail($row[$field], $allow_multi);
                    }
                }
                $row['__owner'] = $driver->getContactOwner();
                $result = $driver->add($row);
                if (is_a($result, 'PEAR_Error')) {
                    $notification->push(sprintf(_("There was an error importing the data: %s"),
                                                $result->getMessage()), 'horde.error');
                    $error = true;
                    break;
                }

                if (!empty($row['category']) &&
                    !in_array($row['category'], $categories)) {
                    $cManager->add($row['category']);
                    $categories[] = $row['category'];
                }
            }
        }
        if (!$error) {
            $notification->push(sprintf(_("%s file successfully imported."),
                                        $file_types[$_SESSION['import_data']['format']]), 'horde.success');
        }
    }
    $next_step = $data->cleanup();
}

switch ($next_step) {
case IMPORT_MAPPED:
case IMPORT_DATETIME:
    foreach ($cfgSources[$_SESSION['import_data']['target']]['map'] as $field => $null) {
        if (substr($field, 0, 2) != '__' && !is_array($null)) {
            $app_fields[$field] = $attributes[$field]['label'];
        }
    }
    break;
}

$title = _("Import/Export Address Books");
require TURBA_TEMPLATES . '/common-header.inc';
require TURBA_TEMPLATES . '/menu.inc';

$default_source = $prefs->getValue('default_dir');
if ($next_step == IMPORT_FILE) {
    /* Build the directory sources select widget. */
    $unique_source = '';
    $source_options = array();
    foreach (Turba::getAddressBooks() as $key => $entry) {
        if (!empty($entry['export'])) {
            $source_options[] = '<option value="' . htmlspecialchars($key) . '">' .
                htmlspecialchars($entry['title']) . "</option>\n";
            $unique_source = $key;
        }
    }

    /* Build the directory destination select widget. */
    $unique_dest = '';
    $dest_options = array();
    $hasWriteable = false;
    foreach (Turba::getAddressBooks(PERMS_EDIT) as $key => $entry) {
        $selected = ($key == $default_source) ? ' selected="selected"' : '';
        $dest_options[] = '<option value="' . htmlspecialchars($key) . '" ' . $selected . '>' .
            htmlspecialchars($entry['title']) . "</option>\n";
        $unique_dest = $key;
        $hasWriteable = true;
    }

    if (!$hasWriteable) {
        array_shift($templates[$next_step]);
    }

    /* Build the charset options. */
    $charsets = $nls['encodings'];
    $all_charsets = $nls['charsets'];
    natcasesort($all_charsets);
    foreach ($all_charsets as $charset) {
        if (!isset($charsets[$charset])) {
            $charsets[$charset] = $charset;
        }
    }
    $my_charset = NLS::getCharset(true);
}

foreach ($templates[$next_step] as $template) {
    require $template;
}
require $registry->get('templates', 'horde') . '/common-footer.inc';
