<?php
/**
 * Mnemo storage implementation for PHP's PEAR database abstraction
 * layer.
 *
 * Required parameters:<pre>
 *      'phptype'       The database type (e.g. 'pgsql', 'mysql', etc.).
 *      'charset'       The database's internal charset.</pre>
 *
 * Optional values:<pre>
 *      'table'         The name of the memos table in 'database'. Defaults
 *                      to 'mnemo_memos'</pre>
 *
 * Required by some database implementations:<pre>
 *      'hostspec'      The hostname of the database server.
 *      'protocol'      The communication protocol ('tcp', 'unix', etc.).
 *      'database'      The name of the database.
 *      'username'      The username with which to connect to the database.
 *      'password'      The password associated with 'username'.
 *      'options'       Additional options to pass to the database.
 *      'tty'           The TTY on which to connect to the database.
 *      'port'          The port on which to connect to the database.</pre>
 *
 * The table structure is defined in scripts/drivers/mnemo_memos.sql.
 *
 * $Horde: mnemo/lib/Driver/sql.php,v 1.28.2.20 2009-02-17 18:42:26 chuck Exp $
 *
 * Copyright 2001-2009 The Horde Project (http://www.horde.org/)
 *
 * See the enclosed file LICENSE for license information (ASL). If you
 * did not receive this file, see http://www.horde.org/licenses/asl.php.
 *
 * @author  Chuck Hagenbuch <chuck@horde.org>
 * @since   Mnemo 1.0
 * @package Mnemo
 */
class Mnemo_Driver_sql extends Mnemo_Driver {

    /**
     * Hash containing connection parameters.
     *
     * @var array
     */
    var $_params = array();

    /**
     * The database connection object.
     *
     * @var DB
     */
    var $_db;

    /**
     * Handle for the current database connection, used for writing. Defaults
     * to the same handle as $_db if a separate write database is not required.
     *
     * @var DB
     */
    var $_write_db;

    /**
     * Construct a new SQL storage object.
     *
     * @param string $notepad   The name of the notepad to load/save notes from.
     * @param array  $params    A hash containing connection parameters.
     */
    function Mnemo_Driver_sql($notepad, $params = array())
    {
        $this->_notepad = $notepad;
        $this->_params = $params;
    }

    /**
     * Attempts to open a connection to the SQL server.
     *
     * @return boolean  True on success, PEAR_Error on failure.
     */
    function initialize()
    {
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

        if (!isset($this->_params['table'])) {
            $this->_params['table'] = 'mnemo_memos';
        }

        /* Connect to the SQL server using the supplied parameters. */
        require_once 'DB.php';
        $this->_write_db = &DB::connect($this->_params,
                                        array('persistent' => !empty($this->_params['persistent']),
                                              'ssl' => !empty($this->_params['ssl'])));
        if (is_a($this->_write_db, 'PEAR_Error')) {
            Horde::fatal($this->_write_db, __FILE__, __LINE__);
        }

        // Set DB portability options.
        switch ($this->_write_db->phptype) {
        case 'mssql':
            $this->_write_db->setOption('portability', DB_PORTABILITY_LOWERCASE | DB_PORTABILITY_ERRORS | DB_PORTABILITY_RTRIM);
            break;
        default:
            $this->_write_db->setOption('portability', DB_PORTABILITY_LOWERCASE | DB_PORTABILITY_ERRORS);
        }

        /* Check if we need to set up the read DB connection
         * seperately. */
        if (!empty($this->_params['splitread'])) {
            $params = array_merge($this->_params, $this->_params['read']);
            $this->_db = &DB::connect($params,
                                      array('persistent' => !empty($params['persistent']),
                                            'ssl' => !empty($params['ssl'])));
            if (is_a($this->_db, 'PEAR_Error')) {
                Horde::fatal($this->_db, __FILE__, __LINE__);
            }

            // Set DB portability options.
            switch ($this->_db->phptype) {
            case 'mssql':
                $this->_db->setOption('portability', DB_PORTABILITY_LOWERCASE | DB_PORTABILITY_ERRORS | DB_PORTABILITY_RTRIM);
                break;
            default:
                $this->_db->setOption('portability', DB_PORTABILITY_LOWERCASE | DB_PORTABILITY_ERRORS);
            }
        } else {
            /* Default to the same DB handle for reads. */
            $this->_db =& $this->_write_db;
        }

        return true;
    }

