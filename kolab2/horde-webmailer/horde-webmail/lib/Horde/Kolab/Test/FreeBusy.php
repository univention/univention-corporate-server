<?php
/**
 * Base for PHPUnit scenarios.
 *
 * $Horde: framework/Kolab_FreeBusy/lib/Horde/Kolab/Test/FreeBusy.php,v 1.1.2.2 2009-04-25 19:16:42 wrobel Exp $
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
require_once 'Horde/Kolab/Test/Storage.php';

/**
 * Base for PHPUnit scenarios.
 *
 * $Horde: framework/Kolab_FreeBusy/lib/Horde/Kolab/Test/FreeBusy.php,v 1.1.2.2 2009-04-25 19:16:42 wrobel Exp $
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
class Horde_Kolab_Test_FreeBusy extends Horde_Kolab_Test_Storage
{
    /**
     * Set up testing.
     */
    protected function setUp()
    {
        $result = $this->prepareBasicSetup();

        $this->server  = &$result['server'];
        $this->storage = &$result['storage'];
        $this->auth    = &$result['auth'];

        global $conf;

        $conf['kolab']['ldap']['phpdn'] = null;
        $conf['fb']['cache_dir']             = '/tmp';
        $conf['kolab']['freebusy']['server'] = 'https://fb.example.org/freebusy';
        $conf['fb']['use_acls'] = true;
    }

    /**
     * Set up testing.
     */
    protected function tearDown()
    {
        if (file_exists('/tmp/aclcache.db')) {
            unlink('/tmp/aclcache.db');
        }
        if (file_exists('/tmp/xaclcache.db')) {
            unlink('/tmp/xaclcache.db');
        }
        if (file_exists('/tmp/example^org')) {
            $this->unlinkDir('/tmp/example^org');
        }
    }

    function unlinkDir($dir)
    {
        if(!$dh = @opendir($dir)) {
            return;
        }
        while (false !== ($obj = readdir($dh))) {
            if($obj == '.' || $obj == '..') {
                continue;
            }
            if (!@unlink($dir . '/' . $obj)) {
                $this->unlinkDir($dir . '/' . $obj);
            }
        }
        closedir($dh);
        @rmdir($dir);

        return;
    } 

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
        case 'adding an event to a folder':
            $world['result']['add_event'][] = $this->addEvent($arguments[0],
                                                              $arguments[1]);
            break;
        case 'triggering the folder':
            include_once 'Horde/Kolab/FreeBusy.php';

            $_GET['folder']   = $arguments[0];
            $_GET['extended'] = '1';

            $fb = &new Horde_Kolab_FreeBusy();

            $world['result']['trigger'] = $fb->trigger();

            break;
        case 'fetching the free/busy information for':
            include_once 'Horde/Kolab/FreeBusy.php';

            $_GET['uid']   = $arguments[0];
            $_GET['extended'] = '1';

            $fb = &new Horde_Kolab_FreeBusy();

            $world['result']['fetch'] = $fb->fetch();

            break;
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
        case 'the fetch result should contain a free/busy time with summary':
            $this->assertTrue($this->freeBusyContainsSummary($world['result']['fetch']->_data['fb']->findComponent('vfreebusy'),
                                                             $arguments[0]));
            break;
        case 'the fetch result should not contain a free/busy time with summary':
            $this->assertFalse($this->freeBusyContainsSummary($world['result']['fetch']->_data['fb']->findComponent('vfreebusy'),
                                                             $arguments[0]));
            break;
        default:
            return parent::runThen($world, $action, $arguments);
        }
    }

    public function freeBusyContainsSummary($vfb, $summary)
    {
        $params = $vfb->getExtraParams();
        $present = false;
        foreach ($params as $event) {
            if (isset($event['X-SUMMARY'])
                && base64_decode($event['X-SUMMARY']) == $summary) {
                $present = true;
            }
        }
        return $present;
    }

    /**
     * Add an event.
     *
     * @return NULL
     */
    public function addEvent($event, $folder)
    {
        include_once 'Horde/Kolab/Storage.php';

        $folder = Kolab_Storage::getShare($folder, 'event');
        $this->assertNoError($folder);
        $data   = Kolab_Storage::getData($folder, 'event', 1);
        $this->assertNoError($data);
        /* Add the event */
        $result = $data->save($event);
        $this->assertNoError($result);
        return $result;
    }

}
