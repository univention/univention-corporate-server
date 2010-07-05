<?php
/**
 * Generic SQL based SyncML Backend.
 *
 * This can be used as a starting point for a custom backend implementation.
 *
 * $Horde: framework/SyncML/SyncML/Backend/Sql.php,v 1.6.2.7 2009-04-05 20:24:43 jan Exp $
 *
 * Copyright 2006-2009 The Horde Project (http://www.horde.org/)
 *
 * See the enclosed file COPYING for license information (LGPL). If you
 * did not receive this file, see http://www.fsf.org/copyleft/lgpl.html.
 *
 * @author  Karsten Fourmont <karsten@horde.org>
 * @package SyncML
 */

require_once 'MDB2.php';

/*
 * The SQL Database must contain five tables as created by the following SQL
 * script:
 *
 * CREATE DATABASE syncml;
 *
 * USE syncml;
 *
 * CREATE TABLE syncml_data(
 *     syncml_id            VARCHAR(255),
 *     syncml_db            VARCHAR(255),
 *     syncml_uid           VARCHAR(255),
 *     syncml_data          TEXT,
 *     syncml_contenttype   VARCHAR(255),
 *     syncml_created_ts    INTEGER,
 *     syncml_modified_ts   INTEGER
 * );
 *
 * CREATE TABLE syncml_map(
 *     syncml_syncpartner VARCHAR(255),
 *     syncml_db          VARCHAR(255),
 *     syncml_uid         VARCHAR(255),
 *     syncml_cuid        VARCHAR(255),
 *     syncml_suid        VARCHAR(255),
 *     syncml_timestamp   INTEGER
 * );
 *
 * CREATE INDEX syncml_syncpartner_idx ON syncml_map (syncml_syncpartner);
 * CREATE INDEX syncml_db_idx ON syncml_map (syncml_db);
 * CREATE INDEX syncml_uid_idx ON syncml_map (syncml_uid);
 * CREATE INDEX syncml_cuid_idx ON syncml_map (syncml_cuid);
 * CREATE INDEX syncml_suid_idx ON syncml_map (syncml_suid);
 *
 * CREATE TABLE syncml_anchors(
 *     syncml_syncpartner   VARCHAR(255),
 *     syncml_db            VARCHAR(255),
 *     syncml_uid           VARCHAR(255),
 *     syncml_clientanchor  VARCHAR(255),
 *     syncml_serveranchor  VARCHAR(255)
 * );
 *
 * CREATE TABLE syncml_suidlist(
 *     syncml_syncpartner    VARCHAR(255),
 *     syncml_db             VARCHAR(255),
 *     syncml_uid            VARCHAR(255),
 *     syncml_suid           VARCHAR(255)
 * );
 *
 * CREATE TABLE syncml_uids(
 *     syncml_uid      VARCHAR(255),
 *     syncml_password VARCHAR(255)
 * );
 */

/**
 */
class SyncML_Backend_Sql extends SyncML_Backend {

    /**
     * A PEAR MDB2 instance.
     *
     * @var MDB2
     */
    var $_db;

    /**
     * Constructor.
     *
     * @param array $params  A hash with parameters. In addition to those
     *                       supported by the SyncML_Backend class one more
     *                       parameter is required for the database connection:
     *                       'dsn' => connection DSN.
     */
    function SyncML_Backend_Sql($params)
    {
        parent::SyncML_Backend($params);

        $this ->_db = &MDB2::connect($params['dsn']);
        if (is_a($this->_db, 'PEAR_Error')) {
            $this->logMessage($this->_db,
                              __FILE__, __LINE__, PEAR_LOG_ERR);
        }
    }

    /**
     * Returns whether a database URI is valid to be synced with this backend.
     *
     * @param string $databaseURI  URI of a database. Like calendar, tasks,
     *                             contacts or notes. May include optional
     *                             parameters:
     *                             tasks?options=ignorecompleted.
     *
     * @return boolean  True if a valid URI.
     */
    function isValidDatabaseURI($databaseURI)
    {
        $database = $this->_normalize($databaseURI);

        switch($database) {
        case 'tasks';
        case 'calendar';
        case 'notes';
        case 'contacts';
        case 'events':
        case 'memo':
            return true;

        default:
            $this->logMessage('Invalid database ' . $database
                              . '. Try tasks, calendar, notes or contacts.',
                              __FILE__, __LINE__, PEAR_LOG_ERR);
            return false;
        }
    }

