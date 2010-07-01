<?php
/**
 * A SyncML Backend provides the interface between the SyncML protocol as
 * provided by the SyncML pear package and an actual calendar or address book
 * application. This "actual application" is called the "data store" in this
 * description.
 *
 * The backend provides the following groups of functions:
 *
 * 1) Access to the datastore
 *    Reading, adding, replacing and deleting of entries.  Also retrieve
 *    information about changes in data store.  This is done via the
 *    retrieveEntry(), addEntry(), replaceEntry(), deleteEntry() and
 *    getServerChanges() methods.
 *
 * 2) User management functions
 *    This is the checkAuthentication() method to verify that a given user
 *    password combination is allowed to access the backend data store, and
 *    the setUser() method which does a "login" to the backend data store if
 *    required by the type of backend data store. Please note that the
 *    password is only transferred once in a sync session, so when handling
 *    the subsequent packets messages, the user may need to be "logged in"
 *    without a password. (Or the session management keeps the user "logged
 *    in").
 *
 * 3) Maintainig the client ID <-> server ID map
 *    The SyncML protocol does not require clients and servers to use the same
 *    primary keys for the data entries. So a map has to be in place to
 *    convert between client primary keys (called cuid's here) and server
 *    primary keys (called suid's). It's up to the server to maintain this
 *    map.  Method for this is createUidMap().
 *
 * 4) Sync anchor handling
 *    After a successful initial sync, the client and server sync timestamps
 *    are stored. This allows to perform subsequent syncs as delta syncs,
 *    where only new changes are replicated. Servers as well as clients need
 *    to be able to store two sync anchors (the client's and the server's) for
 *    a sync. Methods for this are readSyncAnchors() and writeSyncAnchors().
 *
 * 5) Test supporting functions
 *    The SyncML module comes with its own testing framework. All you need to
 *    do is implement the two methods testSetup() and testTearDown() and you
 *    are able to test your backend with all the test cases that are part of
 *    the module.
 *
 * 6) Miscellaneous functions
 *    This involves session handling (sessionStart() and sessionClose()),
 *    logging (logMessage() and logFile()), timestamp creation
 *    (getCurrentTimeStamp()), charset handling (getCharset(), setCharset())
 *    and database identification (isValidDatabaseURI()). For all of these
 *    functions, a default implementation is provided in SyncML_Backend.
 *
 * If you want to create a backend for your own appliction, you can either
 * derive from SyncML_Backend and implement everything in groups 1 to 5 or you
 * derive from SyncML_Backend_Sql which implements an example backend based on
 * direct database access using the PEAR MDB2 package. In this case you only
 * need to implement groups 1 to 3 and can use the implementation from
 * SyncML_Backend_Sql as a guideline for these functions.
 *
 * Key Concepts
 * ------------
 * In order to successfully create a backend, some understanding of a few key
 * concepts in SyncML and the SyncML package are certainly helpful.  So here's
 * some stuff that should make some issues clear (or at lest less obfuscated):
 *
 * 1) DatabaseURIs and Databases
 *    The SyncML protocol itself is completly independant from the data that
 *    is replicated. Normally the data are calendar or address book entries
 *    but it may really be anything from browser bookmarks to comeplete
 *    database tables. An ID (string name) of the database you want to
 *    actually replicate has to be configured in the client. Typically that's
 *    something like 'calendar' or 'tasks'. Client and server must agree on
 *    these names.  In addition this string may be used to provide additional
 *    arguments.  These are provided in a HTTP GET query style: like
 *    tasks?ignorecompletedtasks to replicate only pending tasks. Such a "sync
 *    identifier" is called a DatabaseURI and is really a database name plus
 *    some additional options.
 *    The SyncML package completly ignores these options and simply passes
 *    them on to the backend. It's up to the backend to decide what to do with
 *    them. However when dealing with the internal maps (cuid<->suid and sync
 *    anchors), it's most likely to use the database name only rather than the
 *    full databaseURI. The map information saying that server entry
 *    20070101203040xxa@mypc.org has id 768 in the client device is valid for
 *    the database "tasks", not for "tasks?somesillyoptions". So what you
 *    normally do is calling some kind of <code>$database =
 *    $this->_normalize($databaseURI)</cod> in every backend method that deals
 *    with databaseURIs and use $database afterwards. However actual usage of
 *    options is up to the backend implementation. SyncML works fine without.
 *
 * 2) Suid and Guid mapping
 *    This is the mapping of client IDs to server IDs and vice versa.  Please
 *    note that this map is per user and per client device: the server entry
 *    20070101203040xxa@mypc.org may have ID 720 in your PDA and AA10FC3A in
 *    your mobile phone.
 *
 * 3) Sync Anchors
 *    @todo describe sync anchors
 *    Have a look at the SyncML spec
 *    http://www.openmobilealliance.org/tech/affiliates/syncml/syncmlindex.html
 *    to find out more.
 *
 * 4) Changes and Timestamps
 *    @todo description of Changes and Timestamps, "mirroring effect"
 *    This is real tricky stuff.
 *    First it's important to know, that the SyncML protocol requires the
 *    ending timestamp of the sync timeframe to be exchanged _before_ the
 *    actual syncing starts. So all changes made during a sync have timestamps
 *    that are in the timeframe for the next upcoming sync.  Data exchange in
 *    a sync session works in two steps: 1st) the clients sends its changes to
 *    the server, 2nd) the server sends its changes to the client.
 *    So when in step 2, the backend datastore API is called with a request
 *    like "give me all changes in the server since the last sync".  Thus you
 *    also get the changes induced by the client in step 1 as well.  You have
 *    to somehow "tag" them to avoid echoing (and thus duplicating) them back
 *    to the client. Simply storing the guids in the session is not
 *    sufficient: the changes are made _after_ the end timestamp (see 1) of
 *    the current sync so you'll dupe them in the next sync.
 *    The current implementation deals with this as follows: whenever a client
 *    induced change is done in the backend, the timestamp for this change is
 *    stored in the cuid<->suid map in an additional field. That's the perfect
 *    place as the tagging needs to be done "per client device": when an add
 *    is received from the PDA it must not be sent back as an add to this
 *    device, but to mobile phone it must be sent.
 *    This is sorted out during the getServerChanges() process: if a server
 *    change has a timestamp that's the same as in the guid<->suid map, it
 *    came from the client and must not be added to the list of changes to be
 *    sent to this client.
 *    See the description of SyncML_Backend_Sql::_getChangeTS() for some more
 *    information.
 *
 * 5) Messages and Packages
 *    A message is a single HTTP Request. A package is single "logical
 *    message", a sync step. Normally the two coincide. However due to message
 *    size restrictions one package may be transferred in multiple messages
 *    (HTTP requests).
 *
 * 7) Server mode, client mode and test mode
 *    Per default, a backend is used for an SyncML server. Regarding the
 *    SyncML protocol, the working of client and server is similar, except
 *    that
 *    a) the client initiates the sync requests and the server respons to them,
 *       and
 *    b) the server must maintain the client id<->server id map.
 *
 *    Currently the SyncML package is designed to create servers. But is's an
 *    obvious (and straightforward) extension to do it for clients as well.
 *    And as a client has actually less work to do than a server, the backend
 *    should work for servers _and_ clients. During the sessionStart(), the
 *    backend gets a parameter to let it know whether it's in client or server
 *    mode (or test, see below). When in client mode, it should behave
 *    slightly different:
 *    a) the client doesn't do suid<->cuid mapping, so all invokations to the
 *       map creation method createUidMap().
 *    b) the client has only client ids, no server ids. So all arguments are
 *       considered cuids even when named suid. See the SyncML_Backend_Sql
 *       implementation, it's actually not that difficult.
 *
 *    Finally there's the test mode. The test cases consist of replaying
 *    pre-recorded sessions. For that to work, the test script must "simulate"
 *    user entries in the server data store. To do so, it creates a backend in
 *    test mode. This behaves similar to a client: when an server entry is
 *    created (modified) using addEntry() (replaceEntry()), no map entry must
 *    be done.
 *    The test backend uses also the two methods testSetup() and
 *    testTearDown() to create a clean (empty) enviroment for the test user
 *    "syncmltest".  See the SyncML_Backend_Sql implementation for details.
 *
 * $Horde: framework/SyncML/SyncML/Backend.php,v 1.8.2.19 2009-09-15 13:42:53 jan Exp $
 *
 * Copyright 2005-2009 The Horde Project (http://www.horde.org/)
 *
 * See the enclosed file COPYING for license information (LGPL). If you
 * did not receive this file, see http://www.fsf.org/copyleft/lgpl.html.
 *
 * @author  Karsten Fourmont <karsten@horde.org>
 * @package SyncML
 */

