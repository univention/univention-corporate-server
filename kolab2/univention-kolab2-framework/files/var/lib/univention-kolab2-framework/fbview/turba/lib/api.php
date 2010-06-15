<?php
/**
 * Turba external API interface.
 *
 * $Horde: turba/lib/api.php,v 1.84 2004/05/29 21:12:45 jan Exp $
 *
 * This file defines Turba's external API interface. Other
 * applications can interact with Turba through this API.
 *
 * @package Turba
 */

$_services['perms'] = array(
    'args' => array(),
    'type' => 'stringArray');

$_services['import_vcard'] = array(
    'args' => array('source', 'vcard_data'),
    'type' => 'stringArray');

$_services['show'] = array(
    'link' => '%application%/display.php?source=|source|&key=|key|');

$_services['followLink'] = array(
    'link' => '%application%/display.php?source=|source|&key=|to_value|');

$_services['search'] = array(
    'args' => array('addresses', 'addressbooks', 'fields'),
    'type' => 'stringArray');

$_services['clientSearch'] = array(
    'checkperms' => false,
    'args' => array('addresses', 'fields'),
    'type' => 'stringArray');

$_services['listBy'] = array(
    'args' => array('action', 'timestamp'),
    'type' => 'stringArray');

$_services['add'] = array(
    'args' => array('name', 'address', 'addressbook'),
    'type' => 'boolean');

$_services['sources'] = array(
    'args' => array('writeable'),
    'type' => 'stringArray');

$_services['fields'] = array(
    'args' => array('addressbook'),
    'type' => 'stringArray');

$_services['addField'] = array(
    'args' => array('address', 'name', 'field', 'value', 'addressbook'),
    'type' => 'stringArray');

$_services['deleteField'] = array(
    'args' => array('address', 'field', 'addressbooks'),
    'type' => 'stringArray');

$_services['getField'] = array(
    'args' => array('address', 'field', 'addressbooks'),
    'type' => 'stringArray');

$_services['listField'] = array(
    'args' => array('field', 'addressbooks'),
    'type' => 'stringArray');

$_services['getContact'] = array(
    'args' => array('addressbook', 'key'),
    'type' => 'stringArray');

$_services['getContacts'] = array(
    'args' => array('addressbook', 'keys'),
    'type' => 'stringArray');

$_services['addContact'] = array(
    'args' => array('addressbook', 'attributes'),
    'type' => 'string');

$_services['updateContact'] = array(
    'args' => array('addressbook', 'key', 'attributes'),
    'type' => 'stringArray');

$_services['deleteContact'] = array(
    'args' => array('addressbook', 'key'),
    'type' => 'boolean');

$_services['clientSourceConfigured'] = array(
    'checkperms' => false,
    'args' => array(),
    'type' => 'boolean');

$_services['getClient'] = array(
    'checkperms' => false,
    'args' => array('key'),
    'type' => 'stringArray');

$_services['getClients'] = array(
    'checkperms' => false,
    'args' => array('keys'),
    'type' => 'stringArray');

$_services['getClientSource'] = array(
    'checkperms' => false,
    'args' => array(),
    'type' => 'string');

$_services['addClient'] = array(
    'args' => array('attributes'),
    'type' => 'string');

$_services['updateClient'] = array(
    'args' => array('key', 'attributes'),
    'type' => 'stringArray');

$_services['deleteClient'] = array(
    'args' => array('key'),
    'type' => 'stringArray');

$_services['block'] = array(
    'args' => array('type', 'params'),
    'type' => 'stringArray');

$_services['linkParameters'] = array(
    'args' => array(),
    'type' => 'stringArray');

$_services['getLinkDescription'] = array(
    'args' => array(),
    'type' => 'string');

$_services['getLinkSummary'] = array(
    'args' => array(),
    'type' => 'string');

