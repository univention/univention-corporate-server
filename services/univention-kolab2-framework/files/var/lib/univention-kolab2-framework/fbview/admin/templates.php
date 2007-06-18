<?php
/**
 * Horde Template Admin
 *
 * $Horde: horde/admin/templates.php,v 1.14 2004/04/07 14:43:01 chuck Exp $
 *
 * First stab at a template loader for horde, to be used by the horde
 * admin to load alternate individual templates or entire themes for the
 * Horde_Template system.
 * - gives a list of active horde apps and their /templates directory
 *   contents to choose from
 * - user can drill down to a specific file and load as many alternate
 *   templates as required
 * - it allows saving of templates only on actual files (and not
 *   directories) and does not show hidden files.
 * - the alternate templates are stored in the VFS under the directory
 *   path:
 *      .horde_templates/$app/sometemplatedir/templatefile
 *   so that directory would contain all the alternatives for that
 *   template.
 * - TODO: don't show certain other files, like CVS directories; comments;
 *   theme selection and storing in the VFS under:
 *      .horde_templates/$app/_themes/$theme/sometemplatedir/templatefile
 *   to be able to call up an entire theme group of templates? better error
 *   checking; downloading of original templates; the application side of
 *   allowing a different template to be chosen/prefs/etc.
 *
 * Copyright 2003-2004 Marko Djukic <marko@oblo.com>
 *
 * See the enclosed file COPYING for license information (LGPL).  If you
 * did not receive this file, see http://www.fsf.org/copyleft/lgpl.html.
 */

define('HORDE_BASE', dirname(__FILE__) . '/..');
require_once HORDE_BASE . '/lib/base.php';
require_once 'Horde/Menu.php';
require_once 'Horde/Variables.php';

if (!Auth::isAdmin()) {
    Horde::fatal('Forbidden.', __FILE__, __LINE__);
}
$auth = &Auth::singleton($conf['auth']['driver']);

function _setValuesToKeys($in) {
    $out = array();
    foreach ($in as $value) {
        $out[$value] = $value;
    }
    asort($out);
    return $out;
}

/* Set up VFS. */
require_once 'VFS.php';
$vfs_type = $conf['vfs']['type'];
$vfs_args = Horde::getDriverConfig('vfs', $vfs_type);
$vfs_args['user'] = Auth::getAuth();
$vfs = &VFS::singleton($vfs_type, $vfs_args);
                       
@define('TEMPLATES_VFS_PATH', '.horde_templates');

/* Require Horde_Form libs. */
require_once 'Horde/Form.php';
require_once 'Horde/Form/Renderer.php';
require_once 'Horde/Form/Action.php';

/* Set up Horde_Form. */
$vars = &Variables::getDefaultVariables();
$form = &Horde_Form::singleton('TemplatesForm', $vars);
$action = &Horde_Form_Action::factory('submit');

/* Set up form fields. */
$apps = _setValuesToKeys($registry->listApps());
$select_app = &$form->addVariable(_("Application"), 'app', 'enum', true, false, null, array($apps));
$select_app->setAction($action);
$form->addHidden('', 'old_app', 'text', false, false);

/* Set up some variables. */
$formname = $vars->get('formname');
$app = $vars->get('app');
$old_app = $vars->get('old_app');
$template_path = $vars->get('template_path');
$template_orig = $vars->get('template_orig');
$old_template_orig = $vars->get('old_template_orig');
$has_changed = false;

if ($app != $old_app) {
    $has_changed = true;
    $template_path = '';
    $template_orig = '';
    $old_template_orig = '';
}
$vars->set('old_app', $app);
if ($template_orig != $old_template_orig) {
    $has_changed = true;
}
$vars->set('old_template_orig', $template_orig);

if (!is_null($app)) {
    if ($template_orig == '..') {
        $path_parts = explode('/', $template_path);
        array_pop($path_parts);
        $template_path = implode('/', $path_parts);
        $template_orig = '';
    }

    /* Get the full template path on the file system. */
    $template_path_full = $GLOBALS['registry']->getParam('templates', $app) . '/' . $template_path;

    /* If selected template is directory add to template path. */
    if (!empty($template_orig) &&
        is_dir($template_path_full . '/' . $template_orig)) {
        $template_path .= '/' . $template_orig;
        $template_path_full .= '/' . $template_orig;
    }

    $form->addVariable(sprintf(_("Original templates in %s:"), $template_path), 'orig_templates_header', 'header', false, false);

    /* Add the path to the hidden var in the form. */
    $form->addHidden('', 'template_path', 'text', false, false);
    $vars->set('template_path', $template_path);

    /* Get directory list for chosen directory in templates. */
    if ($templates_dir = opendir($template_path_full)) {
        while (false !== ($file = readdir($templates_dir))) { 
            /* Don't show current dir, hidden files and only show
               '..' if not in root dir of an app's templates. */
            if ($file != "." && !($file == '..' && empty($template_path)) &&
                !($file != '..' && substr($file, 0, 1) == '.')) { 
            //if ($file != ".") { 
                $templates[] = $file;
            } 
        }
        closedir($templates_dir); 
        $templates = _setValuesToKeys($templates);
        $v = &$form->addVariable(_("Original application template"), 'template_orig', 'enum', true, false, null, array($templates));
        $v->setAction($action);
        $form->addHidden('', 'old_template_orig', 'text', false, false);
    }

    /* Only set up these vars if the chosen template is a file. */
    if (is_file($template_path_full . '/' . $template_orig)) {
        $form->addVariable(_("Alternate templates"), 'alt_templates_header', 'header', false, false);

        /* Get the already saved alternate templates. */
        $vfs_path = TEMPLATES_VFS_PATH . '/' . $app . $template_path . '/' . $template_orig;
        $templates_alt = array_keys($vfs->listFolder($vfs_path, null, false));
        $templates_alt = array('' => '') + _setValuesToKeys($templates_alt);
        $form->addVariable(_("Delete existing alternate template"), 'delete_template_alt', 'enum', false, false, null, array($templates_alt));

        $form->addVariable(_("Insert alternate template"), 'template_alt', 'file', false, false);
    }
}

if ($formname && !$has_changed) {
    /* Inserting a new alternate template. */
    $form->validate($vars);

    if ($form->isValid()) {
        $form->getInfo($vars, $info);
        if (!empty($info['delete_template_alt'])) {
            $vfs->deleteFile($vfs_path, $info['delete_template_alt']);
        }
        if (!empty($info['template_alt']['size'])) {
            $vfs->write($vfs_path, $info['template_alt']['name'], $info['template_alt']['tmp_name'], true);
        }
    }
}

$title = _("Template Administration");
require HORDE_TEMPLATES . '/common-header.inc';
require HORDE_TEMPLATES . '/admin/common-header.inc';
$notification->notify(array('listeners' => 'status'));

/* Render the form. */
$renderer = &new Horde_Form_Renderer();
$form->renderActive($renderer, $vars, 'templates.php', 'post');

require HORDE_TEMPLATES . '/common-footer.inc';