/** Types of logfiles. See logFile() method. */
define ('SYNCML_LOGFILE_CLIENTMESSAGE', 1);
define ('SYNCML_LOGFILE_SERVERMESSAGE', 2);
define ('SYNCML_LOGFILE_DEVINF',        3);
define ('SYNCML_LOGFILE_DATA',          4);

/** Backend modes. */
define ('SYNCML_BACKENDMODE_SERVER', 1);
define ('SYNCML_BACKENDMODE_CLIENT', 2);
define ('SYNCML_BACKENDMODE_TEST',   3);

class SyncML_Backend {

    /**
     * The concatenated log messages.
     *
     * @var string
     */
    var $_logtext = '';

    /**
     * The directory where debugging information is stored.
     *
     * @see SyncML_Backend()
     * @var string
     */
    var $_debugDir;

    /**
     * Whether to save SyncML messages in the debug directory.
     *
     * @see SyncML_Backend()
     * @var boolean
     */
    var $_debugFiles;

    /**
     * The log level. One of the PEAR_LOG_* constants.
     *
     * @see PEAR Log package
     * @see SyncML_Backend()
     * @var integer
     */
    var $_logLevel = PEAR_LOG_INFO;

    /**
     * The charset used in the SyncML messages.
     *
     * @var string
     */
    var $_charset;