    /**
     * Returns entries that have been modified in the server database.
     *
     * @param string $databaseURI  URI of Database to sync. Like calendar,
     *                             tasks, contacts or notes. May include
     *                             optional parameters:
     *                             tasks?options=ignorecompleted.
     * @param integer $from_ts     Start timestamp.
     * @param integer $to_ts       Exclusive end timestamp. Not yet
     *                             implemented.
     * @param array &$adds         Output array: hash of adds suid => 0
     * @param array &$mods         Output array: hash of modifications
     *                             suid => cuid
     * @param array &$dels         Output array: hash of deletions suid => cuid
     *
     * @return mixed  True on success or a PEAR_Error object.
     */
    function getServerChanges($databaseURI, $from_ts, $to_ts, &$adds, &$mods,
                              &$dels)
    {
        $database = $this->_normalize($databaseURI);
        $adds = $mods = $dels = array();

        // Handle additions:
        $data = $this->_db->queryAll(
            'SELECT syncml_id, syncml_created_ts from syncml_data '
            . 'WHERE syncml_db = '
            . $this->_db->quote($database, 'text')
            . ' AND syncml_uid = '
            . $this->_db->quote($this->_user, 'text')
            . ' AND syncml_created_ts >= '
            . $this->_db->quote($from_ts, 'integer')
            . ' AND syncml_created_ts < '
            . $this->_db->quote($to_ts, 'integer'));
        if ($this->_checkForError($data)) {
            return $data;
        }

        foreach ($data as $d) {
            $suid = $d[0];
            $suid_ts = $d[1];
            $sync_ts = $this->_getChangeTS($databaseURI, $suid);
            if ($sync_ts && $sync_ts >= $suid_ts) {
                // Change was done by us upon request of client, don't mirror
                // that back to the client.
                $this->logMessage("Added to server from client: $suid ignored",
                                  __FILE__, __LINE__, PEAR_LOG_DEBUG);
                continue;
            }
            $adds[$suid] = 0;
        }

        // Only compile changes on delta sync:
        if ($from_ts > 0) {
            // Handle replaces. We might get IDs that are already in the adds
            // array but that's ok: The calling code takes care to ignore
            // these.
            $data = $this->_db->queryAll(
                'SELECT syncml_id, syncml_modified_ts from syncml_data '
                .'WHERE syncml_db = '
                . $this->_db->quote($database, 'text')
                . ' AND syncml_uid = '
                . $this->_db->quote($this->_user, 'text')
                . ' AND syncml_modified_ts >= '
                . $this->_db->quote($from_ts, 'integer')
                . ' AND syncml_modified_ts < '
                . $this->_db->quote($to_ts, 'integer'));
            if ($this->_checkForError($data)) {
                return $data;
            }

            foreach($data as $d) {
                // Only the server needs to check the change timestamp do
                // identify client-sent changes.
                if ($this->_backendMode == SYNCML_BACKENDMODE_SERVER) {
                    $suid = $d[0];
                    $suid_ts = $d[1];
                    $sync_ts = $this->_getChangeTS($databaseURI, $suid);
                    if ($sync_ts && $sync_ts >= $suid_ts) {
                        // Change was done by us upon request of client, don't
                        // mirror that back to the client.
                        $this->logMessage(
                            "Changed on server after sent from client: $suid ignored",
                            __FILE__, __LINE__, PEAR_LOG_DEBUG);
                        continue;
                    }
                    $mods[$suid] = $this->_getCuid($databaseURI, $suid);
                } else {
                    $mods[$d[0]] = $d[0];
                }
            }
        }

        // Handle deletions:
        // We assume stupid a backend datastore (syncml_data) where deleted
        // items are simply "gone" from the datastore. So we need to do our
        // own bookkeeping to identify entries that have been deleted since
        // the last sync run.
        // This is done by the _trackDeless() helper function: we feed it with
        // a current list of all suids and get the ones missing (and thus
        // deleted) in return.
        $data = $this->_db->queryCol(
            'SELECT syncml_id from syncml_data WHERE syncml_db = '
            . $this->_db->quote($database, 'text')
            . ' AND syncml_uid = '
            . $this->_db->quote($this->_user, 'text'));
        if ($this->_checkForError($data)) {
            return $data;
        }

        // Get deleted items and store current items:
        // Only use the deleted information on delta sync. On initial slowsync
        // we just need to call _trackDeletes() once to init the list.
        $data = $this->_trackDeletes($databaseURI, $data);
        if ($this->_checkForError($data)) {
            return $data;
        }

        if ($from_ts > 0) {
            foreach($data as $suid) {
                // Only the server needs to handle the cuid suid map:
                if ($this->_backendMode == SYNCML_BACKENDMODE_SERVER) {
                    $dels[$suid] = $this->_getCuid($databaseURI, $suid);
                } else {
                    $dels[$suid] = $suid;
                }
            }
        }
    }

    /**
     * Retrieves an entry from the backend.
     *
     * @param string $databaseURI  URI of Database to sync. Like calendar,
     *                             tasks, contacts or notes. May include
     *                             optional parameters:
     *                             tasks?options=ignorecompleted.
     * @param string $suid         Server unique id of the entry: for horde
     *                             this is the guid.
     * @param string $contentType  Content-Type: the MIME type in which the
     *                             function should return the data.
     *
     * @return mixed  A string with the data entry or a PEAR_Error object.
     */
    function retrieveEntry($databaseURI, $suid, $contentType)
    {
        $database = $this->_normalize($databaseURI);

        return $this->_db->queryOne(
            'SELECT syncml_data from syncml_data '
            . 'WHERE syncml_db = '
            . $this->_db->quote($database, 'text')
            . ' AND syncml_uid = '
            . $this->_db->quote($this->_user, 'text')
            . ' AND syncml_id = '
            . $this->_db->quote($suid, 'text'));
    }

