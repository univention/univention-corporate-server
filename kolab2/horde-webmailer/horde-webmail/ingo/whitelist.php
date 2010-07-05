<?php
/**
 * $Horde: ingo/whitelist.php,v 1.18.8.10 2009-01-06 15:24:34 jan Exp $
 *
 * Copyright 2002-2009 The Horde Project (http://www.horde.org/)
 *
 * See the enclosed file LICENSE for license information (ASL).  If you
 * did not receive this file, see http://www.horde.org/licenses/asl.php.
 *
 * @author Mike Cochrane <mike@graftonhall.co.nz>
 * @author Brent J. Nordquist <bjn@horde.org>
 * @author Michael Slusarz <slusarz@horde.org>
 */

@define('INGO_BASE', dirname(__FILE__));
require_once INGO_BASE . '/lib/base.php';

/* Redirect if whitelist not available. */
if (!in_array(INGO_STORAGE_ACTION_WHITELIST, $_SESSION['ingo']['script_categories'])) {
    $notification->push(_("Whitelist is not supported in the current filtering driver."), 'horde.error');
    header('Location: ' . Horde::applicationUrl('filters.php', true));
    exit;
}

$whitelist = &$ingo_storage->retrieve(INGO_STORAGE_ACTION_WHITELIST);

/* Perform requested actions. */
$actionID = Util::getFormData('actionID');
switch ($actionID) {
case 'rule_update':
    $ret = $whitelist->setWhitelist(Util::getFormData('whitelist'));
    if (is_a($ret, 'PEAR_Error')) {
        $notification->push($ret, $ret->getCode());
    } else {
        if (!$ingo_storage->store($whitelist)) {
            $notification->push("Error saving changes.", 'horde.error');
        } else {
            $notification->push(_("Changes saved."), 'horde.success');

            if ($prefs->getValue('auto_update')) {
                /* This does its own $notification->push() on error: */
                Ingo::updateScript();
            }
        }

        /* Update the timestamp for the rules. */
        $_SESSION['ingo']['change'] = time();
    }

    break;
}

/* Get the whitelist rule. */
$filters = &$ingo_storage->retrieve(INGO_STORAGE_ACTION_FILTERS);
$wl_rule = $filters->findRule(INGO_STORAGE_ACTION_WHITELIST);

$title = _("Whitelist Edit");
require INGO_TEMPLATES . '/common-header.inc';
require INGO_TEMPLATES . '/menu.inc';
require INGO_TEMPLATES . '/whitelist/whitelist.inc';
require $registry->get('templates', 'horde') . '/common-footer.inc';