    /**
     * The current user.
     *
     * @var string
     */
    var $_user;

    /**
     * The ID of the client device.
     *
     * This is used for all data access as an ID to allow to distinguish
     * between syncs with different devices.  $this->_user together with
     * $this->_syncDeviceID is used as an additional key for all persistence
     * operations.
     *
     * @var string
     */
    var $_syncDeviceID;

    /**
     * The backend mode. One of the SYNCML_BACKENDMODE_* constants.
     *
     * @var integer
     */
    var $_backendMode;

    /**
     * Constructor.
     *
     * Sets up the default logging mechanism.
     *
     * @param array $params  A hash with parameters. The following are
     *                       supported by the default implementation.
     *                       Individual backends may support other parameters.
     *                       - debug_dir:   A directory to write debug output
     *                                      to. Must be writeable by the web
     *                                      server.
     *                       - debug_files: If true, log all incoming and
     *                                      outgoing packets and data
     *                                      conversions and devinf log in
     *                                      debug_dir.
     *                       - log_level:   PEAR_LOG_*. Only log entries with
     *                                      at least this level. Defaults to
     *                                      PEAR_LOG_INFO.
     */
    function SyncML_Backend($params)
    {
        if (!empty($params['debug_dir']) && is_dir($params['debug_dir'])) {
            $this->_debugDir = $params['debug_dir'];
        }
        $this->_debugFiles = !empty($params['debug_files']);
        if (isset($params['log_level'])) {
            $this->_logLevel = $params['log_level'];
        }

        $this->logMessage('Backend of class ' . get_class($this) . ' created',
                          __FILE__, __LINE__, PEAR_LOG_DEBUG);
     }