$_services['addLink'] = array(
    'link' => '%application%/addlink.php?link_type=|link_type|' .
    ini_get('arg_separator.output') . 'from_application=|from_application|' .
    ini_get('arg_separator.output') . 'from_parameters=|from_parameters|' .
    ini_get('arg_separator.output') . 'url=|url|');


function _turba_perms()
{
    static $perms = array();
    if (!empty($perms)) {
        return $perms;
    }

    @define('TURBA_BASE', dirname(__FILE__) . '/..');
    require_once TURBA_BASE . '/lib/base.php';
    global $cfgSources;

    $perms['tree']['turba']['sources'] = false;
    $perms['title']['turba:sources'] = _("Sources");

    // Run through every contact source.
    foreach ($cfgSources as $source => $curSource) {
        $perms['tree']['turba']['sources'][$source] = false;
        $perms['title']['turba:sources:' . $source] = $curSource['title'];
    }

    return $perms;
}

/**
 * Return the requested block and include needed libs.
 */
function &_turba_block($type, $params)
{
    @define('TURBA_BASE', dirname(__FILE__) . '/..');
    require_once TURBA_BASE . '/lib/base.php';

    include_once TURBA_BASE . '/lib/Block/' . $type . '.php';
    $class = 'Horde_Block_Turba_' . $type;
    if (class_exists($class)) {
        return $ret = &new $class($params);
    }

    return PEAR::raiseError('Not found');
}

function _turba_import_vcard($source, $vcard_data)
{
    require_once dirname(__FILE__) . '/base.php';
    require_once 'Horde/Data.php';
    require_once TURBA_BASE . '/lib/Source.php';
    require_once TURBA_BASE . '/lib/Object.php';
    global $cfgSources;

    if (empty($source) || !isset($cfgSources[$source])) {
        return PEAR::raiseError(_("Invalid address book."), 'horde.error', null, null, $source);
    }

    if ($cfgSources[$source]['readonly']
        && (!isset($cfgSources[$source]['admin'])
        || !in_array(Auth::getAuth(), $cfgSources[$source]['admin']))) {
        return PEAR::raiseError(_("Address book is read-only."), 'horde.error', null, null, $source);
    }

    $vcard = &Horde_Data::singleton('vcard');
    if (!$data = $vcard->importData($vcard_data)) {
        return PEAR::raiseError(_("There was an error importing the vCard data."));
    }

    $driver = &Turba_Source::singleton($source, $cfgSources[$source]);

    $objects = array();
    foreach ($data as $object) {
        if ($object['type'] == 'VCARD') {
            $hash = $vcard->toHash($object);
            $res = $driver->search($hash);
            if (is_a($res, 'PEAR_Error') || $res->count() > 0) {
                $objects[] = PEAR::raiseError(_("This person is already in your address book."), 'horde.message', null, null, $source);
            } else {
                $hash['__owner'] = Auth::getAuth();
                $objectID = $driver->addObject($hash);
                if (!is_a($objectID, 'PEAR_Error')) {
                    $objects[$objectID] = isset($hash['name']) ? $hash['name'] : _("Unnamed Contact");
                } else {
                    if (count($objects)) {
                        foreach ($objects as $id => $name) {
                            $driver->removeObject($id);
                        }
                    }
                    return PEAR::raiseError(_("There was an error importing the vCard data."));
                }
            }
        }
    }

    return $objects;
}

