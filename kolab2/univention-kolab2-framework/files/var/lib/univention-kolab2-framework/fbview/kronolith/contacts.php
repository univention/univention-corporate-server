<?php
/**
 * $Horde: kronolith/contacts.php,v 1.13 2004/02/14 02:40:34 chuck Exp $
 *
 * Copyright 2002-2004 Marcus I. Ryan <marcus@riboflavin.net>
 *
 * See the enclosed file COPYING for license information (GPL). If you
 * did not receive this file, see http://www.fsf.org/copyleft/gpl.html.
 */

define('KRONOLITH_BASE', dirname(__FILE__));
require_once KRONOLITH_BASE . '/lib/base.php';

if (!Auth::getAuth()) {
    Util::closeWindowJS();
    exit;
}

/* Get the lists of address books through API */
$source_list = $registry->call('contacts/sources');

// If we self-submitted, use that source. Otherwise, choose a good
// source.
if (!($source = Util::getFormData('source'))) {
    if ($prefs->getValue('add_source')) {
        // The most likely personal address book is the one we add to.
        $source = $prefs->getValue('add_source');
    } elseif ($prefs->getValue('search_sources')) {
        // If we can't/don't add, do we search?  If so take the first.
        $search_sources = $prefs->getValue('search_sources');
        $source = $search_sources[0];
    }
}
if (empty($source) || !isset($source_list[$source])) {
    $source = key($source_list);
}

/* Get the search as submitted (defaults to '' which should list everyone). */
$search = Util::getFormData('search');
$apiargs = array();
$apiargs['addresses'] = array($search);
$apiargs['addressbooks'] = array($source);
$apiargs['fields'] = array();

if ($search_fields_pref = $prefs->getValue('search_fields')) {
    foreach (explode("\n", $search_fields_pref) as $s) {
        $s = trim($s);
        $s = explode("\t", $s);
        if (!empty($s[0]) && ($s[0] == $source)) {
            $apiargs['fields'][array_shift($s)] = $s;
            break;
        }
    }
}

if ($search || $prefs->getValue('display_contact')) {
    $results = $registry->call('contacts/search', $apiargs);
} else {
    $results = array();
}

/* The results list returns an array for each source searched - at
   least that's how it looks to me. Make it all one array instead. */
$addresses = array();
if (!PEAR::isError($results)) {
    foreach ($results as $r) {
        $addresses = array_merge($addresses, $r);
    }
}

/* If self-submitted, preserve the currently selected users encoded by
   javascript to pass as value|text. */
$selected_addresses = array();
foreach ($_GET as $key => $value) {
    if (substr($key, 0, 2) == 'sa') {
        $a = explode('|', $value);
        $selected_addresses[$a[0]] = $a[1];
    }
}

/* Set the default list display (name or email). */
$display = Util::getFormData('display', 'name');

/* Display the form. */
$tabindex = 1;
$title = _("Contact List");
require KRONOLITH_TEMPLATES . '/common-header.inc';
require KRONOLITH_TEMPLATES . '/contacts/javascript.inc';
require KRONOLITH_TEMPLATES . '/contacts/contacts.inc';
require $registry->getParam('templates', 'horde') . '/common-footer.inc';
