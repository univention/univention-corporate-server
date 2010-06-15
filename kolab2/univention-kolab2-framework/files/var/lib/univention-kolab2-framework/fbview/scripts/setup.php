#!/usr/local/bin/php
<?php
/**
 * The main Horde setup script which allows for a step by step setup
 * or reconfiguration of a Horde installation.
 *
 * $Horde: horde/scripts/setup.php,v 1.21 2004/05/20 15:13:01 jan Exp $
 *
 * Copyright 2003-2004 Marko Djukic <marko@oblo.com>
 * Copyright 2003-2004 Charles J. Hagenbuch <chuck@horde.org>
 *
 * See the enclosed file COPYING for license information (LGPL).  If you
 * did not receive this file, see http://www.fsf.org/copyleft/lgpl.html.
 *
 * @author  Marko Djukic <marko@oblo.com>
 * @author  Charles J. Hagenbuch <chuck@horde.org>
 * @version $Revision: 1.1.2.1 $
 * @since   Horde 3.0
 */

define('AUTH_HANDLER', true);
define('HORDE_BASE', dirname(__FILE__) . '/..');
require_once HORDE_BASE . '/lib/core.php';

$setup = &Setup::singleton();
if (!$setup->check('registry')) {
    $setup->log(_("No Horde registry file."), 'warning');
    $setup->makeRegistry();
} else {
    $setup->log(_("Horde registry file is available."), 'message');
}

/* Horde base libraries. */
$session_control = 'none';
require_once HORDE_BASE . '/lib/base.php';
require_once 'Horde/Form.php';
require_once 'Horde/Config.php';
require_once 'Horde/Variables.php';

if (!$setup->check('domxml')) {
    $this->fatal(_("You need the DOM XML PHP extension to run setup."));
} else {
    $setup->log(_("DOM XML extension is available."), 'message');
}

do {
} while ($setup->appConfig($setup->check('appconf')) != true);


$setup->log(_("Setup completed. Thank you for using Horde!"), 'success');
exit;


/**
 * The Setup:: class provides a set of functions to set up a Horde
 * installation.
 *
 * $Horde: horde/scripts/setup.php,v 1.21 2004/05/20 15:13:01 jan Exp $
 *
 * Copyright 2003-2004 Marko Djukic <marko@oblo.com>
 *
 * See the enclosed file COPYING for license information (LGPL). If you
 * did not receive this file, see http://www.fsf.org/copyleft/lgpl.html.
 *
 * @author  Marko Djukic <marko@oblo.com>
 * @version $Revision: 1.1.2.1 $
 * @since   Horde 3.0
 * @package Horde_Setup
 */
class Setup {

    /**
     * Constructor
     */
    function Setup()
    {
    }

    function &factory($interface)
    {
        $class = 'Setup_' . $interface;
        if (class_exists($class)) {
            return $ret = &new $class();
        } else {
            exit(sprintf(_("Setup is not available through the %s interface."), $interface));
        }
    }

    function &singleton()
    {
        static $instance;

        if (!isset($instance)) {
            require_once 'Horde/CLI.php';
            if (Horde_CLI::runningFromCLI()) {
                $interface = 'cli';
            } else {
                $interface = 'web';
            }
            $instance = &Setup::factory($interface);
        }
        
        return $instance;
    }

    function check($target)
    {
        switch ($target) {
        case 'registry':
            /* We need to have the Horde registry file available. */
            return file_exists(HORDE_BASE . '/config/registry.php');

        case 'domxml':
            /* We need the domxml PHP extension to continue with the setup. */
            return Util::extensionExists('domxml');

        case 'appconf':
            /* Check which apps have a conf.php file. */
            global $registry;
            $apps = $registry->listApps(array('hidden', 'notoolbar', 'active'));
            $all_configured = true;
            foreach ($apps as $app) {
                if (!file_exists($registry->getParam('fileroot', $app))) {
                    $this->log(sprintf(_("Bad file root for %s in registry. Set 'inactive' if not installed."), $app), 'warning');
                } elseif (!file_exists($registry->getParam('fileroot', $app) . '/config/conf.php')) {
                    $all_configured = false;
                    $this->log(sprintf(_("No configuration file (conf.php) for %s."), $app), 'warning');
                } else {
                    $this->log(sprintf(_("Found the configuration file for %s."), $app), 'message');
                }
            }
            return $all_configured;
        }
    }

}


