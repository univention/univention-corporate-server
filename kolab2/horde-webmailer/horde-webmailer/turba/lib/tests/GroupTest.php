<?php

require_once dirname(__FILE__) . '/TestBase.php';

/**
 * $Horde: turba/lib/tests/GroupTest.php,v 1.2.2.1 2007-12-20 14:34:31 jan Exp $
 *
 * @author  Jason M. Felice <jason.m.felice@gmail.com>
 * @package Turba
 * @subpackage UnitTests
 */
class Turba_GroupTest extends Turba_TestBase {

    var $group;

    function setUp()
    {
        parent::setUp();
        $this->setUpDatabase();

        $driver = $this->getDriver();
        $this->group = $driver->getObject('fff');
        $this->assertOk($this->group);
    }

    function test_listMembers_returns_objects_sorted_according_to_parameters()
    {
        $this->assertSortsList(array($this->group, 'listMembers'));
    }

}