    /**
     * Retrieve one note from the database.
     *
     * @param string $noteId      The ID of the note to retrieve.
     * @param string $passphrase  A passphrase with which this note was
     *                            supposed to be encrypted.
     *
     * @return array  The array of note attributes.
     */
    function get($noteId, $passphrase = null)
    {
        /* Build the SQL query. */
        $query = 'SELECT * FROM ' . $this->_params['table'] .
                 ' WHERE memo_owner = ? AND memo_id = ?';
        $values = array($this->_notepad, $noteId);

        /* Log the query at a DEBUG log level. */
        Horde::logMessage(sprintf('Mnemo_Driver_sql::get(): %s', $query),
                          __FILE__, __LINE__, PEAR_LOG_DEBUG);

        /* Execute the query. */
        $row = $this->_db->getRow($query, $values, DB_FETCHMODE_ASSOC);

        if (is_a($row, 'PEAR_Error')) {
            return $row;
        }

        return $this->_buildNote($row, $passphrase);
    }

    /**
     * Retrieve one note from the database by UID.
     *
     * @param string $uid         The UID of the note to retrieve.
     * @param string $passphrase  A passphrase with which this note was
     *                            supposed to be encrypted.
     *
     * @return array  The array of note attributes.
     */
    function getByUID($uid, $passphrase = null)
    {
        /* Build the SQL query. */
        $query = 'SELECT * FROM ' . $this->_params['table'] .
                 ' WHERE memo_uid = ?';
        $values = array($uid);

        /* Log the query at a DEBUG log level. */
        Horde::logMessage(sprintf('Mnemo_Driver_sql::getByUID(): %s', $query),
                          __FILE__, __LINE__, PEAR_LOG_DEBUG);

        /* Execute the query. */
        $row = $this->_db->getRow($query, $values, DB_FETCHMODE_ASSOC);

        if (is_a($row, 'PEAR_Error')) {
            return $row;
        } elseif ($row === null) {
            return PEAR::raiseError(_("Not found"));
        }

        /* Decode and return the task. */
        $this->_notepad = $row['memo_owner'];
        return $this->_buildNote($row, $passphrase);
    }

    /**
     * Add a note to the backend storage.
     *
     * @param string $desc        The first line of the note.
     * @param string $body        The whole note body.
     * @param string $category    The category of the note.
     * @param string $uid         A Unique Identifier for the note.
     * @param string $passphrase  The passphrase to encrypt the note with.
     *
     * @return string  The unique ID of the new note.
     */
    function add($desc, $body, $category = '', $uid = null, $passphrase = null)
    {
        $noteId = md5(uniqid(mt_rand(), true));

        if ($passphrase) {
            $body = $this->encrypt($body, $passphrase);
            if (is_a($body, 'PEAR_Error')) {
                return $body;
            }
            Mnemo::storePassphrase($noteId, $passphrase);
        }

        if (is_null($uid)) {
            $uid = $this->generateUID();
        }

        $query = 'INSERT INTO ' . $this->_params['table'] .
                 ' (memo_owner, memo_id, memo_desc, memo_body, memo_category, memo_uid)' .
                 ' VALUES (?, ?, ?, ?, ?, ?)';
        $values = array($this->_notepad,
                        $noteId,
                        String::convertCharset($desc, NLS::getCharset(), $this->_params['charset']),
                        String::convertCharset($body, NLS::getCharset(), $this->_params['charset']),
                        String::convertCharset($category, NLS::getCharset(), $this->_params['charset']),
                        String::convertCharset($uid, NLS::getCharset(), $this->_params['charset']));

        /* Log the query at a DEBUG log level. */
        Horde::logMessage(sprintf('Mnemo_Driver_sql::add(): %s', $query),
                          __FILE__, __LINE__, PEAR_LOG_DEBUG);

        /* Attempt the insertion query. */
        $result = $this->_write_db->query($query, $values);

        /* Return an error immediately if the query failed. */
        if (is_a($result, 'PEAR_Error')) {
            Horde::logMessage($result, __FILE__, __LINE__, PEAR_LOG_ERR);
            return $result;
        }

        /* Log the creation of this item in the history log. */
        $history = &Horde_History::singleton();
        $history->log('mnemo:' . $this->_notepad . ':' . $uid, array('action' => 'add'), true);

        return $noteId;
    }

