<?php
/**
 * Base for PHPUnit scenarios.
 *
 * $Horde: framework/Kolab_Filter/lib/Horde/Kolab/Test/Filter.php,v 1.1.2.3 2009-03-06 08:43:15 wrobel Exp $
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
 * $Horde: framework/Kolab_Filter/lib/Horde/Kolab/Test/Filter.php,v 1.1.2.3 2009-03-06 08:43:15 wrobel Exp $
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
class Horde_Kolab_Test_Filter extends Horde_Kolab_Test_Storage
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

        $conf['kolab']['imap']['server'] = 'localhost';
        $conf['kolab']['imap']['port']   = 0;
        $conf['kolab']['imap']['allow_special_users'] = true;
        $conf['kolab']['filter']['reject_forged_from_header'] = false;
        $conf['kolab']['filter']['email_domain'] = 'example.org';
        $conf['kolab']['filter']['privileged_networks'] = '127.0.0.1,192.168.0.0/16';
        $conf['kolab']['filter']['verify_from_header'] = true;
        $conf['kolab']['filter']['calendar_id'] = 'calendar';
        $conf['kolab']['filter']['calendar_pass'] = 'calendar';
        $conf['kolab']['filter']['lmtp_host'] = 'imap.example.org';
        $conf['kolab']['filter']['simple_locks'] = true;
        $conf['kolab']['filter']['simple_locks_timeout'] = 3;

        $result = $this->auth->authenticate('wrobel', array('password' => 'none'));
        $this->assertNoError($result);

        $folder = $this->storage->getNewFolder();
        $folder->setName('Kalender');
        $result = $folder->save(array('type' => 'event',
                                      'default' => true));
        $this->assertNoError($result);
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
        default:
            return parent::runThen($world, $action, $arguments);
        }
    }

    /**
     * Fill a Kolab Server with test users.
     *
     * @param Kolab_Server &$server The server to populate.
     *
     * @return Horde_Kolab_Server The empty server.
     */
    public function prepareUsers(&$server)
    {
        parent::prepareUsers(&$server);
        $result = $server->add($this->provideFilterUserOne());
        $this->assertNoError($result);
        $result = $server->add($this->provideFilterUserTwo());
        $this->assertNoError($result);
        $result = $server->add($this->provideFilterUserThree());
        $this->assertNoError($result);
        $result = $server->add($this->provideFilterCalendarUser());
        $this->assertNoError($result);
    }

    /**
     * Return a test user.
     *
     * @return array The test user.
     */
    public function provideFilterUserOne()
    {
        return array('givenName' => 'Me',
                     'sn' => 'Me',
                     'type' => KOLAB_OBJECT_USER,
                     'mail' => 'me@example.org',
                     'uid' => 'me',
                     'userPassword' => 'me',
                     'kolabHomeServer' => 'home.example.org',
                     'kolabImapServer' => 'imap.example.org',
                     'kolabFreeBusyServer' => 'https://fb.example.org/freebusy',
                     KOLAB_ATTR_IPOLICY => array('ACT_REJECT_IF_CONFLICTS'),
                     'alias' => array('me.me@example.org', 'MEME@example.org'),
                );
    }

    /**
     * Return a test user.
     *
     * @return array The test user.
     */
    public function provideFilterUserTwo()
    {
        return array('givenName' => 'You',
                     'sn' => 'You',
                     'type' => KOLAB_OBJECT_USER,
                     'mail' => 'you@example.org',
                     'uid' => 'you',
                     'userPassword' => 'you',
                     'kolabHomeServer' => 'home.example.org',
                     'kolabImapServer' => 'home.example.org',
                     'kolabFreeBusyServer' => 'https://fb.example.org/freebusy',
                     'alias' => array('you.you@example.org'),
                     KOLAB_ATTR_KOLABDELEGATE => 'wrobel@example.org',);
    }

    /**
     * Return a test user.
     *
     * @return array The test user.
     */
    public function provideFilterUserThree()
    {
        return array('givenName' => 'Else',
                     'sn' => 'Else',
                     'type' => KOLAB_OBJECT_USER,
                     'mail' => 'else@example.org',
                     'uid' => 'else',
                     'userPassword' => 'else',
                     'kolabHomeServer' => 'imap.example.org',
                     'kolabImapServer' => 'imap.example.org',
                     'kolabFreeBusyServer' => 'https://fb.example.org/freebusy',
                     KOLAB_ATTR_KOLABDELEGATE => 'me@example.org',);
    }

    /**
     * Return the calendar user.
     *
     * @return array The calendar user.
     */
    public function provideFilterCalendarUser()
    {
        return array('cn' => 'calendar',
                     'sn' => 'calendar',
                     'givenName' => '',
                     'type' => KOLAB_OBJECT_USER,
                     'mail' => 'calendar@example.org',
                     'uid' => 'calendar@home.example.org',
                     'userPassword' => 'calendar',
                     'kolabHomeServer' => 'home.example.org',
                     'kolabImapServer' => 'imap.example.org',
                );
    }

    public function sendFixture($infile, $outfile, $user, $client, $from, $to,
                                $host, $params = array())
    {
        $_SERVER['argv'] = array($_SERVER['argv'][0],
                                 '--sender=' . $from,
                                 '--recipient=' . $to,
                                 '--user=' . $user,
                                 '--host=' . $host,
                                 '--client=' . $client);

        $in = file_get_contents($infile, 'r');

        $tmpfile = Util::getTempFile('KolabFilterTest');
        $tmpfh = @fopen($tmpfile, 'w');
        if (empty($params['unmodified_content'])) {
            @fwrite($tmpfh, sprintf($in, $from, $to));
        } else {
            @fwrite($tmpfh, $in);
        }
        @fclose($tmpfh);

        $inh = @fopen($tmpfile, 'r');

        /* Setup the class */
        if (empty($params['incoming'])) {
            require_once 'Horde/Kolab/Filter/Content.php';
            $parser = &new Horde_Kolab_Filter_Content();
        } else {
            require_once 'Horde/Kolab/Filter/Incoming.php';
            $parser = &new Horde_Kolab_Filter_Incoming();
        }

        ob_start();

        /* Parse the mail */
        $result = $parser->parse($inh, 'echo');
        if (empty($params['error'])) {
            $this->assertNoError($result);
            $this->assertTrue(empty($result));

            $output = ob_get_contents();
            ob_end_clean();

            $out = file_get_contents($outfile);

            $output = preg_replace('/^--+=.*$/m', '----', $output);
            $out    = preg_replace('/^--+=.*$/m', '----', $out);
            $output = preg_replace('/^Message-ID.*$/m', '----', $output);
            $out    = preg_replace('/^Message-ID.*$/m', '----', $out);
            $output = preg_replace('/boundary=.*$/m', '----', $output);
            $out    = preg_replace('/boundary=.*$/m', '----', $out);
            $output = preg_replace('/\s/', '', $output);
            $out    = preg_replace('/\s/', '', $out);

            if (empty($params['unmodified_content'])) {
                $this->assertEquals(sprintf($out, $from, $to), $output);
            } else {
                $this->assertEquals($out, $output);
            }
        } else {
            $this->assertError($result, $params['error']);
        }

    }
}
