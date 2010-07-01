<?php
/**
 * $Horde: turba/lib/Views/Browse.php,v 1.12.2.11 2009-10-01 09:57:34 jan Exp $
 *
 * Copyright 2000-2009 The Horde Project (http://www.horde.org/)
 *
 * See the enclosed file LICENSE for license information (ASL).  If you did
 * did not receive this file, see http://www.horde.org/licenses/asl.php.
 *
 * @author  Chuck Hagenbuch <chuck@horde.org>
 * @package Turba
 */

require_once TURBA_BASE . '/lib/List.php';
require_once TURBA_BASE . '/lib/ListView.php';

/**
 * The Turba_View_Browse class provides the logic for browsing lists
 * of contacts.
 *
 * @author  Chuck Hagenbuch <chuck@horde.org>
 * @since   Turba 2.2
 * @package Turba
 */
class Turba_View_Browse {

    /**
     * @var array
     */
    var $_params;

    /**
     * Constructor;
     *
     * @param array $params Stuff to import into the view's scope.
     */
    function Turba_View_Browse($params)
    {
        $this->_params = $params;
    }

    function updateSortOrderFromVars()
    {
        extract($this->_params, EXTR_REFS);

        if (strlen($sortby = $vars->get('sortby'))) {
            $sources = Turba::getColumns();
            $columns = isset($sources[$source]) ? $sources[$source] : array();
            $column_name = Turba::getColumnName($sortby, $columns);

            $append = true;
            $ascending = ($vars->get('sortdir') == 0);
            if ($vars->get('sortadd')) {
                $sortorder = Turba::getPreferredSortOrder();
                foreach ($sortorder as $i => $elt) {
                    if ($elt['field'] == $column_name) {
                        $sortorder[$i]['ascending'] = $ascending;
                        $append = false;
                    }
                }
            } else {
                $sortorder = array();
            }
            if ($append) {
                $sortorder[] = array('field' => $column_name,
                                     'ascending' => $ascending);
            }
            $prefs->setValue('sortorder', serialize($sortorder));
        }
    }

