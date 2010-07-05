<?php
/**
 * $Horde: framework/RPC/RPC/webdav.php,v 1.1.12.19 2009-01-06 15:23:32 jan Exp $
 *
 * @package Horde_RPC
 */

/** HTTP_WebDAV_Server */
include_once 'HTTP/WebDAV/Server.php';

/**
 * The Horde_RPC_webdav class provides a WebDAV implementation of the
 * Horde RPC system.
 *
 * Copyright 2004-2009 The Horde Project (http://www.horde.org/)
 *
 * See the enclosed file COPYING for license information (LGPL). If you
 * did not receive this file, see http://www.fsf.org/copyleft/lgpl.html.
 *
 * @author  Chuck Hagenbuch <chuck@horde.org>
 * @since   Horde 3.0
 * @package Horde_RPC
 */
class Horde_RPC_webdav extends Horde_RPC {

    /**
     * Resource handler for the WebDAV server.
     *
     * @var HTTP_WebDAV_Server_Horde
     */
    var $_server;

    /**
     * WebDav server constructor.
     *
     * @access private
     */
    function Horde_RPC_webdav()
    {
        parent::Horde_RPC();
        $this->_server = new HTTP_WebDAV_Server_Horde();
    }

    /**
     * WebDAV handles authentication internally, so bypass the
     * system-level auth check by just returning true here.
     */
    function authorize()
    {
        return true;
    }

    /**
     * If the webdav backend is used, the input should not be read, it is
     * being read by HTTP_WebDAV_Server.
     */
    function getInput()
    {
    }

    /**
     * Sends an RPC request to the server and returns the result.
     *
     * @param string  The raw request string.
     *
     * @return string  The XML encoded response from the server.
     */
    function getResponse($request)
    {
        $this->_server->ServeRequest();
        exit;
    }

}

/**
 * Horde extension of the base HTTP_WebDAV_Server class.
 *
 * @package Horde_RPC
 */
class HTTP_WebDAV_Server_Horde extends HTTP_WebDAV_Server {

    /**
     * Realm string to be used in authentification popups
     *
     * @var string
     */
    var $http_auth_realm = 'Horde WebDAV';

    /**
     * String to be used in "X-Dav-Powered-By" header
     *
     * @var string
     */
    var $dav_powered_by = 'Horde WebDAV Server';

    /**
     * GET implementation.
     *
     * @param array $options  Array of input and output parameters.
     * <br><strong>input</strong><ul>
     * <li> path -
     * </ul>
     * <br><strong>output</strong><ul>
     * <li> size -
     * </ul>
     *
     * @return string|boolean  HTTP-Statuscode.
     */
    function GET(&$options)
    {
        if ($options['path'] == '/') {
            $options['mimetype'] = 'httpd/unix-directory';
        } else {
            $result = $this->_list($options['path'], 0, false);
            if (is_a($result, 'PEAR_Error') && $result->getCode()) {
                // Allow called applications to set the result code
                return $this->_checkHTTPCode($result->getCode())
                    . ' ' . $result->getMessage();
            } elseif ($result === false) {
                return '404 File Not Found';
            }
            $options = $result;
        }

        return true;
    }

    /**
     * PUT implementation.
     *
     * @param array &$options  Parameter passing array.
     *
     * @return string|boolean  HTTP-Statuscode.
     */
    function PUT(&$options)
    {
        $path = trim($options['path'], '/');

        if (empty($path)) {
            return '403 PUT requires a path.';
        }

        $pieces = explode('/', $path);

        if (count($pieces) < 2 || empty($pieces[0])) {
            return '403 PUT denied outside of application directories.';
        }

        $content = '';
        while (!feof($options['stream'])) {
            $content .= fgets($options['stream']);
        }

        $result = $GLOBALS['registry']->callByPackage($pieces[0], 'put', array('path' => $path, 'content' => $content, 'type' => $options['content_type']));
        if (is_a($result, 'PEAR_Error')) {
            Horde::logMessage($result, __FILE__, __LINE__, PEAR_LOG_ERR);
            if ($result->getCode()) {
                return $this->_checkHTTPCode($result->getCode())
                    . ' ' . $result->getMessage();
            } else {
                return '500 Internal Server Error. Check server logs';
            }
        }

        return true;
    }

