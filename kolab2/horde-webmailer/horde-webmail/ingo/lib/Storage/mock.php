<?php
/**
 * Ingo_Storage_mock:: is used for testing purposes.  It just keeps the
 * data local and doesn't put it anywhere.
 *
 * $Horde: ingo/lib/Storage/mock.php,v 1.2.2.1 2007-12-20 14:05:49 jan Exp $
 *
 * See the enclosed file LICENSE for license information (ASL).  If you
 * did not receive this file, see http://www.horde.org/licenses/asl.php.
 *
 * @author  Jason M. Felice <jason.m.felice@gmail.com>
 * @package Ingo
 */

class Ingo_Storage_mock extends Ingo_Storage {

    var $_data = array();

    function &_retrieve($field)
    {
        if (empty($this->_data[$field])) {
            switch ($field) {
            case INGO_STORAGE_ACTION_BLACKLIST:
                return new Ingo_Storage_blacklist();

            case INGO_STORAGE_ACTION_FILTERS:
                $ob = &new Ingo_Storage_filters();
                include INGO_BASE . '/config/prefs.php.dist';
                $ob->setFilterList(unserialize($_prefs['rules']['value']));
                return $ob;

            case INGO_STORAGE_ACTION_FORWARD:
                return new Ingo_Storage_forward();

            case INGO_STORAGE_ACTION_VACATION:
                return new Ingo_Storage_vacation();

            case INGO_STORAGE_ACTION_WHITELIST:
                return new Ingo_Storage_whitelist();

            case INGO_STORAGE_ACTION_SPAM:
                return new Ingo_Storage_spam();

            default:
                return false;
            }
        }

        return $this->_data[$field];
    }

    function _store(&$ob)
    {
        $this->_data[$ob->obType()] = $ob;
    }

}
