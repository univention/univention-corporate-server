<?php
/**
 * Base for PHPUnit scenarios.
 *
 * $Horde: framework/Kolab_Storage/lib/Horde/Kolab/Test/Storage.php,v 1.1.2.5 2009-04-25 18:43:40 wrobel Exp $
 *
 * PHP version 5
 *
 * @category Kolab
 * @package  Kolab_Test
 * @author   Gunnar Wrobel <wrobel@pardus.de>
 * @license  http://www.fsf.org/copyleft/lgpl.html LGPL
 * @link     http://pear.horde.org/index.php?package=Kolab_Storage
 */

/**
 *  We need the unit test framework
 */
require_once 'Horde/Kolab/Test/Server.php';

/**
 *  We need the classes to be tested
 */
require_once 'Horde/Kolab/Storage/List.php';

/**
 * Base for PHPUnit scenarios.
 *
 * $Horde: framework/Kolab_Storage/lib/Horde/Kolab/Test/Storage.php,v 1.1.2.5 2009-04-25 18:43:40 wrobel Exp $
 *
 * Copyright 2008-2009 The Horde Project (http://www.horde.org/)
 *
 * See the enclosed file COPYING for license information (LGPL). If you
 * did not receive this file, see http://www.fsf.org/copyleft/lgpl.html.
 *
 * @category Kolab
 * @package  Kolab_Test
 * @author   Gunnar Wrobel <wrobel@pardus.de>
 * @license  http://www.fsf.org/copyleft/lgpl.html LGPL
 * @link     http://pear.horde.org/index.php?package=Kolab_Storage
 */
class Horde_Kolab_Test_Storage extends Horde_Kolab_Test_Server
{
    /**
     * Handle a "given" step.
     *
     * @param array  &$world    Joined "world" of variables.
     * @param string $action    The description of the step.
     * @param array  $arguments Additional arguments to the step.
     *
     * @return mixed The outcome of the step.
     */
    public function runGiven(&$world, $action, $arguments)
    {
        switch($action) {
        case 'an empty Kolab storage':
            $world['storage'] = &$this->prepareEmptyKolabStorage();
            break;
        case 'a Kolab setup':
            $result = $this->prepareKolabSetup();

            $world['server']  = &$result['server'];
            $world['storage'] = &$result['storage'];
            $world['auth']    = &$result['auth'];
            break;
        case 'a populated Kolab setup':
            $result = $this->prepareBasicSetup();

            $world['server']  = &$result['server'];
            $world['storage'] = &$result['storage'];
            $world['auth']    = &$result['auth'];
            break;
        default:
            return parent::runGiven($world, $action, $arguments);
        }
    }

    /**
     * Handle a "when" step.
     *
     * @param array  &$world    Joined "world" of variables.
     * @param string $action    The description of the step.
     * @param array  $arguments Additional arguments to the step.
     *
     * @return mixed The outcome of the step.
     */
    public function runWhen(&$world, $action, $arguments)
    {
        switch($action) {
        case 'create a Kolab default calendar with name':
            $folder = $world['storage']->getNewFolder();
            $folder->setName($arguments[0]);
            $world['folder_creation'] = $folder->save(array('type' => 'event',
                                                            'default' => true));
            $folder->setACL(Auth::getAuth(), 'alrid');
            break;
        case 'allow a group full access to a folder':
            $folder = $world['storage']->getFolder($arguments[1]);
            $folder->setACL($arguments[0], 'alrid');
            break;
        case 'retrieving the list of shares for the application':
            require_once 'Horde/Share.php';

            $shares = Horde_Share::singleton($arguments[0], 'kolab');

            $world['list'] = $shares->listShares(Auth::getAuth());
            break;
        case 'logging in as a user with a password':
            $world['login'] = $world['auth']->authenticate($arguments[0],
                                                           array('password' => $arguments[1]));
            $world['storage'] = &$this->prepareEmptyKolabStorage();
            return parent::runWhen($world, $action, $arguments);
        default:
            return parent::runWhen($world, $action, $arguments);
        }
    }

    /**
     * Handle a "then" step.
     *
     * @param array  &$world    Joined "world" of variables.
     * @param string $action    The description of the step.
     * @param array  $arguments Additional arguments to the step.
     *
     * @return mixed The outcome of the step.
     */
    public function runThen(&$world, $action, $arguments)
    {
        switch($action) {
        case 'the creation of the folder was successful':
            $this->assertNoError($world['folder_creation']);
            break;
        case 'the list contains a share named':
            $this->assertNoError($world['list']);
            $this->assertContains($arguments[0],
                                  array_keys($world['list']));
            break;
        default:
            return parent::runThen($world, $action, $arguments);
        }
    }

    /**
     * Prepare a Kolab server with some basic entries.
     *
     * @return Horde_Kolab_Server The empty server.
     */
    public function &prepareBasicSetup()
    {
        $world = &$this->prepareKolabSetup();
        $this->prepareUsers($world['server']);
        return $world;
    }

    /**
     * Prepare an empty Kolab storage.
     *
     * @return Kolab_List The empty storage.
     */
    public function &prepareEmptyKolabStorage()
    {
        /** Ensure that IMAP runs in testing mode and is empty */
        $GLOBALS['KOLAB_TESTING'] = array();

        /** Prepare a Kolab test storage */
        $storage = Kolab_List::singleton(true);
        return $storage;
    }

    /**
     * Prepare the browser setup.
     *
     * @return NULL
     */
    public function prepareBrowser()
    {
        /** Provide a browser setup */
        include_once 'Horde/Browser.php';
        $GLOBALS['browser'] = new Browser();
    }