    /**
     * Performs a WebDAV DELETE.
     *
     * Deletes a single object from a database. The path passed in must
     * be in [app]/[path] format.
     *
     * @see HTTP_WebDAV_Server::http_DELETE()
     *
     * @param array $options An array of parameters from the setup
     * method in HTTP_WebDAV_Server.
     *
     * @return string|boolean  HTTP-Statuscode.
     */
    function DELETE($options)
    {
        $path = $options['path'];
        $pieces = explode('/', trim($this->path, '/'), 2);

        if (count($pieces) == 2) {
            $app = $pieces[0];
            $path = $pieces[1];

            // TODO: Support HTTP/1.1 If-Match on ETag here

            // Delete access is checked in each app.
            $result = $GLOBALS['registry']->callByPackage($app, 'path_delete', array($path));
            if (is_a($result, 'PEAR_Error')) {
                Horde::logMessage($result, __FILE__, __LINE__, PEAR_LOG_INFO);
                if ($result->getCode()) {
                    return $this->_checkHTTPCode($result->getCode())
                        . ' ' . $result->getMessage();
                } else {
                    return '500 Internal Server Error. Check server logs';
                }
            }
            return '204 No Content';
        } else {
            Horde::logMessage(sprintf(_("Error deleting from path %s; must be [app]/[path]", $options['path'])), __FILE__, __LINE__, PEAR_LOG_INFO);
            return '403 Must supply a resource within the application to delete.';
        }
    }

    /**
     * PROPFIND method handler
     *
     * @param array $options  General parameter passing array.
     * @param array &$files  Return array for file properties.
     *
     * @return boolean  True on success.
     */
    function PROPFIND($options, &$files)
    {
        $list = $this->_list($options['path'], $options['depth'], true);
        if ($list === false || is_a($list, 'PEAR_Error')) {
            // Always return '404 File Not Found';
            // Work around HTTP_WebDAV_Server behavior.
            // See: http://pear.php.net/bugs/bug.php?id=11390
            return false;
        }
        $files['files'] = $list;
        return true;
    }

    /**
     * MKCOL method handler
     *
     * @param array $options
     * @return string HTTP response string
     */
    function MKCOL($options)
    {
        $path = $options['path'];
        if (substr($path, 0, 1) == '/') {
            $path = substr($path, 1);
        }

        // Take the module name from the path
        $pieces = explode('/', $path, 2);
        if (count($pieces) == 2) {
            // Send the request to the application
            $result = $GLOBALS['registry']->callByPackage($pieces[0], 'mkcol', array('path' => $path));
            if (is_a($result, 'PEAR_Error')) {
                Horde::logMessage($result, __FILE__, __LINE__, PEAR_LOG_ERR);
                if ($result->getCode()) {
                    return $this->_checkHTTPCode($result->getCode())
                        . ' ' . $result->getMessage();
                } else {
                    return '500 Internal Server Error. Check server logs';
                }
            }
        } else {
            Horde::logMessage(sprintf(_("Unable to create directory %s; must be [app]/[path]"), $path), __FILE__, __LINE__, PEAR_LOG_INFO);
            return '403 Must specify a resource within an application.  MKCOL disallowed at top level.';
        }

        return '200 OK';
    }

    /**
     * MOVE method handler
     *
     * @param array $options
     * @return string HTTP response string
     */
    function MOVE($options)
    {
        $path = $options['path'];
        if (substr($path, 0, 1) == '/') {
            $path = substr($path, 1);
        }

        // Take the module name from the path
        $sourcePieces = explode('/', $path, 2);
        if (count($sourcePieces) == 2) {
            $destPieces = explode('/', $options['dest'], 2);
            if (!(count($destPieces) == 2) || $sourcesPieces[0] != $destPieces[0]) {
                return '400 Can not move across applications.';
            }
            // Send the request to the module
            $result = $GLOBALS['registry']->callByPackage($sourcePieces[0], 'move', array('path' => $path, 'dest' => $options['dest']));
            if (is_a($result, 'PEAR_Error')) {
                Horde::logMessage($result, __FILE__, __LINE__, PEAR_LOG_ERR);
                if ($result->getCode()) {
                    return $this->_checkHTTPCode($result->getCode())
                        . ' ' . $result->getMessage();
                } else {
                    return '500 Internal Server Error. Check server logs';
                }
            }
        } else {
            Horde::logMessage(sprintf(_("Unable to rename %s; must be [app]/[path] and within the same application."), $path), __FILE__, __LINE__, PEAR_LOG_INFO);
            return '403 Must specify a resource within an application.  MOVE disallowed at top level.';
        }

        return '200 OK';
    }

