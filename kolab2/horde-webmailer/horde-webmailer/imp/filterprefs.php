<?php
/**
 * $Horde: imp/filterprefs.php,v 2.16.10.12 2009-01-06 15:24:01 jan Exp $
 *
 * Copyright 2003-2009 The Horde Project (http://www.horde.org/)
 *
 * See the enclosed file COPYING for license information (GPL). If you
 * did not receive this file, see http://www.fsf.org/copyleft/gpl.html.
 *
 * @author Michael Slusarz <slusarz@horde.org>
 */

@define('IMP_BASE', dirname(__FILE__));
require_once IMP_BASE . '/lib/base.php';
require_once IMP_BASE . '/lib/Template.php';
require_once 'Horde/Help.php';
require_once 'Horde/Prefs/UI.php';
if (is_callable(array('Horde', 'loadConfiguration'))) {
    $result = Horde::loadConfiguration('prefs.php', array('prefGroups', '_prefs'), 'imp');
    if (!is_a($result, 'PEAR_Error')) {
        extract($result);
    }
} else {
    require IMP_BASE . '/config/prefs.php';
}

/* Are preferences locked? */
$login_locked = $prefs->isLocked('filter_on_login') || empty($_SESSION['imp']['filteravail']);
$display_locked = $prefs->isLocked('filter_on_display') || empty($_SESSION['imp']['filteravail']);
$sidebar_locked = $prefs->isLocked('filter_on_sidebar') || empty($_SESSION['imp']['filteravail']);
$anymailbox_locked = $prefs->isLocked('filter_any_mailbox') || empty($_SESSION['imp']['filteravail']);
$menuitem_locked = $prefs->isLocked('filter_menuitem');

/* Run through the action handlers. */
$actionID = Util::getFormData('actionID');
switch ($actionID) {
case 'update_prefs':
    if (!$login_locked) {
        $prefs->setValue('filter_on_login', Util::getFormData('filter_login') ? 1 : 0);
    }
    if (!$display_locked) {
        $prefs->setValue('filter_on_display', Util::getFormData('filter_display') ? 1 : 0);
    }
    if (!$sidebar_locked) {
        $prefs->setValue('filter_on_sidebar', Util::getFormData('filter_sidebar') ? 1 : 0);
    }
    if (!$anymailbox_locked) {
        $prefs->setValue('filter_any_mailbox', Util::getFormData('filter_any_mailbox') ? 1 : 0);
    }
    if (!$menuitem_locked) {
        $prefs->setValue('filter_menuitem', Util::getFormData('filter_menuitem') ? 1 : 0);
    }
    $notification->push(_("Preferences successfully updated."), 'horde.success');
    break;
}

$app = 'imp';
$chunk = Util::nonInputVar('chunk');
$group = 'filters';
Prefs_UI::generateHeader(null, $chunk);

$t = new IMP_Template();
$t->setOption('gettext', true);
$t->set('navcell', Util::bufferOutput(array('Prefs_UI', 'generateNavigationCell'), 'filters'));
$t->set('prefsurl', IMP::prefsURL(true));
$t->set('return_text', _("Return to Options"));

/* Get filter links. */
$blacklist_link = $whitelist_link = $filters_link = false;
if ($registry->hasMethod('mail/showBlacklist')) {
    $blacklist_link = $registry->link('mail/showBlacklist');
}
if ($registry->hasMethod('mail/showWhitelist')) {
    $whitelist_link = $registry->link('mail/showWhitelist');
}
if ($registry->hasMethod('mail/showFilters')) {
    $filters_link = $registry->link('mail/showFilters');
}

/* If filters are disabled. */
if (!$blacklist_link && !$whitelist_link && !$filters_link) {
    $t->set('notactive', true);
} else {
    $t->set('selfurl', Horde::applicationUrl('filterprefs.php'));
    $t->set('forminput', Util::formInput());
    $t->set('group', $group);
    $t->set('app', $app);

    $link_array = array(
        array('g' => _("Edit your Filter Rules"), 'l' => $filters_link, 'h' => 'filter-edit-rules'),
        array('g' => _("Edit your Blacklist"), 'l' => $blacklist_link, 'h' => 'filter-edit-blacklist'),
        array('g' => _("Edit your Whitelist"), 'l' => $whitelist_link, 'h' => 'filter-edit-whitelist')
    );
    $links = array();
    foreach ($link_array as $key => $val) {
        if ($val['l']) {
            $links[] = array(
                'img' => Horde::img('filters.png', $val['g']),
                'link' => Horde::link(Horde::url($val['l'])),
                'help' => Help::link('imp', $val['h']),
                'text' => $val['g']
            );
        }
    }
    $t->set('links', $links);

    $options_array = array(
        'login' => array('g' => _("Apply filter rules upon logging on?"), 'p' => 'filter_on_login', 'h' => 'filter-on-login', 'l' => $login_locked),
        'display' => array('g' => _("Apply filter rules whenever Inbox is displayed?"), 'p' => 'filter_on_display', 'h' => 'filter-on-display', 'l' => $display_locked),
        'sidebar' => array('g' => _("Apply filter rules whenever sidebar is refreshed?"), 'p' => 'filter_on_sidebar', 'h' => 'filter-on-sidebar', 'l' => $sidebar_locked),
        'any_mailbox' => array('g' => _("Allow filter rules to be applied in any mailbox?"), 'p' => 'filter_any_mailbox', 'h' => 'filter-any-mailbox', 'l' => $anymailbox_locked),
        'menuitem' => array('g' => _("Show the filter icon on the menubar?"), 'p' => 'filter_menuitem', 'l' => $menuitem_locked));
    if ($_SESSION['imp']['base_protocol'] == 'pop3') {
        unset($options_array['any_mailbox']);
    }
    $opts = array();
    foreach ($options_array as $key => $val) {
        if (!$val['l']) {
            $opts[] = array(
                'key' => $key,
                'checked' => $prefs->getValue($val['p']),
                'label' => Horde::label('filter_' . $key, $val['g']),
                'help' => isset($val['h']) ? Help::link('imp', $val['h']) : null
            );
        }
    }
    $t->set('opts', $opts);
    if (!empty($opts)) {
        $t->set('save_opts', _("Save Options"));
    }
}

echo $t->fetch(IMP_TEMPLATES . '/filters/prefs.html');
if (!$chunk) {
    require $registry->get('templates', 'horde') . '/common-footer.inc';
}
