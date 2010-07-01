<?php
/**
 * Test cases for Ingo_Script:: and derived classes
 *
 * $Horde: ingo/lib/tests/ScriptTest.php,v 1.1.2.1 2007-12-20 14:05:49 jan Exp $
 *
 * See the enclosed file LICENSE for license information (ASL).  If you
 * did not receive this file, see http://www.horde.org/licenses/asl.php.
 *
 * @author  Jason M. Felice <jason.m.felice@gmail.com>
 * @package Ingo
 * @subpackage UnitTests
 */

require_once dirname(__FILE__) . '/TestBase.php';
require_once INGO_BASE . '/lib/Ingo.php';
require_once INGO_BASE . '/lib/Script.php';
require_once INGO_BASE . '/lib/Script/imap.php';
require_once INGO_BASE . '/lib/Storage.php';

class Ingo_ScriptTest extends Ingo_TestBase {

    function test_blacklist_rule_without_folder_will_discard_matching_message()
    {
        $runner = ScriptTester::factory('all', $this);

        $ob = new Ingo_Storage_blacklist();
        $ob->setBlacklist(array('spammer@example.com'));
        $ob->setBlacklistFolder('');
        $runner->addRule($ob);

        $runner->assertDeletesMessage('from_spammer');
        $runner->assertKeepsMessage('not_from_spammer');
    }

    function test_whitelist_rule_will_prevent_deletion_of_blacklisted_message()
    {
        $runner = ScriptTester::factory('all', $this);

        $bl = new Ingo_Storage_blacklist();
        $bl->setBlacklist(array('spammer@example.com'));
        $bl->setBlacklistFolder('');
        $runner->addRule($bl);

        $wl = new Ingo_Storage_whitelist();
        $wl->setWhitelist(array('spammer@example.com'));
        $runner->addRule($wl);

        $runner->assertKeepsMessage('from_spammer');
        $runner->assertKeepsMessage('not_from_spammer');
    }

    function test_blacklist_rule_with_folder_will_move_matching_messages()
    {
        $runner = ScriptTester::factory('all', $this);

        $ob = new Ingo_Storage_blacklist();
        $ob->setBlacklist(array('spammer@example.com'));
        $ob->setBlacklistFolder('Junk');
        $runner->addRule($ob);

        $runner->assertMovesMessage('from_spammer', 'Junk');
    }

    function test_partial_whitelist_address_should_not_match()
    {
        $runner = ScriptTester::factory('all', $this);

        $bl = new Ingo_Storage_blacklist();
        $bl->setBlacklist(array('spammer@example.com'));
        $bl->setBlacklistFolder('');
        $runner->addRule($bl);

        $wl = new Ingo_Storage_whitelist();
        $wl->setWhitelist(array('ammer@example.com'));
        $runner->addRule($wl);

        $runner->assertDeletesMessage('from_spammer');
    }

    function test_partial_blacklist_address_should_not_match()
    {
        $runner = ScriptTester::factory('all', $this);

        $bl = new Ingo_Storage_blacklist();
        $bl->setBlacklist(array('ammer@example.com'));
        $bl->setBlacklistFolder('');
        $runner->addRule($bl);

        $runner->assertKeepsMessage('from_spammer');
    }

}

/**
 * Abstract base class for strategies for testing different Script backends
 */
class ScriptTester {

    var $test;
    var $rules = array();

    function ScriptTester($test)
    {
        $this->test = $test;
    }

    function addRule($rule)
    {
        $this->rules[] = $rule;
    }

    function assertDeletesMessage($fixture)
    {
        return PEAR::raiseError('Not implemented.');
    }

    function assertKeepsMessage($fixture)
    {
        return PEAR::raiseError('Not implemented.');
    }

    function assertMovesMessage($fixture, $to_folder)
    {
        return PEAR::raiseError('Not implemented.');
    }

    function factory($type, $test)
    {
        $class = 'ScriptTester_' . $type;
        $ob = new $class($test);
        return $ob;
    }

    function _setupStorage()
    {
        $_SESSION['ingo']['change'] = 0;
        $GLOBALS['ingo_storage'] = Ingo_Storage::factory('mock', array());
        foreach ($this->rules as $ob) {
            $GLOBALS['ingo_storage']->store($ob);
        }
    }

}

/**
 * Implementation of ScriptTester:: for testing 'imap' scripts
 */
class ScriptTester_imap extends ScriptTester {

    var $imap;
    var $api;

    function _setup()
    {
        $this->_setupStorage();
        $this->api = Ingo_Script_imap_api::factory('mock', array());

        $result = $this->api->loadFixtures(dirname(__FILE__) . '/_data/');
        $this->test->assertNotA($result, 'PEAR_Error');

        $params = array('api' => $this->api);
        $this->imap = Ingo_Script::factory('imap', $params);
    }

