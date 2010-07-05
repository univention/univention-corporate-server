<?php
/**
 * Test cases for Ingo_Script_sieve:: class
 *
 * $Horde: ingo/lib/tests/MaildropTest.php,v 1.1.2.1 2007-12-20 14:05:49 jan Exp $
 *
 * See the enclosed file LICENSE for license information (ASL).  If you
 * did not receive this file, see http://www.horde.org/licenses/asl.php.
 *
 * @author  Jason M. Felice <jason.m.felice@gmail.com>
 * @package Ingo
 * @subpackage UnitTests
 */

require_once dirname(__FILE__) . '/TestBase.php';

class Ingo_MaildropTest extends Ingo_TestBase {

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

        $GLOBALS['ingo_storage'] = &Ingo_Storage::factory('mock',
                                                 array('maxblacklist' => 3,
                                                       'maxwhitelist' => 3));
        $GLOBALS['ingo_script'] = &Ingo_Script::factory('maildrop', array('path_style' => 'mbox'));
    }

    function testForwardKeep()
    {
        $forward = &new Ingo_Storage_forward();
        $forward->setForwardAddresses('joefabetes@example.com');
        $forward->setForwardKeep(true);

        $this->store($forward);
        $this->assertScript('if( \
/^From: .*/:h \
)
exception {
cc "! joefabetes@example.com"
to "${DEFAULT}"
}');
    }

    function testForwardNoKeep()
    {
        $forward = &new Ingo_Storage_forward();
        $forward->setForwardAddresses('joefabetes@example.com');
        $forward->setForwardKeep(false);

        $this->store($forward);
        $this->assertScript('if( \
/^From: .*/:h \
)
exception {
cc "! joefabetes@example.com"
exit
}');
    }

    function testBlacklistWithFolder()
    {
        $bl = &new Ingo_Storage_blacklist(3);
        $bl->setBlacklist(array('spammer@example.com'));
        $bl->setBlacklistFolder('Junk');

        $this->store($bl);
        $this->assertScript('if( \
/^From: .*spammer@example\.com/:h \
)
exception {
to Junk
}');
    }

    function testBlacklistMarker()
    {
        $bl = &new Ingo_Storage_blacklist(3);
        $bl->setBlacklist(array('spammer@example.com'));
        $bl->setBlacklistFolder(INGO_BLACKLIST_MARKER);

        $this->store($bl);
        $this->assertScript('if( \
/^From: .*spammer@example\.com/:h \
)
exception {
to ++DELETE++
}');
    }

    function testBlacklistDiscard()
    {
        $bl = &new Ingo_Storage_blacklist(3);
        $bl->setBlacklist(array('spammer@example.com'));
        $bl->setBlacklistFolder(null);

        $this->store($bl);
        $this->assertScript('if( \
/^From: .*spammer@example\.com/:h \
)
exception {
to "/dev/null"
}');
    }

    function testWhitelist()
    {
        $wl = &new Ingo_Storage_whitelist(3);
        $wl->setWhitelist(array('spammer@example.com'));

        $this->store($wl);
        $this->assertScript('if( \
/^From: .*spammer@example\.com/:h \
)
exception {
to "${DEFAULT}"
}');
    }

}