    /**
     * Adds an entry into the server database.
     *
     * @param string $databaseURI  URI of Database to sync. Like calendar,
     *                             tasks, contacts or notes. May include
     *                             optional parameters:
     *                             tasks?options=ignorecompleted.
     * @param string $content      The actual data.
     * @param string $contentType  MIME type of the content.
     * @param string $cuid         Client ID of this entry.
     *
     * @return array  PEAR_Error or suid (Horde guid) of new entry
     */
    function addEntry($databaseURI, $content, $contentType, $cuid = null)
    {
        $database = $this->_normalize($databaseURI);

        // Generate an id (suid). It's also possible to use a database
        // generated primary key here.
        $suid = $this->_generateID();
        $created_ts = $this->getCurrentTimeStamp();

        $r = $this->_db->exec(
            'INSERT INTO syncml_data (syncml_id, syncml_db, syncml_uid, '
            . 'syncml_data, syncml_contenttype,  syncml_created_ts, '
            . 'syncml_modified_ts) VALUES ('
            . $this->_db->quote($suid, 'text') . ','
            . $this->_db->quote($database, 'text') . ','
            . $this->_db->quote($this->_user, 'text') . ','
            . $this->_db->quote($content, 'text') . ','
            . $this->_db->quote($contentType, 'text') . ','
            . $this->_db->quote($created_ts, 'integer') . ','
            . $this->_db->quote($created_ts, 'integer')
            . ')');
        if ($this->_checkForError($r)) {
            return $r;
        }

        // Only the server needs to handle the cuid suid map:
        if ($this->_backendMode == SYNCML_BACKENDMODE_SERVER) {
           $this->createUidMap($databaseURI, $cuid, $suid, $created_ts);
        }
    }

    /**
     * Replaces an entry in the server database.
     *
     * @param string $databaseURI  URI of Database to sync. Like calendar,
     *                             tasks, contacts or notes. May include
     *                             optional parameters:
     *                             tasks?options=ignorecompleted.
     * @param string $content      The actual data.
     * @param string $contentType  MIME type of the content.
     * @param string $cuid         Client ID of this entry.
     *
     * @return string  PEAR_Error or server ID (Horde GUID) of modified entry.
     */
    function replaceEntry($databaseURI, $content, $contentType, $cuid)
    {
        $database = $this->_normalize($databaseURI);

        if ($this->_backendMode == SYNCML_BACKENDMODE_SERVER) {
            $suid = $this->_getSuid($databaseURI, $cuid);
        } else {
            $suid = $cuid;
        }

        if ($suid) {
            // Entry exists: replace current one.
            $modified_ts = $this->getCurrentTimeStamp();
            $r = $this->_db->exec(
                'UPDATE syncml_data '
                . 'SET syncml_modified_ts = '
                . $this->_db->quote($modified_ts, 'integer')
                . ', syncml_data = '
                . $this->_db->quote($content, 'text')
                . ', syncml_contenttype = '
                . $this->_db->quote($contentType, 'text')
                . 'WHERE syncml_db = '
                . $this->_db->quote($database, 'text')
                . ' AND syncml_uid = '
                . $this->_db->quote($this->_user, 'text')
                . ' AND syncml_id = '
                . $this->_db->quote($suid, 'text'));
            if ($this->_checkForError($r)) {
                return $r;
            }

            // Only the server needs to keep the map:
            if ($this->_backendMode == SYNCML_BACKENDMODE_SERVER) {
                $this->createUidMap($databaseURI, $cuid, $suid, $modified_ts);
            }
        } else {
            return PEAR::raiseError("No map entry found for client id $cuid replacing on server");
        }

        return $suid;
    }

    /**
     * Deletes an entry from the server database.
     *
     * @param string $databaseURI  URI of Database to sync. Like calendar,
     *                             tasks, contacts or notes. May include
     *                             optional parameters:
     *                             tasks?options=ignorecompleted.
     * @param string $cuid         Client ID of the entry.
     *
     * @return boolean  True on success or false on failed (item not found).
     */
    function deleteEntry($databaseURI, $cuid)
    {
        $database = $this->_normalize($databaseURI);

        // Find ID for this entry:
        if ($this->_backendMode == SYNCML_BACKENDMODE_SERVER) {
            $suid = $this->_getSuid($databaseURI, $cuid);
        } else {
            $suid = $cuid;
        }

        if (!is_a($suid, 'PEAR_Error')) {
            // A clever backend datastore would store some information about a
            // deletion so this information can be extracted from the history.
            // However we do a "stupid" datastore here where deleted items are
            // simply gone. This allows us to illustrate the _trackDeletes()
            // bookkeeping mechanism.
            $r = $this->_db->queryOne(
                'DELETE FROM syncml_data '
                . ' WHERE syncml_db = '
                . $this->_db->quote($database, 'text')
                . ' AND syncml_uid = '
                . $this->_db->quote($this->_user, 'text')
                . ' AND syncml_id = '
                . $this->_db->quote($suid, 'text'));
            if ($this->_checkForError($r)) {
                return $r;
            }

            // Deleted bookkeeping is required for server and client, but not
            // for test mode:
            if ($this->_backendMode != SYNCML_BACKENDMODE_TEST) {
                $this->_removeFromSuidList($databaseURI, $suid);
            }

            // @todo: delete from map!
        } else {
            return false;
        }

        if (is_a($r, 'PEAR_Error')) {
            return false;
        }

        return true;
    }

