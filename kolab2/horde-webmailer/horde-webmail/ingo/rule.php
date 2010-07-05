<?php
/**
 * $Horde: ingo/rule.php,v 1.63.8.13 2009-01-06 15:24:34 jan Exp $
 *
 * Copyright 2002-2009 The Horde Project (http://www.horde.org/)
 *
 * See the enclosed file LICENSE for license information (ASL).  If you
 * did not receive this file, see http://www.horde.org/licenses/asl.php.
 *
 * @author Mike Cochrane <mike@graftonhall.co.nz>
 * @author Michael Slusarz <slusarz@horde.org>
 */

/* Define the key to use to indicate a user-defined header is requested. */
@define('INGO_USER_HEADER', '++USER_HEADER++');

@define('INGO_BASE',  dirname(__FILE__));
require_once INGO_BASE . '/lib/base.php';
require_once INGO_BASE . '/lib/Driver.php';

/* Check rule permissions. */
if (!Ingo::hasPermission('allow_rules')) {
    $message = @htmlspecialchars(_("You are not allowed to create or edit custom rules."), ENT_COMPAT, NLS::getCharset());
    if (!empty($conf['hooks']['permsdenied'])) {
        $message = Horde::callHook('_perms_hook_denied', array('ingo:allow_rules'), 'horde', $message);
    }
    $notification->push($message, 'horde.error', array('content.raw'));
    header('Location: ' . Horde::applicationUrl('filters.php', true));
    exit;
}

/* Load the Ingo_Script:: driver. */
$ingo_script = Ingo::loadIngoScript();

/* Redirect if no rules are available. */
$availActions = $ingo_script->availableActions();
if (empty($availActions)) {
    $notification->push(_("Individual rules are not supported in the current filtering driver."), 'horde.error');
    header('Location: ' . Horde::applicationUrl('filters.php', true));
    exit;
}

/* This provides the $ingo_fields array. */
require INGO_BASE . '/config/fields.php';

/* Get the current rules. */
$filters = &$ingo_storage->retrieve(INGO_STORAGE_ACTION_FILTERS);

