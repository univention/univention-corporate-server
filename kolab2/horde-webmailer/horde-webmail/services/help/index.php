<?php
/**
 * $Horde: horde/services/help/index.php,v 2.80.10.15 2009-01-06 15:27:28 jan Exp $
 *
 * Copyright 1999-2009 The Horde Project (http://www.horde.org/)
 *
 * See the enclosed file COPYING for license information (LGPL). If you
 * did not receive this file, see http://www.fsf.org/copyleft/lgpl.html.
 */

@define('HORDE_BASE', dirname(__FILE__) . '/../..');
@define('AUTH_HANDLER', true);

require_once HORDE_BASE . '/lib/base.php';
require_once 'Horde/Help.php';

$rtl = isset($nls['rtl'][$language]);
$title = _("Help");
$show = String::lower(Util::getFormData('show', 'index'));
$module = String::lower(preg_replace('/\W/', '', Util::getFormData('module', 'horde')));
$topic = Util::getFormData('topic', 'overview');

$base_url = $registry->get('webroot', 'horde') . '/services/help/';

$sidebar_url = Horde::url($base_url);
$sidebar_url = Util::addParameter($sidebar_url, array('show' => 'sidebar',
                                                      'module' => $module,
                                                      'topic' => $topic));

if ($module == 'admin') {
    $help_app = $registry->get('name', 'horde');
    $fileroot = $registry->get('fileroot');
    $help_file = $fileroot . "/admin/locale/$language/help.xml";
    $help_file_fallback = $fileroot . '/admin/locale/en_US/help.xml';
} else {
    $help_app = $registry->get('name', $module);
    $fileroot = $registry->get('fileroot', $module);
    $help_file = $fileroot . "/locale/$language/help.xml";
    $help_file_fallback = $fileroot . '/locale/en_US/help.xml';
}

if ($show == 'index') {
    $main_url = Horde::url($base_url);
    $main_url = Util::addParameter($main_url, array('show' => 'entry',
                                                    'module' => $module,
                                                    'topic' => $topic));
    $menu_url = Horde::url($base_url);
    $menu_url = Util::addParameter($menu_url, array('module' => $module,
                                                    'show' => 'menu'));

    require HORDE_TEMPLATES . '/help/index.inc';
    exit;
}

$bodyClass = 'help help_' . urlencode($show);
require HORDE_TEMPLATES . '/common-header.inc';
if ($show == 'menu') {
    require $fileroot . '/lib/version.php';
    $mod_version_constant = String::upper($module) . '_VERSION';
    if (!defined($mod_version_constant)) {
        exit;
    }
    if (in_array($module, array('imp', 'mimp', 'dimp'))) {
        $version = String::upper($module);
    } else {
        $version = String::ucfirst($module);
    }
    $version .= ' ' . constant($mod_version_constant);
    require HORDE_TEMPLATES . '/help/menu.inc';
} elseif ($show == 'sidebar') {
    require_once 'Horde/Form.php';
    require_once 'Horde/Variables.php';
    require_once 'Horde/Form/Renderer.php';
    require_once 'Horde/UI/Tabs.php';
    require_once 'Horde/Tree.php';

    $vars = Variables::getDefaultVariables();

    /* Get current page and if empty, load the default */
    $side_show = Util::getFormData('side_show', 'index');
    $vars->set('side_show', $side_show);

    /* Generate Tabs */
    $tabs = new Horde_UI_Tabs('side_show', $vars);
    $tabs->addTab(_("Help _Topics"), $sidebar_url, 'index');
    $tabs->addTab(_("Sea_rch"), $sidebar_url, 'search');

    /* Set up the tree. */
    $tree = Horde_Tree::factory('horde_menu', 'javascript');
    $tree->setOption(array('target' => 'help_main'));

    $contents = '';
    switch ($side_show) {
    case 'index':
        $help = new Help(HELP_SOURCE_FILE, array($help_file, $help_file_fallback));
        $topics = $help->topics();
        $added_nodes = array();

        foreach ($topics as $id => $title) {
            if (!$title) {
                continue;
            }

            $parent = null;

            $url = Horde::url($registry->get('webroot', 'horde') . '/services/help/');
            $url = Util::addParameter($url, array('show' => 'entry', 'module' => $module, 'topic' => $id));
            $node_params = array(
                'url' => $url,
                'target' => 'help_main',
                'icon' => 'help.png',
                'icondir' => $registry->getImageDir('horde'),
            );

            /* If the title doesn't begin with :: then replace all
             * double colons with single colons. */
            if (substr($title, 0, 2) != '::') {
                $title = str_replace('::', ': ', $title);
            }

            /* Remove linebreaks that would be rendered in the tree. */
            $title = preg_replace('/\s+/', ' ', $title);

            /* Split title in multiple levels */
            $levels = preg_split('/:\s/', $title);
            if (count($levels) > 1) {
                $parent = null;
                $idx = '';
                while ($name = array_shift($levels)) {
                    $idx .= '|' . $name;
                    if (empty($added_nodes[$idx])) {
                        $added_nodes[$idx] = true;
                        if (count($levels)) {
                            unset($node_params['url']);
                        } else {
                            $node_params['url'] = $url;
                        }
                        $tree->addNode($idx, $parent, $name, 0, false, $node_params);
                    }
                    $parent .= '|' . $name;
                }
            } else {
                $tree->addNode($id, $parent, $title, 0, false, $node_params);
            }
        }
        break;

    case 'search':
        /* Create Form */
        $searchForm = new Horde_Form($vars, null, 'search');
        $searchForm->setButtons(_("Search"));

        $searchForm->addHidden('', 'module', 'text', false);
        $searchForm->addHidden('', 'side_show', 'text', false);
        $vars->set('side_show', $side_show);
        $searchForm->addVariable(_("Keyword"), 'keyword', 'text', false, false, null, array(null, 20));

        $renderer = new Horde_Form_Renderer();
        $renderer->setAttrColumnWidth('50%');
        $contents = Util::bufferOutput(array($searchForm, 'renderActive'), $renderer, $vars, $sidebar_url, 'post') .
            '<br />';

        $keywords = $vars->get('keyword');
        if (!empty($keywords)) {
            $help = new Help(HELP_SOURCE_FILE, array($help_file, $help_file_fallback));
            $results = $help->search($keywords);
            foreach ($results as $id => $title) {
                if (empty($title)) {
                    continue;
                }
                $link = Horde::url($registry->get('webroot', 'horde') . '/services/help/');
                $link = Util::addParameter($link, array('show' => 'entry', 'module' => $module, 'topic' => $id));
                $contents .= Horde::link($link, null, null, 'help_main') .
                    htmlspecialchars($title) . "</a><br />\n";
            }
        }
        break;
    }

    require HORDE_TEMPLATES . '/help/sidebar.inc';
} else {
    $help = new Help(HELP_SOURCE_FILE, array($help_file, $help_file_fallback));
    if (($show == 'entry') && $topic) {
        $help->lookup($topic);
        $help->display();
    }
}

require HORDE_TEMPLATES . '/common-footer.inc';