function _turba_search($names = array(), $addressbooks = array(), $fields = array())
{
    require_once dirname(__FILE__) . '/base.php';
    require_once TURBA_BASE . '/lib/Source.php';
    require TURBA_BASE . '/config/attributes.php';
    global $cfgSources;

    if (!isset($cfgSources) || !is_array($cfgSources) || !count($cfgSources)) {
        return array();
    }

    if (count($addressbooks) == 0) {
        $addressbooks = array(key($cfgSources));
    }

    $results = array();
    $seen = array();
    foreach ($addressbooks as $source) {
        if (isset($cfgSources[$source])) {
            $driver = &Turba_Source::singleton($source, $cfgSources[$source]);
            if (is_a($driver, 'PEAR_Error')) {
                return PEAR::raiseError(_("Failed to connect to the specified directory."), 'horde.error', null, null, $source);
            }

            foreach ($names as $name) {
                $criteria = array();
                if (isset($fields[$source])) {
                    foreach ($fields[$source] as $field) {
                        $criteria[$field] = trim($name);
                    }
                }
                if (count($criteria) == 0) {
                    $criteria['name'] = trim($name);
                }
                $res = $driver->search($criteria, 'lastname', 'OR');

                if (!isset($results[$name])) {
                    $results[$name] = array();
                }
                if (is_a($res, 'Turba_List')) {
                    while ($ob = $res->next()) {
                        if (!$ob->isGroup()) {
                            /* Not a group. */
                            $att = $ob->getAttributes();

                            $email = null;
                            foreach (array_keys($att) as $key) {
                                if ($ob->getValue($key) && isset($attributes[$key]) &&
                                    $attributes[$key]['type'] == 'email') {
                                    $email = $ob->getValue($key);
                                    break;
                                }
                            }
                            if (!is_null($email)) {
                                $seen_key = trim(String::lower($ob->getValue('name'))) . '/' . trim(String::lower($email));
                                if (!empty($seen[$seen_key])) {
                                    continue;
                                }
                                $seen[$seen_key] = true;
                            }
                            $results[$name][] = array_merge($att,
                                                array('id' => $att['__key'],
                                                      'name' => $ob->getValue('name'),
                                                      'email' => $email,
                                                      '__type' => 'Object',
                                                      'source' => $source));
                        } else {
                            /* Is a distribution list. */
                            $listatt = $ob->getAttributes();
                            $seeninlist = array();
                            $members = $ob->listMembers();
                            if (is_a($members, 'Turba_List')) {
                                if ($members->count() == 1) {
                                    $ob = $members->next();
                                    $att = $ob->getAttributes();
                                    $email = '';
                                    foreach ($att as $key => $value) {
                                        if (!empty($value) && isset($attributes[$key]) &&
                                            $attributes[$key]['type'] == 'email') {
                                            $email = $value;
                                        }
                                    }
                                    $results[$name][] = array('name' => $listatt['name'] . ' - ' . $att['name'], 'email' => $email, 'id' => $att['__key'], 'source' => $source );
                                } else {
                                    $email = '';
                                    while ($ob = $members->next()) {
                                        $att = $ob->getAttributes();
                                        foreach ($att as $key => $value) {
                                            if (!empty($value) && isset($attributes[$key]) &&
                                                $attributes[$key]['type'] == 'email' &&
                                                empty($seeninlist[trim(String::lower($att['name'])) . trim(String::lower($value))])) {

                                                $email .= ($email == '') ? '' : ', ';
                                                $email .= '"' . $att['name'] . '" <' . $value . '>';
                                                $seeninlist[trim(String::lower($att['name'])) . trim(String::lower($value))] = true;
                                            }
                                        }
                                    }
                                    $results[$name][] = array('name' => $listatt['name'], 'email' => $email, 'id' => $listatt['__key'], 'source' => $source);
                                }
                            }
                        }
                    }
                }
            }
        }
    }
    return $results;
}

function _turba_clientSearch($names = array(), $fields = array())
{
    global $conf;
    return _turba_search($names, array($conf['client']['addressbook']),
                         $fields);
}