/* Run through action handlers. */
$actionID = Util::getFormData('actionID');
$edit_number = Util::getFormData('edit');
switch ($actionID) {
case 'create_folder':
case 'rule_save':
case 'rule_update':
case 'rule_delete':
    if (!Ingo::hasPermission('shares', PERMS_EDIT)) {
        $notification->push(_("You do not have permission to edit filter rules."), 'horde.error');
        header('Location: ' . Horde::applicationUrl('filters.php', true));
        exit;
    }
    $rule = array();
    $rule['id'] = Util::getFormData('id');
    $rule['name'] = Util::getFormData('name');
    $rule['combine'] = Util::getFormData('combine');
    $rule['conditions'] = array();

    $field = Util::getFormData('field');
    $match = Util::getFormData('match');
    $userheader = Util::getFormData('userheader');
    $value = Util::getFormData('value');
    if ($ingo_script->caseSensitive()) {
        $casesensitive = Util::getFormData('case');
    }

    $valid = true;
    foreach ($field as $key => $val) {
        if (!empty($val)) {
            $condition = array();
            if ($val == INGO_USER_HEADER) {
                $condition['field'] = (empty($userheader[$key])) ? '' : $userheader[$key];
                $condition['type'] = INGO_STORAGE_TYPE_HEADER;
            } elseif (!isset($ingo_fields[$val])) {
                $condition['field'] = $val;
                $condition['type'] = INGO_STORAGE_TYPE_HEADER;
            } else {
                $condition['field'] = $val;
                $condition['type'] = $ingo_fields[$val]['type'];
            }
            $condition['match'] = isset($match[$key]) ? $match[$key] : '';

            if ($actionID == 'rule_save'
                && empty($value[$key])
                && $condition['match'] != 'exists'
                && $condition['match'] != 'not exist') {
                $notification->push(sprintf(_("You cannot create empty conditions. Please fill in a value for \"%s\"."), $condition['field']), 'horde.error');
                $valid = false;
            }
            $condition['value'] = isset($value[$key]) ? $value[$key] : '';

            if (isset($casesensitive)) {
                $condition['case'] = isset($casesensitive[$key]) ? $casesensitive[$key] : '';
            }
            $rule['conditions'][] = $condition;
        }
    }

    if ($actionID == 'create_folder') {
        $rule['action-value'] = Ingo::createFolder(Util::getFormData('new_folder_name'));
    } else {
        $rule['action-value'] = Util::getFormData('actionvalue');
    }

    $rule['action'] = Util::getFormData('action');
    $rule['stop'] = Util::getFormData('stop');

    $rule['flags'] = 0;
    $flags = Util::getFormData('flags', array());
    if (!empty($flags)) {
        foreach ($flags as $val) {
            $rule['flags'] |= $val;
        }
    }

    /* Update the timestamp for the rules. */
    $_SESSION['ingo']['change'] = time();

    /* Save the rule. */
    if ($actionID == 'rule_save' && $valid) {
        if (is_null($edit_number)) {
            if (Ingo::hasPermission('max_rules') !== true &&
                Ingo::hasPermission('max_rules') <= count($filters->getFilterList())) {
                header('Location: ' . Horde::applicationUrl('filters.php', true));
                exit;
            }
            $filters->addRule($rule);
        } else {
            $filters->updateRule($rule, $edit_number);
        }
        $ingo_storage->store($filters);
        $notification->push(_("Changes saved."), 'horde.success');

        if ($prefs->getValue('auto_update')) {
            Ingo::updateScript();
        }

        header('Location: ' . Horde::applicationUrl('filters.php'));
        exit;
    } elseif ($actionID == 'rule_delete') {
        if (!Ingo::hasPermission('shares', PERMS_DELETE)) {
            $notification->push(_("You do not have permission to delete filter rules."), 'horde.error');
            header('Location: ' . Horde::applicationUrl('filters.php', true));
            exit;
        }
        $cond_num = Util::getFormData('conditionnumber');
        if (!is_null($cond_num)) {
            unset($rule['conditions'][$cond_num]);
            $rule['conditions'] = array_values($rule['conditions']);
        }
    }
    break;

default:
    if (!Ingo::hasPermission('shares', PERMS_EDIT)) {
        $notification->push(_("You do not have permission to edit filter rules."), 'horde.error');
        header('Location: ' . Horde::applicationUrl('filters.php', true));
        exit;
    }
    if (is_null($edit_number)) {
        if (Ingo::hasPermission('max_rules') !== true &&
            Ingo::hasPermission('max_rules') <= count($filters->getFilterList())) {
            $message = @htmlspecialchars(sprintf(_("You are not allowed to create more than %d rules."), Ingo::hasPermission('max_rules')), ENT_COMPAT, NLS::getCharset());
            if (!empty($conf['hooks']['permsdenied'])) {
                $message = Horde::callHook('_perms_hook_denied', array('ingo:max_rules'), 'horde', $message);
            }
            $notification->push($message, 'horde.error', array('content.raw'));
            header('Location: ' . Horde::applicationUrl('filters.php', true));
            exit;
        }
        $rule = $filters->getDefaultRule();
    } else {
        $rule = $filters->getRule($edit_number);
    }
    break;
}

if (!$rule) {
    $notification->push(_("Filter not found."), 'horde.error');
    header('Location: ' . Horde::applicationUrl('filters.php', true));
    exit;
}

if ($registry->hasMethod('mail/createFolder')) {
    Horde::addScriptFile('new_folder.js');
}

$title = $rule['name'];
require INGO_TEMPLATES . '/common-header.inc';
require INGO_TEMPLATES . '/menu.inc';
require INGO_TEMPLATES . '/rule/header.inc';

/* Add new, blank condition. */
$rule['conditions'][] = array();

/* Available conditions. */
$avail_types = $ingo_script->availableTypes();
$lastcond = count($rule['conditions']) - 1;