    function run()
    {
        extract($this->_params, EXTR_REFS);

        $this->updateSortOrderFromVars();

        $title = _("Address Book Listing");
        if (!$browse_source_count && $vars->get('key') != '**search') {
            $notification->push(_("There are no browseable address books."), 'horde.warning');
        } else {
            $driver = &Turba_Driver::singleton($source);
            if (is_a($driver, 'PEAR_Error')) {
                $notification->push(sprintf(_("Failed to access the address book: %s"), $driver->getMessage()), 'horde.error');
                unset($driver);
            }
        }

        if (isset($driver)) {
            $actionID = $vars->get('actionID');

            // Run through the action handlers.
            switch ($actionID) {
            case 'delete':
                $keys = $vars->get('objectkeys');
                if (!is_array($keys)) {
                    break;
                }

                $key = false;
                if ($vars->exists('key')) {
                    $key = $vars->get('key');
                }
                if ($key && $key != '**search') {
                    // We are removing a contact from a list.
                    $errorCount = 0;
                    $list = &$driver->getObject($key);
                    foreach ($keys as $sourceKey) {
                        list($objectSource, $objectKey) = explode(':', $sourceKey, 2);
                        if (!$list->removeMember($objectKey, $objectSource)) {
                            $errorCount++;
                        }
                    }
                    if (!$errorCount) {
                        $notification->push(sprintf(_("Successfully removed %d contact(s) from list."), count($keys)), 'horde.success');
                    } elseif (count($keys) == $errorCount) {
                        $notification->push(sprintf(_("Error removing %d contact(s) from list."), count($keys)), 'horde.error');
                    } else {
                        $notification->push(sprintf(_("Error removing %d of %d requested contact(s) from list."), $errorCount, count($keys)), 'horde.error');
                    }
                    $list->store();
                } else {
                    // We are deleting an object.
                    $errorCount = 0;
                    foreach ($keys as $sourceKey) {
                        list($objectSource, $objectKey) = explode(':', $sourceKey, 2);
                        if (is_a($driver->delete($objectKey), 'PEAR_Error')) {
                            $errorCount++;
                        }
                    }
                    if (!$errorCount) {
                        $notification->push(sprintf(_("Successfully deleted %d contact(s)."), count($keys)), 'horde.success');
                    } elseif (count($keys) == $errorCount) {
                        $notification->push(sprintf(_("Error deleting %d contact(s)."), count($keys)), 'horde.error');
                    } else {
                        $notification->push(sprintf(_("Error deleting %d of %d requested contacts(s)."), $errorCount, count($keys)), 'horde.error');
                    }
                }
                break;

            case 'move':
            case 'copy':
                $keys = $vars->get('objectkeys');
                if (!(is_array($keys) && $keys)) {
                    break;
                }

                // If we have data, try loading the target address book driver.
                $targetSource = $vars->get('targetAddressbook');
                $targetDriver = &Turba_Driver::singleton($targetSource);
                if (is_a($targetDriver, 'PEAR_Error')) {
                    $notification->push(sprintf(_("Failed to access the address book: %s"), $targetDriver->getMessage()), 'horde.error');
                    break;
                }

                $max_contacts = Turba::getExtendedPermission($targetDriver, 'max_contacts');
                if ($max_contacts !== true
                    && $max_contacts <= $targetDriver->count()) {
                    $message = @htmlspecialchars(sprintf(_("You are not allowed to create more than %d contacts in \"%s\"."), $max_contacts, $cfgSources[$targetSource]['title']), ENT_COMPAT, NLS::getCharset());
                    if (!empty($this->_conf['hooks']['permsdenied'])) {
                        $message = Horde::callHook('_perms_hook_denied', array('turba:max_contacts'), 'horde', $message);
                    }
                    $notification->push($message, 'horde.error', array('content.raw'));
                    break;
                }

                foreach ($keys as $sourceKey) {
                    // Split up the key into source and object ids.
                    list($objectSource, $objectKey) = explode(':', $sourceKey, 2);

                    // Ignore this entry if the target is the same as the
                    // source.
                    if ($objectSource == $targetDriver->getName()) {
                        continue;
                    }

                    // Try and load the driver for the source.
                    $sourceDriver = &Turba_Driver::singleton($objectSource);
                    if (is_a($sourceDriver, 'PEAR_Error')) {
                        $notification->push(sprintf(_("Failed to access the address book: %s"), $sourceDriver->getMessage()), 'horde.error');
                        continue;
                    }

                    $object = &$sourceDriver->getObject($objectKey);
                    if (is_a($object, 'PEAR_Error')) {
                        $notification->push(sprintf(_("Failed to find object to be added: %s"), $object->getMessage()), 'horde.error');
                        continue;
                    } elseif ($object->isGroup()) {
                        if ($actionID == 'move') {
                            $notification->push(sprintf(_("\"%s\" was not moved because it is a list."), $object->getValue('name')), 'horde.warning');
                        } else {
                            $notification->push(sprintf(_("\"%s\" was not copied because it is a list."), $object->getValue('name')), 'horde.warning');
                        }
                        continue;
                    }

                    // Try adding to the target.
                    $objAttributes = array();

                    // Get the values through the Turba_Object class.
                    foreach ($targetDriver->getCriteria() as $info_key => $info_val) {
                        if (!is_array($targetDriver->map[$info_key]) ||
                            isset($targetDriver->map[$info_key]['attribute'])) {
                            $objectValue = $object->getValue($info_key);

                            // Get 'data' value if object type is image, the
                            // direct value in other case.
                            $objAttributes[$info_key] = isset($GLOBALS['attributes'][$info_key]) && $GLOBALS['attributes'][$info_key]['type'] == 'image' ? $objectValue['load']['data'] : $objectValue;
                        }
                    }
                    unset($objAttributes['__owner']);

                    $result = $targetDriver->add($objAttributes);
                    if (is_a($result, 'PEAR_Error')) {
                        $notification->push(sprintf(_("Failed to add %s to %s: %s"), $object->getValue('name'), $targetDriver->title, $result->getMessage()), 'horde.error');
                        break;
                    }

                    $notification->push(sprintf(_("Successfully added %s to %s"), $object->getValue('name'), $targetDriver->title), 'horde.success');

                    // If we're moving objects, and we succeeded,
                    // delete them from the original source now.
                    if ($actionID == 'move') {
                        if (is_a($sourceDriver->delete($objectKey), 'PEAR_Error')) {
                            $notification->push(sprintf(_("There was an error deleting \"%s\" from the source address book."), $object->getValue('name')), 'horde.error');
                        }

                        /* Log the adding of this item in the history again,
                         * because otherwise the delete log would be after the
                         * add log. */
                        $history = &Horde_History::singleton();
                        $history->log('turba:' . $targetDriver->getName() . ':' . $objAttributes['__uid'],
                                      array('action' => 'add'), true);
                    }
                }
                break;

            case 'add':
                // Add a contact to a list.
                $keys = $vars->get('objectkeys');
                $targetKey = $vars->get('targetList');
                if (empty($targetKey)) {
                    break;
                }

                if (!$vars->exists('targetNew') || $vars->get('targetNew') == '') {
                    list($targetSource, $targetKey) = explode(':', $targetKey, 2);
                    if (!isset($cfgSources[$targetSource])) {
                        break;
                    }
                    $targetDriver = &Turba_Driver::singleton($targetSource);
                    $target = &$targetDriver->getObject($targetKey);
                    if (is_a($target, 'PEAR_Error')) {
                        $notification->push($target, 'horde.error');
                        break;
                    }
                } else {
                    $targetSource = $vars->get('targetAddressbook');
                    $targetDriver = &Turba_Driver::singleton($targetSource);
                }
                if (!empty($target) && $target->isGroup()) {
                    // Adding contact to an existing list.
                    if (is_array($keys)) {
                        $errorCount = 0;
                        foreach ($keys as $sourceKey) {
                            list($objectSource, $objectKey) = explode(':', $sourceKey, 2);
                            if (!$target->addMember($objectKey, $objectSource)) {
                                $errorCount++;
                            }
                        }
                        if (!$errorCount) {
                            $notification->push(sprintf(_("Successfully added %d contact(s) to list."), count($keys)), 'horde.success');
                        } elseif ($errorCount == count($keys)) {
                            $notification->push(sprintf(_("Error adding %d contact(s) to list."), count($keys)), 'horde.error');
                        } else {
                            $notification->push(sprintf(_("Error adding %d of %d requested contact(s) to list."), $errorCount, count($keys)), 'horde.error');
                        }
                        $target->store();
                    }
                } else {
                    // Check permissions.
                    $max_contacts = Turba::getExtendedPermission($driver, 'max_contacts');
                    if ($max_contacts !== true &&
                        $max_contacts <= $driver->count()) {
                        $message = @htmlspecialchars(sprintf(_("You are not allowed to create more than %d contacts in \"%s\"."), $max_contacts, $cfgSources[$source]['title']), ENT_COMPAT, NLS::getCharset());
                        if (!empty($this->_conf['hooks']['permsdenied'])) {
                            $message = Horde::callHook('_perms_hook_denied', array('turba:max_contacts'), 'horde', $message);
                        }

                        $notification->push($message, 'horde.error', array('content.raw'));
                        break;
                    }

                    // Adding contact to a new list.
                    $newList = array('__owner' => $targetDriver->getContactOwner(),
                                     '__type' => 'Group',
                                     'name' => $targetKey);
                    $targetKey = $targetDriver->add($newList);
                    if (!is_a($targetKey, 'PEAR_Error')) {
                        $target = &$targetDriver->getObject($targetKey);
                        if (!is_a($target, 'PEAR_Error') && $target->isGroup()) {
                            $notification->push(sprintf(_("Successfully created the contact list \"%s\"."), $newList['name']), 'horde.success');
                            if (is_array($keys)) {
                                $errorCount = 0;
                                foreach ($keys as $sourceKey) {
                                    list($objectSource, $objectKey) = explode(':', $sourceKey, 2);
                                    if (!$target->addMember($objectKey, $objectSource)) {
                                        $errorCount++;
                                    }
                                }
                                if (!$errorCount) {
                                    $notification->push(sprintf(_("Successfully added %d contact(s) to list."), count($keys)), 'horde.success');
                                } elseif ($errorCount == count($keys)) {
                                    $notification->push(sprintf(_("Error adding %d contact(s) to list."), count($keys)), 'horde.error');
                                } else {
                                    $notification->push(sprintf(_("Error adding %d of %d requested contact(s) to list."), $errorCount, count($keys)), 'horde.error');
                                }
                                $target->store();
                            }
                        }
                    } else {
                        $notification->push(_("There was an error creating a new list."), 'horde.error');
                    }
                }
                break;
            }

            // We might get here from the search page but are not allowed to browse
            // the current address book.
            if ($actionID && empty($cfgSources[$source]['browse'])) {
                header('Location: ' . Horde::applicationUrl($prefs->getValue('initial_page'), true));
                exit;
            }
        }

        $templates = array();
        if (isset($driver)) {
            $templates[] = '/browse/javascript.inc';

            // Read the columns to display from the preferences.
            $sources = Turba::getColumns();
            $columns = isset($sources[$source]) ? $sources[$source] : array();
            $sortorder = Turba::getPreferredSortOrder();

            if ($vars->get('key')) {
                // We are displaying a list.
                $list = &$driver->getObject($vars->get('key'));
                if (isset($list) && is_object($list) &&
                    !is_a($list, 'PEAR_Error') && $list->isGroup()) {
                    $title = sprintf(_("Contacts in list: %s"),
                                     $list->getValue('name'));
                    $templates[] = '/browse/header.inc';

                    // Show List Members.
                    if (!is_object($results = $list->listMembers($sortorder))) {
                        $notification->push(_("Failed to browse list"), 'horde.error');
                    } else {
                        if ($results->count() != $list->count()) {
                            $count = $list->count() - $results->count();
                            $notification->push(sprintf(ngettext("There is %d contact in this list that is not viewable to you", "There are %d contacts in this list that are not viewable to you", $count), $count), 'horde.message');
                        }
                        $view = &new Turba_ListView($results, null, $columns);
                        $view->setType('list');
                    }
                } else {
                    $notification->push(_("There was an error displaying the list"), 'horde.error');
                }
            } else {
                // We are displaying an address book.
                $title = $cfgSources[$source]['title'];
                $templates[] = '/browse/header.inc';
                if (empty($cfgSources[$source]['browse'])) {
                    $notification->push(_("Your default address book is not browseable."), 'horde.warning');
                } else {
                    $type_filter = array();
                    switch ($vars->get('show')) {
                    case 'contacts':
                        $type_filter = array('__type' => 'Object');
                        break;

                    case 'lists':
                        $type_filter = array('__type' => 'Group');
                        break;
                    }
                    $results = $driver->search($type_filter, $sortorder, 'AND', $columns);
                    if (!is_object($results)) {
                        $notification->push(_("Failed to browse the directory"), 'horde.error');
                    } elseif (is_a($results, 'PEAR_Error')) {
                        $notification->push($results, 'horde.error');
                    } else {
                        $view = &new Turba_ListView($results, null, $columns);
                        $view->setType('directory');
                    }
                }
            }
        } else {
            $templates[] = '/browse/header.inc';
        }

        Horde::addScriptFile('prototype.js', 'turba', true);
        Horde::addScriptFile('QuickFinder.js', 'turba', true);
        Horde::addScriptFile('effects.js', 'turba', true);
        Horde::addScriptFile('redbox.js', 'turba', true);
        require TURBA_TEMPLATES . '/common-header.inc';
        require TURBA_TEMPLATES . '/menu.inc';
        foreach ($templates as $template) {
            require TURBA_TEMPLATES . $template;
        }

        if (isset($view) && is_object($view)) {
            $view->display();
        }

        require $registry->get('templates', 'horde') . '/common-footer.inc';
    }

}
