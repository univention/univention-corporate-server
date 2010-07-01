<?php
/**
 * $Horde: mnemo/data.php,v 1.36.2.12 2009-01-06 15:24:57 jan Exp $
 *
 * Copyright 2001-2009 The Horde Project (http://www.horde.org/)
 *
 * See the enclosed file LICENSE for license information (ASL). If you
 * did not receive this file, see http://www.horde.org/licenses/asl.php.
 *
 * @author  Jan Schneider <jan@horde.org>
 * @since   Mnemo 1.0
 * @package Mnemo
 */

function _cleanup()
{
    global $import_step;
    $import_step = 1;
    return IMPORT_FILE;
}

@define('MNEMO_BASE', dirname(__FILE__));
require_once MNEMO_BASE . '/lib/base.php';
require_once 'Horde/Data.php';

if (!$conf['menu']['import_export']) {
    require MNEMO_BASE . '/index.php';
    exit;
}

/* Importable file types. */
$file_types = array('csv' => _("CSV"),
                    'vnote' => _("vNote"));

/* Templates for the different import steps. */
$templates = array(
    IMPORT_CSV => array($registry->get('templates', 'horde') . '/data/csvinfo.inc'),
    IMPORT_MAPPED => array($registry->get('templates', 'horde') . '/data/csvmap.inc'),
);
if (Mnemo::hasPermission('max_notes') !== true &&
    Mnemo::hasPermission('max_notes') <= Mnemo::countMemos()) {
    $message = @htmlspecialchars(sprintf(_("You are not allowed to create more than %d notes."), Mnemo::hasPermission('max_notes')), ENT_COMPAT, NLS::getCharset());
    if (!empty($conf['hooks']['permsdenied'])) {
        $message = Horde::callHook('_perms_hook_denied', array('mnemo:max_notes'), 'horde', $message);
    }
    $notification->push($message, 'horde.warning', array('content.raw'));
    $templates[IMPORT_FILE] = array(MNEMO_TEMPLATES . '/data/export.inc');
} else {
    $templates[IMPORT_FILE] = array(MNEMO_TEMPLATES . '/data/import.inc', MNEMO_TEMPLATES . '/data/export.inc');
}

/* Field/clear name mapping. */
$app_fields = array('body' => _("Memo Text"),
                    'category' => _("Category"));

/* Initial values. */
$param = array('file_types'  => $file_types);
$import_format = Util::getFormData('import_format', '');
$import_step = Util::getFormData('import_step', 0) + 1;
$actionID = Util::getFormData('actionID');
$error = false;

/* Loop through the action handlers. */
switch ($actionID) {
case 'export':
    $exportID = Util::getFormData('exportID');

    /* Create a Mnemo storage instance. */
    $storage = &Mnemo_Driver::singleton(Auth::getAuth());
    $storage->retrieve();

    /* Get the full, sorted memo list. */
    $notes = Mnemo::listMemos();

    switch ($exportID) {
    case EXPORT_CSV:
        if (count($notes) == 0) {
            $notification->push(_("There were no memos to export."), 'horde.message');
            $error = true;
        } else {
            $data = array();
            foreach ($notes as $note) {
                unset($note['memo_id']);
                unset($note['memolist_id']);
                unset($note['desc']);
                unset($note['uid']);
                $data[] = $note;
            }
            $csv = &Horde_Data::singleton('csv');
            $csv->exportFile(_("notes.csv"), $data, true);
            exit;
        }
    }
    break;

case IMPORT_FILE:
    $_SESSION['import_data']['target'] = Util::getFormData('notepad_target');
    break;
}

$next_step = null;
if (!$error) {
    $data = &Horde_Data::singleton($import_format);
    if (is_a($data, 'PEAR_Error')) {
        $notification->push(_("This file format is not supported."), 'horde.error');
        $next_step = IMPORT_FILE;
    } else {
        $next_step = $data->nextStep($actionID, $param);
        if (is_a($next_step, 'PEAR_Error')) {
            $notification->push($next_step->getMessage(), 'horde.error');
            $next_step = $data->cleanup();
        }
    }
}