    /**
     * Attempts to return a concrete SyncML_Backend instance based on $driver.
     *
     * @param string $driver The type of concrete Backend subclass to return.
     *                       The code is dynamically included from
     *                       Backend/$driver.php if no path is given or
     *                       directly with "include_once $driver . '.php'"
     *                       if a path is included. So make sure this parameter
     *                       is "safe" and not directly taken from web input.
     *                       The class in the file must be named
     *                       'SyncML_Backend_' . basename($driver) and extend
     *                       SyncML_Backend.
     * @param array $params  A hash containing any additional configuration or
     *                       connection parameters a subclass might need.
     *
     * @return SyncML_Backend  The newly created concrete SyncML_Backend
     *                         instance, or false on an error.
     */
    function factory($driver, $params = null)
    {
        if (empty($driver) || ($driver == 'none')) {
            return false;
        }

        if (basename($driver) == $driver) {
            include_once 'SyncML/Backend/' . $driver . '.php';
        } else {
            include_once $driver . '.php';
        }

        $driver = basename($driver);
        $class = 'SyncML_Backend_' . $driver;
        if (class_exists($class)) {
            $backend = new $class($params);
        } else {
            return false;
        }

        return $backend;
    }

    /**
     * Sets the charset.
     *
     * All data passed to the backend uses this charset and data returned from
     * the backend must use this charset, too.
     *
     * @param string $charset  A valid charset.
     */
    function setCharset($charset)
    {
        $this->_charset = $charset;
    }

    /**
     * Returns the charset.
     *
     * @return string  The charset used when talking to the backend.
     */
    function getCharset()
    {
        return $this->_charset;
    }

    /**
     * Returns the current device's ID.
     *
     * @return string  The device ID.
     */
    function getSyncDeviceID()
    {
        return $this->_syncDeviceID;
    }

    /**
     * Sets the user used for this session.
     *
     * This method is called by SyncML right after sessionStart() when either
     * authentication is accepted via checkAuthentication() or a valid user
     * has been retrieved from the state.  $this->_user together with
     * $this->_syncDeviceID is used as an additional key for all persistence
     * operations.
     * This method may have to force a "login", when the backend doesn't keep
     * auth state within a session or when in test mode.
     *
     * @param string $user  A user name.
     */
    function setUser($user)
    {
        $this->_user = $user;
    }

    /**
     * Returns the current user.
     *
     * @return string  The current user.
     */
    function getUser()
    {
        return $this->_user;
    }

    /**
     * Is called after the SyncML_State object has been set up, either
     * restored from the session, or freshly created.
     *
     * @param SyncML_State  The current state object.
     */
    function setupState(&$state)
    {
    }

    /**
     * Starts a PHP session.
     *
     * @param string $syncDeviceID  The device ID.
     * @param string $session_id    The session ID to use.
     * @param integer $backendMode  The backend mode, one of the
     *                              SYNCML_BACKENDMODE_* constants.
     */
    function sessionStart($syncDeviceID, $sessionId,
                          $backendMode = SYNCML_BACKENDMODE_SERVER)
    {
        $this->_syncDeviceID = $syncDeviceID;
        $this->_backendMode = $backendMode;

        // Only the server needs to start a session:
        if ($this->_backendMode == SYNCML_BACKENDMODE_SERVER) {
            $sid = md5($syncDeviceID . $sessionId);
            session_id($sid);
            @session_start();
        }
    }

    /**
     * Closes the PHP session.
     */
    function sessionClose()
    {
        // Only the server needs to start a session:
        if ($this->_backendMode == SYNCML_BACKENDMODE_SERVER) {
            session_unset();
            session_destroy();
        }
    }

