<?php
/**
 * $Horde: horde/services/help/index.php,v 2.74 2004/04/15 14:10:28 jan Exp $
 *
 * Copyright 1999-2004 Jon Parise <jon@horde.org>
 *
 * See the enclosed file COPYING for license information (LGPL). If you
 * did not receive this file, see http://www.fsf.org/copyleft/lgpl.html.
 */

@define('HORDE_BASE', dirname(__FILE__) . '/../..');
@define('AUTH_HANDLER', true);

require_once HORDE_BASE . '/lib/base.php';
require_once 'Horde/Help.php';

$title = _("Help");
$show = String::lower(Util::getFormData('show', 'index'));
$module = String::lower(basename(Util::getFormData('module', 'horde')));
$topic = Util::getFormData('topic');

if ($module == 'admin') {
    $fileroot = $registry->getParam('fileroot');
    $help_file = $fileroot . "/admin/locale/$language/help.xml";
    $help_file_fallback = $fileroot . '/admin/locale/en_US/help.xml';
} else {
    $fileroot = $registry->getParam('fileroot', $module);
    $help_file = $fileroot . "/locale/$language/help.xml";
    $help_file_fallback = $fileroot . '/locale/en_US/help.xml';
}

if ($show == 'index') {
    require HORDE_TEMPLATES . '/help/index.inc';
} else {
    require HORDE_TEMPLATES . '/common-header.inc';
    if ($show == 'menu') {
        require HORDE_TEMPLATES . '/help/menu.inc';
    } elseif ($show == 'about') {
        require $fileroot . '/lib/version.php';
        eval('$version = "' . ucfirst($module) . ' " . ' . String::upper($module) . '_VERSION;');
        $credits = Util::bufferOutput('include', $fileroot . '/docs/CREDITS');
        $credits = String::convertCharset($credits, 'iso-8859-1', NLS::getCharset());
        require HORDE_TEMPLATES . '/help/about.inc';
    } else {
        require HORDE_TEMPLATES . '/help/header.inc';

        $help = new Help(HELP_SOURCE_FILE, array($help_file, $help_file_fallback));
        if (($show == 'entry') && !empty($topic)) {
            $help->lookup($topic);
            $help->display();
        } else {
            $topics = $help->topics();
            foreach ($topics as $id => $title) {
                $link = Horde::url($registry->getParam('webroot', 'horde') . '/services/help/');
                $link = Util::addParameter($link, array('show' => 'entry', 'module' => $module, 'topic' => $id));
                echo Horde::link($link, '', 'helpitem');
                echo $title . "</a><br />\n";
            }
        }
        $help->cleanup();

        require HORDE_TEMPLATES . '/help/footer.inc';
    }
}

require HORDE_TEMPLATES . '/common-footer.inc';