    /**
     * Authenticates the user at the backend.
     *
     * @param string $username    A user name.
     * @param string $password    A password.
     *
     * @return boolean|string  The user name if authentication succeeded, false
     *                         otherwise.
     */
    function _checkAuthentication($username, $password)
    {
            // Empty passwords result in errors for some authentication
            // backends, don't call the backend in this case.
            if ($pwd === '') {
                return false;
            }
            $r = $this->_db->queryOne(
                'SELECT syncml_uid FROM syncml_uids'
                . ' WHERE syncml_uid = '
                . $this->_db->quote($username, 'text')
                . ' AND syncml_password = '
                . $this->_db->quote($pwd, 'text'));
            $this->_checkForError($r);

            if ($r === $username) {
                return $username;
            }
            return false;
    }

    /**
     * Sets a user as being authenticated at the backend.
     *
     * @abstract
     *
     * @param string $username    A user name.
     * @param string $credData    Authentication data provided by <Cred><Data>
     *                            in the <SyncHdr>.
     *
     * @return string  The user name.
     */
    function setAuthenticated($username, $credData)
    {
        return $username;
    }

    /**
     * Stores Sync anchors after a successful synchronization to allow two-way
     * synchronization next time.
     *
     * The backend has to store the parameters in its persistence engine
     * where user, syncDeviceID and database are the keys while client and
     * server anchor ar the payload. See readSyncAnchors() for retrieval.
     *
     * @param string $databaseURI       URI of database to sync. Like calendar,
     *                                  tasks, contacts or notes. May include
     *                                  optional parameters:
     *                                  tasks?options=ignorecompleted.
     * @param string $clientAnchorNext  The client anchor as sent by the
     *                                  client.
     * @param string $serverAnchorNext  The anchor as used internally by the
     *                                  server.
     */
    function writeSyncAnchors($databaseURI, $clientAnchorNext,
                              $serverAnchorNext)
    {
        $database = $this->_normalize($databaseURI);

        // Check if entry exists. If not insert, otherwise update.
        if (!$this->readSyncAnchors($databaseURI)) {
            $r = $this->_db->exec(
                'INSERT INTO syncml_anchors (syncml_syncpartner, '
                . 'syncml_db,syncml_uid, syncml_clientanchor, '
                . 'syncml_serveranchor) VALUES ('
                . $this->_db->quote($this->_syncDeviceID, 'text') . ', '
                . $this->_db->quote($database, 'text') . ', '
                . $this->_db->quote($this->_user, 'text') . ', '
                . $this->_db->quote($clientAnchorNext, 'text') . ', '
                . $this->_db->quote($serverAnchorNext, 'text')
                . ')');
        } else {
            $r = $this->_db->exec(
                'UPDATE syncml_anchors '
                . ' SET syncml_clientanchor = '
                . $this->_db->quote($clientAnchorNext, 'text')
                . ', syncml_serveranchor = '
                . $this->_db->quote($serverAnchorNext, 'text')
                . ' WHERE syncml_syncpartner = '
                . $this->_db->quote($this->_syncDeviceID, 'text')
                . ' AND syncml_db = '
                . $this->_db->quote($database, 'text')
                . ' AND syncml_uid = '
                . $this->_db->quote($this->_user, 'text'));
        }
        if ($this->_checkForError($r)) {
            return $r;
        }

        return true;
    }

    /**
     * Reads the previously written sync anchors from the database.
     *
     * @param string $databaseURI  URI of database to sync. Like calendar,
     *                             tasks, contacts or notes. May include
     *                             optional parameters:
     *                             tasks?options=ignorecompleted.
     *
     * @return mixed  Two-element array with client anchor and server anchor as
     *                stored in previous writeSyncAnchor() calls. False if no
     *                data found.
     */
    function readSyncAnchors($databaseURI)
    {
        $database = $this->_normalize($databaseURI);

        $r = $this->_db->queryRow(
            'SELECT syncml_clientanchor, syncml_serveranchor '
            . 'FROM syncml_anchors WHERE syncml_syncpartner = '
            . $this->_db->quote($this->_syncDeviceID, 'text')
            . ' AND syncml_db = '
            . $this->_db->quote($database, 'text')
            . ' AND syncml_uid = '
            . $this->_db->quote($this->_user, 'text'));
        $this->_checkForError($r);

        if (!is_array($r)) {
            return false;
        }

        return array($r[0], $r[1]);
    }