    /**
     * Returns whether a database URI is valid to be synced with this backend.
     *
     * This default implementation accepts "tasks", "calendar", "notes" and
     * "contacts".  However individual backends may offer replication of
     * different or completly other databases (like browser bookmarks or
     * cooking recipes).
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
     * @abstract
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
        die('getServerChanges() not implemented!');
    }

    /**
     * Retrieves an entry from the backend.
     *
     * @abstract
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
        die('retrieveEntry() not implemented!');
    }

    /**
     * Adds an entry into the server database.
     *
     * @abstract
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
    function addEntry($databaseURI, $content, $contentType, $cuid)
    {
        die('addEntry() not implemented!');
    }

    /**
     * Replaces an entry in the server database.
     *
     * @abstract
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
        die('replaceEntry() not implemented!');
    }

    /**
     * Deletes an entry from the server database.
     *
     * @abstract
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
        die('deleteEntry() not implemented!');
    }

    /**
     * Authenticates the user at the backend.
     *
     * For some types of authentications (notably auth:basic) the username
     * gets extracted from the authentication data and is then stored in
     * username.  For security reasons the caller must ensure that this is the
     * username that is used for the session, overriding any username
     * specified in <LocName>.
     *
     * @param string $username    Username as provided in the <SyncHdr>.
     *                            May be overwritten by $credData.
     * @param string $credData    Authentication data provided by <Cred><Data>
     *                            in the <SyncHdr>.
     * @param string $credFormat  Format of data as <Cread><Meta><Format> in
     *                            the <SyncHdr>. Typically 'b64'.
     * @param string $credType    Auth type as provided by <Cred><Meta><Type>
     *                            in the <SyncHdr>. Typically
     *                            'syncml:auth-basic'.
     *
     * @return boolean|string  The user name if authentication succeeded, false
     *                         otherwise.
     */
    function checkAuthentication(&$username, $credData, $credFormat, $credType)
    {
        if (empty($credData) || empty($credType)) {
            return false;
        }

        switch ($credType) {
        case 'syncml:auth-basic':
            list($username, $pwd) = explode(':', base64_decode($credData), 2);
            $this->logMessage('Checking authentication for user ' . $username,
                              __FILE__, __LINE__, PEAR_LOG_DEBUG);
            return $this->_checkAuthentication($username, $pwd);

        case 'syncml:auth-md5':
            /* syncml:auth-md5 only transfers hash values of passwords.
             * Currently the syncml:auth-md5 hash scheme is not supported
             * by the authentication backend. So we can't use Horde to do
             * authentication. Instead here is a very crude direct manual hook:
             * To allow authentication for a user 'dummy' with password 'sync',
             * run
             * php -r 'print base64_encode(pack("H*",md5("dummy:sync")));'
             * from the command line. Then create an entry like
             *  'dummy' => 'ZD1ZeisPeQs0qipHc9tEsw==' in the users array below,
             * where the value is the command line output.
             * This user/password combination is then accepted for md5-auth.
             */
            $users = array(
                  // example for user dummy with pass pass:
                  // 'dummy' => 'ZD1ZeisPeQs0qipHc9tEsw=='
                          );
            if (empty($users[$username])) {
                return false;
            }

            // @todo: nonce may be specified by client. Use it then.
            $nonce = '';
            if (base64_encode(pack('H*', md5($users[$username] . ':' . $nonce))) === $credData) {
                return $this->_setAuthenticated($username, $credData);
            }
            return false;

        default:
            $this->logMessage('Unsupported authentication type ' . $credType,
                              __FILE__, __LINE__, PEAR_LOG_ERR);
            return false;
        }
    }

    /**
     * Authenticates the user at the backend.
     *
     * @abstract
     *
     * @param string $username    A user name.
     * @param string $password    A password.
     *
     * @return boolean|string  The user name if authentication succeeded, false
     *                         otherwise.
     */
    function _checkAuthentication($username, $password)
    {
        die('_checkAuthentication() not implemented!');
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
        die('setAuthenticated() not implemented!');
    }

    /**
     * Stores Sync anchors after a successful synchronization to allow two-way
     * synchronization next time.
     *
     * The backend has to store the parameters in its persistence engine
     * where user, syncDeviceID and database are the keys while client and
     * server anchor ar the payload. See readSyncAnchors() for retrieval.
     *
     * @abstract
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
    }

    /**
     * Reads the previously written sync anchors from the database.
     *
     * @abstract
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
    }

    /**
     * Creates a map entry to map between server and client IDs.
     *
     * If an entry already exists, it is overwritten.
     *
     * @abstract
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
    }

    /**
     * Erases all mapping entries for one combination of user, device ID.
     *
     * This is used during SlowSync so that we really sync everything properly
     * and no old mapping entries remain.
     *
     * @abstract
     *
     * @param string $databaseURI  URI of database to sync. Like calendar,
     *                             tasks, contacts or notes. May include
     *                             optional parameters:
     *                             tasks?options=ignorecompleted.
     */
    function eraseMap($databaseURI)
    {
    }

