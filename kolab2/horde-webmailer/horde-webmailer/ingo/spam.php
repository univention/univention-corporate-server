<?php
/**
 * $Horde: ingo/spam.php,v 1.13.2.5 2009-01-06 15:24:34 jan Exp $
 *
 * Copyright 2002-2009 The Horde Project (http://www.horde.org/)
 *
 * See the enclosed file LICENSE for license information (ASL).  If you
 * did not receive this file, see http://www.horde.org/licenses/asl.php.
 *
 * @author Jason Felice <jason.m.felice@gmail.com>
 * @author Jan Schneider <jan@horde.org>
 */

@define('INGO_BASE', dirname(__FILE__));
require_once INGO_BASE . '/lib/base.php';

if (!in_array(INGO_STORAGE_ACTION_SPAM, $_SESSION['ingo']['script_categories'])) {
    $notification->push(_("Simple spam filtering is not supported in the current filtering driver."), 'horde.error');
    header('Location: ' . Horde::applicationUrl('filters.php', true));
    exit;
}

/* Load libraries. */
require_once 'Horde/Form.php';
require_once 'Horde/Form/Renderer.php';
require_once 'Horde/Variables.php';

/**
 * Dummy class to hold the select box created by {@link Ingo::flistSelect()}.
 *
 * @see Horde_UI_VarRenderer_ingo
 * @see Ingo::flistSelect()
 */
class Horde_Form_Type_ingo_folders extends Horde_Form_Type {

    var $_folder;

    function isValid(&$var, &$vars, $value, &$message)
    {
        return true;
    }

    function getFolder()
    {
        return $this->_folder;
    }

    function setFolder($folder)
    {
        $this->_folder = $folder;
    }

}

/* Get the spam object and rule. */
$spam = &$ingo_storage->retrieve(INGO_STORAGE_ACTION_SPAM);
$filters = &$ingo_storage->retrieve(INGO_STORAGE_ACTION_FILTERS);
$spam_id = $filters->findRuleId(INGO_STORAGE_ACTION_SPAM);
$spam_rule = $filters->getRule($spam_id);

$vars = &Variables::getDefaultVariables();
if ($vars->get('submitbutton') == _("Return to Rules List")) {
    header('Location: ' . Horde::applicationUrl('filters.php', true));
    exit;
}

/* Build form. */
$form = &new Horde_Form($vars);
$renderer = new Horde_Form_Renderer(array('varrenderer_driver' => array('ingo', 'ingo'), 'encode_title' => false));

$v = &$form->addVariable(_("Spam Level:"), 'level', 'int', false, false, _("Messages with a likely spam score greater than or equal to this number will be treated as spam."));
$v->setHelp('spam-level');

$folder_var = &$form->addVariable(_("Folder to receive spam:"), 'folder', 'ingo_folders', false);
$folder_var->setHelp('spam-folder');
$form->addHidden('', 'actionID', 'text', false);
$form->addHidden('', 'new_folder_name', 'text', false);

$form->setButtons(_("Save"));

/* Perform requested actions. */
if ($form->validate($vars)) {
    $success = true;

    // Create a new folder if requested.
    if ($vars->get('actionID') == 'create_folder') {
        $result = Ingo::createFolder($vars->get('new_folder_name'));
        if (is_string($result)) {
            $spam->setSpamFolder($result);
        } else {
            $success = false;
            if (is_a($result, 'PEAR_Error')) {
                $notification->push($result->getMessage());
            }
        }
    } else {
        $spam->setSpamFolder($vars->get('folder'));
    }

    $spam->setSpamLevel($vars->get('level'));

    if (is_a($result = $ingo_storage->store($spam), 'PEAR_Error')) {
        $notification->push($result);
        $success = false;
    } else {
        $notification->push(_("Changes saved."), 'horde.success');
        if ($vars->get('submitbutton') == _("Save and Enable")) {
            $filters->ruleEnable($spam_id);
            if (is_a($result = $ingo_storage->store($filters), 'PEAR_Error')) {
                $notification->push($result);
                $success = false;
            } else {
                $notification->push(_("Rule Enabled"), 'horde.success');
                $spam_rule['disable'] = false;
            }
        } elseif ($vars->get('submitbutton') == _("Save and Disable")) {
            $filters->ruleDisable($spam_id);
            if (is_a($result = $ingo_storage->store($filters), 'PEAR_Error')) {
                $notification->push($result);
                $success = false;
            } else {
                $notification->push(_("Rule Disabled"), 'horde.success');
                $spam_rule['disable'] = true;
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
if (empty($spam_rule['disable'])) {
    $form->appendButtons(_("Save and Disable"));
} else {
    $form->appendButtons(_("Save and Enable"));
}
$form->appendButtons(_("Return to Rules List"));

/* Set default values. */
$folder_var->type->setFolder($spam->getSpamFolder());
if (!$form->isSubmitted()) {
    $vars->set('level', $spam->getSpamLevel());
    $vars->set('folder', $spam->getSpamFolder());
    $vars->set('actionID', '');
    $vars->set('new_folder_name', '');
}

/* Include new folder JS if necessary. */
if ($registry->hasMethod('mail/createFolder')) {
    Horde::addScriptFile('new_folder.js');
}

/* Set form title. */
$form_title = _("Spam Filtering");
if (!empty($spam_rule['disable'])) {
    $form_title .= ' [<span class="form-error">' . _("Disabled") . '</span>]';
}
$form_title .= ' ' . Help::link('ingo', 'spam');
$form->setTitle($form_title);

$title = _("Spam Filtering");
require INGO_TEMPLATES . '/common-header.inc';
require INGO_TEMPLATES . '/menu.inc';
$form->renderActive($renderer, $vars, 'spam.php', 'post');
require $registry->get('templates', 'horde') . '/common-footer.inc';