/* Display the conditions. */
foreach ($rule['conditions'] as $cond_num => $condition) {
    $lastfield = ($lastcond == $cond_num);

    /* Create the field listing. */
    $field_select = '';
    $option_selected = !isset($condition['field']);

    if ($lastfield) {
        $field_select .= '<option value="">' . _("Select a field") . "</option>\n" .
            "<option disabled=\"disabled\" value=\"\">- - - - - - - - -</option>\n";
    }

    foreach ($ingo_fields as $key => $val) {
        if (in_array($val['type'], $avail_types)) {
            $field_select .= '<option value="' . htmlspecialchars($key) . '"';
            if (isset($condition['field'])) {
                if ($key == $condition['field']) {
                    $field_select .= ' selected="selected"';
                    $option_selected = true;
                }
            }
            $field_select .= '>' . htmlspecialchars($val['label']) . "</option>\n";
        }
    }

    /* Add any special types. */
    $special = $ingo_script->specialTypes();
    if (count($special)) {
        $field_select .= "<option disabled=\"disabled\" value=\"\">- - - - - - - - -</option>\n";
        foreach ($special as $type) {
            $selected = '';
            if (isset($condition['field'])) {
                if ($type == $condition['field']) {
                    $selected = ' selected="selected"';
                    $option_selected = true;
                }
            }
            $field_select .= '<option value="' . htmlspecialchars($type) . '"' . $selected . '>' . htmlspecialchars($type) . '</option>';
        }
    }

    /* Add user defined header option. */
    $header_entry = false;
    if ($conf['rules']['userheader']) {
        $field_select .= "<option disabled=\"disabled\" value=\"\">- - - - - - - - -</option>\n" .
            '<option value="' . INGO_USER_HEADER . '"' . ((!$option_selected) ? ' selected="selected"' : '') . '>' . _("Self-Defined Header") . (($lastfield) ? '' : ':') . "</option>\n";
        if (!$option_selected) {
            $header_entry = true;
            $userheader = Util::getFormData('userheader');
            if (empty($userheader)) {
                $userheader = isset($condition['field']) ? $condition['field'] : '';
            } else {
                $userheader = $userheader[$cond_num];
            }
        }
    }

    if ($lastfield) {
        require INGO_TEMPLATES . '/rule/filter.inc';
        continue;
    }

    /* Create the match listing. */
    if (!isset($condition['field']) ||
        ($condition['field'] == INGO_USER_HEADER) ||
        !isset($ingo_fields[$condition['field']]['tests'])) {
        $avail_tests = $ingo_script->availableTests();
    } else {
        $avail_tests = $ingo_fields[$condition['field']]['tests'];
    }

    $match_select = '';
    $selected_test = null;
    if (!empty($condition['match'])) {
        $selected_test = $condition['match'];
    }

    if (empty($avail_tests)) {
        $match_select = "<option disabled=\"disabled\" value=\"\">- - - - - - - - -</option>\n";
    } else {
        $first_test = null;
        foreach ($avail_tests as $test) {
            if (is_null($selected_test)) {
                $selected_test = $test;
            }

            $testOb = $ingo_storage->getTestInfo($test);
            $match_select .= '<option value="' . htmlspecialchars($test) . '"';
            if (!empty($condition['match'])) {
                if ($test == $condition['match']) {
                    $match_select .= ' selected="selected"';
                }
            }
            $match_select .= '>' . htmlspecialchars($testOb->label) . "</option>\n";
        }
    }

    /* Create the matching input elements. */
    $testOb = $ingo_storage->getTestInfo(!empty($condition['match']) ? $condition['match'] : 'contains');
    $value = isset($condition['value']) ? htmlspecialchars($condition['value']): '';

    $match_value = '';
    if (!in_array($selected_test, array('exists', 'not exist'))) {
        $match_value = '<label for="value_' . (int)$cond_num . '" class="hidden">Value</label>' .
            '<input id="value_' . (int)$cond_num . '" name="value[' . (int)$cond_num . ']" size="40" value="' . $value . '" />';
    }

    switch ($testOb->type) {
    case 'text':
        if ($ingo_script->caseSensitive()) {
            $match_value .= '<input type="checkbox" id="case_' . (int)$cond_num . '" name="case[' . (int)$cond_num . ']" value="1" ' .
                ((isset($condition['case']) && $condition['case']) ? 'checked="checked" ' : '') .
                '/> ' . Horde::label('case_' . (int)$cond_num, _("Case Sensitive"));
        }
        break;
    }
    require INGO_TEMPLATES . '/rule/filter.inc';
}

/* Get the action select output. */
$actionselect = '';
foreach ($availActions as $val) {
    $actionselect .= '<option value="' . htmlspecialchars($val) . '"';
    $action = $ingo_storage->getActionInfo($val);
    if ($val == $rule['action']) {
        $actionselect .= ' selected="selected"';
        $current_action = $action;
        $action->label .= ':';
    }
    $actionselect .= '>' . htmlspecialchars($action->label) . "</option>\n";
}

/* Get the action value output. */
$actionvaluelabel = '';
$actionvalue = '';
switch ($current_action->type) {
case 'folder':
    $actionvaluelabel = '<label for="actionvalue" class="hidden">' . _("Select target folder") . '</label>';
    $actionvalue = Ingo::flistSelect($rule['action-value'], 'rule');
    break;

case 'text':
case 'int':
    $actionvaluelabel = '<label for="actionvalue" class="hidden">' . _("Value") . '</label>';
    $actionvalue = '<input id="actionvalue" name="actionvalue" size="40" value="' . htmlspecialchars($rule['action-value']) . '" />';
    break;
}

require INGO_TEMPLATES . '/rule/footer.inc';
require $registry->get('templates', 'horde') . '/common-footer.inc';
