<?php
/**
 * Ingo_Driver_null:: Implements a null api -- useful for just testing
 * the UI and storage.
 *
 * $Horde: ingo/lib/Driver/null.php,v 1.10.10.3 2007-12-20 14:05:47 jan Exp $
 *
 * See the enclosed file LICENSE for license information (ASL).  If you
 * did not receive this file, see http://www.horde.org/licenses/asl.php.
 *
 * @author  Brent J. Nordquist <bjn@horde.org>
 * @package Ingo
 */

class Ingo_Driver_null extends Ingo_Driver {

    /**
     * Whether this driver allows managing other users' rules.
     *
     * @var boolean
     */
    var $_support_shares = true;

}
