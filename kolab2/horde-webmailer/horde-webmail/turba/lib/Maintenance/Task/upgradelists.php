<?php
/**
 * Maintenance task for upgrading contact lists after upgrading to Turba 2.2
 *
 * $Horde: turba/lib/Maintenance/Task/upgradelists.php,v 1.6.2.3 2008-06-09 03:28:08 chuck Exp $
 *
 * @author Michael J. Rubinsky <mrubinsk@horde.org>
 * @package Turba
 * @since Turba 2.2
 */

class Maintenance_Task_Turba_upgradelists {

    /**
     * Holds an array of Horde_Share_Object objects.
     *
     * @var array
     */
    var $_shares;

    /**
     * Perform all functions for this task.
     *
     * @return mixed True | PEAR_Error
     */
    function doMaintenance()
    {
        if (!empty($_SESSION['turba']['has_share'])) {
            $criteria = array('__type' => 'Group');
            $sources = array_keys($GLOBALS['cfgSources']);
            foreach ($sources as $sourcekey) {
                $driver = &Turba_Driver::singleton($sourcekey);
                $lists = $driver->search($criteria);
                if (is_a($lists, 'PEAR_Error')) {
                    return $lists;
                }
                $cnt = $lists->count();
                for ($j = 0; $j < $cnt; ++$j) {
                    $list = $lists->next();
                    $attributes = $list->getAttributes();
                    $members = @unserialize($attributes['__members']);
                    if (is_array($members) && !empty($members[0])) {
                        $c = count($members);
                        for ($i = 0; $i < $c; ++$i) {
                            if (substr_count($members[$i], ':') == 2) {
                                preg_match('/^([a-zA-Z0-9]+:[a-zA-Z0-9]+)(:[a-zA-Z0-9]+)$/', $members[$i], $matches);
                                $source = $matches[1];
                                $contact_key = substr($matches[2], 1);
                            } elseif (substr_count($members[$i], ':') == 1) {
                                list($source, $contact_key) = explode(':', $members[$i]);
                            } else {
                                break;
                            }
                            $source = $this->_updateShareName($source);
                            $members[$i] = $source . ':' . $contact_key;
                        }
                        $list->setValue('__members', serialize($members));
                        $list->store();
                    }
                }
            }
        }
        return true;

    }

    /**
     * Helper function to update a 'legacy' share name
     * to the new flattened share style.
     */
    function _updateShareName($book)
    {
        static $cache = array();

        // No sense going through all the logic if we know we're empty.
        if (empty($book)) {
            return $book;
        }

        if (empty($this->_shares)) {
            $this->_shares = Turba::listShares();
        }

        // Have we seen this one yet?
        if (!empty($cache[$book])) {
            return $cache[$book];
        }

        // Is it an unmodified share key already?
        if (strpos($book, ':') !== false) {
            list($source, $key) = explode(':', $book, 2);
            $source = trim($source);
            $key = trim($key);
            if (isset($this->_shares[$key])) {
                $params = @unserialize($this->_shares[$key]->get('params'));
                // I'm not sure if this would ever be not true, but...
                if ($params['source'] == $source) {
                    $cache[$book] = $key;
                    return $key;
                }
            } else {
                // Maybe a key the upgrade script modified?
                foreach ($this->_shares as $skey => $share) {
                    $params = @unserialize($share->get('params'));
                    if ($params['name'] == $key &&
                        $params['source'] == $source) {

                       $cache[$book] = $skey;
                       return $skey;
                    }
                }
            }
        } else {
            // Need to check if this is a default address book for
            // one of our sources that is share enabled.
            foreach ($this->_shares as $skey => $share) {
                $params = @unserialize($share->get('params'));
                if ($params['source'] == $book &&
                    !empty($params['default'])) {
                    $cache[$book] = $skey;
                    return $skey;
                }
            }
        }

        // Special case for contacts from an IMSP source. The cfgSource
        // keys changed from 2.1 to 2.2 due to needs of the share code.
        if (strpos($book, 'IMSP_')) {
            // @TODO: Perform magical matching of IMSP-# to username.bookname.
        }

        // Must be a normal, non-shared source, just pass it back.
        $cache[$book] = $book;
        return $book;
    }

    function describeMaintenance()
    {

    }

}