/**
 * The Setup_cli:: class provides a CLI interface to the Horde setup
 * script.
 *
 * $Horde: horde/scripts/setup.php,v 1.21 2004/05/20 15:13:01 jan Exp $
 *
 * Copyright 2003-2004 Marko Djukic <marko@oblo.com>
 *
 * See the enclosed file COPYING for license information (LGPL).  If you
 * did not receive this file, see http://www.fsf.org/copyleft/lgpl.html.
 *
 * @author  Marko Djukic <marko@oblo.com>
 * @version $Revision: 1.1.2.1 $
 * @since   Horde 3.0
 * @package Horde_Setup
 */
class Setup_cli extends Setup {

    var $cli = null;

    /**
     * Constructs a new Setup object using the CLI interface.
     */
    function Setup_cli()
    {
        parent::Setup();

        require_once 'Horde/CLI.php';
        $this->cli = &new Horde_CLI();

    }

    function log($message, $type = 'message')
    {
        /* Wrap the messages with an indent, neater screen display. */
        $message = wordwrap($message, 69, "\n           ");
        $this->cli->message($message, 'cli.' . $type);
    }

    function makeRegistry()
    {
        $file     = HORDE_BASE . '/config/registry.php';
        $distfile = $file . '.dist';

        if (file_exists($distfile)) {
           $create_registry = $this->cli->prompt(_("Create a Horde registry from default now?"), array('y' => _("Yes"), 'n' => _("No")));
        } else {
            $this->cli->fatal(sprintf(_("The default Horde Registry file '%s' is not available, check your installation."), $distfile));
        }

        if ($create_registry == 'y') {
            if (!copy($file . '.dist', $file)) {
                $this->cli->fatal(sprintf(_("Copying '%1$s.dist' to '%1$s' failed. Check your installation."), $file));
            }
            $this->log(_("Registry created."), 'success');
        } else {
            $this->cli->fatal(sprintf(_("You need the Horde registry file to continue setup and to use Horde."), $file));
        }
    }

    function appConfig($is_config_ok)
    {
        if ($is_config_ok) {
            $run_config = $this->cli->prompt(_("All the installed applications seem to be configured, reconfigure any app?"), array('y' => _("Yes"), 'n' => _("No")));
            if ($run_config == 'n') {
                return true;
            }
        }

        global $registry;

        $applist = $registry->listApps(array('hidden', 'notoolbar', 'active'));
        sort($applist);
        $apps = array(0 => _("All applications"));
        foreach ($applist as $app) {
            if (@file_exists($registry->getParam('fileroot', $app) . '/config/conf.xml')) {
                array_push($apps, $app);
            }
        }
        $apps = $apps + array('x' => 'exit');
        $app_choice = $this->cli->prompt(_("Which app do you wish to reconfigure?"), $apps);
        if ($app_choice == 'x') {
            return true;
        }

        if ($app_choice > 0) {
            $apps = array($apps[$app_choice]);
        } else {
            $apps = array_slice($apps, 1, count($apps) - 2);
        }
        $vars = Variables::getDefaultVariables();
        foreach ($apps as $app) {
            $config = &new Horde_Config($app);
            $php = $config->generatePHPConfig($vars);
            $fp = @fopen($registry->getParam('fileroot', $app) . '/config/conf.php', 'w');
            if ($fp) {
                fwrite($fp, String::convertCharset($php, NLS::getCharset(), 'iso-8859-1'));
                fclose($fp);
                $this->log(sprintf(_("Wrote configuration file '%s'."), $registry->getParam('fileroot', $app) . '/config/conf.php'), 'success');
            } else {
                $this->log(sprintf(_("Can not write configuration file '%s'."), $registry->getParam('fileroot', $app) . '/config/conf.php'), 'error');
            }
        }

    }

}