    function _run()
    {
        $params = array('api' => $this->api);
        $this->imap->perform($params);
    }

    function assertDeletesMessage($fixture)
    {
        $this->_setup();
        $this->test->assertTrue($this->api->hasMessage($fixture));
        $this->_run();
        $this->test->assertFalse($this->api->hasMessage($fixture));
    }

    function assertKeepsMessage($fixture)
    {
        $this->_setup();
        $this->test->assertTrue($this->api->hasMessage($fixture));
        $this->_run();
        $this->test->assertTrue($this->api->hasMessage($fixture));
    }

    function assertMovesMessage($fixture, $to_folder)
    {
        $this->_setup();
        $this->test->assertTrue($this->api->hasMessage($fixture));
        $this->_run();
        $this->test->assertFalse($this->api->hasMessage($fixture));
        $this->test->assertTrue($this->api->hasMessage($fixture, $to_folder));
    }

}

/**
 * This script tester iterates through all enabled backends to verify that
 * each one works properly.
 */
class ScriptTester_all extends ScriptTester {

    var $backends = array('imap', 'sieve');

    function _delegate($method, $params)
    {
        foreach ($this->backends as $backend) {
            $runner = ScriptTester::factory($backend, $this->test);
            foreach ($this->rules as $rule) {
                $runner->addRule($rule);
            }
            call_user_func_array(array($runner, $method), $params);
        }
    }

    function assertDeletesMessage($fixture)
    {
        $this->_delegate('assertDeletesMessage', array($fixture));
    }

    function assertKeepsMessage($fixture)
    {
        $this->_delegate('assertKeepsMessage', array($fixture));
    }

    function assertMovesMessage($fixture, $to_folder)
    {
        $this->_delegate('assertMovesMessage', array($fixture, $to_folder));
    }

}

/**
 * Test the sieve Script backend.  This uses the command-line `sieve' from
 * the GNU mailutils package.
 */
class ScriptTester_sieve extends ScriptTester {

    function assertDeletesMessage($fixture)
    {
        $this->_run();
        $this->_assertOutput("DISCARD on msg uid " . $this->uids[$fixture]);
    }

    function assertKeepsMessage($fixture)
    {
        $this->_run();
        $this->_assertOutput("KEEP on msg uid " . $this->uids[$fixture]);
    }

    function assertMovesMessage($fixture, $to_folder)
    {
        $this->_run();
        $this->_assertOutput("FILEINTO on msg uid " . $this->uids[$fixture] .
                             ": delivering into " . $to_folder);
    }

    function _assertOutput($want)
    {
        $answer = $this->test->assertWantedPattern('/' .
                                                   preg_quote($want, '/') . '/',
                                                   $this->output);
        if (!$answer) {
            echo "FAILED SIEVE SCRIPT:\n\n", $this->sieve_text, "\n\n";
        }
    }

    var $mbox;
    var $sieve;
    var $script_text;
    var $output;
    var $uids;

    function _run()
    {
        $this->_buildMailboxFile();
        $this->_writeSieveScript();
        $this->_runSieve();

        @unlink($this->mbox);
        @unlink($this->sieve);
    }

    function _buildMailboxFile()
    {
        $this->uids = array();
        $this->mbox = tempnam('/tmp', 'mbox');
        $mh = fopen($this->mbox, 'w');
        $uid = 1;

        $dh = opendir(dirname(__FILE__) . '/_data');
        while (($dent = readdir($dh)) !== false) {
            if ($dent == '.' || $dent == '..' || $dent == 'CVS') {
                continue;
            }
            $filespec = dirname(__FILE__) . '/_data/' . $dent;
            $fh = fopen($filespec, 'r');
            $data = fread($fh, filesize($filespec));
            fclose($fh);

            fwrite($mh, $data);
            if ($data{strlen($data)-1} != "\n") {
                fwrite($mh, "\n");
            }

            $this->uids[$dent] = $uid++;
        }
        closedir($dh);

        fclose($mh);
    }

    function _writeSieveScript()
    {
        $params = array();

        $this->_setupStorage();
        $script = Ingo_Script::factory('sieve', $params);

        $this->sieve = tempnam('/tmp', 'sieve');
        $fh = fopen($this->sieve, 'w');

        $this->sieve_text = $script->generate();
        fwrite($fh, $this->sieve_text);
        fclose($fh);
    }

    function _runSieve()
    {
        $this->output = '';
        $ph = popen("sieve -vv -n -f " . escapeshellarg($this->mbox) . " " .
                    escapeshellarg($this->sieve), 'r');
        while (!feof($ph)) {
            $data = fread($ph, 512);
            if (is_string($data)) {
                $this->output .= $data;
            }
        }
        pclose($ph);
    }

}

