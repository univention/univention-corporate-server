<?php
/**
 * $Horde: turba/search.php,v 1.94.4.22 2009-01-06 15:27:39 jan Exp $
 *
 * Copyright 2000-2009 The Horde Project (http://www.horde.org/)
 *
 * See the enclosed file LICENSE for license information (ASL).  If you
 * did not receive this file, see http://www.horde.org/licenses/asl.php.
 *
 * @author Chuck Hagenbuch <chuck@horde.org>
 */

/**
 * Add a virtual address book for the current user.
 *
 * @param array  The parameters for this virtual address book.
 *
 * @return mixed  The virtual address book ID | PEAR_Error
 */
function _createVBook($params)
{
    $params = array(
        'name' => $params['name'],
        'params' => serialize(array('type' => 'vbook',
                                    'source' => $params['source'],
                                    'criteria' => $params['criteria'])));

    $share = &Turba::createShare(md5(microtime()), $params);
    if (is_a($share, 'PEAR_Error')) {
        return $share;
    }

    return $share->getName();
}

/**
 * Check for requested changes in sort order and apply to prefs.
 */
function updateSortOrderFromVars()
{
    require_once 'Horde/Variables.php';
    $vars = Variables::getDefaultVariables();
    $source = Util::getFormData('source');

    if (($sortby = $vars->get('sortby')) !== null && $sortby != '') {
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
        $GLOBALS['prefs']->setValue('sortorder', serialize($sortorder));
    }
}

require_once dirname(__FILE__) . '/lib/base.php';
require_once TURBA_BASE . '/lib/List.php';
require_once TURBA_BASE . '/lib/ListView.php';

/* Verify if the search mode variable is passed in form or is
 * registered in the session. Always use basic search by default. */
if (Util::getFormData('search_mode')) {
    $_SESSION['turba']['search_mode'] = Util::getFormData('search_mode');
}
if (!isset($_SESSION['turba']['search_mode'])) {
    $_SESSION['turba']['search_mode'] = 'basic';
}

/* Get the current source. */
$source = Util::getFormData('source', $default_source);
if (!isset($cfgSources[$source])) {
    reset($cfgSources);
    $source = key($cfgSources);

    /* If there are absolutely no valid sources, abort. */
    if (!isset($cfgSources[$source])) {
        $notification->push(_("No Address Books are currently available. Searching is disabled."), 'horde.error');
        require TURBA_TEMPLATES . '/common-header.inc';
        require TURBA_TEMPLATES . '/menu.inc';
        require $registry->get('templates', 'horde') . '/common-footer.inc';
        exit;
    }
}

/* Grab the form data. */
$criteria = Util::getFormData('criteria');
$val = Util::getFormData('val');
$action = Util::getFormData('actionID');
$driver = &Turba_Driver::singleton($source);
if (is_a($driver, 'PEAR_Error')) {
    $notification->push(sprintf(_("Failed to access the address book: %s"), $driver->getMessage()), 'horde.error');
    $map = array();
} else {
    $map = $driver->getCriteria();
    if ($_SESSION['turba']['search_mode'] == 'advanced') {
        $criteria = array();
        foreach ($map as $key => $value) {
            if ($key != '__key') {
                $val = Util::getFormData($key);
                if (strlen($val)) {
                    $criteria[$key] = $val;
                }
            }
        }
    }

    /* Check for updated sort criteria */
    updateSortOrderFromVars();

    /* Only try to perform a search if we actually have search criteria. */
    if ((is_array($criteria) && count($criteria)) || !empty($val)) {
        if (Util::getFormData('save_vbook')) {
            /* We create the vbook and redirect before we try to search
             * since we are not displaying the search results on this page
             * anyway. */
            $vname = Util::getFormData('vbook_name');
            if (empty($vname)) {
                $notification->push(_("You must provide a name for virtual address books."), 'horde.error');
                header('Location: ' . Horde::applicationUrl('search.php', true));
                exit;
            }

            /* Create the vbook. */
            $params = array(
                'name' => $vname,
                'source' => $source,
                'criteria' => $_SESSION['turba']['search_mode'] == 'basic' ? array($criteria => $val) : $criteria,
            );
            $vid = _createVBook($params);
            if (is_a($vid, 'PEAR_Error')) {
                $notification->push(sprintf(_("There was a problem creating the virtual address book: %s"), $vid->getMessage()), 'horde.error');
                header('Location: ' . Horde::applicationUrl('search.php', true));
                exit;
            }
            $notification->push(sprintf(_("Successfully created virtual address book \"%s\""), $vname), 'horde.success');

            $url = Horde::applicationURL('browse.php', true);
            $url = Util::addParameter($url, array('source' => $vid, null, false));
            header('Location: ' . $url);
            exit;
        }

        /* Perform a search. */
        if (($_SESSION['turba']['search_mode'] == 'basic' &&
             is_object($results = $driver->search(array($criteria => $val)))) ||
            ($_SESSION['turba']['search_mode'] == 'advanced' &&
             is_object($results = $driver->search($criteria)))) {
            if (is_a($results, 'PEAR_Error')) {
                $notification->push($results, 'horde.error');
            } else {
                /* Read the columns to display from the preferences. */
                $sources = Turba::getColumns();
                $columns = isset($sources[$source]) ? $sources[$source] : array();
                $results->sort(Turba::getPreferredSortOrder());

                $view = &new Turba_ListView($results, null, $columns);
                $view->setType('search');
            }
        } else {
            $notification->push(_("Failed to search the address book"), 'horde.error');
        }
    }
}

if ($_SESSION['turba']['search_mode'] == 'basic') {
    $title = _("Basic Search");
    $notification->push('document.directory_search.val.focus();', 'javascript');
} else {
    $title = _("Advanced Search");
    $notification->push('document.directory_search.name.focus();', 'javascript');
}

Horde::addScriptFile('prototype.js', 'turba', true);
Horde::addScriptFile('QuickFinder.js', 'turba', true);
Horde::addScriptFile('effects.js', 'turba', true);
Horde::addScriptFile('redbox.js', 'turba', true);
require TURBA_TEMPLATES . '/common-header.inc';
require TURBA_TEMPLATES . '/menu.inc';
require TURBA_TEMPLATES . '/browse/search.inc';
if ($_SESSION['turba']['search_mode'] == 'advanced') {
    require TURBA_TEMPLATES . '/browse/search_criteria.inc';
}
require TURBA_TEMPLATES . '/browse/search_vbook.inc';
if (isset($view) && is_object($view)) {
    require TURBA_TEMPLATES . '/browse/javascript.inc';
    require TURBA_TEMPLATES . '/browse/header.inc';
    $view->display();
}
require $registry->get('templates', 'horde') . '/common-footer.inc';