    /**
     * Logs a message in the backend.
     *
     * @param mixed $message     Either a string or a PEAR_Error object.
     * @param string $file       What file was the log function called from
     *                           (e.g. __FILE__)?
     * @param integer $line      What line was the log function called from
     *                           (e.g. __LINE__)?
     * @param integer $priority  The priority of the message. One of:
     *                           - PEAR_LOG_EMERG
     *                           - PEAR_LOG_ALERT
     *                           - PEAR_LOG_CRIT
     *                           - PEAR_LOG_ERR
     *                           - PEAR_LOG_WARNING
     *                           - PEAR_LOG_NOTICE
     *                           - PEAR_LOG_INFO
     *                           - PEAR_LOG_DEBUG
     */
    function logMessage($message, $file, $line, $priority = PEAR_LOG_INFO)
    {
        if ($priority > $this->_logLevel)  {
            return;
        }

        // Internal logging to logtext
        if (is_string($this->_logtext)) {
            switch ($priority) {
            case PEAR_LOG_EMERG:
                $this->_logtext .= 'EMERG:  ';
                break;
            case PEAR_LOG_ALERT:
                $this->_logtext .= 'ALERT:  ';
                break;
            case PEAR_LOG_CRIT:
                $this->_logtext .= 'CIRT:   ';
                break;
            case PEAR_LOG_ERR:
                $this->_logtext .= 'ERR:    ';
                break;
            case PEAR_LOG_WARNING:
                $this->_logtext .= 'WARNING:';
                break;
            case PEAR_LOG_NOTICE:
                $this->_logtext .= 'NOTICE: ';
                break;
            case PEAR_LOG_INFO:
                $this->_logtext .= 'INFO:   ';
                break;
            case PEAR_LOG_DEBUG:
                $this->_logtext .= 'DEBUG:  ';
                break;
            default:
                $this->_logtext .= 'UNKNOWN:';
            }
            if (is_string($message)) {
                $this->_logtext .= $message;
            } elseif (is_a($message, 'PEAR_Error')) {
                $this->_logtext .= $message->getMessage();
            }
            $this->_logtext .= "\n";
        }
    }

    /**
     * Logs data to a file in the debug directory.
     *
     * @param integer $type          The data type. One of the SYNCML_LOGFILE_*
     *                               constants.
     * @param string $content        The data content.
     * @param boolean $wbxml         Whether the data is wbxml encoded.
     * @param boolean $sessionClose  Whether this is the last SyncML message
     *                               in a session. Bump the file number.
     */
    function logFile($type, $content, $wbxml = false, $sessionClose = false)
    {
        if (empty($this->_debugDir) || !$this->_debugFiles) {
            return;
        }

        switch ($type) {
        case SYNCML_LOGFILE_CLIENTMESSAGE:
            $filename = 'client_';
            $mode = 'wb';
            break;
        case SYNCML_LOGFILE_SERVERMESSAGE:
            $filename = 'server_';
            $mode = 'wb';
            break;
        case SYNCML_LOGFILE_DEVINF:
            $filename = 'devinf.txt';
            $mode = 'wb';
            break;
        case SYNCML_LOGFILE_DATA:
            $filename = 'data.txt';
            $mode = 'a';
            break;
        default:
            // Unkown type. Use $type as filename:
            $filename = $type;
            $mode = 'a';
            break;
        }

        if ($type === SYNCML_LOGFILE_CLIENTMESSAGE ||
            $type === SYNCML_LOGFILE_SERVERMESSAGE) {
            $packetNum = @intval(file_get_contents($this->_debugDir
                                                   . '/packetnum.txt'));
            if (empty($packetNum)) {
                $packetNum = 10;
            }
            if ($wbxml) {
                $filename .= $packetNum . '.wbxml';
            } else {
                $filename .= $packetNum . '.xml';
            }
        }

        /* Write file */
        $fp = @fopen($this->_debugDir . '/' . $filename, $mode);
        if ($fp) {
            @fwrite($fp, $content);
            @fclose($fp);
        }

        if ($type === SYNCML_LOGFILE_CLIENTMESSAGE) {
            $this->logMessage('Started at ' . date('Y-m-d H:i:s')
                              . '. Packet logged in '
                              . $this->_debugDir . '/' . $filename,
                              __FILE__, __LINE__, PEAR_LOG_DEBUG);
        }

        /* Increase packet number. */
        if ($type === SYNCML_LOGFILE_SERVERMESSAGE) {
            $this->logMessage('Finished at ' . date('Y-m-d H:i:s')
                              . '. Packet logged in '
                              . $this->_debugDir . '/' . $filename,
                              __FILE__, __LINE__, PEAR_LOG_DEBUG);

            $fp = @fopen($this->_debugDir . '/packetnum.txt', 'w');
            if ($fp) {
                /* When one complete session is finished: go to next 10th. */
                if ($sessionClose) {
                    $packetNum += 10 - $packetNum % 10;
                } else {
                    $packetNum += 1;
                }
                fwrite($fp, $packetNum);
                fclose($fp);
            }
        }
    }

