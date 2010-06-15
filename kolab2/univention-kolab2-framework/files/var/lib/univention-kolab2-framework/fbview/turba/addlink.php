<?php
/**
 * $Horde: turba/addlink.php,v 1.16 2004/04/07 14:43:52 chuck Exp $
 *
 * Copyright 2000-2004 Chuck Hagenbuch <chuck@horde.org>
 *
 * See the enclosed file COPYING for license information (GPL). If you
 * did not receive this file, see http://www.fsf.org/copyleft/gpl.html.
 */

define('TURBA_BASE', dirname(__FILE__));
require_once TURBA_BASE . '/lib/base.php';
require_once 'Horde/Menu.php';

$return_url = Util::getFormData('url');
$link_type = Util::getFormData('link_type');
$reverse = (substr($link_type, -8) == '/reverse') ? '/reverse' : '';
if (!empty($reverse)) {
    $link_type = substr($link_type, 0, -8);
}
$from_application = Util::getFormData('from_application');
$from_parameters = @unserialize(Util::getFormData('from_parameters'));
$to_application = Util::getFormData('to_application');

switch (Util::getFormData('actionID')) {
case 'addlink_add':
    if (!empty($to_application)) {
        require_once 'Horde/Links.php';
        $links = &Horde_Links::singleton($registry->getApp());

        $to_parameters = @unserialize(Util::getFormData('to_parameters'));
       
        if (empty($reverse)) {
            $link_data = array('to_params' => $to_parameters, 
                               'from_params' => $from_parameters, 
                               'link_params' => array('link_type' => $link_type,
                                                      'to_application' => $to_application,
                                                      'from_application' => $from_application));
        } else {
            // Switch 'to' and 'from' for reverse links.
            $link_data = array('to_params' => $from_parameters, 
                               'from_params' => $to_parameters, 
                               'link_params' => array('link_type' => $link_type,
                                                      'to_application' => $from_application,
                                                      'from_application' => $to_application));
        }
        $status = $links->addLink($link_data);

        if (is_a($status, 'PEAR_Error')) {
            $notification->push($status, 'horde.error');
        } elseif ($registry->hasMethod($to_application . '/getLinkSummary')) {
            $notification->push(sprintf(_("Added a %s link to %s."), $link_type,
                                        $registry->call($to_application . '/getLinkSummary', array($link_data))), 'horde.success');
        } else {
            $notification->push(_("Link added."), 'horde.success');
        }

        header('Location: ' . $return_url);
        exit;
    }
    break;

case 'addlink_cancel':
    $notification->push(_("Link canceled."), 'horde.message');
    header('Location: ' . $return_url);
    exit;
}

/* Get the lists of address books through the API. */
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

$results = $registry->call('contacts/search', $apiargs);

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

/* Set the to_application to be included in the form. */
$to_application = $registry->getParam('provides');
if (is_array($to_application)) {
    $to_application = $to_application[0];
}

/* Display the form. */
$tabindex = 1;
$title = _("Contact List");
require TURBA_TEMPLATES . '/common-header.inc';
require TURBA_TEMPLATES . '/addlink/menu.inc';
$notification->notify(array('listeners' => 'status'));
require TURBA_TEMPLATES . '/addlink/contacts.inc';
require $registry->getParam('templates', 'horde') . '/common-footer.inc';
