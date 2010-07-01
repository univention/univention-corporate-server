<?php
/**
 * $Horde: ingo/vacation.php,v 1.28.8.12 2009-01-06 15:24:34 jan Exp $
 *
 * Copyright 2002-2009 The Horde Project (http://www.horde.org/)
 *
 * See the enclosed file LICENSE for license information (ASL).  If you
 * did not receive this file, see http://www.horde.org/licenses/asl.php.
 *
 * @author Mike Cochrane <mike@graftonhall.co.nz>
 */

@define('INGO_BASE', dirname(__FILE__));
require_once INGO_BASE . '/lib/base.php';

/* Redirect if vacation is not available. */
if (!in_array(INGO_STORAGE_ACTION_VACATION, $_SESSION['ingo']['script_categories'])) {
    $notification->push(_("Vacation is not supported in the current filtering driver."), 'horde.error');
    header('Location: ' . Horde::applicationUrl('filters.php', true));
    exit;
}

/* Get vacation object and rules. */
$vacation = &$ingo_storage->retrieve(INGO_STORAGE_ACTION_VACATION);
$filters = &$ingo_storage->retrieve(INGO_STORAGE_ACTION_FILTERS);
$vac_id = $filters->findRuleId(INGO_STORAGE_ACTION_VACATION);
$vac_rule = $filters->getRule($vac_id);

/* Load libraries. */
require_once 'Horde/Form.php';
require_once 'Horde/Form/Renderer.php';
require_once 'Horde/Variables.php';
$vars = Variables::getDefaultVariables();
if ($vars->get('submitbutton') == _("Return to Rules List")) {
    header('Location: ' . Horde::applicationUrl('filters.php', true));
    exit;
}

/* Build form. */
$form = &new Horde_Form($vars);
$form->setSection('basic', _("Basic Settings"));

$v = &$form->addVariable(_("Start of vacation:"), 'start', 'monthdayyear', '');
$v->setHelp('vacation-period');
$form->addVariable(_("End of vacation:"), 'end', 'monthdayyear', '');
$v = &$form->addVariable(_("Subject of vacation message:"), 'subject', 'text', false);
$v->setHelp('vacation-subject');
$v = &$form->addVariable(_("Reason:"), 'reason', 'longtext', false, false, null, array(10, 40));
$v->setHelp('vacation-reason');
$form->setSection('advanced', _("Advanced Settings"));
if (empty($conf['hooks']['vacation_addresses']) ||
    empty($conf['hooks']['vacation_only'])) {
    $v = &$form->addVariable(_("My email addresses:"), 'addresses', 'longtext', true, false, null, array(5, 40));
    $v->setHelp('vacation-myemail');
}
$v = &$form->addVariable(_("Addresses to not send responses to:"), 'excludes', 'longtext', false, false, null, array(10, 40));
$v->setHelp('vacation-noresponse');
$v = &$form->addVariable(_("Do not send responses to bulk or list messages?"), 'ignorelist', 'boolean', false);
$v->setHelp('vacation-bulk');
$v = &$form->addVariable(_("Number of days between vacation replies:"), 'days', 'int', false);
$v->setHelp('vacation-days');
$form->setButtons(_("Save"));

/* Perform requested actions. */
if ($form->validate($vars)) {
    $form->getInfo($vars, $info);
    $vacation->setVacationAddresses(isset($info['addresses']) ? $info['addresses'] : '');
    $vacation->setVacationDays($info['days']);
    $vacation->setVacationExcludes($info['excludes']);
    $vacation->setVacationIgnorelist(($info['ignorelist'] == 'on'));
    $vacation->setVacationReason($info['reason']);
    $vacation->setVacationSubject($info['subject']);
    $vacation->setVacationStart($info['start']);
    $vacation->setVacationEnd($info['end']);

    $success = true;
    if (is_a($result = $ingo_storage->store($vacation), 'PEAR_Error')) {
        $notification->push($result);
        $success = false;
    } else {
        $notification->push(_("Changes saved."), 'horde.success');
        if ($vars->get('submitbutton') == _("Save and Enable")) {
            $filters->ruleEnable($vac_id);
            if (is_a($result = $ingo_storage->store($filters), 'PEAR_Error')) {
                $notification->push($result);
                $success = false;
            } else {
                $notification->push(_("Rule Enabled"), 'horde.success');
                $vac_rule['disable'] = false;
            }
        } elseif ($vars->get('submitbutton') == _("Save and Disable")) {
            $filters->ruleDisable($vac_id);
            if (is_a($result = $ingo_storage->store($filters), 'PEAR_Error')) {
                $notification->push($result);
                $success = false;
            } else {
                $notification->push(_("Rule Disabled"), 'horde.success');
                $vac_rule['disable'] = true;
            }
        }
    }

    if ($success && $prefs->getValue('auto_update')) {
        Ingo::updateScript();
    }

    /* Update the timestamp for the rules. */
    $_SESSION['ingo']['change'] = time();
}

/* Add buttons depending on the above actions. */
if (empty($vac_rule['disable'])) {
    $form->appendButtons(_("Save and Disable"));
} else {
    $form->appendButtons(_("Save and Enable"));
}
$form->appendButtons(_("Return to Rules List"));

/* Make sure we have at least one address. */
if (!$vacation->getVacationAddresses()) {
    require_once 'Horde/Identity.php';
    $identity = &Identity::singleton('none');
    $addresses = implode("\n", $identity->getAll('from_addr'));
    /* Remove empty lines. */
    $addresses = preg_replace('/\n+/', "\n", $addresses);
    if (empty($addresses)) {
        $addresses = Auth::getAuth();
    }
    $vacation->setVacationAddresses($addresses);
}

/* Set default values. */
if (!$form->isSubmitted()) {
    $vars->set('addresses', implode("\n", $vacation->getVacationAddresses()));
    $vars->set('excludes', implode("\n", $vacation->getVacationExcludes()));
    $vars->set('ignorelist', $vacation->getVacationIgnorelist());
    $vars->set('days', $vacation->getVacationDays());
    $vars->set('subject', $vacation->getVacationSubject());
    $vars->set('reason', $vacation->getVacationReason());
    $vars->set('start', $vacation->getVacationStart());
    $vars->set('end', $vacation->getVacationEnd());
    $vars->set('start_year', $vacation->getVacationStartYear());
    $vars->set('start_month', $vacation->getVacationStartMonth() - 1);
    $vars->set('start_day', $vacation->getVacationStartDay() - 1);
    $vars->set('end_year', $vacation->getVacationEndYear());
    $vars->set('end_month', $vacation->getVacationEndMonth() - 1);
    $vars->set('end_day', $vacation->getVacationEndDay() - 1);
}

/* Set form title. */
$form_title = _("Vacation");
if (!empty($vac_rule['disable'])) {
    $form_title .= ' [<span class="form-error">' . _("Disabled") . '</span>]';
}
$form_title .= ' ' . Help::link('ingo', 'vacation');
$form->setTitle($form_title);

$title = _("Vacation Edit");
require INGO_TEMPLATES . '/common-header.inc';
require INGO_TEMPLATES . '/menu.inc';
$form->renderActive(new Horde_Form_Renderer(array('encode_title' => false)), $vars, 'vacation.php', 'post');
require $registry->get('templates', 'horde') . '/common-footer.inc';