function _turba_add($name = '', $address = '', $addressbook = '')
{
    require_once dirname(__FILE__) . '/base.php';
    require_once TURBA_BASE . '/lib/Source.php';
    global $cfgSources;

    if (empty($addressbook) || !isset($cfgSources[$addressbook])) {
        return PEAR::raiseError(_("Invalid address book."), 'horde.error', null, null, $addressbook);
    }

    if (empty($name)) {
        return PEAR::raiseError(_("Invalid name."), 'horde.error', null, null, $addressbook);
    }

    if (empty($address)) {
        return PEAR::raiseError(_("Invalid e-mail address."), 'horde.error', null, null, $addressbook);
    }

    if ($cfgSources[$addressbook]['readonly']
        && (!isset($cfgSources[$addressbook]['admin'])
        || !in_array(Auth::getAuth(), $cfgSources[$addressbook]['admin']))) {
        return PEAR::raiseError(_("Address book is read-only."), 'horde.error', null, null, $addressbook);
    }

    $driver = &Turba_Source::singleton($addressbook, $cfgSources[$addressbook]);
    $res = $driver->search(array('name' => $name, 'email' => $address));
    if (is_a($res, 'PEAR_Error') || $res->count() > 0) {
        return PEAR::raiseError(_("This person is already in your address book."), 'horde.message', null, null, $addressbook);
    }

    return $driver->addObject(array('name' => $name, 'email' => $address, '__owner' => Auth::getAuth()));
}

function _turba_sources($writeable = false)
{
    require_once dirname(__FILE__) . '/base.php';
    global $cfgSources;

    if (!isset($cfgSources) || !is_array($cfgSources) || !count($cfgSources)) {
        return array();
    }

    $sources = array();
    foreach ($cfgSources as $key => $entry) {
        if (!$writeable || (!$entry['readonly'] ||
                           (isset($entry['admin']) && in_array(Auth::getAuth(), $entry['admin'])))) {
            $sources[$key] = $entry['title'];
        }
    }
    return $sources;
}

function _turba_fields($addressbook = '')
{
    require_once dirname(__FILE__) . '/base.php';
    require TURBA_BASE . '/config/attributes.php';
    global $cfgSources;

    if (empty($addressbook) || !isset($cfgSources[$addressbook])) {
        return PEAR::raiseError(_("Invalid address book."), 'horde.error', null, null, $addressbook);
    }

    $fields = array();
    foreach ($cfgSources[$addressbook]['map'] as $field_name => $null) {
        if (substr($field_name, 0, 2) != '__') {
            $fields[$field_name] = array('name' => $field_name,
                                         'type' => $attributes[$field_name]['type'],
                                         'label' => $attributes[$field_name]['label'],
                                         'search' => in_array($field_name, $cfgSources[$addressbook]['search']));
        }
    }

    return $fields;
}

/**
 * Returns an array of GUIDs for contacts that have had $action happen
 * since $timestamp.
 *
 * @param integer $timestamp  The time to start the search.
 * @param string  $action     The action to check for - add, modify, or delete.
 *
 * @return array  An array of GUIDs matching the action and time criteria.
 */
function &_turba_listBy($action, $timestamp)
{
    require_once dirname(__FILE__) . '/base.php';
    require_once 'Horde/History.php';

    $history = &Horde_History::singleton();
    $histories = $history->getByTimestamp('>', $timestamp, array(array('op' => '=', 'field' => 'action', 'value' => $action)), 'turba');
    if (is_a($histories, 'PEAR_Error')) {
        return $histories;
    }

    return array_keys($histories);
}

