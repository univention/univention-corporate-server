<?php
/**
 * $Horde: horde/admin/setup/index.php,v 1.14 2004/04/07 14:43:01 chuck Exp $
 *
 * Copyright 1999-2004 Charles J. Hagenbuch <chuck@horde.org>
 * Copyright 1999-2004 Jon Parise <jon@horde.org>
 *
 * See the enclosed file COPYING for license information (LGPL).  If you
 * did not receive this file, see http://www.fsf.org/copyleft/lgpl.html.
 */

define('HORDE_BASE', dirname(__FILE__) . '/../..');
require_once HORDE_BASE . '/lib/base.php';
require_once 'Horde/Menu.php';
require_once 'Horde/Template.php';

if (!Auth::isAdmin()) {
    Horde::fatal('Forbidden.', __FILE__, __LINE__);
}

/**
 * Returns the CVS version for a given file.
 */
function _getVersion($file)
{
    $size = @filesize($file);
    if (!$size || !is_resource($fp = @fopen($file, 'r'))) {
        return false;
    }
    $data = @fread($fp, $size);
    if (preg_match('/\$.*?conf\.xml,v (.*?) .*\$/', $data, $match)) {
        return $match[1];
    } else {
        return false;
    }
}

/**
 * Does an FTP upload to save the configuration.
 */
function _uploadFTP($params)
{
    global $registry, $notification;

    require_once 'VFS.php';
    $params['hostspec'] = 'localhost';
    $vfs = &VFS::singleton('ftp', $params);
    if (is_a($vfs, 'PEAR_Error')) {
        $notification->push(sprintf(_("Could not connect to server '%s' using FTP: %s"), $params['hostspec'], $vfs->getMessage()), 'horde.error');
        return false;
    }

    /* Loop through the config and write to FTP. */
    $no_errors = true;
    foreach ($_SESSION['_config'] as $app => $config) {
        $path = $registry->getParam('fileroot', $app) . '/config';
        $write = $vfs->writeData($path, 'conf.php', $config);
        if (is_a($write, 'PEAR_Error')) {
            $no_errors = false;
            $notification->push(sprintf(_("Could not write configuration for '%s': %s"), $app, $write->getMessage()), 'horde.error');
        } else {
            $notification->push(sprintf(_("Successfully wrote %s"), $path . '/conf.php'), 'horde.success');
            unset($_SESSION['_config'][$app]);
        }
    }
    return $no_errors;
}

/* Set up some icons. */
$success = Horde::img('alerts/success.gif', '', '', $registry->getParam('graphics', 'horde'));
$warning = Horde::img('alerts/warning.gif', '', '', $registry->getParam('graphics', 'horde'));
$error = Horde::img('alerts/error.gif', '', '', $registry->getParam('graphics', 'horde'));

$conf_url = Horde::applicationUrl('admin/setup/config.php');
$a = $registry->listApps(array('inactive', 'hidden', 'notoolbar', 'active', 'admin'));
$apps = array();
$i = -1;
foreach ($a as $app) {
    /* Skip virtual applications. */
    if ($app == 'logout' || $app == 'problem') {
        continue;
    }

    /* Skip app if no conf.xml file. */
    $path = $registry->getParam('fileroot', $app) . '/config';
    if (!file_exists($path . '/conf.xml')) {
        continue;
    }

    $i++;

    $conf_link = Util::addParameter($conf_url, 'app', $app);
    $conf_link = Horde::link($conf_link, sprintf(_("Configure %s"), $app), '', '', '', sprintf(_("Configure %s"), $app));
    $apps[$i]['sort'] = $registry->getParam('name', $app) . ' (' . $app . ')';
    $apps[$i]['name'] = $conf_link . $apps[$i]['sort'] . '</a>';
    if (!file_exists($path . '/conf.php')) {
        /* No conf.php exists. */
        $apps[$i]['conf'] = $conf_link . $error;
        $apps[$i]['status'] = _("Missing configuration. You have to generate it now if you want to use this application.");
    } else {
        /* A conf.php exists, get the xml version. */
        if (($xml_ver = _getVersion($path . '/conf.xml')) === false) {
            $apps[$i]['conf'] = $conf_link . $warning . '</a>';
            $apps[$i]['status'] = _("No version found in original configuration. Regenerate configuration.");
            continue;
        }
        /* Get the generated php version. */
        if (($php_ver = _getVersion($path . '/conf.php')) === false) {
            /* No version found in generated php, suggest regenarating
             * just in case. */
            $apps[$i]['conf'] = $conf_link . $warning . '</a>';
            $apps[$i]['status'] = _("No version found in your configuration. Regenerate configuration.");
            continue;
        }

        if ($xml_ver != $php_ver) {
            /* Versions are not the same, configuration needs updating. */
            $apps[$i]['conf'] = $conf_link . $error . '</a>';
            $apps[$i]['status'] = _("Configuration needs updating.");
            continue;
        } else {
            /* Configuration is ok. */
            $apps[$i]['conf'] = $conf_link . $success . '</a>';
            $apps[$i]['status'] = _("Application is ready.");
        }
    }
}
/* Sort the apps by name. */
require_once 'Horde/Array.php';
Horde_Array::arraySort($apps, 'sort');
$i = 0;
foreach (array_keys($apps) as $app) {
    $apps[$app]['class'] = ($i++ % 2) ? 'item1' : 'item0';
}

