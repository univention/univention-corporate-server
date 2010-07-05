<?php
/**
 * $Horde: imp/stationery.php,v 2.1.2.11 2009-01-06 15:24:02 jan Exp $
 *
 * Copyright 2005-2009 The Horde Project (http://www.horde.org/)
 *
 * See the enclosed file COPYING for license information (GPL). If you
 * did not receive this file, see http://www.fsf.org/copyleft/gpl.html.
 *
 * @author Jan Schneider <jan@horde.org>
 */

@define('IMP_BASE', dirname(__FILE__));
$authentication = 'horde';
require_once IMP_BASE . '/lib/base.php';
require_once IMP_BASE . '/lib/Template.php';
require_once 'Horde/Prefs/UI.php';

$compose_url = Util::addParameter(Horde::url($registry->get('webroot', 'horde') . '/services/prefs.php', true), 'app', 'imp', false);

/* Is the preference locked? */
if ($prefs->isLocked('stationery')) {
    header('Location: ' . $compose_url);
    exit;
}

/* Retrieve stationery. */
$stationery_list = @unserialize($prefs->getValue('stationery', false));
if (is_array($stationery_list)) {
    $stationery_list = String::convertCharset($stationery_list, $prefs->getCharset());
} else {
    $stationery_list = array();
}

/* Get form data. */
$selected = Util::getFormData('stationery');
if (strlen($selected)) {
    $selected = (int)$selected;
}

/* Always check for stationery type switches. */
$content = Util::getFormData('content', '');
$last_type = Util::getFormData('last_type');
$name = Util::getFormData('name', '');
$type = Util::getFormData('type', 'plain');
if (!empty($last_type) && $last_type != $type) {
    if ($type == 'plain') {
        require_once 'Horde/Text/Filter.php';
        $content = Text_Filter::filter($content, 'html2text');
    } else {
        $content = nl2br(htmlspecialchars(htmlspecialchars($content)));
    }
}
$stationery = array('n' => $name, 't' => $type, 'c' => $content);

/* Run through the action handlers. */
$actionID = Util::getFormData('actionID');
$updated = false;
switch ($actionID) {
case 'update':
    if (Util::getFormData('edit')) {
        /* Stationery has been switched. */
        if (strlen($selected)) {
            /* Edit existing. */
            $stationery = array('n' => $stationery_list[$selected]['n'],
                                't' => $stationery_list[$selected]['t'],
                                'c' => $stationery_list[$selected]['c']);
        } else {
            $stationery = array('n' => '', 't' => 'plain', 'c' => '');
        }
    } elseif (Util::getFormData('delete')) {
        /* Delete stationery. */
        if (isset($stationery_list[$selected])) {
            $updated = sprintf(_("The stationery \"%s\" has been deleted."), $stationery_list[$selected]['n']);
            unset($stationery_list[$selected]);
            $selected = null;
        }
        $stationery = array('n' => '', 't' => 'plain', 'c' => '');
    } elseif (Util::getFormData('save')) {
        /* Saving stationery. */
        if (!strlen($selected)) {
            $selected = count($stationery_list);
            $stationery_list[] = $stationery;
            $updated = sprintf(_("The stationery \"%s\" has been added."), $stationery['n']);
        } else {
            $stationery_list[$selected] = $stationery;
            $updated = sprintf(_("The stationery \"%s\" has been updated."), $stationery['n']);
        }
    }
    break;
}

if ($updated) {
    $prefs->setValue('stationery', serialize(String::convertCharset($stationery_list, NLS::getCharset(), $prefs->getCharset())), false);
    $notification->push($updated, 'horde.success');
}

if ($stationery['t'] == 'html') {
    require_once 'Horde/Editor.php';
    $editor = &Horde_Editor::singleton($prefs->getValue('jseditor'), array('id' => 'content'));
}

/* Show the header. */
require_once 'Horde/Prefs/UI.php';
if (is_callable(array('Horde', 'loadConfiguration'))) {
    $result = Horde::loadConfiguration('prefs.php', array('prefGroups', '_prefs'), 'imp');
    if (!is_a($result, 'PEAR_Error')) {
        extract($result);
    }
} else {
    require IMP_BASE . '/config/prefs.php';
}

$app = 'imp';
$chunk = Util::nonInputVar('chunk');
Prefs_UI::generateHeader(null, $chunk);

$t = new IMP_Template();
$t->setOption('gettext', true);
$t->set('action', Horde::selfUrl());
$t->set('forminput', Util::formInput());
$t->set('navcell', Util::bufferOutput(array('Prefs_UI', 'generateNavigationCell'), 'compose'));

$slist = array();
foreach ($stationery_list as $key => $choice) {
    $slist[] = array(
        'val' => $key,
        'selected' => ($selected === $key),
        'text' => $choice['n'] . ' ' . ($choice['t'] == 'html' ? _("(HTML)") : _("(Plain Text)"))
    );
}
$t->set('slist', $slist);
$t->set('selected', strlen($selected));
$t->set('last_type', $stationery['t']);
$t->set('name_label', Horde::label('name', _("Stationery name:")));
$t->set('name', $stationery['n']);
$t->set('type_label', Horde::label('name', _("Stationery type:")));
$t->set('plain', $stationery['t'] == 'plain');
$t->set('html', $stationery['t'] == 'html');
$t->set('content_label', Horde::label('content', _("Stationery:")));
$t->set('content', $stationery['c']);
$t->set('button_href', Util::addParameter($compose_url, 'group', 'compose'));
$t->set('button_val', htmlspecialchars(_("Return to Message Composition"), ENT_COMPAT, NLS::getCharset()));

echo $t->fetch(IMP_TEMPLATES . '/stationery/stationery.html');
if (!$chunk) {
    require $registry->get('templates', 'horde') . '/common-footer.inc';
}
