<?php
/**
 * $Horde: turba/browse.php,v 1.64 2004/04/07 14:43:52 chuck Exp $
 *
 * Turba: Copyright 2000-2004 Charles J. Hagenbuch <chuck@horde.org>
 *
 * You should have received a copy of the GNU Public
 * License along with this package; if not, write to the
 * Free Software Foundation, Inc., 59 Temple Place - Suite 330,
 * Boston, MA 02111-1307, USA.
 */

@define('TURBA_BASE', dirname(__FILE__));
require_once TURBA_BASE . '/lib/base.php';
require_once TURBA_BASE . '/lib/Source.php';
require_once TURBA_BASE . '/lib/List.php';
require TURBA_BASE . '/config/attributes.php';

/* Sort out the sorting values. */
if (($sortby = Util::getFormData('sortby')) !== null) {
    if ($sortby == 'name') {
        if ($prefs->getValue('name_format') == 'first_last') {
            $sortby = 'name';
        } else {
            $sortby = 'lastname';
        }
    }
    $prefs->setValue('sortby', $sortby);
}
if (($sortdir = Util::getFormData('sortdir')) !== null) {
    $prefs->setValue('sortdir', $sortdir);
}

$title = _("Address Book Listing");

/* Build the directory sources select widget. */
$source = Util::getFormData('source', $prefs->getValue('default_dir'));
$source_options = '';
$add_source_options = '';
$source_count = 0;
foreach ($cfgSources as $key => $curSource) {
    if (!empty($curSource['export'])) {
        $selected = ($key == $source) ? ' selected="selected"' : '';
        $source_options .= '<option value="' . $key . '" ' . $selected;
        $source_options .= '>' . htmlspecialchars($curSource['title']) . '</option>';
        if ($key != $source && empty($curSource['readonly']) || (isset($curSource['admin']) && in_array(Auth::getAuth(), $curSource['admin']))) {
            $add_source_options .= '<option value="' . $key . '">' . htmlspecialchars($curSource['title']) . '</option>';
        }
        $source_count++;
        if (empty($source)) {
            $source = $key;
        }
    }
}

if ($source_count == 0) {
    $notification->push(_("There are no browseable address books."), 'horde.warning');
} else {
    $driver = &Turba_Source::singleton($source, $cfgSources[$source]);
    if (is_a($driver, 'PEAR_Error')) {
        $notification->push(sprintf(_("Failed to access the specified address book: %s"), $driver->getMessage()), 'horde.error');
        unset($driver);
    }
}