function _turba_addField($address = '', $name = '', $field = '', $value = '', $addressbook = '')
{
    require_once dirname(__FILE__) . '/base.php';
    require_once TURBA_BASE . '/lib/Source.php';
    global $cfgSources;

    if (empty($addressbook) || !isset($cfgSources[$addressbook])) {
        return PEAR::raiseError(_("Invalid address book."), 'horde.error', null, null, $addressbook);
    }

    if (empty($address)) {
        return PEAR::raiseError(_("Invalid e-mail address."), 'horde.error', null, null, $addressbook);
    }

    if (empty($name)) {
        return PEAR::raiseError(_("Invalid name."), 'horde.error', null, null, $addressbook);
    }

    if (empty($value)) {
        return PEAR::raiseError(_("Invalid entry."), 'horde.error', null, null, $addressbook);
    }

    if ($cfgSources[$addressbook]['readonly']
        && (!isset($cfgSources[$addressbook]['admin'])
        || !in_array(Auth::getAuth(), $cfgSources[$addressbook]['admin']))) {
        return PEAR::raiseError(_("Address book is read-only."), 'horde.error', null, null, $addressbook);
    }

    $driver = &Turba_Source::singleton($addressbook, $cfgSources[$addressbook]);
    $res = $driver->search(array('email' => trim($address)), null, 'AND');
    if (is_a($res, 'PEAR_Error')) {
        return PEAR::raiseError(_("Error while searching directory."), 'horde.message', null, null, $addressbook);
    } elseif ($res->count() > 1) {
        $res2 = $driver->search(array('email' => trim($address), 'name' => trim($name)), null, 'AND');
        if (is_a($res2, 'PEAR_Error')) {
            return PEAR::raiseError(_("Error while searching directory."), 'horde.message', null, null, $addressbook);
        } elseif ($res2->count() > 0) {
            $res3 = $driver->search(array('email' => $address, 'name' => $name, $field => $value));
            if (is_a($res3, 'PEAR_Error')) {
                return PEAR::raiseError(_("Error while searching directory."), 'horde.message', null, null, $addressbook);
            } elseif ($res3->count() > 0) {
                return PEAR::raiseError(sprintf(_("This person already has a %s entry in the address book."), $field), 'horde.message', null, null, $addressbook);
            } else {
                $ob = $res2->next();
                $ob->setValue($field, $value);
                $ob->store();
            }
        } else {
            return PEAR::raiseError(sprintf(_("Multiple persons with address [%s], but none with name [%s] in address book."), trim($address), trim($name)), 'horde.message', null, null, $addressbook);
        }
    } elseif ($res->count() == 1) {
        $res4 = $driver->search(array('email' => $address, $field => $value));
        if (is_a($res4, 'PEAR_Error')) {
            return PEAR::raiseError(_("Error while searching directory."), 'horde.message', null, null, $addressbook);
        } elseif ($res4->count() > 0) {
            return PEAR::raiseError(sprintf(_("This person already has a %s entry in the address book."), $field), 'horde.message', null, null, $addressbook);
        } else {
            $ob = $res->next();
            $ob->setValue($field, $value);
            $ob->store();
        }
    } else {
        return $driver->addObject(array('email' => $address, 'name' => $name, $field => $value, '__owner' => Auth::getAuth()));
    }

    return;
}

function _turba_getField($address = '', $field = '', $addressbooks = array())
{
    require_once dirname(__FILE__) . '/base.php';
    require_once TURBA_BASE . '/lib/Source.php';
    require TURBA_BASE . '/config/attributes.php';
    global $cfgSources;

    if (empty($address)) {
        return PEAR::raiseError(_("Invalid email."), 'horde.error');
    }

    if (!isset($cfgSources) || !is_array($cfgSources) || !count($cfgSources)) {
        return array();
    }

    if (count($addressbooks) == 0) {
        $addressbooks = array(key($cfgSources));
    }

    $count = 0;
    foreach ($addressbooks as $source) {
        if (isset($cfgSources[$source])) {
            $driver = &Turba_Source::singleton($source, $cfgSources[$source]);
            if (!is_a($driver, 'PEAR_Error')) {
                $res = $driver->search(array('email' => $address));
                if (is_a($res, 'Turba_List')) {
                    $count += $res->count();
                    if ($res->count() == 1) {
                        $ob = $res->next();
                        if ($ob->hasValue($field)) {
                            $result = $ob->getValue($field);
                        }
                    }
                }
            }
        }
    }

    if ($count > 1) {
        return PEAR::raiseError(_("More than 1 entry returned."), 'horde.warning', null, null, $source);
    } elseif (!isset($result)) {
        return PEAR::raiseError(sprintf(_("No %s entry found for %s."), $field, $address), 'horde.warning', null, null, $source);
    }

    return $result;
}

