<?php
/**
 * Ingo_Storage_prefs:: implements the Ingo_Storage:: API to save Ingo data
 * via the Horde preferences system.
 *
 * $Horde: ingo/lib/Storage/prefs.php,v 1.14.12.14 2009-05-14 13:48:15 jan Exp $
 *
 * See the enclosed file LICENSE for license information (ASL).  If you
 * did not receive this file, see http://www.horde.org/licenses/asl.php.
 *
 * @author  Michael Slusarz <slusarz@horde.org>
 * @author  Jan Schneider <jan@horde.org>
 * @package Ingo
 */
class Ingo_Storage_prefs extends Ingo_Storage {

    /**
     * Constructor.
     *
     * @param array $params  Additional parameters for the subclass.
     */
    function Ingo_Storage_prefs($params = array())
    {
        $this->_params = $params;
    }

    /**
     * Retrieves the specified data from the storage backend.
     *
     * @param integer $field     The field name of the desired data.
     *                           See lib/Storage.php for the available fields.
     * @param boolean $readonly  Whether to disable any write operations.
     *
     * @return Ingo_Storage_rule|Ingo_Storage_filters  The specified data.
     */
    function &_retrieve($field, $readonly = false)
    {
        $prefs = &Prefs::singleton($GLOBALS['conf']['prefs']['driver'],
                                   $GLOBALS['registry']->getApp(),
                                   Ingo::getUser(), '', null, false);
        $prefs->retrieve();

        switch ($field) {
        case INGO_STORAGE_ACTION_BLACKLIST:
            $ob = new Ingo_Storage_blacklist();
            $data = @unserialize($prefs->getValue('blacklist'));
            if ($data) {
                $ob->setBlacklist($data['a'], false);
                $ob->setBlacklistFolder($data['f']);
            }
            break;

        case INGO_STORAGE_ACTION_WHITELIST:
            $ob = new Ingo_Storage_whitelist();
            $data = @unserialize($prefs->getValue('whitelist'));
            if ($data) {
                $ob->setWhitelist($data, false);
            }
            break;

        case INGO_STORAGE_ACTION_FILTERS:
            $ob = new Ingo_Storage_filters();
            $data = @unserialize($prefs->getValue('rules', false));
            if ($data === false) {
                /* Convert rules from the old format. */
                $data = @unserialize($prefs->getValue('rules'));
            } else {
                $data = String::convertCharset($data, $prefs->getCharset(), NLS::getCharset());
            }
            if ($data) {
                $ob->setFilterlist($data);
            }
            break;

        case INGO_STORAGE_ACTION_FORWARD:
            $ob = new Ingo_Storage_forward();
            $data = @unserialize($prefs->getValue('forward'));
            if ($data) {
                $ob->setForwardAddresses($data['a'], false);
                $ob->setForwardKeep($data['k']);
            }
            break;

        case INGO_STORAGE_ACTION_VACATION:
            $ob = new Ingo_Storage_vacation();
            $data = @unserialize($prefs->getValue('vacation', false));
            if ($data === false) {
                /* Convert vacation from the old format. */
                $data = unserialize($prefs->getValue('vacation'));
            } elseif (is_array($data)) {
                $data = $prefs->convertFromDriver($data, NLS::getCharset());
            }
            if ($data) {
                $ob->setVacationAddresses($data['addresses'], false);
                $ob->setVacationDays($data['days']);
                $ob->setVacationExcludes($data['excludes'], false);
                $ob->setVacationIgnorelist($data['ignorelist']);
                $ob->setVacationReason($data['reason']);
                $ob->setVacationSubject($data['subject']);
                if (isset($data['start'])) {
                    $ob->setVacationStart($data['start']);
                }
                if (isset($data['end'])) {
                    $ob->setVacationEnd($data['end']);
                }
            }
            break;

        case INGO_STORAGE_ACTION_SPAM:
            $ob = new Ingo_Storage_spam();
            $data = @unserialize($prefs->getValue('spam'));
            if ($data) {
                $ob->setSpamFolder($data['folder']);
                $ob->setSpamLevel($data['level']);
            }
            break;

        default:
            $ob = false;
            break;
        }

        return $ob;
    }

    /**
     * Stores the specified data in the storage backend.
     *
     * @access private
     *
     * @param Ingo_Storage_rule|Ingo_Storage_filters $ob  The object to store.
     *
     * @return boolean  True on success.
     */
    function _store($ob)
    {
        $prefs = &Prefs::singleton($GLOBALS['conf']['prefs']['driver'],
                                   $GLOBALS['registry']->getApp(),
                                   Ingo::getUser(), '', null, false);
        $prefs->retrieve();

        switch ($ob->obType()) {
        case INGO_STORAGE_ACTION_BLACKLIST:
            $data = array(
                'a' => $ob->getBlacklist(),
                'f' => $ob->getBlacklistFolder(),
            );
            return $prefs->setValue('blacklist', serialize($data));

        case INGO_STORAGE_ACTION_FILTERS:
            return $prefs->setValue('rules', serialize(String::convertCharset($ob->getFilterlist(), NLS::getCharset(), $prefs->getCharset())), false);

        case INGO_STORAGE_ACTION_FORWARD:
            $data = array(
                'a' => $ob->getForwardAddresses(),
                'k' => $ob->getForwardKeep(),
            );
            return $prefs->setValue('forward', serialize($data));

        case INGO_STORAGE_ACTION_VACATION:
            $data = array(
                'addresses' => $ob->getVacationAddresses(),
                'days' => $ob->getVacationDays(),
                'excludes' => $ob->getVacationExcludes(),
                'ignorelist' => $ob->getVacationIgnorelist(),
                'reason' => $ob->getVacationReason(),
                'subject' => $ob->getVacationSubject(),
                'start' => $ob->getVacationStart(),
                'end' => $ob->getVacationEnd(),
            );
            return $prefs->setValue('vacation', serialize($prefs->convertToDriver($data, NLS::getCharset())), false);

        case INGO_STORAGE_ACTION_WHITELIST:
            return $prefs->setValue('whitelist', serialize($ob->getWhitelist()));

        case INGO_STORAGE_ACTION_SPAM:
            $data = array(
                'folder' => $ob->getSpamFolder(),
                'level' => $ob->getSpamLevel(),
            );
            return $prefs->setValue('spam', serialize($data));
        }

        return false;
    }

}