    /**
     * Cleanup function called after all message processing is finished.
     *
     * Allows for things like closing databases or flushing logs.  When
     * running in test mode, tearDown() must be called rather than close.
     */
    function close()
    {
        if (!empty($this->_debugDir)) {
            $f = @fopen($this->_debugDir . '/log.txt', 'a');
            if ($f) {
                fwrite($f, $this->_logtext . "\n");
                fclose($f);
            }
        }
        session_write_close();
    }

    /**
     * Returns the current timestamp in the same format as used by
     * getServerChanges().
     *
     * Backends can use their own way to represent timestamps, like unix epoch
     * integers or UTC Datetime strings.
     *
     * @return mixed  A timestamp of the current time.
     */
    function getCurrentTimeStamp()
    {
        /* Use unix epoch as default method for timestamps. */
        return time();
    }

    /**
     * Creates a clean test environment in the backend.
     *
     * Ensures there's a user with the given credentials and an empty data
     * store.
     *
     * @abstract
     *
     * @param string $user This user accout has to be created in the backend.
     * @param string $pwd  The password for user $user.
     */
    function testSetup($user, $pwd)
    {
        die('testSetup() not implemented!');
    }

    /**
     * Prepares the test start.
     *
     * @param string $user This user accout has to be created in the backend.
     */
    function testStart($user)
    {
        die('testStart() not implemented!');
    }

    /**
     * Tears down the test environment after the test is run.
     *
     * @abstract
     *
     * Should remove the testuser created during testSetup and all its data.
     */
    function testTearDown()
    {
        die('testTearDown() not implemented!');
    }

    /**
     * Normalizes a databaseURI to a database name, so that
     * _normalize('tasks?ignorecompleted') should return just 'tasks'.
     *
     * @param string $databaseURI  URI of a database. Like calendar, tasks,
     *                             contacts or notes. May include optional
     *                             parameters:
     *                             tasks?options=ignorecompleted.
     *
     * @return string  The normalized database name.
     */
    function _normalize($databaseURI)
    {
        $database = String::lower(
            basename(preg_replace('|\?.*$|', '', $databaseURI)));

        /* Convert some commonly encountered types to a fixed set of known
         * service names: */
        switch($database) {
        case 'contacts':
        case 'contact':
        case 'card':
        case 'scard':
            return 'contacts';
        case 'calendar':
        case 'event':
        case 'events':
        case 'cal':
        case 'scal':
            return 'calendar';
        case 'notes':
        case 'memo':
        case 'note':
        case 'snote':
            return 'notes';
        case 'tasks':
        case 'task':
        case 'stask':
            return 'tasks';
        default:
            return $database;
        }
    }

    /**
     * Extracts an HTTP GET like parameter from an URL.
     *
     * Example: <code>getParameter('test?q=1', 'q') == 1</code>
     *
     * @static
     *
     * @param string $url        The complete URL.
     * @param string $parameter  The parameter name to extract.
     * @param string $default    A default value to return if none has been
     *                           provided in the URL.
     */
    function getParameter($url, $parameter, $default = null)
    {
        if (preg_match('|[&\?]' . $parameter . '=([^&]*)|', $url, $m)) {
            return $m[1];
        }
        return $default;
    }

}