    /**
     * Modify an existing note.
     *
     * @param string $noteId      The note to modify.
     * @param string $desc        The description (long) of the note.
     * @param string $body        The description (long) of the note.
     * @param string $category    The category of the note.
     * @param string $passphrase  The passphrase to encrypt the note with.
     */
    function modify($noteId, $desc, $body, $category = null, $passphrase = null)
    {
        if ($passphrase) {
            $body = $this->encrypt($body, $passphrase);
            if (is_a($body, 'PEAR_Error')) {
                return $body;
            }
            Mnemo::storePassphrase($noteId, $passphrase);
        }

        $query  = 'UPDATE ' . $this->_params['table'] .
                  ' SET memo_desc = ?, memo_body = ?';
        $values = array(String::convertCharset($desc, NLS::getCharset(), $this->_params['charset']),
                        String::convertCharset($body, NLS::getCharset(), $this->_params['charset']));

        // Don't change the category if it isn't provided.
        if (!is_null($category)) {
            $query .= ', memo_category = ?';
            $values[] = String::convertCharset($category, NLS::getCharset(), $this->_params['charset']);
        }
        $query .= ' WHERE memo_owner = ? AND memo_id = ?';
        array_push($values, $this->_notepad, $noteId);

        /* Log the query at a DEBUG log level. */
        Horde::logMessage(sprintf('Mnemo_Driver_sql::modify(): %s', $query),
                          __FILE__, __LINE__, PEAR_LOG_DEBUG);

        /* Attempt the update query. */
        $result = $this->_write_db->query($query, $values);

        if (is_a($result, 'PEAR_Error')) {
            Horde::logMessage($result, __FILE__, __LINE__, PEAR_LOG_ERR);
            return $result;
        }

        /* Log the modification of this item in the history log. */
        $note = $this->get($noteId);
        if (!empty($note['uid'])) {
            $history = &Horde_History::singleton();
            $history->log('mnemo:' . $this->_notepad . ':' . $note['uid'], array('action' => 'modify'), true);
        }

        return true;
    }

    /**
     * Move a note to a new notepad.
     *
     * @param string $noteId      The note to move.
     * @param string $newNotepad  The new notepad.
     */
    function move($noteId, $newNotepad)
    {
        /* Get the note's details for use later. */
        $note = $this->get($noteId);

        $query = 'UPDATE ' . $this->_params['table'] .
                 ' SET memo_owner = ?' .
                 ' WHERE memo_owner = ? AND memo_id = ?';
        $values = array($newNotepad, $this->_notepad, $noteId);

        /* Log the query at a DEBUG log level. */
        Horde::logMessage(sprintf('Mnemo_Driver_sql::move(): %s', $query),
                          __FILE__, __LINE__, PEAR_LOG_DEBUG);

        /* Attempt the move query. */
        $result = $this->_write_db->query($query, $values);
        if (is_a($result, 'PEAR_Error')) {
            Horde::logMessage($result, __FILE__, __LINE__, PEAR_LOG_ERR);
            return $result;
        }

        /* Log the moving of this item in the history log. */
        if (!empty($note['uid'])) {
            $history = &Horde_History::singleton();
            $history->log('mnemo:' . $this->_notepad . ':' . $note['uid'], array('action' => 'delete'), true);
            $history->log('mnemo:' . $newNotepad . ':' . $note['uid'], array('action' => 'add'), true);
        }

        return true;
    }