function _turba_getContact($addressbook = '', $key = '')
{
    require_once dirname(__FILE__) . '/base.php';
    require_once TURBA_BASE . '/lib/Source.php';
    require TURBA_BASE . '/config/attributes.php';
    global $cfgSources;
    $result = array();

    if (!isset($cfgSources) || !is_array($cfgSources) || !count($cfgSources)) {
        return array();
    }

    if (isset($cfgSources[$addressbook])) {
        $driver = &Turba_Source::singleton($addressbook, $cfgSources[$addressbook]);
        if (!is_a($driver, 'PEAR_Error')) {
            $object = $driver->getObject($key);
            /* Check permissions on this object. */
            if (Turba::checkPermissions($object, 'object', PERMS_READ)) {
                $result = $object->attributes;
            }
        }
    }

    return $result;
}

function _turba_getContacts($addressbook = '', $keys = array())
{
    require_once dirname(__FILE__) . '/base.php';
    require_once TURBA_BASE . '/lib/Source.php';
    require TURBA_BASE . '/config/attributes.php';
    global $cfgSources;
    $result = array();
    if (!is_array($keys)) {
        $keys = array($keys);
    }

    if (!isset($cfgSources) || !is_array($cfgSources) || !count($cfgSources)) {
        return array();
    }

    if (isset($cfgSources[$addressbook])) {
        $driver = &Turba_Source::singleton($addressbook, $cfgSources[$addressbook]);
        if (!is_a($driver, 'PEAR_Error')) {
            $objects = $driver->getObjects($keys);
            foreach ($objects as $object) {
                /* Check permissions on this object. */
                if (Turba::checkPermissions($object, 'object', PERMS_READ)) {
                    $result[] = $object->attributes;
                }
            }
        }
    }

    return $result;
}


function _turba_addContact($addressbook = '', $attributes = array())
{
    require_once dirname(__FILE__) . '/base.php';
    require_once TURBA_BASE . '/lib/Source.php';
    global $cfgSources;

    $key = null;

    if (!isset($cfgSources) || !is_array($cfgSources) || !count($cfgSources) || !isset($cfgSources[$addressbook])) {
        return PEAR::raiseError(_("The source you requested does not exist."), 'horde.warning');
    }

    $driver = &Turba_Source::singleton($addressbook, $cfgSources[$addressbook]);

    /* Create Object. */
    $key = $driver->addObject($attributes);

    return $key;
}

function _turba_updateContact($addressbook = '', $key = '', $attributes = array())
{
    require_once dirname(__FILE__) . '/base.php';
    require_once TURBA_BASE . '/lib/Source.php';
    global $cfgSources;

    $result = null;

    if (!isset($cfgSources) || !is_array($cfgSources) || !count($cfgSources) || !isset($cfgSources[$addressbook])) {
        return PEAR::raiseError(_("The object you requested does not exist."), 'horde.warning');
    }

    $driver = &Turba_Source::singleton($addressbook, $cfgSources[$addressbook]);

    $object = $driver->getObject($key);
    /* Check permissions on this object. */
    if (!Turba::checkPermissions($object, 'object', PERMS_EDIT)) {
        $result = PEAR::raiseError(_("You do not have permission to edit this object."), 'horde.warning');
    } else {
        foreach ($attributes as $info_key => $info_val) {
            if ($info_key != '__key') {
                $object->setValue($info_key, $info_val);
            }
        }
        $success = $object->store();
        if (!is_a($success, 'PEAR_Error')) {
            $result = PEAR::raiseError(sprintf(_("Entry for %s updated."), $object->getValue('name')), 'horde.success');
        } else {
            $result = PEAR::raiseError(sprintf(_("There was an error updating this entry: %s."), $success->getMessage()), 'horde.error');
        }
    }

    return $result;
}