    /**
     * Generates a response to a GET or PROPFIND request.
     *
     * @param string $path       Path of GET or PROPFIND request.
     * @param string $depth      0, 1, or infinity.
     * @param array $properties  A list of requested properties on the object.
     *
     * @return mixed  Array of objects with properties if the request is a dir,
     *                array of file metadata + data if request is a file,
     *                false if the object is not found.
     */
    function _list($path, $depth, $properties)
    {
        global $registry;

        $list = array(
            array('path' => $this->path,
                  'props' => array(
                      $this->mkprop('displayname', $this->path),
                      $this->mkprop('creationdate', time()),
                      $this->mkprop('getlastmodified', time()),
                      $this->mkprop('resourcetype', 'collection'),
                      $this->mkprop('getcontenttype', 'httpd/unix-directory'),
                      $this->mkprop('getcontentlength', 0))));
        if ($path == '/') {
            $apps = $registry->listApps(null, false, PERMS_READ);
            if (is_a($apps, 'PEAR_Error')) {
                Horde::logMessage($apps, __FILE__, __LINE__, PEAR_LOG_ERR);
                return $apps;
            }
            foreach ($apps as $app) {
                if ($registry->hasMethod('browse', $app)) {
                    $props = array(
                        $this->mkprop('displayname', String::convertCharset($registry->get('name', $app), NLS::getCharset(), 'UTF-8')),
                        $this->mkprop('creationdate', time()),
                        $this->mkprop('getlastmodified', time()),
                        $this->mkprop('resourcetype', 'collection'),
                        $this->mkprop('getcontenttype', 'httpd/unix-directory'),
                        $this->mkprop('getcontentlength', 0));
                    $item = array('path' => $this->path . '/' . $app,
                                  'props' => $props);
                    $list[] = $item;
                }
            }
        } else {
            if (substr($path, 0, 1) == '/') {
                $path = substr($path, 1);
            }
            $pieces = explode('/', $path);
            $items = $registry->callByPackage($pieces[0], 'browse', array('path' => $path, 'properties' => array('name', 'browseable', 'contenttype', 'contentlength', 'created', 'modified')));
            if ($items === false) {
                // File not found
                return $items;
            }
            if (is_a($items, 'PEAR_Error')) {
                Horde::logMessage($items, __FILE__, __LINE__, PEAR_LOG_ERR);
                return $items;
            }
            if (empty($items)) {
                // No content exists at this level.
                return array();
            }
            if (!is_array(reset($items))) {
                /* A one-dimensional array means we have an actual object with
                 * data to return to the client.
                 */
                if ($properties) {
                    $props = array(
                        $this->mkprop('displayname', String::convertCharset(isset($items['name']) ? $items['name'] : $path, NLS::getCharset(), 'UTF-8')),
                        $this->mkprop('getlastmodified', empty($items['mtime']) ? time() : $items['mtime']),
                        $this->mkprop('resourcetype', ''),
                        $this->mkprop('getcontenttype', empty($items['mimetype']) ? 'application/octet-stream' : $items['mimetype']),
                        $this->mkprop('getcontentlength', empty($items['contentlength']) ? strlen($items['data']) : $items['contentlength']));
                    if (!empty($items['created'])) {
                        $props[] = $this->mkprop('creationdate', $items['created']);
                    }
                    $items = array(array('path' => $this->path,
                                         'props' => $props));
                }
                return $items;
            }

            /* A directory full of objects has been returned. */
            foreach ($items as $sub_path => $i) {
                $props = array(
                    $this->mkprop('displayname', String::convertCharset($i['name'], NLS::getCharset(), 'UTF-8')),
                    $this->mkprop('creationdate', empty($i['created']) ? 0 : $i['created']),
                    $this->mkprop('getlastmodified', empty($i['modified']) ? 0 : $i['modified']),
                    $this->mkprop('resourcetype', $i['browseable'] ? 'collection' : ''),
                    $this->mkprop('getcontenttype', $i['browseable'] ? 'httpd/unix-directory' : (empty($i['contenttype']) ? 'application/octet-stream' : $i['contenttype'])),
                    $this->mkprop('getcontentlength', empty($i['contentlength']) ? 0 : $i['contentlength']));
                $item = array('path' => '/' . $sub_path,
                              'props' => $props);
                $list[] = $item;
            }
        }

        return $list;
    }

