<?php
/**
 * Base for PHPUnit scenarios.
 *
 * $Horde: framework/Kolab_Server/lib/Horde/Kolab/Test/Server.php,v 1.1.2.3 2009-01-06 15:23:17 jan Exp $
 *
 * PHP version 5
 *
 * @category Kolab
 * @package  Kolab_Test
 * @author   Gunnar Wrobel <wrobel@pardus.de>
 * @license  http://www.fsf.org/copyleft/lgpl.html LGPL
 * @link     http://pear.horde.org/index.php?package=Share
 */

/**
 *  We need the unit test framework
 */
require_once 'PHPUnit/Framework.php';
require_once 'PHPUnit/Extensions/Story/TestCase.php';

/**
 *  We need the classes to be tested
 */
require_once 'Horde.php';
require_once 'Horde/Kolab/Server.php';

/**
 * Base for PHPUnit scenarios.
 *
 * $Horde: framework/Kolab_Server/lib/Horde/Kolab/Test/Server.php,v 1.1.2.3 2009-01-06 15:23:17 jan Exp $
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
 * @link     http://pear.horde.org/index.php?package=Share
 */
class Horde_Kolab_Test_Server extends PHPUnit_Extensions_Story_TestCase
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
        case 'an empty Kolab server':
            $world['server'] = &$this->prepareEmptyKolabServer();
            break;
        case 'a basic Kolab server':
            $world['server'] = &$this->prepareBasicKolabServer();
            break;
        case 'the Kolab auth driver has been selected':
            $world['auth'] = &$this->prepareKolabAuthDriver();
            break;
        default:
            return $this->notImplemented($action);
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
        case 'adding a Kolab server object':
            $world['result']['add'] = $world['server']->add($arguments[0]);
            break;
        case 'logging in as a user with a password':
            $world['login'] = $world['auth']->authenticate($arguments[0],
                                                           array('password' => $arguments[1]));
            break;
        case 'adding an object list':
            foreach ($arguments[0] as $object) {
                $result = $world['server']->add($object);
                if (is_a($result, 'PEAR_Error')) {
                    $world['result']['add'] = $result;
                    return;
                }
            }
            $world['result']['add'] = true;
            break;
        case 'adding a user without first name':
            $world['result']['add'] = $world['server']->add($this->provideInvalidUserWithoutGivenName());
            break;
        case 'adding a user without last name':
            $world['result']['add'] = $world['server']->add($this->provideInvalidUserWithoutLastName());
            break;
        case 'adding a user without password':
            $world['result']['add'] = $world['server']->add($this->provideInvalidUserWithoutPassword());
            break;
        case 'adding a user without primary mail':
            $world['result']['add'] = $world['server']->add($this->provideInvalidUserWithoutMail());
            break;
        case 'adding a distribution list':
            $world['result']['add'] = $world['server']->add($this->provideDistributionList());
            break;
        case 'listing all users':
            $world['list'] = $world['server']->listObjects(KOLAB_OBJECT_USER);
            break;
        case 'listing all groups':
            $world['list'] = $world['server']->listObjects(KOLAB_OBJECT_GROUP);
            break;
        case 'listing all objects of type':
            $world['list'] = $world['server']->listObjects($arguments[0]);
            break;
        case 'retrieving a hash list with all objects of type':
            $world['list'] = $world['server']->listHash($arguments[0]);
            break;
        default:
            return $this->notImplemented($action);
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
        case 'the result should be an object of type':
            if (!isset($world['result'])) {
                $this->fail('Did not receive a result!');
            }
            foreach ($world['result'] as $result) { 
                if ($result instanceOf PEAR_Error) {
                    $this->assertEquals('', $result->getMessage());
                } else {
                    $this->assertEquals($arguments[0], get_class($result));
                }
            }
            break;
        case 'the result indicates success.':
            if (!isset($world['result'])) {
                $this->fail('Did not receive a result!');
            }
            foreach ($world['result'] as $result) { 
                if ($result instanceOf PEAR_Error) {
                    $this->assertEquals('', $result->getMessage());
                } else {
                    $this->assertTrue($result);
                }
            }
            break;
        case 'the result should indicate an error with':
            if (!isset($world['result'])) {
                $this->fail('Did not receive a result!');
            }
            foreach ($world['result'] as $result) { 
                if ($result instanceOf PEAR_Error) {
                    $this->assertEquals($arguments[0], $result->getMessage());
                } else {
                    $this->assertEquals($arguments[0], 'Action succeeded without an error.');
                }
            }
            break;
        case 'the list has a number of entries equal to':
            if ($world['list'] instanceOf PEAR_Error) {
                $this->assertEquals('', $world['list']->getMessage());
            } else {
                $this->assertEquals($arguments[0], count($world['list']));
            }
            break;
        case 'the list is an empty array':
            if ($world['list'] instanceOf PEAR_Error) {
                $this->assertEquals('', $world['list']->getMessage());
            } else {
                $this->assertEquals(array(), $world['list']);
            }
            break;
        case 'the list is an empty array':
            if ($world['list'] instanceOf PEAR_Error) {
                $this->assertEquals('', $world['list']->getMessage());
            } else {
                $this->assertEquals(array(), $world['list']);
            }
            break;
        case 'the provided list and the result list match with regard to these attributes':
            if ($world['list'] instanceOf PEAR_Error) {
                $this->assertEquals('', $world['list']->getMessage());
            } else {
                $provided_vals = array();
                foreach ($arguments[2] as $provided_element) {
                    if (isset($provided_element[$arguments[0]])) {
                        $provided_vals[] = $provided_element[$arguments[0]];
                    } else {
                        $this->fail(sprintf('The provided element %s does have no value for %s.',
                                            print_r($provided_element, true),
                                            print_r($arguments[0])));
                    }
                }
                $result_vals = array();
                foreach ($world['list'] as $result_element) {
                    if (isset($result_element[$arguments[1]])) {
                        $result_vals[] = $result_element[$arguments[1]];
                    } else {
                        $this->fail(sprintf('The result element %s does have no value for %s.',
                                            print_r($result_element, true),
                                            print_r($arguments[1])));
                    }
                }
                $this->assertEquals(array(),
                                    array_diff($provided_vals, $result_vals));
            }
            break;
        case 'each element in the result list has an attribute':
            if ($world['list'] instanceOf PEAR_Error) {
                $this->assertEquals('', $world['list']->getMessage());
            } else {
                $result_vals = array();
                foreach ($world['list'] as $result_element) {
                    if (!isset($result_element[$arguments[0]])) {
                        $this->fail(sprintf('The result element %s does have no value for %s.',
                                            print_r($result_element, true),
                                            print_r($arguments[0])));
                    }
                }
            }
            break;
        case 'each element in the result list has an attribute set to a given value':
            if ($world['list'] instanceOf PEAR_Error) {
                $this->assertEquals('', $world['list']->getMessage());
            } else {
                $result_vals = array();
                foreach ($world['list'] as $result_element) {
                    if (!isset($result_element[$arguments[0]])) {
                        $this->fail(sprintf('The result element %s does have no value for %s.',
                                            print_r($result_element, true),
                                            print_r($arguments[0], true)));
                    }
                    if ($result_element[$arguments[0]] != $arguments[1]) {
                        $this->fail(sprintf('The result element %s has an unexpected value %s for %s.',
                                            print_r($result_element, true),
                                            print_r($result_element[$arguments[0]], true),
                                            print_r($arguments[0], true)));
                    }
                }
            }
            break;
        case 'the login was successful':
            $this->assertNoError($world['login']);
            $this->assertTrue($world['login']);
            break;
        case 'the list contains a number of elements equal to':
            $this->assertEquals($arguments[0], count($world['list']));
            break;
        default:
            return $this->notImplemented($action);
        }
    }

    
    /**
     * Prepare an empty Kolab server.
     *
     * @return Horde_Kolab_Server The empty server.
     */
    public function &prepareEmptyKolabServer()
    {
        global $conf;

        include_once 'Horde/Kolab/Server.php';

        $GLOBALS['KOLAB_SERVER_TEST_DATA'] = array();

        /** Prepare a Kolab test server */
        $conf['kolab']['server']['driver'] = 'test';

        $server = Horde_Kolab_Server::singleton();

        /** Ensure we don't use a connection from older tests */
        $server->unbind();

        /** Set base DN */
        $server->_base_dn = 'dc=example,dc=org';

        /** Clean the server data */

        return $server;
    }

    /**
     * Prepare a Kolab server with some basic entries.
     *
     * @return Horde_Kolab_Server The empty server.
     */
    public function &prepareBasicServer()
    {
        $server = $this->prepareEmptyKolabServer();
        $this->prepareUsers($server);
        return $server;
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
        $result = $server->add($this->provideBasicUserOne());
        $this->assertNoError($result);
        $result = $server->add($this->provideBasicUserTwo());
        $this->assertNoError($result);
        $result = $server->add($this->provideBasicAddress());
        $this->assertNoError($result);
        $result = $server->add($this->provideBasicAdmin());
        $this->assertNoError($result);
        $result = $server->add($this->provideBasicDomainMaintainer());
        $this->assertNoError($result);
        $result = $server->add($this->provideBasicGroupOne());
        $this->assertNoError($result);
        $result = $server->add($this->provideBasicGroupTwo());
        $this->assertNoError($result);
        $result = $server->add($this->provideBasicMaintainer());
        $this->assertNoError($result);
        $result = $server->add($this->provideBasicSharedFolder());
        $this->assertNoError($result);
    }

    /**
     * Prepare a Kolab Auth Driver.
     *
     * @return Auth The auth driver.
     */
    public function &prepareKolabAuthDriver()
    {
        include_once 'Horde/Auth.php';

        $auth = Auth::singleton('kolab');
        return $auth;
    }

    /**
     * Return a test user.
     *
     * @return array The test user.
     */
    public function provideBasicUserOne()
    {
        return array('givenName' => 'Gunnar',
                      'sn' => 'Wrobel',
                      'type' => KOLAB_OBJECT_USER,
                      'mail' => 'wrobel@example.org',
                      'uid' => 'wrobel',
                      'userPassword' => 'none',
                      'kolabHomeServer' => 'home.example.org',
                      'kolabImapServer' => 'imap.example.org',
                      'kolabFreeBusyServer' => 'https://fb.example.org/freebusy',
                      KOLAB_ATTR_IPOLICY => array('ACT_REJECT_IF_CONFLICTS'),
                      'alias' => array('gunnar@example.org',
                                       'g.wrobel@example.org'),
                );
    }

    /**
     * Return a test user.
     *
     * @return array The test user.
     */
    public function provideBasicUserTwo()
    {
        return array('givenName' => 'Test',
                     'sn' => 'Test',
                     'type' => KOLAB_OBJECT_USER,
                     'mail' => 'test@example.org',
                     'uid' => 'test',
                     'userPassword' => 'test',
                     'kolabHomeServer' => 'home.example.org',
                     'kolabImapServer' => 'home.example.org',
                     'kolabFreeBusyServer' => 'https://fb.example.org/freebusy',
                     'alias' => array('t.test@example.org'),
                     KOLAB_ATTR_KOLABDELEGATE => 'wrobel@example.org',);
    }

    /**
     * Return a test address.
     *
     * @return array The test address.
     */
    public function provideBasicAddress()
    {
        return array('givenName' => 'Test',
                     'sn' => 'Address',
                     'type' => KOLAB_OBJECT_ADDRESS,
                     'mail' => 'address@example.org');
    }

    /**
     * Return a test administrator.
     *
     * @return array The test administrator.
     */
    public function provideBasicAdmin()
    {
        return array('sn' => 'Administrator',
                     'givenName' => 'The',
                     'uid' => 'admin',
                     'type' => KOLAB_OBJECT_ADMINISTRATOR,
                     'userPassword' => 'none');
    }

    /**
     * Return a test maintainer.
     *
     * @return array The test maintainer.
     */
    public function provideBasicMaintainer()
    {
        return array('sn' => 'Tainer',
                     'givenName' => 'Main',
                     'uid' => 'maintainer',
                     'type' => KOLAB_OBJECT_MAINTAINER,
                     'userPassword' => 'none',
        );
    }

    /**
     * Return a test domain maintainer.
     *
     * @return array The test domain maintainer.
     */
    public function provideBasicDomainMaintainer()
    {
        return array('sn' => 'Maintainer',
                     'givenName' => 'Domain',
                     'uid' => 'domainmaintainer',
                     'type' => KOLAB_OBJECT_DOMAINMAINTAINER,
                     'userPassword' => 'none',
                     'domain' => array('example.com'),
        );
    }

    /**
     * Return a test shared folder.
     *
     * @return array The test shared folder.
     */
    public function provideBasicSharedFolder()
    {
        return array('cn' => 'shared@example.org',
                     'kolabHomeServer' => 'example.org',
                     'type' => KOLAB_OBJECT_SHAREDFOLDER);
    }

    /**
     * Return a test group.
     *
     * @return array The test group.
     */
    public function provideBasicGroupOne()
    {
        return array('mail' => 'empty.group@example.org',
                     'type' => KOLAB_OBJECT_GROUP);
    }

    /**
     * Return a test group.
     *
     * @return array The test group.
     */
    public function provideBasicGroupTwo()
    {
        return array('mail' => 'group@example.org',
                     'type' => KOLAB_OBJECT_GROUP,
                     'member' => array('cn=Test Test,dc=example,dc=org',
                                       'cn=Gunnar Wrobel,dc=example,dc=org'));
    }

    public function provideDistributionList()
    {
        return array('mail' => 'distlist@example.org',
                     'type' => KOLAB_OBJECT_DISTLIST,
                     'member' => array('cn=Test Test,dc=example,dc=org',
                                       'cn=Gunnar Wrobel,dc=example,dc=org'));
    }

    public function provideInvalidUserWithoutPassword()
    {
        return array('givenName' => 'Test',
                     'sn' => 'Test',
                     'type' => KOLAB_OBJECT_USER,
                     'mail' => 'test@example.org');
    }

    public function provideInvalidUserWithoutGivenName()
    {
        return array('sn' => 'Test',
                     'userPassword' => 'none',
                     'type' => KOLAB_OBJECT_USER,
                     'mail' => 'test@example.org');
    }

    public function provideInvalidUserWithoutLastName()
    {
        return array('givenName' => 'Test',
                     'userPassword' => 'none',
                     'type' => KOLAB_OBJECT_USER,
                     'mail' => 'test@example.org');
    }

    public function provideInvalidUserWithoutMail()
    {
        return array('givenName' => 'Test',
                     'sn' => 'Test',
                     'userPassword' => 'none',
                     'type' => KOLAB_OBJECT_USER);
    }

    public function provideInvalidUsers()
    {
        return array(
            array(
                $this->provideInvalidUserWithoutPassword(),
                'Adding object failed: The value for "userPassword" is missing!'
            ),
            array(
                $this->provideInvalidUserWithoutGivenName(),
                'Adding object failed: Either the last name or the given name is missing!'
            ),
            array(
                $this->provideInvalidUserWithoutLastName(),
                'Adding object failed: Either the last name or the given name is missing!'
            ),
            array(
                $this->provideInvalidUserWithoutMail(),
                'Adding object failed: The value for "mail" is missing!'
            ),
        );
    }

    /** FIXME: Prefix the stuff bewlow with provide...() */

    public function validUsers()
    {
        return array(
            array(
                $this->provideBasicUserOne(),
            ),
            array(
                $this->provideBasicUserTwo(),
            ),
        );
    }

    public function validAddresses()
    {
        return array(
            array(
                $this->provideBasicAddress(),
            ),
        );
    }

    public function validAdmins()
    {
        return array(
            array(
                $this->provideBasicAdmin(),
            ),
        );
    }

    public function validMaintainers()
    {
        return array(
            array(
                $this->provideBasicMaintainer(),
            )
        );
    }

    public function validDomainMaintainers()
    {
        return array(
            array(
                $this->provideBasicDomainMaintainer(),
            )
        );
    }

    public function validGroups()
    {
        return array(
            array(
                $this->validGroupWithoutMembers(),
            ),
            array(
                array('mail' => 'group@example.org',
                      'type' => KOLAB_OBJECT_GROUP,
                      'member' => array('cn=Test Test,dc=example,dc=org',
                                        'cn=Gunnar Wrobel,dc=example,dc=org')
                ),
            ),
            array(
                array('mail' => 'group2@example.org',
                      'type' => KOLAB_OBJECT_GROUP,
                      'member' => array('cn=Gunnar Wrobel,dc=example,dc=org')
                ),
            ),
        );
    }

    public function validSharedFolders()
    {
        return array(
            array('cn' => 'Shared',
                  'type' => KOLAB_OBJECT_SHAREDFOLDER
            ),
        );
    }

    public function validGroupWithoutMembers()
    {
        return array('mail' => 'empty.group@example.org',
                     'type' => KOLAB_OBJECT_GROUP,
        );
    }

    public function userLists()
    {
        return array(
        );
    }

    public function groupLists()
    {
        return array(
            array(
                array(
                    array('type' => KOLAB_OBJECT_GROUP,
                          'mail' => 'empty.group@example.org',
                    ),
                )
            ),
            array(
                array(
                    array('mail' => 'empty.group@example.org',
                          'type' => KOLAB_OBJECT_GROUP,
                    ),
                ),
                array(
                    array('mail' => 'group@example.org',
                          'type' => KOLAB_OBJECT_GROUP,
                          'member' => array('cn=Test Test,dc=example,dc=org',
                                            'cn=Gunnar Wrobel,dc=example,dc=org')
                    ),
                ),
                array(
                    array('mail' => 'group2@example.org',
                          'type' => KOLAB_OBJECT_GROUP,
                          'member' => array('cn=Gunnar Wrobel,dc=example,dc=org')
                    ),
                ),
            )
        );
    }

    public function userListByLetter()
    {
        return array(
        );
    }

    public function userListByAttribute()
    {
        return array(
        );
    }

    public function userAdd()
    {
        return array(
        );
    }

    public function invalidMails()
    {
        return array(
        );
    }

    public function largeList()
    {
        return array(
        );
    }

    /**
     * Ensure that the variable contains no PEAR_Error and fail if it does.
     *
     * @param mixed $var The variable to check.
     *
     * @return NULL.
     */
    public function assertNoError($var)
    {
        if (is_a($var, 'PEAR_Error')) {
            $this->assertEquals('', $var->getMessage());
        }
    }

    /**
     * Ensure that the variable contains a PEAR_Error and fail if it does
     * not. Optionally compare the error message with the provided message and
     * fail if both do not match.
     *
     * @param mixed  $var The variable to check.
     * @param string $msg The expected error message.
     *
     * @return NULL.
     */
    public function assertError($var, $msg = null)
    {
        $this->assertEquals('PEAR_Error', get_class($var));
        if (isset($msg)) {
            $this->assertEquals($msg, $var->getMessage());
        }
    }
}