function _turba_deleteContact($addressbook = '', $key = '')
{
    require_once dirname(__FILE__) . '/base.php';
    require_once TURBA_BASE . '/lib/Source.php';
    global $cfgSources;

    if (empty($addressbook) || !isset($cfgSources[$addressbook])) {
        return PEAR::raiseError(_("Invalid address book."), 'horde.error', null, null, $addressbook);
    }

    if (empty($key)) {
        return PEAR::raiseError(_("Invalid key."), 'horde.error', null, null, $addressbook);
    }

    if ($cfgSources[$addressbook]['readonly']
        && (!isset($cfgSources[$addressbook]['admin'])
            || !in_array(Auth::getAuth(), $cfgSources[$addressbook]['admin']))) {
        return PEAR::raiseError(_("Address book is read-only."), 'horde.error', null, null, $addressbook);
    }

    $driver = &Turba_Source::singleton($addressbook, $cfgSources[$addressbook]);

    // Check if entry is in addressbook, if not raise a warning.
    $res = $driver->search(array('__key' => $key));
    if (is_a($res, 'PEAR_Error') || $res->count() == 0) {
        return PEAR::raiseError(_("Address not in addressbook."), 'horde.warning', null, null, $addressbook);
    }

    if (!$driver->removeObject($key)) {
        return PEAR::raiseError(_("There was an error deleting this entry."), 'horde.message', null, null, $addressbook);
    }

    return true;
}

function _turba_clientSourceConfigured()
{
    global $conf;
    if (!empty($conf['client']['addressbook'])) {
        return true;
    } else {
        return false;
    }
}

function _turba_getClient($key = '')
{
    global $conf;
    $args = array('addressbook' => $conf['client']['addressbook'],
                  'key' => $key);
    return $GLOBALS['registry']->call('clients/getContact', $args);
}

function _turba_getClients($keys = array())
{
    global $conf;
    $args = array('addressbook' => $conf['client']['addressbook'],
                  'keys' => $keys);
    return $GLOBALS['registry']->call('clients/getContacts', $args);
}

function _turba_getClientSource()
{
    global $conf;
    return $conf['client']['addressbook'];
}

function _turba_addClient($attributes = array())
{
    $addressbook = $GLOBALS['registry']->call('clients/getClientSource', array());
    return $GLOBALS['registry']->call('clients/addContact', array($addressbook, $attributes));
}

function _turba_updateClient($key = '', $attributes = array())
{
    $addressbook = $GLOBALS['registry']->call('clients/getClientSource', array());
    return $GLOBALS['registry']->call('clients/updateContact', array($addressbook, $key, $attributes));
}

function _turba_deleteClient($key = '')
{
    $addressbook = $GLOBALS['registry']->call('clients/getClientSource', array());
    return $GLOBALS['registry']->call('clients/deleteContact', array($addressbook, $key));
}

function _turba_getFieldById($source, $id, $field)
{
    require_once dirname(__FILE__) . '/base.php';
    require_once TURBA_BASE . '/lib/Source.php';
    require TURBA_BASE . '/config/attributes.php';
    global $cfgSources;

    if (empty($id)) {
        return PEAR::raiseError(_("Empty key"), 'horde.error');
    }

    if (empty($source)) {
        return PEAR::raiseError(_("Empty source"), 'horde.error');
    }

    if (!isset($cfgSources[$source])) {
        return PEAR::raiseError(_("Unknown source"), 'horde.error');
    }

    $count = 0;
    $driver = &Turba_Source::singleton($source, $cfgSources[$source]);
    if (is_a($driver, 'PEAR_Error')) {
        return PEAR::raiseError(_("Failed to connect to the specified directory."), 'horde.error', null, null, $source);
    }

    $ob = $driver->getObject($id);
    if ($ob->hasValue($field)) {
        return $ob->getValue($field);
    } else {
        return PEAR::raiseError(sprintf(_("No %s entry found for %s."), $field, $address), 'horde.warning', null, null, $source);
    }
}

