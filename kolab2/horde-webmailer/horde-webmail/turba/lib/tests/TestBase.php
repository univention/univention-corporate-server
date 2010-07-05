<?php
/**
 * Base class for Turba test cases
 *
 * $Horde: turba/lib/tests/TestBase.php,v 1.3.2.1 2007-12-20 14:34:31 jan Exp $
 *
 * @author  Jason M. Felice <jason.m.felice@gmail.com>
 * @package Turba
 * @subpackage UnitTests
 */
class Turba_TestBase extends PHPUnit_Framework_TestCase {

    var $_driver;
    var $_driverConfig = array(
        'title' => "My Address Book",
        'type' => 'sql',
        'params' => null,
        'map' => array(
            '__key' => 'object_id',
            '__owner' => 'owner_id',
            '__type' => 'object_type',
            '__members' => 'object_members',
            '__uid' => 'object_uid',
            'name' => 'object_name',
            'email' => 'object_email',
            'alias' => 'object_alias',
            'homeAddress' => 'object_homeaddress',
            'workAddress' => 'object_workaddress',
            'homePhone' => 'object_homephone',
            'workPhone' => 'object_workphone',
            'cellPhone' => 'object_cellphone',
            'fax' => 'object_fax',
            'title' => 'object_title',
            'company' => 'object_company',
            'notes' => 'object_notes',
            'pgpPublicKey' => 'object_pgppublickey',
            'smimePublicKey' => 'object_smimepublickey',
            'freebusyUrl' => 'object_freebusyurl'
        ),
        'search' => array(
            'name',
            'email'
        ),
        'strict' => array(
            'object_id',
            'owner_id',
            'object_type',
        ),
        'export' => true,
        'browse' => true,
        'use_shares' => false,
    );

    var $_fixtures = array(array('object_id' => 'aaa',
                                 'object_type' => 'Object',
                                 'owner_id' => '1',
                                 'object_name' => 'Jason Felice',
                                 'object_company' => 'Cronosys, LLC'),
                           array('object_id' => 'bbb',
                                 'object_type' => 'Object',
                                 'owner_id' => '1',
                                 'object_name' => 'Joe Fabetes',
                                 'object_company' => 'Example, Inc.'),
                           array('object_id' => 'ccc',
                                 'object_type' => 'Object',
                                 'owner_id' => '1',
                                 'object_name' => 'Alice Z',
                                 'object_company' => 'Example, Inc.'),
                           array('object_id' => 'ddd',
                                 'object_type' => 'Object',
                                 'owner_id' => '1',
                                 'object_name' => 'Zoe A',
                                 'object_company' => 'Example, Inc.'),
                           array('object_id' => 'eee',
                                 'object_type' => 'Object',
                                 'owner_id' => '1',
                                 'object_name' => 'Alan Garrison',
                                 'object_company' => 'Cronosys, LLC'),
                           array('object_id' => 'fff',
                                 'owner_id' => '1',
                                 'object_type' => 'Group',
                                 'object_name' => 'Test Group',
                                 'object_members' => 'a:5:{i:0;s:3:"aaa";i:1;s:3:"bbb";i:2;s:3:"ccc";i:3;s:3:"ddd";i:4;s:3:"eee";}'),
                           array('object_id' => 'ggg',
                                 'owner_id' => '1',
                                 'object_type' => 'Group',
                                 'object_name' => 'Alpha First Group',
                                 'object_members' => 'a:4:{i:0;s:3:"aaa";i:1;s:3:"bbb";i:2;s:3:"ccc";i:3;s:3:"ddd";}'));

    var $_sortedByLastname = array('Zoe A', 'Joe Fabetes', 'Jason Felice',
                                   'Alan Garrison', 'Alice Z');
    var $_groups = array("Test Group", "Alpha First Group");
    var $_sortedByCompanyThenLastname = array('Jason Felice', 'Alan Garrison',
                                              'Zoe A', 'Joe Fabetes',
                                              'Alice Z');
    var $_sortedByCompanyThenLastnameDesc = array('Alan Garrison',
                                                  'Jason Felice',
                                                  'Alice Z', 'Joe Fabetes',
                                                  'Zoe A');

    /**
     * Retrieves an SQL driver instance.
     *
     * @return object Initialized Turba_Driver_sql:: instance connected to the
     *                test database.
     */
    function getDriver()
    {
        if (is_null($this->_driver)) {
            $this->_driver = Turba_Driver::factory('_test_sql',
                                                   $this->getDriverConfig());
            $this->assertOk($this->_driver);
            $this->assertOk($this->_driver->_init());
        }
        return $this->_driver;
    }

