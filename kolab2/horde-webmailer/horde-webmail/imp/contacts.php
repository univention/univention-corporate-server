<?php
/**
 * $Horde: imp/contacts.php,v 2.67.10.12 2009-01-06 15:24:01 jan Exp $
 *
 * Copyright 2002-2009 The Horde Project (http://www.horde.org/)
 *
 * See the enclosed file COPYING for license information (GPL). If you
 * did not receive this file, see http://www.fsf.org/copyleft/gpl.html.
 */

@define('IMP_BASE', dirname(__FILE__));
$authentication = 'horde';
require_once IMP_BASE . '/lib/base.php';
require_once IMP_BASE . '/lib/Compose.php';
require_once IMP_BASE . '/lib/Template.php';

/* Get the lists of address books through the API. */
$source_list = $registry->call('contacts/sources');

/* If we self-submitted, use that source. Otherwise, choose a good
 * source. */
$source = Util::getFormData('source');
if (empty($source) || !isset($source_list[$source])) {
    /* We don't just pass the second argument to getFormData() because
     * we want to trap for invalid sources, not just no source. */
    reset($source_list);
    $source = key($source_list);
}

/* Get the search as submitted (defaults to '' which should list everyone). */
$search = Util::getFormData('search');

/* Get the name of the calling form (Defaults to 'compose'). */
$formname = Util::getFormData('formname', 'compose');

/* Are we limiting to only the 'To:' field? */
$to_only = Util::getFormData('to_only');

$apiargs = array(
    'addresses' => array($search),
    'addressbooks' => array($source),
    'fields' => array()
);

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

$results = array();
if (Util::getFormData('searched') || $prefs->getValue('display_contact')) {
    $results = $registry->call('contacts/search', $apiargs);
}

/* The results list returns an array for each source searched - at least
 * that's how it looks to me. Make it all one array instead. */
$addresses = array();
foreach ($results as $r) {
    $addresses = array_merge($addresses, $r);
}

/* If self-submitted, preserve the currently selected users encoded by
 * javascript to pass as value|text. */
$selected_addresses = array();
foreach (explode('|', Util::getFormData('sa')) as $addr) {
    if (strlen(trim($addr))) {
        $selected_addresses[] = @htmlspecialchars($addr, ENT_QUOTES, NLS::getCharset());
    }
}

/* Prepare the contacts template. */
$template = new IMP_Template();
$template->setOption('gettext', true);

$template->set('action', Horde::url(Util::addParameter(Horde::applicationUrl('contacts.php'), 'uniq', base_convert(microtime(), 10, 36))));
$template->set('formname', $formname);
$template->set('formInput', Util::formInput());
$template->set('search', htmlspecialchars($search));
if (count($source_list) > 1) {
    $template->set('multiple_source', true);
    $s_list = array();
    foreach ($source_list as $key => $select) {
       $s_list[] = array('val' => $key, 'selected' => ($key == $source), 'label' => htmlspecialchars($select));
    }
    $template->set('source_list', $s_list);
} else {
    $template->set('source_list', key($source_list));
}
if ($browser->isBrowser('msie')) {
    $template->set('select_event', ' ondblclick="addAddress(\'to\')"');
    $template->set('option_event', null);
} else {
    $template->set('select_event', null);
    $template->set('option_event', ' ondblclick="addAddress(\'to\')"');
}
$a_list = array();
foreach ($addresses as $addr) {
    if (!empty($addr['email'])) {
        if (strpos($addr['email'], ',') !== false) {
            $a_list[] = @htmlspecialchars(IMP_Compose::rfc2822Encode($addr['name'], 'personal') . ': ' . $addr['email'] . ';', ENT_QUOTES, NLS::getCharset());
        } else {
            $mbox_host = explode('@', $addr['email']);
            if (isset($mbox_host[1])) {
                $a_list[] = @htmlspecialchars(MIME::rfc822WriteAddress($mbox_host[0], $mbox_host[1], $addr['name']), ENT_QUOTES, NLS::getCharset());
            }
        }
    }
}
$template->set('a_list', $a_list);
$template->set('cc', !$to_only);
$template->set('sa', $selected_addresses);

/* Display the form. */
$title = _("Address Book");
Horde::addScriptFile('prototype.js', 'imp', true);
Horde::addScriptFile('contacts.js', 'imp', true);
require IMP_TEMPLATES . '/common-header.inc';
IMP::addInlineScript(array(
    'var formname = \'' . $formname . '\'',
    'var to_only = ' . intval($to_only),
));
echo $template->fetch(IMP_TEMPLATES . '/contacts/contacts.html');
require $registry->get('templates', 'horde') . '/common-footer.inc';