    /**
     * Creates a map entry to map between server and client IDs.
     *
     * If an entry already exists, it is overwritten.
     *
     * @param string $databaseURI  URI of database to sync. Like calendar,
     *                             tasks, contacts or notes. May include
     *                             optional parameters:
     *                             tasks?options=ignorecompleted.
     * @param string $cuid         Client ID of the entry.
     * @param string $suid         Server ID of the entry.
     * @param integer $timestamp   Optional timestamp. This can be used to
     *                             'tag' changes made in the backend during the
     *                             sync process. This allows to identify these,
     *                             and ensure that these changes are not
     *                             replicated back to the client (and thus
     *                             duplicated). See key concept "Changes and
     *                             timestamps".
     */
    function createUidMap($databaseURI, $cuid, $suid, $timestamp = 0)
    {
        $database = $this->_normalize($databaseURI);

        // Check if entry exists. If not insert, otherwise update.
        if (!$this->_getSuid($databaseURI, $cuid)) {
            $r = $this->_db->exec(
                'INSERT INTO syncml_map (syncml_syncpartner, '
                . 'syncml_db, syncml_uid, syncml_cuid, syncml_suid, '
                . 'syncml_timestamp) VALUES ('
                . $this->_db->quote($this->_syncDeviceID, 'text') . ', '
                . $this->_db->quote($database, 'text') . ', '
                . $this->_db->quote($this->_user, 'text') . ', '
                . $this->_db->quote($cuid, 'text') . ', '
                . $this->_db->quote($suid, 'text') . ', '
                . $this->_db->quote($timestamp, 'integer')
                . ')');
        } else {
            $r = $this->_db->exec(
                'UPDATE syncml_map SET syncml_suid = '
                . $this->_db->quote($suid, 'text')
                . ', syncml_timestamp = '
                . $this->_db->quote($timestamp, 'text')
                . ' WHERE syncml_syncpartner = '
                . $this->_db->quote($this->_syncDeviceID, 'text')
                . ' AND syncml_db = '
                . $this->_db->quote($database, 'text')
                . ' AND syncml_uid = '
                . $this->_db->quote($this->_user, 'text')
                . ' AND syncml_cuid = '
                . $this->_db->quote($cuid, 'text'));
        }
        if ($this->_checkForError($r)) {
            return $r;
        }

        return true;
    }

    /**
     * Retrieves the Server ID for a given Client ID from the map.
     *
     * @param string $databaseURI  URI of database to sync. Like calendar,
     *                             tasks, contacts or notes. May include
     *                             optional parameters:
     *                             tasks?options=ignorecompleted.
     * @param string $cuid         The client ID.
     *
     * @return mixed  The server ID string or false if no entry is found.
     */
    function _getSuid($databaseURI, $cuid)
    {
        $database = $this->_normalize($databaseURI);

        $r = $this->_db->queryOne(
            'SELECT syncml_suid FROM syncml_map '
            . ' WHERE syncml_syncpartner = '
            . $this->_db->quote($this->_syncDeviceID, 'text')
            . ' AND syncml_db = '
            . $this->_db->quote($database, 'text')
            . ' AND syncml_uid = '
            . $this->_db->quote($this->_user, 'text')
            . ' AND syncml_cuid = '
            . $this->_db->quote($cuid, 'text'));
        $this->_checkForError($r);

        if (!empty($r)) {
            return $r;
        }

        return false;
    }

    /**
     * Retrieves the Client ID for a given Server ID from the map.
     *
     * @param string $databaseURI  URI of database to sync. Like calendar,
     *                             tasks, contacts or notes. May include
     *                             optional parameters:
     *                             tasks?options=ignorecompleted.
     * @param string $suid         The server ID.
     *
     * @return mixed  The client ID string or false if no entry is found.
     */
    function _getCuid($databaseURI, $suid)
    {
        $database = $this->_normalize($databaseURI);

        $r = $this->_db->queryOne(
            'SELECT syncml_cuid FROM syncml_map '
            . ' WHERE syncml_syncpartner = '
            . $this->_db->quote($this->_syncDeviceID, 'text')
            . ' AND syncml_db = '
            . $this->_db->quote($database, 'text')
            . ' AND syncml_uid = '
            . $this->_db->quote($this->_user, 'text')
            . ' AND syncml_suid = '
            . $this->_db->quote($suid, 'text'));

        $this->_checkForError($r);

        if (!empty($r)) {
            return $r;
        }

        return false;
    }