    function getDriverConfig()
    {
        if (is_null($this->_driverConfig['params'])) {
            $this->_driverConfig['params'] = array_merge(
                $this->getTestDatabaseSQLDriverConfig(),
                array('table' => 'hordetest_turba_objects'));
        }

        return $this->_driverConfig;
    }

    /**
     * Gets the driver's database connection
     *
     * FIXME: Should use acceptance environment's method of connecting, and
     * treat the driver more opaquely.
     *
     * @return object PEAR DB reference
     */
    function getDb()
    {
        $driver = $this->getDriver();
        return $driver->_db;
    }

    /**
     * Asserts that the supplied result is not a PEAR_Error
     *
     * Fails with a descriptive message if so
     * @param mixed $result  The value to check
     * @return boolean  Whether the assertion was successful
     */
    function assertOk($result)
    {
        if (is_a($result, 'DB_Error')) {
            $this->fail($result->getDebugInfo());
            return false;
        } elseif (is_a($result, 'PEAR_Error')) {
            $this->fail($result->getMessage());
            return false;
        }

        return true;
    }

    function setUp()
    {
        @define('TURBA_BASE', dirname(__FILE__) . '/../..');
        @define('TURBA_TEMPLATES', $GLOBALS['registry']->get('templates', 'turba'));
        require_once TURBA_BASE . '/lib/Driver.php';
        require_once TURBA_BASE . '/lib/Object.php';
        require_once TURBA_BASE . '/lib/List.php';
        require_once TURBA_BASE . '/lib/Turba.php';
    }

    function setUpDatabase()
    {
        // Create a new test table, overwriting old ones.
        require_once 'MDB2/Schema.php';
        $config = $this->getDriverConfig();
        $manager = MDB2_Schema::factory($config['params']);
        $defs = $manager->parseDatabaseDefinition(dirname(dirname(dirname(__FILE__))) . '/scripts/sql/test.xml',
                                                  false,
                                                  array('name' => $config['params']['database']),
                                                  false);
        $result = $manager->createTable('hordetest_turba_objects', $defs['tables']['hordetest_turba_objects'], true);
        $this->assertOk($result);

        foreach ($this->_fixtures as $fixture) {
            $this->assertOk($this->_insert($fixture));
        }
    }

    function _insert($object)
    {
        require_once 'Horde/SQL.php';
        $db = $this->getDb();
        $sql = "INSERT INTO hordetest_turba_objects " .
               Horde_SQL::insertValues($db, $object) .
               ";";
        $result = $db->query($sql);
        $this->assertOk($result);
        return $result;
    }


    function assertSortsList($callback)
    {
        $names = $this->_sortedByLastname;
        sort($names);

        $tests = array(array('order'   => array(array('field' => 'lastname',
                                                      'ascending' => true)),
                             'results' => $this->_sortedByLastname),
                       array('order'   => array(array('field' => 'lastname',
                                                      'ascending' => false)),
                             'results' => array_reverse($this->_sortedByLastname)),
                       array('order'   => array(array('field' => 'company',
                                                      'ascending' => true),
                                                array('field' => 'lastname',
                                                      'ascending' => true)),
                             'results' => $this->_sortedByCompanyThenLastname),
                       array('order'   => array(array('field' => 'company',
                                                      'ascending' => true),
                                                array('field' => 'lastname',
                                                      'ascending' => false)),
                             'results' => $this->_sortedByCompanyThenLastnameDesc),
                       array('order'   => array(array('field' => 'name',
                                                      'ascending' => true)),
                             'results' => $names),
                       array('order'   => array(array('field' => 'name',
                                                      'ascending' => false)),
                             'results' => array_reverse($names)));

        foreach ($tests as $test) {
            $list = call_user_func($callback, $test['order']);
            $this->assertOk($list);
            if (!$this->assertTrue(is_a($list, 'Turba_List'))) {
                return;
            }
            $this->assertOk($list->reset());

            foreach ($test['results'] as $name) {
                $this->assertTrue($ob = $list->next());
                if (!$this->assertTrue(is_a($ob, 'Turba_Object'))) {
                    continue;
                }
                $this->assertEqual($name, $ob->getValue('name'));
            }
        }
    }

    function fakeAuth()
    {
        /* Turba_Driver::search() is coupled with authentication global
         * state. */
        $_SESSION['__auth'] = array('authenticated' => true,
                                    'userId' => '1');
        $this->assertEqual('1', Auth::getAuth());
    }

    /**
     * Constructs and returns a Turba_List:: object populated with items
     *
     * @return Turba_List
     */
    function getList()
    {
        $list = new Turba_List();
        $driver = $this->getDriver();
        foreach (array('eee', 'ccc', 'ddd', 'bbb', 'aaa') as $id) {
            $result = $list->insert($driver->getObject($id));
            $this->assertOk($result);
        }
        return $list;
    }

}