    function delete($noteId)
    {
        /* Get the note's details for use later. */
        $note = $this->get($noteId);

        $query = 'DELETE FROM ' . $this->_params['table'] .
                 ' WHERE memo_owner = ? AND memo_id = ?';
        $values = array($this->_notepad, $noteId);

        /* Log the query at a DEBUG log level. */
        Horde::logMessage(sprintf('Mnemo_Driver_sql::delete(): %s', $query),
                          __FILE__, __LINE__, PEAR_LOG_DEBUG);

        /* Attempt the delete query. */
        $result = $this->_write_db->query($query, $values);

        if (is_a($result, 'PEAR_Error')) {
            Horde::logMessage($result, __FILE__, __LINE__, PEAR_LOG_ERR);
            return $result;
        }

        /* Log the deletion of this item in the history log. */
        if (!empty($note['uid'])) {
            $history = &Horde_History::singleton();
            $history->log('mnemo:' . $this->_notepad . ':' . $note['uid'], array('action' => 'delete'), true);
        }

        return true;
    }

    function deleteAll()
    {
        $query = 'DELETE FROM ' . $this->_params['table'] .
                 ' WHERE memo_owner = ?';
        $values = array($this->_notepad);

        /* Log the query at a DEBUG log level. */
        Horde::logMessage(sprintf('Mnemo_Driver_sql::deleteAll(): %s', $query),
                          __FILE__, __LINE__, PEAR_LOG_DEBUG);

        /* Attempt the delete query. */
        $result = $this->_write_db->query($query, $values);

        return is_a($result, 'PEAR_Error') ? $result : true;
    }

    /**
     * Retrieves all of the notes from $this->_notepad from the
     * database.
     *
     * @return mixed  True on success, PEAR_Error on failure.
     */
    function retrieve()
    {
        /* Build the SQL query. */
        $query = 'SELECT * FROM ' . $this->_params['table'] .
                 ' WHERE memo_owner = ?';
        $values = array($this->_notepad);

        /* Log the query at a DEBUG log level. */
        Horde::logMessage(sprintf('Mnemo_Driver_sql::retrieve(): %s', $query),
                          __FILE__, __LINE__, PEAR_LOG_DEBUG);

        /* Execute the query. */
        $result = $this->_db->query($query, $values);
        if (is_a($result, 'PEAR_Error')) {
            return $result;
        }

        /* Store the retrieved values in a fresh $memos list. */
        $this->_memos = array();
        while ($row = $result->fetchRow(DB_FETCHMODE_ASSOC)) {
            $this->_memos[$row['memo_id']] = $this->_buildNote($row);
        }
        $result->free();

        return true;
    }

    /**
     */
    function _buildNote($row, $passphrase = null)
    {
        /* Make sure notes always have a UID. */
        if (empty($row['memo_uid'])) {
            $row['memo_uid'] = $this->generateUID();

            $query = 'UPDATE ' . $this->_params['table'] .
                ' SET memo_uid = ?' .
                ' WHERE memo_owner = ? AND memo_id = ?';
            $values = array($row['memo_uid'], $row['memo_owner'], $row['memo_id']);

            /* Log the query at a DEBUG log level. */
            Horde::logMessage(sprintf('Mnemo_Driver_sql adding missing UID: %s', $query),
                              __FILE__, __LINE__, PEAR_LOG_DEBUG);
            $this->_write_db->query($query, $values);
        }

        /* Decrypt note if requested. */
        $encrypted = false;
        $body = String::convertCharset($row['memo_body'], $this->_params['charset']);
        if (strpos($body, '-----BEGIN PGP MESSAGE-----') === 0) {
            $encrypted = true;
            if (empty($passphrase)) {
                $passphrase = Mnemo::getPassphrase($row['memo_id']);
            }
            if (empty($passphrase)) {
                $body = PEAR::raiseError(_("This note has been encrypted."), MNEMO_ERR_NO_PASSPHRASE);
            } else {
                $body = $this->decrypt($body, $passphrase);
                if (is_a($body, 'PEAR_Error')) {
                    $body->code = MNEMO_ERR_DECRYPT;
                } else {
                    $body = $body->message;
                    Mnemo::storePassphrase($row['memo_id'], $passphrase);
                }
            }
        }

        /* Create a new task based on $row's values. */
        return array('memolist_id' => $row['memo_owner'],
                     'memo_id' => $row['memo_id'],
                     'uid' => String::convertCharset($row['memo_uid'], $this->_params['charset']),
                     'desc' => String::convertCharset($row['memo_desc'], $this->_params['charset']),
                     'body' => $body,
                     'category' => String::convertCharset($row['memo_category'], $this->_params['charset']),
                     'encrypted' => $encrypted);
    }

}
