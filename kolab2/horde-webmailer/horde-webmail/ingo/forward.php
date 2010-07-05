<?php
/**
 * $Horde: ingo/forward.php,v 1.11.8.9 2009-01-06 15:24:34 jan Exp $
 *
 * Copyright 2003-2009 The Horde Project (http://www.horde.org/)
 *
 * See the enclosed file LICENSE for license information (ASL).  If you
 * did not receive this file, see http://www.horde.org/licenses/asl.php.
 *
 * @author Todd Merritt <tmerritt@email.arizona.edu>
 */

@define('INGO_BASE',  dirname(__FILE__));
require_once INGO_BASE . '/lib/base.php';

/* Redirect if forward is not available. */
if (!in_array(INGO_STORAGE_ACTION_FORWARD, $_SESSION['ingo']['script_categories'])) {
    $notification->push(_("Forward is not supported in the current filtering driver."), 'horde.error');
    header('Location: ' . Horde::applicationUrl('filters.php', true));
    exit;
}

/* Get the forward object and rule. */
$forward = &$ingo_storage->retrieve(INGO_STORAGE_ACTION_FORWARD);
$filters = &$ingo_storage->retrieve(INGO_STORAGE_ACTION_FILTERS);
$fwd_id = $filters->findRuleId(INGO_STORAGE_ACTION_FORWARD);
$fwd_rule = $filters->getRule($fwd_id);

/* Load libraries. */
require_once 'Horde/Form.php';
require_once 'Horde/Form/Renderer.php';
require_once 'Horde/Variables.php';
$vars = &Variables::getDefaultVariables();
if ($vars->get('submitbutton') == _("Return to Rules List")) {
    header('Location: ' . Horde::applicationUrl('filters.php', true));
    exit;
}

/* Build form. */
$form = &new Horde_Form($vars);
$v = &$form->addVariable(_("Keep a copy of messages in this account?"), 'keep_copy', 'boolean', false);
$v->setHelp('forward-keepcopy');
$v = &$form->addVariable(_("Address(es) to forward to:"), 'addresses', 'longtext', false, false, null, array(5, 40));
$v->setHelp('forward-addresses');
$form->setButtons(_("Save"));

/* Perform requested actions. */
if ($form->validate($vars)) {
    $forward->setForwardAddresses($vars->get('addresses'));
    $forward->setForwardKeep($vars->get('keep_copy') == 'on');
    $success = true;
    if (is_a($result = $ingo_storage->store($forward), 'PEAR_Error')) {
        $notification->push($result);
        $success = false;
    } else {
        $notification->push(_("Changes saved."), 'horde.success');
        if ($vars->get('submitbutton') == _("Save and Enable")) {
            $filters->ruleEnable($fwd_id);
            if (is_a($result = $ingo_storage->store($filters), 'PEAR_Error')) {
                $notification->push($result);
                $success = false;
            } else {
                $notification->push(_("Rule Enabled"), 'horde.success');
                $fwd_rule['disable'] = false;
            }
        } elseif ($vars->get('submitbutton') == _("Save and Disable")) {
            $filters->ruleDisable($fwd_id);
            if (is_a($result = $ingo_storage->store($filters), 'PEAR_Error')) {
                $notification->push($result);
                $success = false;
            } else {
                $notification->push(_("Rule Disabled"), 'horde.success');
                $fwd_rule['disable'] = true;
            }
        }
    }
    if ($success && $prefs->getValue('auto_update')) {
        Ingo::updateScript();
    }
}

/* Add buttons depending on the above actions. */
if (empty($fwd_rule['disable'])) {
    $form->appendButtons(_("Save and Disable"));
} else {
    $form->appendButtons(_("Save and Enable"));
}
$form->appendButtons(_("Return to Rules List"));

/* Set default values. */
if (!$form->isSubmitted()) {
    $vars->set('keep_copy', $forward->getForwardKeep());
    $vars->set('addresses', implode("\n", $forward->getForwardAddresses()));
}

/* Set form title. */
$form_title = _("Forward");
if (!empty($fwd_rule['disable'])) {
    $form_title .= ' [<span class="form-error">' . _("Disabled") . '</span>]';
}
$form_title .= ' ' . Help::link('ingo', 'forward');
$form->setTitle($form_title);

$title = _("Forwards Edit");
require INGO_TEMPLATES . '/common-header.inc';
require INGO_TEMPLATES . '/menu.inc';
$form->renderActive(new Horde_Form_Renderer(array('encode_title' => false)), $vars, 'forward.php', 'post');
require $registry->get('templates', 'horde') . '/common-footer.inc';
