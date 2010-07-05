<?php
/**
 * Script to show the differences between the currently saved and the newly
 * generated configuration.
 *
 * $Horde: horde/admin/setup/diff.php,v 1.4.10.9 2009-01-06 15:22:11 jan Exp $
 *
 * Copyright 2004-2009 The Horde Project (http://www.horde.org/)
 *
 * See the enclosed file COPYING for license information (LGPL). If you
 * did not receive this file, see http://www.fsf.org/copyleft/lgpl.html.
 */

define('HORDE_BASE', dirname(__FILE__) . '/../..');
require_once HORDE_BASE . '/lib/base.php';
require_once 'Horde/Form.php';
require_once 'Horde/Config.php';
require_once 'Horde/Template.php';
include_once 'Text/Diff.php';
include_once 'Text/Diff/Renderer.php';

if (!Auth::isAdmin()) {
    Horde::fatal('Forbidden.', __FILE__, __LINE__);
}

/* Set up the diff renderer. */
$render_type = Util::getFormData('render', 'inline');
include_once 'Text/Diff/Renderer/' . $render_type . '.php';
$class = 'Text_Diff_Renderer_' . $render_type;
$renderer = new $class();

/**
 * Private function to render the differences for a specific app.
 */
function _getDiff($app)
{
    global $renderer, $registry;

    /* Read the existing configuration. */
    $current_config = '';
    $path = $registry->get('fileroot', $app) . '/config';
    $current_config = @file_get_contents($path . '/conf.php');

    /* Calculate the differences. */
    $diff = new Text_Diff(explode("\n", $current_config),
                          explode("\n", $_SESSION['_config'][$app]));
    $diff = $renderer->render($diff);
    if (!empty($diff)) {
        return $diff;
    } else {
        return _("No change.");
    }
}

$diffs = array();
/* Only bother to do anything if there is any config. */
if (!empty($_SESSION['_config'])) {
    /* Set up the toggle button for inline/unified. */
    $url = Horde::applicationUrl('admin/setup/diff.php');
    $url = Util::addParameter($url, 'render', ($render_type == 'inline') ? 'unified' : 'inline');

    if ($app = Util::getFormData('app')) {
        /* Handle a single app request. */
        $toggle_renderer = Horde::link($url . '#' . $app) . (($render_type == 'inline') ? _("unified") : _("inline")) . '</a>';
        $diff = _getDiff($app);
        if ($render_type != 'inline') {
            $diff = htmlspecialchars($diff);
        }
        $diffs[] = array('app'  => $app,
                         'diff' => $diff,
                         'toggle_renderer' => $toggle_renderer);
    } else {
        /* List all the apps with generated configuration. */
        ksort($_SESSION['_config']);
        foreach ($_SESSION['_config'] as $app => $config) {
            $toggle_renderer = Horde::link($url . '#' . $app) . (($render_type == 'inline') ? _("unified") : _("inline")) . '</a>';
            $diff = _getDiff($app);
            if ($render_type != 'inline') {
                $diff = htmlspecialchars($diff);
            }
            $diffs[] = array('app'  => $app,
                             'diff' => $diff,
                             'toggle_renderer' => $toggle_renderer);
        }
    }
}

/* Set up the template. */
$template = new Horde_Template();
$template->setOption('gettext', true);
$template->set('diffs', $diffs, true);

$title = _("Configuration Differences");
require HORDE_TEMPLATES . '/common-header.inc';
echo $template->fetch(HORDE_TEMPLATES . '/admin/setup/diff.html');
require HORDE_TEMPLATES . '/common-footer.inc';