    /**
     * Attempts to set a lock on a specified resource.
     *
     * @param array &$params  Reference to array of parameters.  These
     *                        parameters should be overwritten with the lock
     *                        information.
     *
     * @return int            HTTP status code
     */
    function LOCK(&$params)
    {
        if (!isset($GLOBALS['conf']['lock']['driver']) ||
            $GLOBALS['conf']['lock']['driver'] == 'none') {
            return 500;
        }

        if (empty($params['path'])) {
            Horde::logMessage('Empty path supplied to LOCK()', __FILE__, __LINE__, PEAR_LOG_ERR);
            return 403;
        }
        if ($params['path'] == '/') {
            // Locks are always denied to the root directory
            return 403;
        }
        if (isset($params['depth']) && $params['depth'] == 'infinity') {
            // For now we categorically disallow recursive locks
            return 403;
        }

        if (!is_array($params['timeout']) || count($params['timeout']) != 1) {
            // Unexpected timeout parameter.  Assume 600 seconds.
            $timeout = 600;
        }
        $tmp = explode('-', $params['timeout'][0]);
        if (count($tmp) != 2) {
            // Unexpected timeout parameter.  Assume 600 seconds.
            $timeout = 600;
        }
        if (strtolower($tmp[0]) == 'second') {
            $timeout = $tmp[1];
        } else {
            // Unexpected timeout parameter.  Assume 600 seconds.
            $timeout = 600;
        }

        require_once 'Horde/Lock.php';
        $locks = &Horde_Lock::singleton($GLOBALS['conf']['lock']['driver']);
        if (is_a($locks, 'PEAR_Error')) {
            Horde::logMessage($locks, __FILE__, __LINE__, PEAR_LOG_ERR);
            return 500;
        }

        $locktype = HORDE_LOCK_TYPE_SHARED;
        if ($params['scope'] == 'exclusive') {
            $locktype = HORDE_LOCK_TYPE_EXCLUSIVE;
        }

        $lockid = $locks->setLock(Auth::getAuth(), 'webdav', $params['path'],
                                  $timeout, $locktype);

        if (is_a($lockid, 'PEAR_Error')) {
            Horde::logMessage($lockid, __FILE__, __LINE__, PEAR_LOG_ERR);
            return 500;
        } elseif ($lockid === false) {
            // Resource is already locked.
            return 423;
        }

        $params['locktoken'] = $lockid;
        $params['owner'] = Auth::getAuth();
        $params['timeout'] = $timeout;

        return "200";
    }

    /**
     * Attempts to remove a specified lock.
     *
     * @param array &$params  Reference to array of parameters.  These
     *                        parameters should be overwritten with the lock
     *                        information.
     *
     * @return int            HTTP status code
     */
    function UNLOCK(&$params)
    {
        if (!isset($GLOBALS['conf']['lock']['driver']) ||
            $GLOBALS['conf']['lock']['driver'] == 'none') {
            return 500;
        }

        require_once 'Horde/Lock.php';
        $locks = &Horde_Lock::singleton($GLOBALS['conf']['lock']['driver']);
        if (is_a($locks, 'PEAR_Error')) {
            Horde::logMessage($locks, __FILE__, __LINE__, PEAR_LOG_ERR);
            return 500;
        }

        $res = $locks->clearLock($params['token']);
        if (is_a($res, 'PEAR_Error')) {
            Horde::logMessage($res, __FILE__, __LINE__, PEAR_LOG_ERR);
            return 500;
        } elseif ($res === false) {
            Horde::logMessage('clearLock() returned false', __FILE__, __LINE__, PEAR_LOG_ERR);
            // Something else has failed:  424 (Method Failure)
            return 424;
        }

        // Lock cleared.  Use 204 (No Content) instead of 200 because there is
        // no lock information to return to the client.
        return 204;
    }

