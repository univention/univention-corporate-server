<?php

require_once dirname(__FILE__) . '/TestBase.php';

/**
 * Test cases for the Turba_Driver:: class
 *
 * $Horde: turba/lib/tests/DriverTest.php,v 1.2.2.1 2007-12-20 14:34:31 jan Exp $
 *
 * @author  Jason M. Felice <jason.m.felice@gmail.com>
 * @package Turba
 * @subpackage UnitTests
 */
class Turba_DriverTest extends Turba_TestBase {

    function setUp()
    {
        parent::setUp();
        $this->setUpDatabase();
    }

    function test_search_results_should_be_sorted_according_to_supplied_sort_order()
    {
        $this->assertSortsList(array($this, 'doSearch'));
    }

    /**
     * This is how we are called from the addField API
     */
    function test_search_with_null_order_parameter_works()
    {
        $driver = $this->getDriver();
        $this->fakeAuth();
        $list = $driver->search(array(), null, 'AND');
        $this->assertOk($list);
        if (!$this->assertTrue(is_a($list, 'Turba_List'))) {
            return;
        }
        $this->assertOk($list->reset());
        $this->assertTrue($list->next());
        $this->assertTrue($list->next());
    }

    function doSearch($order)
    {
        $driver = $this->getDriver();
        $this->fakeAuth();
        return $driver->search(array('__type' => 'Object'), $order, 'AND');
    }

}