function _turba_listField($field = '', $addressbooks = array())
{
    require_once dirname(__FILE__) . '/base.php';
    require_once TURBA_BASE . '/lib/Source.php';
    require TURBA_BASE . '/config/attributes.php';
    global $cfgSources;

    $results = array();

    if (!isset($cfgSources) || !is_array($cfgSources) || !count($cfgSources)) {
        return array();
    }

    if (count($addressbooks) == 0) {
        $addressbooks = array(key($cfgSources));
    }

    foreach ($addressbooks as $source) {
        if (isset($cfgSources[$source])) {
            $driver = &Turba_Source::singleton($source, $cfgSources[$source]);
            if (is_a($driver, 'PEAR_Error')) {
                return PEAR::raiseError(_("Failed to connect to the specified directory."), 'horde.error', null, null, $source);
            } else {
                $res = $driver->search(array());
                if (is_a($res, 'Turba_List')) {
                    while ($ob = $res->next()) {
                        if ($ob->hasValue($field)) {
                            $results[$ob->getValue('email')]['name'] = $ob->getValue('name');
                            $results[$ob->getValue('email')][$field] = $ob->getValue($field);
                        }
                    }
                } else {
                    return PEAR::raiseError(_("Failed to search the specified directory."), 'horde.error', null, null, $source);
                }
            }
        }
    }

    return $results;
}

function _turba_deleteField($address = '', $field = '', $addressbooks = array())
{
    require_once dirname(__FILE__) . '/base.php';
    require_once TURBA_BASE . '/lib/Source.php';
    require TURBA_BASE . '/config/attributes.php';
    global $cfgSources;

    if (empty($address)) {
        return PEAR::raiseError(_("Invalid email."), 'horde.error');
    }

    if (!isset($cfgSources) || !is_array($cfgSources) || !count($cfgSources)) {
        return array();
    }

    if (count($addressbooks) == 0) {
        $addressbooks = array(key($cfgSources));
    }

    foreach ($addressbooks as $source) {
        if (isset($cfgSources[$source])) {
            $driver = &Turba_Source::singleton($source, $cfgSources[$source]);
            if (is_a($driver, 'PEAR_Error')) {
                return PEAR::raiseError(_("Failed to connect to the specified directory."), 'horde.error', null, null, $source);
            } else {
                $res = $driver->search(array('email' => $address));
                if (is_a($res, 'Turba_List')) {
                    if ($res->count() > 1) {
                        return PEAR::raiseError(_("More than 1 entry returned."), 'horde.error', null, null, $source);
                    } else {
                        $ob = $res->next();
                        if (is_object($ob) && $ob->hasValue($field)) {
                            $ob->setValue($field, '');
                            $ob->store();
                        } else {
                            return PEAR::raiseError(sprintf(_("No %s entry found for %s."), $field, $address), 'horde.error', null, null, $source);
                        }
                    }
                }
            }
        }
    }

    return;
}

function _turba_linkParameters()
{
    return array('source', 'id');
}

function _turba_getLinkDescription($link_data = array())
{
    if (!isset($link_data['to_params']['source']) || !isset($link_data['to_params']['to_value'])) {
        return PEAR::raiseError(_("Missing information"));
    }
    return _turba_getFieldById($link_data['to_params']['source'], $link_data['to_params']['to_value'], $field = 'name');
}

function _turba_getLinkSummary($link_data = array())
{
    if (!isset($link_data['to_params']['source']) || !isset($link_data['to_params']['to_value'])) {
        return PEAR::raiseError(_("Missing information"));
    }
    $source = $link_data['to_params']['source'];
    $id = $link_data['to_params']['to_value'];
    $t = _turba_getFieldById($source, $id, $field = 'name');
    if (!is_a($t, 'PEAR_Error')) {
        return $t;
    } else {
        return _("Contact not found.") . "source: $source. id: $id";
    }
}