    function checkLock($resource)
    {
        if (!isset($GLOBALS['conf']['lock']['driver']) ||
            $GLOBALS['conf']['lock']['driver'] == 'none') {
            Horde::logMessage('WebDAV locking failed because no lock driver has been configured.', __FILE__, __LINE__, PEAR_LOG_WARNING);
            return false;
        }

        require_once 'Horde/Lock.php';
        $locks = &Horde_Lock::singleton($GLOBALS['conf']['lock']['driver']);
        if (is_a($locks, 'PEAR_Error')) {
            Horde::logMessage($locks, __FILE__, __LINE__, PEAR_LOG_ERR);
            return false;
        }

        $res =  $locks->getLocks('webdav', $resource);
        if (is_a($res, 'PEAR_Error')) {
            Horde::logMessage($res, __FILE__, __LINE__, PEAR_LOG_ERR);
            return false;
        }

        if (empty($res)) {
            // No locks found.
            return $res;
        }

        // WebDAV only supports one lock.  Return the first lock.
        $lock = reset($res);

        // Format the array keys for HTTP_WebDAV_Server
        $ret = array();
        if ($lock['lock_type'] == HORDE_LOCK_TYPE_EXCLUSIVE) {
            $ret['scope'] = 'exclusive';
        } else {
            $ret['scope'] = 'shared';
        }
        $ret['type'] = 'write';
        $ret['expires'] = $lock['lock_expiry_timestamp'];
        $ret['token'] = $lock['lock_id'];
        $ret['depth'] = 1;

        return $ret;
    }

    /**
     * Check authentication. We always return true here since we
     * handle permissions based on the resource that's requested, but
     * we do record the authenticated user for later use.
     *
     * @param string $type      Authentication type, e.g. "basic" or "digest"
     * @param string $username  Transmitted username.
     * @param string $password  Transmitted password.
     *
     * @return boolean  Authentication status. Always true.
     */
    function check_auth($type, $username, $password)
    {
        $auth = &Auth::singleton($GLOBALS['conf']['auth']['driver']);
        return $auth->authenticate($username, array('password' => $password));
    }

    /**
     * Make sure the error code returned in the PEAR_Error object is a valid
     * HTTP response code.
     *
     * This is necessary because in pre-Horde 3.2 apps the response codes are
     * not sanitized.  This backward compatibility check can be removed when
     * we drop support for pre-3.2 apps.  Intentionally, not every valid HTTP
     * code is listed here.  Only common ones are here to reduce the
     * possibility of an invalid code being confused with a valid HTTP code.
     *
     * @todo Remove for Horde 4.0
     *
     * @param integer $code  Status code to check for validity.
     *
     * @return integer  Either the original code if valid or 500 for internal
     *                  server error.
     */
    function _checkHTTPcode($code)
    {
        $valid = array(200, // OK
                       201, // Created
                       202, // Accepted
                       204, // No Content
                       301, // Moved Permanently
                       302, // Found
                       304, // Not Modified
                       307, // Temporary Redirect
                       400, // Bad Request
                       401, // Unauthorized
                       403, // Forbidden
                       404, // Not Found
                       405, // Method Not Allowed
                       406, // Not Acceptable
                       408, // Request Timeout
                       413, // Request Entity Too Large
                       415, // Unsupported Media Type
                       500, // Internal Server Error
                       501, // Not Implemented
                       503, // Service Unavailable
        );
        if (in_array($code, $valid)) {
            return $code;
        } else {
            return 500;
        }
    }

}
