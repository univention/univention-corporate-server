<?php
/**
 * Ingo_Storage_sql implements the Ingo_Storage API to save Ingo data via
 * PHP's PEAR database abstraction layer.
 *
 * Required values for $params:<pre>
 *   'phptype'  - The database type (e.g. 'pgsql', 'mysql', etc.).
 *   'charset'  - The database's internal charset.</pre>
 *
 * Required by some database implementations:<pre>
 *   'database' - The name of the database.
 *   'hostspec' - The hostname of the database server.
 *   'protocol' - The communication protocol ('tcp', 'unix', etc.).
 *   'username' - The username with which to connect to the database.
 *   'password' - The password associated with 'username'.
 *   'options'  - Additional options to pass to the database.
 *   'tty'      - The TTY on which to connect to the database.
 *   'port'     - The port on which to connect to the database.</pre>
 *
 * The table structure can be created by the scripts/drivers/sql/ingo.sql
 * script.
 *
 * $Horde: ingo/lib/Storage/sql.php,v 1.21.2.7 2009-07-24 14:08:17 jan Exp $
 *
 * See the enclosed file LICENSE for license information (ASL).  If you
 * did not receive this file, see http://www.horde.org/licenses/asl.php.
 *
 * @author  Jan Schneider <jan@horde.org>
 * @since   Ingo 1.2
 * @package Ingo
 */
class Ingo_Storage_sql extends Ingo_Storage {

    /**
     * Handle for the current database connection.
     *
     * @var DB
     */
    var $_db;

    /**
     * Handle for the current database connection, used for writing.
     *
     * Defaults to the same handle as $_db if a separate write database is not
     * required.
     *
     * @var DB
     */
    var $_write_db;

    /**
     * Boolean indicating whether or not we're connected to the SQL server.
     *
     * @var boolean
     */
    var $_connected = false;

