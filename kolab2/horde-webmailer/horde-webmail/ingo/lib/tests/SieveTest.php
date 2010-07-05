<?php
/**
 * Test cases for Ingo_Script_sieve:: class
 *
 * $Horde: ingo/lib/tests/SieveTest.php,v 1.1.2.1 2007-12-20 14:05:49 jan Exp $
 *
 * See the enclosed file LICENSE for license information (ASL).  If you
 * did not receive this file, see http://www.horde.org/licenses/asl.php.
 *
 * @author  Jason M. Felice <jason.m.felice@gmail.com>
 * @package Ingo
 * @subpackage UnitTests
 */

require_once dirname(__FILE__) . '/TestBase.php';

class Ingo_SieveTest extends Ingo_TestBase {

    function store($ob)
    {
        return $GLOBALS['ingo_storage']->store($ob);
    }

    function setUp()
    {
        require_once INGO_BASE . '/lib/Session.php';
        require_once INGO_BASE . '/lib/Script.php';
        require_once INGO_BASE . '/lib/Storage.php';
        require_once INGO_BASE . '/lib/Ingo.php';

        $GLOBALS['conf']['spam'] = array('enabled' => true,
                                         'char' => '*',
                                         'header' => 'X-Spam-Level');
        $GLOBALS['ingo_storage'] = &Ingo_Storage::factory('mock',
                                                 array('maxblacklist' => 3,
                                                       'maxwhitelist' => 3));
        $GLOBALS['ingo_script'] = &Ingo_Script::factory('sieve', array());
    }

    function testForwardKeep()
    {
        $forward = &new Ingo_Storage_forward();
        $forward->setForwardAddresses('joefabetes@example.com');
        $forward->setForwardKeep(true);

        $this->store($forward);
        $this->assertScript('if true {
redirect "joefabetes@example.com";
keep;
}');
    }

    function testForwardNoKeep()
    {
        $forward = &new Ingo_Storage_forward();
        $forward->setForwardAddresses('joefabetes@example.com');
        $forward->setForwardKeep(false);

        $this->store($forward);
        $this->assertScript('if true {
redirect "joefabetes@example.com";
}');
    }

    function testBlacklistMarker()
    {
        $bl = &new Ingo_Storage_blacklist(3);
        $bl->setBlacklist(array('spammer@example.com'));
        $bl->setBlacklistFolder(INGO_BLACKLIST_MARKER);

        $this->store($bl);
        $this->assertScript('require "imapflags";
if address :all :comparator "i;ascii-casemap" :is ["From", "Sender", "Resent-From"] "spammer@example.com"  {
addflag "\\\\Deleted";
keep;
removeflag "\\\\Deleted";
stop;
}');
    }

    function testWhitelist()
    {
        $wl = &new Ingo_Storage_whitelist(3);
        $wl->setWhitelist(array('spammer@example.com'));

        $this->store($wl);
        $this->assertScript('if address :all :comparator "i;ascii-casemap" :is ["From", "Sender", "Resent-From"] "spammer@example.com"  {
keep;
stop;
}');
    }

    function testVacationDisabled()
    {
        $vacation = &new Ingo_Storage_vacation();
        $vacation->setVacationAddresses(array('from@example.com'));
        $vacation->setVacationSubject('Subject');
        $vacation->setVacationReason("Because I don't like working!");

        $this->store($vacation);
        $this->assertScript('');
    }

    function testVacationEnabled()
    {
        $vacation = &new Ingo_Storage_vacation();
        $vacation->setVacationAddresses(array('from@example.com'));
        $vacation->setVacationSubject('Subject');
        $vacation->setVacationReason("Because I don't like working!");

        $this->store($vacation);
        $this->_enableRule(INGO_STORAGE_ACTION_VACATION);

        $this->assertScript('require "vacation";
if allof ( not exists ["list-help", "list-unsubscribe", "list-subscribe", "list-owner", "list-post", "list-archive", "list-id"], not header :comparator "i;ascii-casemap" :is "Precedence" "list,bulk" ) {
vacation :days 7 :addresses "from@example.com" :subject "Subject" "Because I don\'t like working!";
}');
    }

    function testSpamDisabled()
    {
        $spam = &new Ingo_Storage_spam();
        $spam->setSpamLevel(7);
        $spam->setSpamFolder("Junk");

        $this->store($spam);
        $this->assertScript('');
    }

    function testSpamEnabled()
    {
        $spam = &new Ingo_Storage_spam();
        $spam->setSpamLevel(7);
        $spam->setSpamFolder("Junk");

        $this->store($spam);
        $this->_enableRule(INGO_STORAGE_ACTION_SPAM);
        $this->assertScript('require "fileinto";
if header :comparator "i;ascii-casemap" :contains "X-Spam-Level" "*******"  {
fileinto "Junk";
}');
    }

}
