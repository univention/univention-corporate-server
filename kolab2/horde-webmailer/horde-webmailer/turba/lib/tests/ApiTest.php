<?php

require_once dirname(__FILE__) . '/TestBase.php';

/**
 * $Horde: turba/lib/tests/ApiTest.php,v 1.2.2.1 2007-12-20 14:34:31 jan Exp $
 *
 * @author  Jason M. Felice <jason.m.felice@gmail.com>
 * @package Turba
 * @subpackage UnitTests
 */
class Turba_ApiTest extends Turba_TestBase {

    function setUp()
    {
        parent::setUp();
        require_once TURBA_BASE . '/lib/api.php';
        $this->setUpDatabase();
    }

    function test_search_api_should_return_results()
    {
        global $registry;

        /* HACK: ensure we've included this so that it won't get included
         * again, then override the globals it provides. */
        $pushed = $registry->pushApp('turba', false);
        if (!$this->assertNotA($pushed, 'PEAR_Error')) {
            return;
        }
        require_once TURBA_BASE . '/lib/base.php';
        $GLOBALS['source'] = '_test_sql';
        $GLOBALS['cfgSources'] = array('_test_sql' => $this->getDriverConfig());

        $this->fakeAuth();

        $results = _turba_search(array('Fabetes'));
        $this->assertNotEqual(0, count($results));
        if ($this->assertTrue(!empty($results['Fabetes']))) {
            $entry = array_shift($results['Fabetes']);
            $this->assertEqual('_test_sql', $entry['source']);
            $this->assertEqual('Joe Fabetes', $entry['name']);
        }

        if ($pushed) {
            $registry->popApp();
        }
    }

}