if (isset($driver)) {
    $actionID = Util::getFormData('actionID');

    /* Run through the action handlers. */
    switch ($actionID) {
    case 'delete':
        /* Remove a contact from a list. */
        $keys = Util::getFormData('objectkeys');
        if (is_array($keys)) {
            $key = Util::getFormData('key', false);
            if ($key && $key != '**search') {
                /* We are removing a contact from a list. */
                $list = $driver->getObject($key);
                foreach ($keys as $sourceKey) {
                    list($source, $objectKey) = explode(':', $sourceKey, 2);
                    if (!$list->removeMember($driver->getObject($objectKey))) {
                        $notification->push(_("There was an error removing this object."), 'horde.error');
                    } else {
                        $notification->push(_("Contact removed from list."), 'horde.success');
                    }
                }
            } else {
                /* We are deleting an object. */
                foreach ($keys as $sourceKey) {
                    list($source, $objectKey) = explode(':', $sourceKey, 2);
                    if (!$driver->removeObject($objectKey)) {
                        $notification->push(_("There was an error deleting this object."), 'horde.error');
                    }
                }
            }

            /* Remove the objects from search results too. */
            if (!empty($_SESSION['turba_search_results'])) {
                require_once TURBA_BASE . '/lib/Object.php';
                $list = Turba_List::unserialize($_SESSION['turba_search_results']);
                foreach ($keys as $sourceKey) {
                    list($source, $objectKey) = explode(':', $sourceKey, 2);
                    $list->remove($objectKey);
                }
                $_SESSION['turba_search_results'] = $list->serialize();
            }
        }
        break;

    case 'move':
    case 'copy':
        $keys = Util::getFormData('objectkeys');
        if (is_array($keys) && count($keys)) {
            // If we have data, try loading the target address book
            // driver.
            $targetSource = Util::getFormData('targetAddressbook');
            $targetDriver = &Turba_Source::singleton($targetSource, $cfgSources[$targetSource]);

            if (is_a($targetDriver, 'PEAR_Error')) {
                $notification->push(sprintf(_("Failed to access the specified address book: %s"), $targetDriver->getMessage()), 'horde.error');
            } else {
                foreach ($keys as $sourceKey) {
                    // Split up the key into source and object ids.
                    list($source, $objectKey) = explode(':', $sourceKey, 2);

                    // Ignore this entry if the target is the same as
                    // the source.
                    if ($source == $targetDriver->name) {
                        continue;
                    }

                    // Try and load the driver for the source.
                    $sourceDriver = &Turba_Source::singleton($source, $cfgSources[$source]);
                    if (is_a($sourceDriver, 'PEAR_Error')) {
                        $notification->push(sprintf(_("Failed to access the specified address book: %s"), $sourceDriver->getMessage()), 'horde.error');
                    } else {
                        // Get the object.
                        $object = $sourceDriver->getObject($objectKey);
                        if (is_a($object, 'PEAR_Error')) {
                            $notification->push(sprintf(_("Failed to find object to be added: %s"), $object->getMessage()), 'horde.error');
                        } else {
                            // Try adding to the target.
                            $result = $targetDriver->addObject($object->getAttributes());
                            if (is_a($result, 'PEAR_Error')) {
                                $notification->push(sprintf(_("Failed to add %s to %s: %s"), $object->getValue('name'), $targetDriver->title, $result->getMessage()), 'horde.error');
                            } else {
                                $notification->push(sprintf(_("Successfully added %s to %s"), $object->getValue('name'), $targetDriver->title), 'horde.success');

                                // If we're moving objects, and we
                                // succeeded, delete it from the
                                // original source now.
                                if ($actionID == 'move') {
                                    if (!$sourceDriver->removeObject($objectKey)) {
                                        $notification->push(sprintf(_("There was an error deleting %s from the source address book."), $object->getValue('name')), 'horde.error');
                                    }
                                }
                            }
                        }
                    }
                }
            }
        }
        break;

    case 'add':
        /* Add a contact to a list. */
        $keys = Util::getFormData('objectkeys');
        $targetKey = Util::getFormData('targetList');
        if (empty($targetKey)) {
            break;
        }

        if (!Util::getFormData('targetNew')) {
            $target = $driver->getObject($targetKey);
        }

        if (!empty($target) && is_object($target) && $target->isGroup()) {
            /* Adding contact to an existing list */
            if (is_array($keys)) {
                foreach ($keys as $sourceKey) {
                    list($source, $objectKey) = explode(':', $sourceKey, 2);
                    $target->addMember($driver->getObject($objectKey));
                }
                $target->store();
            }
        } else {
            /* Adding contact to a new list. */
            $newList = array();
            $newList['__owner'] = Auth::getAuth();
            $newList['__type'] = 'Group';
            $newList['name'] = $targetKey;

            $targetKey = $driver->addObject($newList);
            $target = $driver->getObject($targetKey);
            if (!empty($target) && is_object($target) && $target->isGroup()) {
                if (is_array($keys)) {
                    foreach ($keys as $sourceKey) {
                        list($source, $objectKey) = explode(':', $sourceKey, 2);
                        $target->addMember($driver->getObject($objectKey));
                    }
                    $target->store();
                }
            } else {
                $notification->push(_("There was an error creating a new list."), 'horde.error');
            }
        }
        break;
    }
}