    /**
     * Constructor.
     *
     * @param array $params  Additional parameters for the subclass.
     */
    function Ingo_Storage_sql($params = array())
    {
        $this->_params = $params;

        Horde::assertDriverConfig($this->_params, 'storage',
                                  array('phptype', 'charset'));

        if (!isset($this->_params['database'])) {
            $this->_params['database'] = '';
        }
        if (!isset($this->_params['username'])) {
            $this->_params['username'] = '';
        }
        if (!isset($this->_params['hostspec'])) {
            $this->_params['hostspec'] = '';
        }
        $this->_params['table_rules'] = 'ingo_rules';
        $this->_params['table_lists'] = 'ingo_lists';
        $this->_params['table_vacations'] = 'ingo_vacations';
        $this->_params['table_forwards'] = 'ingo_forwards';
        $this->_params['table_spam'] = 'ingo_spam';

        /* Connect to the SQL server using the supplied parameters. */
        require_once 'DB.php';
        $this->_write_db = &DB::connect($this->_params,
                                        array('persistent' => !empty($this->_params['persistent']),
                                              'ssl' => !empty($this->_params['ssl'])));
        if (is_a($this->_write_db, 'PEAR_Error')) {
            Horde::fatal($this->_write_db, __FILE__, __LINE__);
        }
        /* Set DB portability options. */
        switch ($this->_write_db->phptype) {
        case 'mssql':
            $this->_write_db->setOption('portability', DB_PORTABILITY_LOWERCASE | DB_PORTABILITY_ERRORS | DB_PORTABILITY_RTRIM);
            break;
        default:
            $this->_write_db->setOption('portability', DB_PORTABILITY_LOWERCASE | DB_PORTABILITY_ERRORS);
        }


        /* Check if we need to set up the read DB connection seperately. */
        if (!empty($this->_params['splitread'])) {
            $params = array_merge($this->_params, $this->_params['read']);
            $this->_db = &DB::connect($params,
                                      array('persistent' => !empty($params['persistent']),
                                            'ssl' => !empty($params['ssl'])));
            if (is_a($this->_db, 'PEAR_Error')) {
                Horde::fatal($this->_db, __FILE__, __LINE__);
            }

            switch ($this->_db->phptype) {
            case 'mssql':
                $this->_db->setOption('portability', DB_PORTABILITY_LOWERCASE | DB_PORTABILITY_ERRORS | DB_PORTABILITY_RTRIM);
                break;
            default:
                $this->_db->setOption('portability', DB_PORTABILITY_LOWERCASE | DB_PORTABILITY_ERRORS);
            }
        } else {
            /* Default to the same DB handle for the writer too. */
            $this->_db =& $this->_write_db;
        }
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
        switch ($field) {
        case INGO_STORAGE_ACTION_BLACKLIST:
        case INGO_STORAGE_ACTION_WHITELIST:
            if ($field == INGO_STORAGE_ACTION_BLACKLIST) {
                $ob = new Ingo_Storage_blacklist();
                $filters = &$this->retrieve(INGO_STORAGE_ACTION_FILTERS);
                if (is_a($filters, 'PEAR_Error')) {
                    return $filters;
                }
                $rule = $filters->findRule($field);
                if (isset($rule['action-value'])) {
                    $ob->setBlacklistFolder($rule['action-value']);
                }
            } else {
                $ob = new Ingo_Storage_whitelist();
            }
            $query = sprintf('SELECT list_address FROM %s WHERE list_owner = ? AND list_blacklist = ?',
                             $this->_params['table_lists']);
            $values = array(Ingo::getUser(),
                            (int)($field == INGO_STORAGE_ACTION_BLACKLIST));
            Horde::logMessage('Ingo_Storage_sql::_retrieve(): ' . $query,
                              __FILE__, __LINE__, PEAR_LOG_DEBUG);
            $addresses = $this->_db->getCol($query, 0, $values);
            if (is_a($addresses, 'PEAR_Error')) {
                Horde::logMessage($addresses, __FILE__, __LINE__, PEAR_LOG_ERR);
                return $addresses;
            }
            if ($field == INGO_STORAGE_ACTION_BLACKLIST) {
                $ob->setBlacklist($addresses, false);
            } else {
                $ob->setWhitelist($addresses, false);
            }
            break;

        case INGO_STORAGE_ACTION_FILTERS:
            $ob = &new Ingo_Storage_filters_sql($this->_db, $this->_write_db, $this->_params);
            if (is_a($result = $ob->init($readonly), 'PEAR_Error')) {
                return $result;
            }
            break;

        case INGO_STORAGE_ACTION_FORWARD:
            $query = sprintf('SELECT * FROM %s WHERE forward_owner = ?',
                             $this->_params['table_forwards']);
            Horde::logMessage('Ingo_Storage_sql::_retrieve(): ' . $query,
                              __FILE__, __LINE__, PEAR_LOG_DEBUG);
            $result = $this->_db->query($query, Ingo::getUser());
            $data = $result->fetchRow(DB_FETCHMODE_ASSOC);

            $ob = new Ingo_Storage_forward();
            if ($data && !is_a($data, 'PEAR_Error')) {
                $ob->setForwardAddresses(explode("\n", $data['forward_addresses']), false);
                $ob->setForwardKeep((bool)$data['forward_keep']);
                $ob->setSaved(true);
            } elseif ($data = @unserialize($GLOBALS['prefs']->getDefault('vacation'))) {
                $ob->setForwardAddresses($data['a'], false);
                $ob->setForwardKeep($data['k']);
            }
            break;

        case INGO_STORAGE_ACTION_VACATION:
            $query = sprintf('SELECT * FROM %s WHERE vacation_owner = ?',
                             $this->_params['table_vacations']);
            Horde::logMessage('Ingo_Storage_sql::_retrieve(): ' . $query,
                              __FILE__, __LINE__, PEAR_LOG_DEBUG);
            $result = $this->_db->query($query, Ingo::getUser());
            $data = $result->fetchRow(DB_FETCHMODE_ASSOC);

            $ob = new Ingo_Storage_vacation();
            if ($data && !is_a($data, 'PEAR_Error')) {
                $ob->setVacationAddresses(explode("\n", $data['vacation_addresses']), false);
                $ob->setVacationDays((int)$data['vacation_days']);
                $ob->setVacationStart((int)$data['vacation_start']);
                $ob->setVacationEnd((int)$data['vacation_end']);
                $ob->setVacationExcludes(explode("\n", $data['vacation_excludes']), false);
                $ob->setVacationIgnorelist((bool)$data['vacation_ignorelists']);
                $ob->setVacationReason(String::convertCharset($data['vacation_reason'], $this->_params['charset']));
                $ob->setVacationSubject(String::convertCharset($data['vacation_subject'], $this->_params['charset']));
                $ob->setSaved(true);
            } elseif ($data = @unserialize($GLOBALS['prefs']->getDefault('vacation'))) {
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
            $query = sprintf('SELECT * FROM %s WHERE spam_owner = ?',
                             $this->_params['table_spam']);
            Horde::logMessage('Ingo_Storage_sql::_retrieve(): ' . $query,
                              __FILE__, __LINE__, PEAR_LOG_DEBUG);
            $result = $this->_db->query($query, Ingo::getUser());
            $data = $result->fetchRow(DB_FETCHMODE_ASSOC);

            $ob = new Ingo_Storage_spam();
            if ($data && !is_a($data, 'PEAR_Error')) {
                $ob->setSpamFolder($data['spam_folder']);
                $ob->setSpamLevel((int)$data['spam_level']);
                $ob->setSaved(true);
            } elseif ($data = @unserialize($GLOBALS['prefs']->getDefault('spam'))) {
                $ob->setSpamFolder($data['folder']);
                $ob->setSpamLevel($data['level']);
            }
            break;

        default:
            $ob = false;
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
    function _store(&$ob)
    {
        switch ($ob->obType()) {
        case INGO_STORAGE_ACTION_BLACKLIST:
        case INGO_STORAGE_ACTION_WHITELIST:
            $is_blacklist = (int)($ob->obType() == INGO_STORAGE_ACTION_BLACKLIST);
            if ($is_blacklist) {
                $filters = &$this->retrieve(INGO_STORAGE_ACTION_FILTERS);
                if (is_a($filters, 'PEAR_Error')) {
                    return $filters;
                }
                $id = $filters->findRuleId(INGO_STORAGE_ACTION_BLACKLIST);
                if ($id !== null) {
                    $rule = $filters->getRule($id);
                    if (!isset($rule['action-value']) ||
                        $rule['action-value'] != $ob->getBlacklistFolder()) {
                        $rule['action-value'] = $ob->getBlacklistFolder();
                        $filters->updateRule($rule, $id);
                    }
                }
            }
            $query = sprintf('DELETE FROM %s WHERE list_owner = ? AND list_blacklist = ?',
                             $this->_params['table_lists']);
            $values = array(Ingo::getUser(), $is_blacklist);
            Horde::logMessage('Ingo_Storage_sql::_store(): ' . $query,
                              __FILE__, __LINE__, PEAR_LOG_DEBUG);
            $result = $this->_write_db->query($query, $values);
            if (is_a($result, 'PEAR_Error')) {
                Horde::logMessage($result, __FILE__, __LINE__, PEAR_LOG_ERR);
                return $result;
            }
            $query = sprintf('INSERT INTO %s (list_owner, list_blacklist, list_address) VALUES (?, ?, ?)',
                             $this->_params['table_lists']);
            Horde::logMessage('Ingo_Storage_sql::_store(): ' . $query,
                              __FILE__, __LINE__, PEAR_LOG_DEBUG);
            $addresses = $is_blacklist ? $ob->getBlacklist() : $ob->getWhitelist();
            foreach ($addresses as $address) {
                $result = $this->_write_db->query($query,
                                                  array(Ingo::getUser(),
                                                        $is_blacklist,
                                                        $address));
                if (is_a($result, 'PEAR_Error')) {
                    Horde::logMessage($result, __FILE__, __LINE__, PEAR_LOG_ERR);
                    return $result;
                }
            }
            $ob->setSaved(true);
            $ret = true;
            break;

        case INGO_STORAGE_ACTION_FILTERS:
            $ret = true;
            break;

        case INGO_STORAGE_ACTION_FORWARD:
            if ($ob->isSaved()) {
                $query = 'UPDATE %s SET forward_addresses = ?, forward_keep = ? WHERE forward_owner = ?';
            } else {
                $query = 'INSERT INTO %s (forward_addresses, forward_keep, forward_owner) VALUES (?, ?, ?)';
            }
            $query = sprintf($query, $this->_params['table_forwards']);
            $values = array(
                implode("\n", $ob->getForwardAddresses()),
                (int)(bool)$ob->getForwardKeep(),
                Ingo::getUser());
            Horde::logMessage('Ingo_Storage_sql::_store(): ' . $query,
                              __FILE__, __LINE__, PEAR_LOG_DEBUG);
            $ret = $this->_write_db->query($query, $values);
            if (!is_a($ret, 'PEAR_Error')) {
                $ob->setSaved(true);
            }
            break;

        case INGO_STORAGE_ACTION_VACATION:
            if ($ob->isSaved()) {
                $query = 'UPDATE %s SET vacation_addresses = ?, vacation_subject = ?, vacation_reason = ?, vacation_days = ?, vacation_start = ?, vacation_end = ?, vacation_excludes = ?, vacation_ignorelists = ? WHERE vacation_owner = ?';
            } else {
                $query = 'INSERT INTO %s (vacation_addresses, vacation_subject, vacation_reason, vacation_days, vacation_start, vacation_end, vacation_excludes, vacation_ignorelists, vacation_owner) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)';
            }
            $query = sprintf($query, $this->_params['table_vacations']);
            $values = array(
                implode("\n", $ob->getVacationAddresses()),
                String::convertCharset($ob->getVacationSubject(),
                                       NLS::getCharset(),
                                       $this->_params['charset']),
                String::convertCharset($ob->getVacationReason(),
                                       NLS::getCharset(),
                                       $this->_params['charset']),
                (int)$ob->getVacationDays(),
                (int)$ob->getVacationStart(),
                (int)$ob->getVacationEnd(),
                implode("\n", $ob->getVacationExcludes()),
                (int)(bool)$ob->getVacationIgnorelist(),
                Ingo::getUser());
            Horde::logMessage('Ingo_Storage_sql::_store(): ' . $query,
                              __FILE__, __LINE__, PEAR_LOG_DEBUG);
            $ret = $this->_write_db->query($query, $values);
            if (!is_a($ret, 'PEAR_Error')) {
                $ob->setSaved(true);
            }
            break;

        case INGO_STORAGE_ACTION_SPAM:
            if ($ob->isSaved()) {
                $query = 'UPDATE %s SET spam_level = ?, spam_folder = ? WHERE spam_owner = ?';
            } else {
                $query = 'INSERT INTO %s (spam_level, spam_folder, spam_owner) VALUES (?, ?, ?)';
            }
            $query = sprintf($query, $this->_params['table_spam']);
            $values = array(
                (int)$ob->getSpamLevel(),
                $ob->getSpamFolder(),
                Ingo::getUser());
            Horde::logMessage('Ingo_Storage_sql::_store(): ' . $query,
                              __FILE__, __LINE__, PEAR_LOG_DEBUG);
            $ret = $this->_write_db->query($query, $values);
            if (!is_a($ret, 'PEAR_Error')) {
                $ob->setSaved(true);
            }
            break;

        default:
            $ret = false;
            break;
        }

        if (is_a($ret, 'PEAR_Error')) {
            Horde::logMessage($ret, __FILE__, __LINE__);
        }

        return $ret;
    }

    /**
     * Removes the data of the specified user from the storage backend.
     *
     * @param string $user  The user name to delete filters for.
     *
     * @return mixed  True | PEAR_Error
     */
    function removeUserData($user)
    {
        if (!Auth::isAdmin() && $user != Auth::getAuth()) {
            return PEAR::raiseError(_("Permission Denied"));
        }

        $queries = array(sprintf('DELETE FROM %s WHERE rule_owner = ?',
                                 $this->_params['table_rules']),
                         sprintf('DELETE FROM %s WHERE list_owner = ?',
                                 $this->_params['table_lists']),
                         sprintf('DELETE FROM %s WHERE vacation_owner = ?',
                                 $this->_params['table_vacations']),
                         sprintf('DELETE FROM %s WHERE forward_owner = ?',
                                 $this->_params['table_forwards']),
                         sprintf('DELETE FROM %s WHERE spam_owner = ?',
                                 $this->_params['table_spam']));

        $values = array($user);
        foreach ($queries as $query) {
            Horde::logMessage('Ingo_Storage_sql::removeUserData(): ' . $query, __FILE__, __LINE__, PEAR_LOG_DEBUG);
            $result = $this->_write_db->query($query, $values);
            if (is_a($result, 'PEAR_Error')) {
                return $result;
            }
        }

        return true;
    }

}

/**
 * Ingo_Storage_filters_sql is the object used to hold user-defined filtering
 * rule information.
 *
 * @author  Jan Schneider <jan@horde.org>
 * @since   Ingo 1.2
 * @package Ingo
 */
class Ingo_Storage_filters_sql extends Ingo_Storage_filters {

    /**
     * Handle for the current database connection.
     *
     * @var DB
     */
    var $_db;

    /**
     * Handle for the current database connection, used for writing.
     *
     * Defaults to the same handle as $_db if a separate write database is not
     * required.
     *
     * @var DB
     */
    var $_write_db;

    /**
     * Driver specific parameters.
     *
     * @var array
     */
    var $_params;

    /**
     * Constructor.
     *
     * @param DB $db         Handle for the database connection.
     * @param DB $write_db   Handle for the database connection, used for
     *                       writing.
     * @param array $params  Driver specific parameters.
     */
    function Ingo_Storage_filters_sql($db, $write_db, $params)
    {
        $this->_db = $db;
        $this->_write_db = $write_db;
        $this->_params = $params;
    }

    /**
     * Loads all rules from the DB backend.
     *
     * @param boolean $readonly  Whether to disable any write operations.
     */
    function init($readonly = false)
    {
        $query = sprintf('SELECT * FROM %s WHERE rule_owner = ? ORDER BY rule_order',
                         $this->_params['table_rules']);
        $values = array(Ingo::getUser());
        Horde::logMessage('Ingo_Storage_filters_sql(): ' . $query, __FILE__, __LINE__, PEAR_LOG_DEBUG);
        $result = $this->_db->query($query, $values);
        if (is_a($result, 'PEAR_Error')) {
            return $result;
        }
        $data = array();
        while ($row = $result->fetchRow(DB_FETCHMODE_ASSOC)) {
            $data[$row['rule_order']] = array(
                'id' => (int)$row['rule_id'],
                'name' => String::convertCharset($row['rule_name'], $this->_params['charset']),
                'action' => (int)$row['rule_action'],
                'action-value' => String::convertCharset($row['rule_value'], $this->_params['charset']),
                'flags' => (int)$row['rule_flags'],
                'conditions' => empty($row['rule_conditions']) ? null : String::convertCharset(unserialize($row['rule_conditions']), $this->_params['charset']),
                'combine' => (int)$row['rule_combine'],
                'stop' => (bool)$row['rule_stop'],
                'disable' => !(bool)$row['rule_active']);
        }
        $this->setFilterlist($data);

        if (empty($data) && !$readonly) {
            $data = @unserialize($GLOBALS['prefs']->getDefault('rules'));
            if ($data) {
                foreach ($data as $val) {
                    $this->addRule($val, false);
                }
            } else {
                $this->addRule(
                    array('name' => 'Whitelist',
                          'action' => INGO_STORAGE_ACTION_WHITELIST),
                    false);
                $this->addRule(
                    array('name' => 'Vacation',
                          'action' => INGO_STORAGE_ACTION_VACATION,
                          'disable' => true),
                    false);
                $this->addRule(
                    array('name' => 'Blacklist',
                          'action' => INGO_STORAGE_ACTION_BLACKLIST),
                    false);
                $this->addRule(
                    array('name' => 'Spam Filter',
                          'action' => INGO_STORAGE_ACTION_SPAM,
                          'disable' => true),
                    false);
                $this->addRule(
                    array('name' => 'Forward',
                          'action' => INGO_STORAGE_ACTION_FORWARD),
                    false);
            }
        }
    }

    /**
     * Converts a rule hash from Ingo's internal format to the database
     * format.
     *
     * @param array $rule  Rule hash in Ingo's format.
     *
     * @return array  Rule hash in DB's format.
     */
    function _ruleToBackend($rule)
    {
        return array(String::convertCharset($rule['name'], NLS::getCharset(), $this->_params['charset']),
                     (int)$rule['action'],
                     isset($rule['action-value']) ? String::convertCharset($rule['action-value'], NLS::getCharset(), $this->_params['charset']) : null,
                     isset($rule['flags']) ? (int)$rule['flags'] : null,
                     isset($rule['conditions']) ? serialize(String::convertCharset($rule['conditions'], NLS::getCharset(), $this->_params['charset'])) : null,
                     isset($rule['combine']) ? (int)$rule['combine'] : null,
                     isset($rule['stop']) ? (int)$rule['stop'] : null,
                     isset($rule['disable']) ? (int)(!$rule['disable']) : 1);
    }

    /**
     * Adds a rule hash to the filters list.
     *
     * @param array $rule       A rule hash.
     * @param boolean $default  If true merge the rule hash with default rule
     *                          values.
     */
    function addRule($rule, $default = true)
    {
        if ($default) {
            $rule = array_merge($this->getDefaultRule(), $rule);
        }

        $query = sprintf('INSERT INTO %s (rule_id, rule_owner, rule_name, rule_action, rule_value, rule_flags, rule_conditions, rule_combine, rule_stop, rule_active, rule_order) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)',
                         $this->_params['table_rules']);
        $id = $this->_write_db->nextId($this->_params['table_rules']);
        if (is_a($id, 'PEAR_Error')) {
            return $id;
        }
        $order = key(array_reverse($this->_filters, true)) + 1;
        $values = array_merge(array($id, Ingo::getUser()),
                              $this->_ruleToBackend($rule),
                              array($order));
        Horde::logMessage('Ingo_Storage_filters_sql::addRule(): ' . $query, __FILE__, __LINE__, PEAR_LOG_DEBUG);
        $result = $this->_write_db->query($query, $values);
        if (is_a($result, 'PEAR_Error')) {
            Horde::logMessage($result, __FILE__, __LINE__, PEAR_LOG_ERR);
            return $result;
        }

        $rule['id'] = $id;
        $this->_filters[$order] = $rule;
    }

    /**
     * Updates an existing rule with a rule hash.
     *
     * @param array $rule  A rule hash
     * @param integer $id  A rule number
     */
    function updateRule($rule, $id)
    {
        $query = sprintf('UPDATE %s SET rule_name = ?, rule_action = ?, rule_value = ?, rule_flags = ?, rule_conditions = ?, rule_combine = ?, rule_stop = ?, rule_active = ?, rule_order = ? WHERE rule_id = ? AND rule_owner = ?',
                         $this->_params['table_rules']);
        $values = array_merge($this->_ruleToBackend($rule),
                              array($id, $rule['id'], Ingo::getUser()));
        Horde::logMessage('Ingo_Storage_filters_sql::updateRule(): ' . $query, __FILE__, __LINE__, PEAR_LOG_DEBUG);
        $result = $this->_write_db->query($query, $values);
        if (is_a($result, 'PEAR_Error')) {
            Horde::logMessage($result, __FILE__, __LINE__, PEAR_LOG_ERR);
            return $result;
        }

        $this->_filters[$id] = $rule;
    }

    /**
     * Deletes a rule from the filters list.
     *
     * @param integer $id  Number of the rule to delete.
     *
     * @return boolean  True if the rule has been found and deleted.
     */
    function deleteRule($id)
    {
        if (!isset($this->_filters[$id])) {
            return false;
        }

        $query = sprintf('DELETE FROM %s WHERE rule_id = ? AND rule_owner = ?',
                         $this->_params['table_rules']);
        $values = array($this->_filters[$id]['id'], Ingo::getUser());
        Horde::logMessage('Ingo_Storage_filters_sql::deleteRule(): ' . $query, __FILE__, __LINE__, PEAR_LOG_DEBUG);
        $result = $this->_write_db->query($query, $values);
        if (is_a($result, 'PEAR_Error')) {
            Horde::logMessage($result, __FILE__, __LINE__, PEAR_LOG_ERR);
            return $result;
        }
        unset($this->_filters[$id]);

        $query = sprintf('UPDATE %s SET rule_order = rule_order - 1 WHERE rule_owner = ? AND rule_order > ?',
                         $this->_params['table_rules']);
        $values = array(Ingo::getUser(), $id);
        Horde::logMessage('Ingo_Storage_filters_sql::deleteRule(): ' . $query,
                          __FILE__, __LINE__, PEAR_LOG_DEBUG);
        $result = $this->_write_db->query($query, $values);
        if (is_a($result, 'PEAR_Error')) {
            Horde::logMessage($result, __FILE__, __LINE__, PEAR_LOG_ERR);
            return $result;
        }

        return true;
    }

    /**
     * Creates a copy of an existing rule.
     *
     * The created copy is added to the filters list right after the original
     * rule.
     *
     * @param integer $id  Number of the rule to copy.
     *
     * @return boolean  True if the rule has been found and copied.
     */
    function copyRule($id)
    {
        if (isset($this->_filters[$id])) {
            $newrule = $this->_filters[$id];
            $newrule['name'] = sprintf(_("Copy of %s"), $this->_filters[$id]['name']);
            $this->addRule($newrule, false);
            $this->ruleUp(count($this->_filters) - 1, count($this->_filters) - $id - 2);
            return true;
        }

        return false;
    }

    /**
     * Moves a rule up in the filters list.
     *
     * @param integer $id     Number of the rule to move.
     * @param integer $steps  Number of positions to move the rule up.
     */
    function ruleUp($id, $steps = 1)
    {
        return $this->_ruleMove($id, -$steps);
    }

    /**
     * Moves a rule down in the filters list.
     *
     * @param integer $id     Number of the rule to move.
     * @param integer $steps  Number of positions to move the rule down.
     */
    function ruleDown($id, $steps = 1)
    {
        return $this->_ruleMove($id, $steps);
    }

    /**
     * Moves a rule in the filters list.
     *
     * @param integer $id     Number of the rule to move.
     * @param integer $steps  Number of positions and direction to move the
     *                        rule.
     */
    function _ruleMove($id, $steps)
    {
        $query = sprintf('UPDATE %s SET rule_order = rule_order %s 1 WHERE rule_owner = ? AND rule_order %s ? AND rule_order %s ?',
                         $this->_params['table_rules'],
                         $steps > 0 ? '-' : '+',
                         $steps > 0 ? '>' : '>=',
                         $steps > 0 ? '<=' : '<');
        $values = array(Ingo::getUser());
        if ($steps < 0) {
            $values[] = (int)($id + $steps);
            $values[] = (int)$id;
        } else {
            $values[] = (int)$id;
            $values[] = (int)($id + $steps);
        }
        Horde::logMessage('Ingo_Storage_filters_sql::ruleUp(): ' . $query,
                          __FILE__, __LINE__, PEAR_LOG_DEBUG);
        $result = $this->_write_db->query($query, $values);
        if (is_a($result, 'PEAR_Error')) {
            Horde::logMessage($result, __FILE__, __LINE__, PEAR_LOG_ERR);
            return $result;
        }
        $query = sprintf('UPDATE %s SET rule_order = ? WHERE rule_owner = ? AND rule_id = ?',
                         $this->_params['table_rules']);
        $values = array((int)($id + $steps),
                        Ingo::getUser(),
                        $this->_filters[$id]['id']);
        Horde::logMessage('Ingo_Storage_filters_sql::ruleUp(): ' . $query,
                          __FILE__, __LINE__, PEAR_LOG_DEBUG);
        $result = $this->_write_db->query($query, $values);
        if (is_a($result, 'PEAR_Error')) {
            Horde::logMessage($result, __FILE__, __LINE__, PEAR_LOG_ERR);
            return $result;
        }

        $this->init();
    }

    /**
     * Disables a rule.
     *
     * @param integer $id  Number of the rule to disable.
     */
    function ruleDisable($id)
    {
        $rule = $this->_filters[$id];
        $rule['disable'] = true;
        $this->updateRule($rule, $id);
    }

    /**
     * Enables a rule.
     *
     * @param integer $id  Number of the rule to enable.
     */
    function ruleEnable($id)
    {
        $rule = $this->_filters[$id];
        $rule['disable'] = false;
        $this->updateRule($rule, $id);
    }

}