    /**
     * Returns a timestamp stored in the map for a given Server ID.
     *
     * The timestamp is the timestamp of the last change to this server ID
     * that was done inside a sync session (as a result of a change received
     * by the server). It's important to distinguish changes in the backend a)
     * made by the user during normal operation and b) changes made by SyncML
     * to reflect client updates.  When the server is sending its changes it
     * is only allowed to send type a). However the history feature in the
     * backend my not know if a change is of type a) or type b). So the
     * timestamp is used to differentiate between the two.
     *
     * @param string $databaseURI  URI of database to sync. Like calendar,
     *                             tasks, contacts or notes. May include
     *                             optional parameters:
     *                             tasks?options=ignorecompleted.
     * @param string $suid         The server ID.
     *
     * @return mixed  The previously stored timestamp or false if no entry is
     *                found.
     */
    function _getChangeTS($databaseURI, $suid)
    {
        $database = $this->_normalize($databaseURI);

        $r = $this->_db->queryOne(
            'SELECT syncml_timestamp FROM syncml_map '
            . ' WHERE syncml_syncpartner = '
            . $this->_db->quote($this->_syncDeviceID, 'text')
            . ' AND syncml_db = '
            . $this->_db->quote($database, 'text')
            . ' AND syncml_uid = '
            . $this->_db->quote($this->_user, 'text')
            . ' AND syncml_suid = '
            . $this->_db->quote($suid, 'text'));
        $this->_checkForError($r);

        if (!empty($r)) {
            return $r;
        }

        return false;
    }

    /**
     * Erases all mapping entries for one combination of user, device ID.
     *
     * This is used during SlowSync so that we really sync everything properly
     * and no old mapping entries remain.
     *
     * @param string $databaseURI  URI of database to sync. Like calendar,
     *                             tasks, contacts or notes. May include
     *                             optional parameters:
     *                             tasks?options=ignorecompleted.
     */
    function eraseMap($databaseURI)
    {
        $database = $this->_normalize($databaseURI);

        $r = $this->_db->exec(
            'DELETE FROM syncml_map '
            . ' WHERE syncml_syncpartner = '
            . $this->_db->quote($this->_syncDeviceID, 'text')
            . ' AND syncml_db = '
            . $this->_db->quote($database, 'text')
            . ' AND syncml_uid = '
            . $this->_db->quote($this->_user, 'text'));
        if ($this->_checkForError($r)) {
            return $r;
        }

        $r = $this->_db->exec(
            'DELETE FROM syncml_suidlist '
            . ' WHERE syncml_syncpartner = '
            . $this->_db->quote($this->_syncDeviceID, 'text')
            . ' AND syncml_db = '
            . $this->_db->quote($database, 'text')
            . ' AND syncml_uid = '
            . $this->_db->quote($this->_user, 'text'));
        if ($this->_checkForError($r)) {
            return $r;
        }

        return true;
    }

    /**
     * Cleanup function called after all message processing is finished.
     *
     * Allows for things like closing databases or flushing logs.  When
     * running in test mode, tearDown() must be called rather than close.
     */
    function close()
    {
        parent::close();
        $this->_db->disconnect();
    }

    /**
     * Generates a unique ID used as suid
     *
     * @return string  A unique ID.
     */
    function _generateID()
    {
        return date('YmdHis') . '.'
            . substr(str_pad(base_convert(microtime(), 10, 36),
                             16,
                             uniqid(mt_rand()),
                             STR_PAD_LEFT),
                     -16)
            . '@'
            . (!empty($_SERVER['SERVER_NAME'])
               ? $_SERVER['SERVER_NAME']
               : 'localhost');
    }

    /**
     * Checks if the parameter is a PEAR_Error object and if so logs the
     * error.
     *
     * @param mixed $o  An object or value to check.
     *
     * @return mixed  The error object if an error has been passed or false if
     *                no error has been passed.
     */
    function _checkForError($o)
    {
        if (is_a($o, 'PEAR_Error')) {
            $this->logMessage($o);
            return $o;
        }
        return false;
    }