/* We have a final result set. */
if (is_array($next_step)) {
    /* Create a category manager. */
    require_once 'Horde/Prefs/CategoryManager.php';
    $cManager = new Prefs_CategoryManager();
    $categories = $cManager->get();

    /* Create a Mnemo storage instance. */
    $storage = &Mnemo_Driver::singleton($_SESSION['import_data']['target']);
    $max_memos = Mnemo::hasPermission('max_notes');
    $num_memos = Mnemo::countMemos();
    foreach ($next_step as $row) {
        if ($max_memos !== true && $num_memos >= $max_memos) {
            $message = @htmlspecialchars(sprintf(_("You are not allowed to create more than %d notes."), Mnemo::hasPermission('max_notes')), ENT_COMPAT, NLS::getCharset());
            if (!empty($conf['hooks']['permsdenied'])) {
                $message = Horde::callHook('_perms_hook_denied', array('mnemo:max_notes'), 'horde', $message);
            }
            $notification->push($message, 'horde.error', array('content.raw'));
            break;
        }

        /* Check if we need to convert from iCalendar data into an array. */
        if (is_a($row, 'Horde_iCalendar_vnote')) {
            $row = $storage->fromiCalendar($row);
        }

        foreach ($app_fields as $field => $null) {
            if (!isset($row[$field])) {
                $row[$field] = '';
            }
        }

        /* Default the category if there isn't one. */
        if (empty($row['category'])) {
            $row['category'] = '';
        }

        /* Parse out the first line as the description if necessary. */
        if (empty($row['desc'])) {
            $tmp = explode("\n", $row['body'], 2);
            $row['desc'] = array_shift($tmp);
        }

        $result = $storage->add($row['desc'], $row['body'], $row['category']);
        if (is_a($result, 'PEAR_Error')) {
            break;
        }
        $note = $storage->get($result);

        /* If we have created or modified dates for the note, set them
         * correctly in the history log. */
        if (!empty($row['created'])) {
            $history = &Horde_History::singleton();
            if (is_array($row['created'])) {
                $row['created'] = $row['created']['ts'];
            }
            $history->log('mnemo:' . $_SESSION['import_data']['target'] . ':' . $note['uid'],
                          array('action' => 'add', 'ts' => $row['created']), true);
        }
        if (!empty($row['modified'])) {
            $history = &Horde_History::singleton();
            if (is_array($row['modified'])) {
                $row['modified'] = $row['modified']['ts'];
            }
            $history->log('mnemo:' . $_SESSION['import_data']['target'] . ':' . $note['uid'],
                          array('action' => 'modify', 'ts' => $row['modified']), true);
        }

        if (!empty($row['category']) &&
            !in_array($row['category'], $categories)) {
            $cManager->add($row['category']);
            $categories[] = $row['category'];
        }

        $num_memos++;
    }

    if (!count($next_step)) {
        $notification->push(sprintf(_("The %s file didn't contain any notes."),
                                    $file_types[$_SESSION['import_data']['format']]), 'horde.error');
    } elseif (is_a($result, 'PEAR_Error')) {
        $notification->push(sprintf(_("There was an error importing the data: %s"),
                                    $result->getMessage()), 'horde.error');
    } else {
        $notification->push(sprintf(_("%s file successfully imported"),
                                    $file_types[$_SESSION['import_data']['format']]), 'horde.success');
    }
    $next_step = $data->cleanup();
}

$title = _("Import/Export Notes");
require MNEMO_TEMPLATES . '/common-header.inc';
require MNEMO_TEMPLATES . '/menu.inc';

if (isset($templates[$next_step])) {
    foreach ($templates[$next_step] as $template) {
        require $template;
    }
}

require $registry->get('templates', 'horde') . '/common-footer.inc';