$templates = array();
if (isset($driver)) {
    $templates[] = '/browse/javascript.inc';

    /* Read the columns to display from the preferences. */
    $sources = Turba::string2Columns($prefs->getValue('columns'));
    $columns = isset($sources[$source]) ? $sources[$source] : array();
    $width = floor(90 / (count($columns) + 1));

    /* Determine the name of the column to sort by. */
    $sortcolumn = ($prefs->getValue('sortby') == 0 ||
                   !isset($columns[$prefs->getValue('sortby') - 1])) ?
        (($prefs->getValue('name_format') == 'first_last') ? 'name' : 'lastname') : $columns[$prefs->getValue('sortby') - 1];

    /* Create list of lists for Add to. */
    $addToList = array();
    if (!empty($cfgSources[$source]['map']['__type'])) {
        $listList = $driver->search(array('__type' => 'Group'));
        $listList->reset();
        while ($listObject = $listList->next()) {
            $addToList[] = array('name' => $listObject->getValue('name'), 'key' => $listObject->getValue('__key'));
        }
    }

    if (isset($_SESSION['turba_search_results']) &&
        (Util::getFormData('key') == '**search')) {
        /* We are displaying some search results. */
        $results = Turba_List::unserialize($_SESSION['turba_search_results']);
        $results->sort($sortcolumn, $prefs->getValue('sortdir'));

        $templates[] = '/browse/search.inc';

        if ($_SESSION['turba_search_mode'] == 'advanced') {
            $map = $driver->getCriteria();
            $templates[] = '/browse/search_criteria.inc';
        }

        $templates[] = '/browse/header.inc';
        $templates[] = '/browse/actions.inc';
        $templates[] = '/browse/column_headers.inc';

        $title =_("Search Results");
        $listType = 'search';

        if ($_SESSION['turba_search_mode'] == 'basic') {
            $notification->push('document.directory_search.val.focus();', 'javascript');
        } else {
            $notification->push('document.directory_search.name.focus();', 'javascript');
        }

        require_once TURBA_BASE . '/lib/ListView.php';
        $display = &new Turba_ListView($results, TURBA_TEMPLATES . '/browse/contactrow.inc');
    } elseif (Util::getFormData('key')) {
        /* We are displaying the contents of a list. */
        $list = $driver->getObject(Util::getFormData('key'));
        if (isset($list) && is_object($list) && !is_a($list, 'PEAR_Error') && $list->isGroup()) {
            $title = sprintf(_("Contacts in list: %s"), $list->getValue('name'));
            $templates[] = '/browse/header.inc';

            /* Show List Members. */
            if (!is_object($results = $list->listMembers($sortcolumn, $prefs->getValue('sortdir')))) {
                $notification->push(_("Failed to browse list"), 'horde.error');
            } else {
                $listType = 'list';
                $templates[] = '/browse/actions.inc';
                $templates[] = '/browse/column_headers.inc';

                require_once TURBA_BASE . '/lib/ListView.php';
                $display = &new Turba_ListView($results, TURBA_TEMPLATES . '/browse/contactrow.inc');
            }
        } else {
            $notification->push(_("There was an error displaying the select List"), 'horde.error');
        }
    } else {
        /* We are displaying the contents of the address book. */
        if ($source_count > 1) {
            $templates[] = '/browse/select.inc';
        }
        $title = sprintf(_("Contents of %s"), $cfgSources[$source]['title']);
        $templates[] = '/browse/header.inc';
        if (Util::getFormData('show', 'all') == 'contacts') {
            /* Show Contacts. */
            $results = $driver->search(array('__type' => 'Object'), $sortcolumn, 'AND', $prefs->getValue('sortdir'));
        } elseif (Util::getFormData('show', 'all') == 'lists') {
            /* Show Lists. */
            $results = $driver->search(array('__type' => 'Group'), $sortcolumn, 'AND', $prefs->getValue('sortdir'));
        } else {
            /* Show All. */
            $results = $driver->search(array(), $sortcolumn, 'AND', $prefs->getValue('sortdir'));
        }

        if (!is_object($results)) {
            $notification->push(_("Failed to browse the directory"), 'horde.error');
        } else {
            $listType = 'directory';
            $templates[] = '/browse/actions.inc';
            $templates[] = '/browse/column_headers.inc';

            require_once TURBA_BASE . '/lib/ListView.php';
            $display = &new Turba_ListView($results, TURBA_TEMPLATES . '/browse/contactrow.inc');
        }
    }
} else {
    $templates[] = '/browse/select.inc';
    $templates[] = '/browse/header.inc';
}

require TURBA_TEMPLATES . '/common-header.inc';
Turba::menu();

foreach ($templates as $template) {
    require TURBA_TEMPLATES . $template;
}

$footer = 'footer.inc';

if (isset($display) && is_object($display)) {
    require_once 'Horde/UI/Pager.php';
    require_once 'Horde/Variables.php';

    if (!Util::getFormData('source') == '') {
        $urlSource = Util::getFormData('source');
    } else {
        $urlSource = $source;
    }
    $viewurl = Util::addParameter('browse.php', array(
        'sortby' => $sortby,
        'sortdir' => $sortdir,
        'key' => Util::getFormData('key'),
        'source' => $urlSource
    ));

    if (Util::getFormData('key') == '**search') {
        $page = Util::getFormData('page', 0);
        $numitem = $results->count();
        $maxpage = $prefs->getValue('maxpage');
        $perpage = $prefs->getValue('perpage');

        $min = $page * $perpage;
        while ($min > $numitem) {
            $page--;
            $min = $page * $perpage;
        }
        $max = $min + $perpage;

        $start = ($page * $perpage) + 1;
        $end = min($numitem, $start + $perpage - 1);

        $numDisplayed = $display->display($min, $max);

        $vars = &Variables::getDefaultVariables();
        $pager = &new Horde_UI_Pager('page', $vars, array('num' => $numDisplayed,
                                                          'url' => $viewurl,
                                                          'page_count' => $maxpage,
                                                          'perpage' => $perpage));
    } else {
        $page = Util::getFormData('page', '*');
        if (empty($page) || !preg_match('/^[A-Za-z*]$/', $page)) {
            $page = '*';
        }

        $display->displayAlpha($page);
        $numDisplayed = $results->count();
        $footer = 'footerAlpha.inc';
    }

    require TURBA_TEMPLATES . '/browse/column_footers.inc';
}

require TURBA_TEMPLATES . '/browse/' . $footer;
require $registry->getParam('templates', 'horde') . '/common-footer.inc';