    /**
     * Returns a list of item IDs that have been deleted since the last sync
     * run and stores a complete list of IDs for next sync run.
     *
     * Some backend datastores don't keep information about deleted entries.
     * So we have to create a workaround that finds out what entries have been
     * deleted since the last sync run. This method provides this
     * functionality: it is called with a list of all IDs currently in the
     * database. It then compares this list with its own previously stored
     * list of IDs to identify those missing (and thus deleted). The passed
     * list is then stored for the next invocation.
     *
     * @param string $databaseURI  URI of database to sync. Like calendar,
     *                             tasks, contacts or notes. May include
     *                             optional parameters:
     *                             tasks?options=ignorecompleted.
     * @param array $currentSuids  Array of all SUIDs (primary keys) currently
     *                             in the server datastore.
     *
     * @return array  Array of all entries that have been deleted since the
     *                last call.
     */
    function _trackDeletes($databaseURI, $currentSuids)
    {
        $database = $this->_normalize($databaseURI);
        if (!is_array($currentSuids)) {
            $currentSuids = array();
        }

        $this->logMessage('_trackDeletes() with ' . count($currentSuids)
                          . ' current ids',
                          __FILE__, __LINE__, PEAR_LOG_DEBUG);

        $r = $this->_db->queryCol(
            'SELECT syncml_suid FROM syncml_suidlist '
            . ' WHERE syncml_syncpartner = '
            . $this->_db->quote($this->_syncDeviceID, 'text')
            . ' AND syncml_db = '
            . $this->_db->quote($database, 'text')
            . ' AND syncml_uid = '
            . $this->_db->quote($this->_user, 'text'));
        if ($this->_checkForError($r)) {
            return $r;
        }

        $this->logMessage('_trackDeletes() found ' . count($r)
                          . ' items in prevlist',
                          __FILE__, __LINE__, PEAR_LOG_DEBUG);

        // Convert to hash with suid as key.
        if (is_array($r)) {
            $prevSuids = array_flip($r);
        } else {
            $prevSuids = array();
        }

        foreach ($currentSuids as $suid) {
            if (isset($prevSuids[$suid])) {
                // Entry is there now and in $prevSuids. Unset in $prevSuids
                // array so we end up with only those in $prevSuids that are
                // no longer there now.
                unset($prevSuids[$suid]);
            } else {
                // Entry is there now but not in $prevSuids. New entry, store
                // in syncml_suidlist
                $r = $this->_db->exec(
                    'INSERT INTO syncml_suidlist '
                    . ' (syncml_syncpartner, syncml_db, syncml_uid, '
                    . 'syncml_suid) VALUES ('
                    . $this->_db->quote($this->_syncDeviceID, 'text') . ', '
                    . $this->_db->quote($database, 'text') . ', '
                    . $this->_db->quote($this->_user, 'text') . ', '
                    . $this->_db->quote($suid, 'text')
                    . ')');
                if ($this->_checkForError($r)) {
                    return $r;
                }
            }
        }

        // $prevSuids now contains the deleted suids. Remove those from
        // syncml_suidlist so we have a current list of all existing suids.
        foreach ($prevSuids as $suid => $cuid) {
            $r = $this->_removeFromSuidList($databaseURI, $suid);
        }

        $this->logMessage('_trackDeletes() with ' . count($prevSuids)
                          . ' deleted items',
                          __FILE__, __LINE__, PEAR_LOG_DEBUG);

        return array_keys($prevSuids);
    }

    /**
     * Removes a suid from the suidlist.
     *
     * Called by _trackDeletes() when updating the suidlist and deleteEntry()
     * when removing an entry due to a client request.
     *
     * @param string $databaseURI  URI of database to sync. Like calendar,
     *                             tasks, contacts or notes. May include
     *                             optional parameters:
     *                             tasks?options=ignorecompleted.
     * @param array $suid          The suid to remove from the list.
     */
    function _removeFromSuidList($databaseURI, $suid)
    {
        $database = $this->_normalize($databaseURI);

        $this->logMessage('_removeFromSuidList(): item ' . $suid,
                          __FILE__, __LINE__, PEAR_LOG_DEBUG);
        $r = $this->_db->queryCol(
            'DELETE FROM syncml_suidlist '
            . 'WHERE syncml_syncpartner = '
            . $this->_db->quote($this->_syncDeviceID, 'text')
            . ' AND syncml_db = '
            . $this->_db->quote($database, 'text')
            . ' AND syncml_uid = '
            . $this->_db->quote($this->_user, 'text')
            . ' AND syncml_suid = '
            . $this->_db->quote($suid, 'text'));
        if ($this->_checkForError($r)) {
            return $r;
        }

        $this->logMessage('_removeFromSuidList(): result ' . implode('!', $r),
                          __FILE__, __LINE__, PEAR_LOG_DEBUG);

        return true;
    }

    /**
     * Creates a clean test environment in the backend.
     *
     * Ensures there's a user with the given credentials and an empty data
     * store.
     *
     * @param string $user This user accout has to be created in the backend.
     * @param string $pwd  The password for user $user.
     */
    function testSetup($user, $pwd)
    {
        $this->_user = $user;
        $this->_cleanUser($user);
        $this->_backend->_user = $user;

        $r = $this->_db->exec(
            'INSERT INTO syncml_uids (syncml_uid, syncml_password)'
            . ' VALUES ('
            . $this->_db->quote($user, 'text') . ', '
            . $this->_db->quote($pwd, 'text') . ')');
        $this->_checkForError($r);
    }

    /**
     * Prepares the test start.
     *
     * @param string $user This user accout has to be created in the backend.
     */
    function testStart($user)
    {
        $this->_user = $user;
        $this->_backend->_user = $user;
    }

    /**
     * Tears down the test environment after the test is run.
     *
     * Should remove the testuser created during testSetup and all its data.
     */
    function testTearDown()
    {
        $this->_cleanUser($this->_user);
        $this->_db->disconnect();
    }

    /* Database access functions. The following methods are not part of the
     * backend API. They are here to illustrate how a backend application
     * (like a web calendar) has to modify the data with respect to the
     * history. There are three functions:
     * addEntry_backend(), replaceEntry_backend(), deleteEntry_backend().
     * They are very similar to the API methods above, but don't use cuids or
     * syncDeviceIDs as these are only relevant for syncing. */

