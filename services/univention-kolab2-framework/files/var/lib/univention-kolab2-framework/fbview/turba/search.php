<?php
/**
 * $Horde: turba/search.php,v 1.89 2004/02/25 21:21:37 chuck Exp $
 *
 * Copyright 2000-2004 Charles J. Hagenbuch <chuck@horde.org>
 *
 * See the enclosed file COPYING for license information (GPL). If you did not
 * receive this file, see http://www.fsf.org/copyleft/gpl.html.
 */

@define('TURBA_BASE', dirname(__FILE__));
require_once TURBA_BASE . '/lib/base.php';
require_once TURBA_BASE . '/lib/Source.php';
require TURBA_BASE . '/config/attributes.php';

/* Verify if the search mode variable is passed in form or is registered in
   the session. Always use basic search by default */
if (Util::getFormData('search_mode')) {
    $_SESSION['turba_search_mode'] = Util::getFormData('search_mode');
}
if (!isset($_SESSION['turba_search_mode'])) {
    $_SESSION['turba_search_mode'] = 'basic';
}

/* Make sure the search session variable is registered in the session,
 * and obtain a global-scope reference to it. */
if (!$conf['search']['cache'] || !isset($_SESSION['turba_search_results'])) {
    $_SESSION['turba_search_results'] = null;
} else {
    if (Util::getFormData('clear')) {
        $_SESSION['turba_search_results'] = null;
    } elseif (!empty($_SESSION['turba_search_results'])) {
        require_once TURBA_BASE . '/lib/List.php';
        require_once TURBA_BASE . '/lib/Object.php';
        $_SESSION['turba_search_results'] = Turba_List::unserialize($_SESSION['turba_search_results']);
    }
}

/* Run search if there is one. */
$source = Util::getFormData('source');
if (!isset($source) && isset($cfgSources) && is_array($cfgSources) && count($cfgSources) > 0) {
    $source = $prefs->getValue('default_dir');
}
if (!isset($cfgSources[$source])) {
    reset($cfgSources);
    $source = key($cfgSources);
}

$criteria = Util::getFormData('criteria');
$val = Util::getFormData('val');
$driver = &Turba_Source::singleton($source, $cfgSources[$source]);
if (is_a($driver, 'PEAR_Error')) {
    $notification->push(_("Failed to connect to the specified directory."), 'horde.error');
    $map = array();
} else {
    $map = $driver->getCriteria();

    if ($_SESSION['turba_search_mode'] == 'advanced') {
        $criteria = array();
        foreach ($map as $key => $value) {
            if ($key != '__key') {
                $val = Util::getFormData($key);
                if (!empty($val)) {
                    $criteria[$key] = $val;
                }
            }
        }
    }

    if (isset($criteria) && isset($val)) {
        if (($_SESSION['turba_search_mode'] == 'basic' && is_object($results = $driver->search(array($criteria => $val)))) ||
            ($_SESSION['turba_search_mode'] == 'advanced' && is_object($results = $driver->search($criteria)))) {

            if (!is_object($_SESSION['turba_search_results'])) {
                $_SESSION['turba_search_results'] = &new Turba_List();
            }
            $combinedResults = &new Turba_List();
            $combinedResults->merge($_SESSION['turba_search_results'], false);
            $combinedResults->merge($results);
            $_SESSION['turba_search_results'] = $combinedResults->serialize();

            $url = Util::addParameter('browse.php', 'key', '**search');
            $url = Util::addParameter($url, 'source', $source);

            header('Location: ' . Horde::applicationUrl($url, true));
        } else {
            $notification->push(sprintf(_("Failed to search the directory: %s"), ''), 'horde.error');
        }
    }
}

if ($_SESSION['turba_search_mode'] == 'basic') {
    $title = _("Basic Search");
    $notification->push('document.directory_search.val.focus();', 'javascript');
} else {
    $title = _("Advanced Search");
    $notification->push('document.directory_search.name.focus();', 'javascript');
}

require TURBA_TEMPLATES . '/common-header.inc';
Turba::menu();
require TURBA_TEMPLATES . '/browse/search.inc';
if ($_SESSION['turba_search_mode'] == 'advanced') {
    require TURBA_TEMPLATES . '/browse/search_criteria.inc';
}
require $registry->getParam('templates', 'horde') . '/common-footer.inc';

if (is_object($_SESSION['turba_search_results'])) {
    $_SESSION['turba_search_results'] = $_SESSION['turba_search_results']->serialize();
}