    /**
     * Prepare the configuration.
     *
     * @return NULL
     */
    public function prepareConfiguration()
    {
        $fh = fopen(HORDE_BASE . '/config/conf.php', 'w');
        $data = <<<EOD
\$conf['use_ssl'] = 2;
\$conf['server']['name'] = \$_SERVER['SERVER_NAME'];
\$conf['server']['port'] = \$_SERVER['SERVER_PORT'];
\$conf['debug_level'] = E_ALL;
\$conf['umask'] = 077;
\$conf['compress_pages'] = true;
\$conf['menu']['always'] = false;
\$conf['portal']['fixed_blocks'] = array();
\$conf['imsp']['enabled'] = false;

/** Additional config variables required for a clean Horde setup */
\$conf['session']['use_only_cookies'] = false;
\$conf['session']['timeout'] = 0;
\$conf['cookie']['path'] = '/';
\$conf['cookie']['domain'] = \$_SERVER['SERVER_NAME'];
\$conf['use_ssl'] = false;
\$conf['session']['cache_limiter'] = 'nocache';
\$conf['session']['name'] = 'Horde';
\$conf['log']['enabled'] = false;
\$conf['prefs']['driver'] = 'session';
\$conf['auth']['driver'] = 'kolab';
\$conf['share']['driver'] = 'kolab';
\$conf['debug_level'] = E_ALL;

/** Make the share driver happy */
\$conf['kolab']['enabled'] = true;

/** Ensure we still use the LDAP test driver */
\$conf['kolab']['server']['driver'] = 'test';

/** Ensure that we do not trigger on folder update */
\$conf['kolab']['no_triggering'] = true;

/** Storage location for the free/busy system */
\$conf['fb']['cache_dir']             = '/tmp';
\$conf['kolab']['freebusy']['server'] = 'https://fb.example.org/freebusy';

/** Setup the virtual file system for Kolab */
\$conf['vfs']['params']['all_folders'] = true;
\$conf['vfs']['type'] = 'kolab';
EOD;
        fwrite($fh, "<?php\n" . $data);
        fclose($fh);
    }

    /**
     * Prepare the registry.
     *
     * @return NULL
     */
    public function prepareRegistry()
    {
        $fh = fopen(HORDE_BASE . '/config/registry.php', 'w');
        $data = <<<EOD
\$this->applications['horde'] = array(
    'fileroot' => dirname(__FILE__) . '/..',
    'webroot' => '/',
    'initial_page' => 'login.php',
    'name' => _("Horde"),
    'status' => 'active',
    'templates' => dirname(__FILE__) . '/../templates',
    'provides' => 'horde',
);
EOD;
        fwrite($fh, "<?php\n" . $data);
        fclose($fh);
    }

    /**
     * Prepare the notification setup.
     *
     * @return NULL
     */
    public function prepareNotification()
    {

        $fh = fopen(HORDE_BASE . '/config/nls.php', 'w');
        $data = <<<EOD
\$nls['defaults']['language'] = '';
\$nls['languages']['en_US'] = '&#x202d;English (American)';
\$nls['aliases']['en'] = 'en_US';
\$nls['spelling']['en_US'] = '-d american';
\$GLOBALS['nls'] = &\$nls;
EOD;
        fwrite($fh, "<?php\n" . $data);
        fclose($fh);
    }

    /**
     * Prepare a Kolab setup.
     *
     * @return NULL
     */
    public function &prepareKolabSetup()
    {
        $world = array();

        $world['server']  = &$this->prepareEmptyKolabServer();
        $world['storage'] = &$this->prepareEmptyKolabStorage();
        $world['auth']    = &$this->prepareKolabAuthDriver();

        $this->prepareBasicConfiguration();

        if (!defined('HORDE_BASE')) {
            define('HORDE_BASE', $this->provideHordeBase());
        }

        if (!file_exists(HORDE_BASE . '/config')) {
            $result = mkdir(HORDE_BASE . '/config', 0755, true);
        }

        $this->prepareConfiguration();
        $this->prepareRegistry();
        $this->prepareNotification();

        if (!isset($GLOBALS['perms'])) {
            $GLOBALS['perms'] = &Perms::singleton();
        }

        /** Provide the horde registry */
        include_once 'Horde/Registry.php';
        include_once 'Horde/Notification.php';

        $GLOBALS['registry'] = &Registry::singleton();
        $GLOBALS['notification'] = &Notification::singleton();

        $this->prepareFixedConfiguration();

        $this->prepareBrowser();

        /* Make sure the configuration is correct after initializing the registry */
        $this->prepareBasicConfiguration();

        return $world;
    }

    /**
     * Fix the read configuration.
     *
     * @return NULL
     */
    public function prepareFixedConfiguration()
    {
        $GLOBALS['conf'] = &$GLOBALS['registry']->_confCache['horde'];
    }

    /**
     * Prepare a basic Kolab configuration.
     *
     * @return NULL
     */
    public function prepareBasicConfiguration()
    {
        /** We need a server name for MIME processing */
        $_SERVER['SERVER_NAME'] = $this->provideServerName();
        $_SERVER['SERVER_PORT'] = 80;

        $_SERVER['REMOTE_ADDR'] = '127.0.0.1';
    }

    /**
     * Create a new folder.
     *
     * @param string  $name    Name of the new folder.
     * @param string  $type    Type of the new folder.
     * @param boolean $default Should the new folder be a default folder?
     *
     * @return Kolab_Folder The new folder.
     */
    public function &prepareNewFolder(&$storage, $name, $type, $default = false)
    {
        $folder = $storage->getNewFolder();
        $folder->setName($name);
        $this->assertNoError($folder->save(array('type' => $type,
                                                 'default' => $default)));
        return $folder;
    }

    function provideServerName() {
        return 'localhost';
    }

    function provideHordeBase() {
        return Horde::getTempDir() . '/test_config';
    }
}