    /**
     * Adds an entry into the server database.
     *
     * @param string $user         The username to use. Not strictly necessery
     *                             to store this, but it helps for the test
     *                             environment to clean up all entries for a
     *                             test user.
     * @param string $databaseURI  URI of Database to sync. Like calendar,
     *                             tasks, contacts or notes. May include
     *                             optional parameters:
     *                             tasks?options=ignorecompleted.
     * @param string $content      The actual data.
     * @param string $contentType  MIME type of the content.
     *
     * @return array  PEAR_Error or suid of new entry.
     */
    function addEntry_backend($user, $databaseURI, $content, $contentType)
    {
        $database = $this->_normalize($databaseURI);

        // Generate an id (suid). It's also possible to use a database
        // generated primary key here. */
        $suid = $this->_generateID();

        $created_ts = $this->getCurrentTimeStamp();
        $r = $this->_db->exec(
            'INSERT INTO syncml_data (syncml_id, syncml_db, syncml_uid, '
            . 'syncml_data, syncml_contenttype, syncml_created_ts, '
            . 'syncml_modified_ts) VALUES ('
            . $this->_db->quote($suid, 'text') . ', '
            . $this->_db->quote($database, 'text') . ', '
            . $this->_db->quote($user, 'text') . ', '
            . $this->_db->quote($content, 'text') . ', '
            . $this->_db->quote($contentType, 'text') . ', '
            . $this->_db->quote($created_ts, 'integer') . ', '
            . $this->_db->quote($created_ts, 'integer')
            . ')');
        if ($this->_checkForError($r)) {
            return $r;
        }

        return $suid;
    }

    /**
     * Replaces an entry in the server database.
     *
     * @param string $user         The username to use. Not strictly necessery
     *                             to store this but, it helps for the test
     *                             environment to clean up all entries for a
     *                             test user.
     * @param string $databaseURI  URI of Database to sync. Like calendar,
     *                             tasks, contacts or notes. May include
     *                             optional parameters:
     *                             tasks?options=ignorecompleted.
     * @param string $content      The actual data.
     * @param string $contentType  MIME type of the content.
     * @param string $suid         Server ID of this entry.
     *
     * @return string  PEAR_Error or suid of modified entry.
     */
    function replaceEntry_backend($user, $databaseURI, $content, $contentType,
                                  $suid)
    {
        $database = $this->_normalize($databaseURI);
        $modified_ts = $this->getCurrentTimeStamp();

        // Entry exists: replace current one.
        $r = $this->_db->exec(
            'UPDATE syncml_data '
            . 'SET syncml_modified_ts = '
            . $this->_db->quote($modified_ts, 'integer')
            . ',syncml_data = '
            . $this->_db->quote($content, 'text')
            . ',syncml_contenttype = '
            . $this->_db->quote($contentType, 'text')
            . 'WHERE syncml_db = '
            . $this->_db->quote($database, 'text')
            . ' AND syncml_uid = '
            . $this->_db->quote($user, 'text')
            . ' AND syncml_id = '
            . $this->_db->quote($suid, 'text'));
        if ($this->_checkForError($r)) {
            return $r;
        }

        return $suid;
    }

    /**
     * Deletes an entry from the server database.
     *
     * @param string $user         The username to use. Not strictly necessery
     *                             to store this, but it helps for the test
     *                             environment to clean up all entries for a
     *                             test user.
     * @param string $databaseURI  URI of Database to sync. Like calendar,
     *                             tasks, contacts or notes. May include
     *                             optional parameters:
     *                             tasks?options=ignorecompleted.
     * @param string $suid         Server ID of the entry.
     *
     * @return boolean  True on success or false on failed (item not found).
     */
    function deleteEntry_backend($user, $databaseURI, $suid)
    {
        $database = $this->_normalize($databaseURI);

        $r = $this->_db->queryOne(
            'DELETE FROM syncml_data '
            . 'WHERE syncml_db = '
            . $this->_db->quote($database, 'text')
            . ' AND syncml_uid = '
            . $this->_db->quote($user, 'text')
            . ' AND syncml_id = '
            . $this->_db->quote($suid, 'text'));
        if ($this->_checkForError($r)) {
            return false;
        }

        return true;
    }

    function _cleanUser($user)
    {
        $r = $this->_db->exec('DELETE FROM syncml_data WHERE syncml_uid = '
                              . $this->_db->quote($user, 'text'));
        $this->_checkForError($r);

        $r = $this->_db->exec('DELETE FROM syncml_map WHERE syncml_uid = '
                              . $this->_db->quote($user, 'text'));
        $this->_checkForError($r);

        $r = $this->_db->exec('DELETE FROM syncml_anchors WHERE syncml_uid = '
                              . $this->_db->quote($user, 'text'));
        $this->_checkForError($r);

        $r = $this->_db->exec('DELETE FROM syncml_uids WHERE syncml_uid = '
                              . $this->_db->quote($user, 'text'));
        $this->_checkForError($r);

        $r = $this->_db->exec('DELETE FROM syncml_suidlist WHERE syncml_uid = '
                              . $this->_db->quote($user, 'text'));
        $this->_checkForError($r);
    }

}