/* Set up any actions that may be offered. */
$actions = array();
$ftpform = '';
if (!empty($_SESSION['_config'])) {
    $url = Horde::applicationUrl('admin/setup/scripts.php');
    /* Action to download the configuration upgrade PHP script. */
    $url = Util::addParameter($url, array('setup' => 'conf', 'type' => 'php'));
    $action = _("Download generated configuration as PHP script.");
    $actions[] = Horde::link($url, $action, '', '', '', $action) . $action . '</a>';
    /* Action to save the configuration upgrade PHP script. */
    $url = Util::addParameter($url, 'save', 'tmp');
    $action = _("Save generated configuration as a PHP script to your server's temporary directory.");
    $actions[] = Horde::link($url, $action, '', '', '', $action) . $action . '</a>';

    /* Set up the form for FTP upload of scripts. */
    require_once 'Horde/Form.php';
    require_once 'Horde/Variables.php';

    $vars = &Variables::getDefaultVariables();
    $ftpform = &Horde_Form::singleton('', $vars);
    $ftpform->setTitle(_("FTP upload of setup"));
    $ftpform->setButtons(_("Upload"), true);
    $ftpform->addVariable(_("Username"), 'username', 'text', true, false, null, array('', 20));
    $ftpform->addVariable(_("Password"), 'password', 'password', false);

    if ($ftpform->validate($vars)) {
        $ftpform->getInfo($vars, $info);
        $upload = _uploadFTP($info);
        if ($upload) {
            $notification->push(_("Uploaded all application setup files to the server."), 'horde.success');
            $url = Horde::applicationUrl('admin/setup/index.php', true);
            header('Location: ' . $url);
            exit;
        }
    }
    /* Render the form. */
    require_once 'Horde/Form/Renderer.php';
    $renderer = &new Horde_Form_Renderer();
    $ftpform = Util::bufferOutput(array($ftpform, 'renderActive'), $renderer, $vars, 'index.php', 'post');
}

if (file_exists(Horde::getTempDir() . '/horde_setup_upgrade.php')) {
    /* Action to remove the configuration upgrade PHP script. */
    $url = Horde::applicationUrl('admin/setup/scripts.php');
    $url = Util::addParameter($url, 'clean', 'tmp');
    $action = _("Remove saved script from server's temporary directory.");
    $actions[] = Horde::link($url, $action, '', '', '', $action) . $action . '</a>';
}

/* Set up the template. */
$template = &new Horde_Template();
$menu = &new Menu(true, true, true);
$template->set('apps', $apps);
$template->set('actions', $actions, true);
$template->set('ftpform', $ftpform, true);
$template->set('menu', $menu->getMenu());
$template->set('notify', Util::bufferOutput(array($notification, 'notify')));

$title = _("Horde Configuration");
require HORDE_TEMPLATES . '/common-header.inc';
require HORDE_TEMPLATES . '/admin/common-header.inc';
echo $template->fetch(HORDE_TEMPLATES . '/admin/setup/index.html');
require HORDE_TEMPLATES . '/common-footer.inc';
