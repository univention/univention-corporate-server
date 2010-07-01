<?php
/**
 * $Horde: kronolith/contacts.php,v 1.16.10.8 2009-01-06 15:24:43 jan Exp $
 *
 * Copyright 2002-2009 The Horde Project (http://www.horde.org/)
 *
 * See the enclosed file COPYING for license information (GPL). If you
 * did not receive this file, see http://www.fsf.org/copyleft/gpl.html.
 */

@define('KRONOLITH_BASE', dirname(__FILE__));
require_once KRONOLITH_BASE . '/lib/base.php';

if (!Auth::getAuth()) {
    Util::closeWindowJS();
    exit;
}

/* Get the lists of address books through API */
$source_list = $registry->call('contacts/sources');

/* If we self-submitted, use that source. Otherwise, choose a good
 * source. */
$source = Util::getFormData('source');
if (empty($source) || !isset($source_list[$source])) {
    /* We don't just pass the second argument to getFormData() because
     * we want to trap for invalid sources, not just no source. */
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

/* The results list returns an array for each source searched - at least
   that's how it looks to me. Make it all one array instead. */
$addresses = array();
if (!is_a($results, 'PEAR_Error')) {
    foreach ($results as $r) {
        $addresses = array_merge($addresses, $r);
    }
}

/* If self-submitted, preserve the currently selected users encoded by
   javascript to pass as value|text. */
$selected_addresses = array();
$sa = explode('|', Util::getFormData('sa'));
for ($i = 0; $i < count($sa) - 1; $i += 2) {
    $selected_addresses[$sa[$i]] = $sa[$i + 1];
}

/* Set the default list display (name or email). */
$display = Util::getFormData('display', 'name');

/* Display the form. */
$title = _("Address Book");
require KRONOLITH_TEMPLATES . '/common-header.inc';
require KRONOLITH_TEMPLATES . '/contacts/contacts.inc';
require $registry->get('templates', 'horde') . '/common-footer.inc';
