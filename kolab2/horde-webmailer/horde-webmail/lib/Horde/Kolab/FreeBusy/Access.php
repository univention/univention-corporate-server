<?php
/**
 * Access handlers for Kolab free/busy.
 *
 * $Horde: framework/Kolab_FreeBusy/lib/Horde/Kolab/FreeBusy/Access.php,v 1.15.2.2 2009-03-06 20:47:39 wrobel Exp $
 *
 * @package Kolab_FreeBusy
 */

/** Load the required Horde libraries */ 
require_once 'Horde.php';

/** Load the Auth library */ 
require_once 'Horde/Auth.php';

/**
 * The Horde_Kolab_FreeBusy_Access:: class provides functionality to check
 * free/busy access rights for the specified folder.
 *
 * $Horde: framework/Kolab_FreeBusy/lib/Horde/Kolab/FreeBusy/Access.php,v 1.15.2.2 2009-03-06 20:47:39 wrobel Exp $
 *
 * Copyright 2004-2008 Klarälvdalens Datakonsult AB
 *
 * See the enclosed file COPYING for license information (LGPL). If you
 * did not receive this file, see http://www.gnu.org/licenses/old-licenses/lgpl-2.1.html.
 *
 * @author  Gunnar Wrobel <p@rdus.de>
 * @author  Steffen Hansen <steffen@klaralvdalens-datakonsult.se>
 * @package Kolab_FreeBusy
 */
class Horde_Kolab_FreeBusy_Access {

    /**
     * The user calling the script.
     *
     * @var string
     */
    var $user;

    /**
     * Did the above combination authenticate?
     *
     * @var string
     */
    var $_authenticated = false;

    /**
     * The object representing the user calling the script.
     *
     * @var string
     */
    var $user_object;

    /**
     * The requested owner.
     *
     * @var string
     */
    var $owner;

    /**
     * The object representing the folder owner.
     *
     * @var string
     */
    var $owner_object;

    /**
     * The object representing the server configuration.
     *
     * @var string
     */
    var $server_object;

    /**
     * The folder we try to access.
     *
     * @var string
     */
    var $folder;

    /**
     * The IMAP path of folder we try to access.
     *
     * @var string
     */
    var $imap_folder;

    /**
     * The common name (CN) of the owner.
     *
     * @var string
     */
    var $cn = '';

    /**
     * The free/busy server for the folder owner.
     *
     * @var string
     */
    var $freebusyserver;

    /**
     * Constructor.
     *
     * @param array       $params        Any additional options
     */
    function Horde_Kolab_FreeBusy_Access()
    {
        $this->_parseUser();
    }

    /**
     * Parse the requested folder for the owner of that folder.
     *
     * @param string $req_folder The folder requested.
     *
     * @return boolean|PEAR_Error True if successful.
     */
    function parseFolder($req_folder = '')
    {
        /* Load the string library */
        require_once 'Horde/String.php';

        /* Handle the owner/folder name and make sure the owner part is in lower case */
        $req_folder = String::convertCharset($req_folder, 'UTF-8', 'UTF7-IMAP');
        $folder = explode('/', $req_folder);
        if (count($folder) < 2) {
            return PEAR::raiseError(sprintf(_("No such folder %s"), $req_folder));
        }

        $folder[0] = strtolower($folder[0]);
        $req_folder = implode('/', $folder);
        $this->owner = $folder[0];
        unset($folder[0]);
        $this->folder = join('/', $folder);

        $result = $this->_process();
        if (is_a($result, 'PEAR_Error')) {
            return $result;
        }
        return true;
    }

    /**
     * Parse the owner value.
     *
     * @param string $owner The owner that should be processed.
     *
     * @return boolean|PEAR_Error True if successful.
     */
    function parseOwner($owner = '')
    {
        $this->owner = $owner;

        $result = $this->_process();
        if (is_a($result, 'PEAR_Error')) {
            return $result;
        }
        return true;
    }

    /**
     * Fetch remote free/busy user if the current user is not local or
     * redirect to the other server if configured this way.
     *
     * @param boolean $trigger Have we been called for triggering?
     * @param boolean $extended Should the extended information been delivered?
     */
    function fetchRemote($trigger = false, $extended = false)
    {
        global $conf;

        if (!empty($conf['kolab']['freebusy']['server'])) {
            $server = $conf['kolab']['freebusy']['server'];
        } else {
            $server = 'https://localhost/freebusy';
        }
        if (!empty($conf['fb']['redirect'])) {
            $do_redirect = $conf['fb']['redirect'];
        } else {
            $do_redirect = false;
        }

        if ($trigger) {
            $path = sprintf('/trigger/%s/%s.' . ($extended)?'pxfb':'pfb',
                            urlencode($this->owner), urlencode($this->imap_folder));
        } else {
            $path = sprintf('/%s.' . ($extended)?'xfb':'ifb', urlencode($this->owner));
        }

        /* Check if we are on the right server and redirect if appropriate */
        if ($this->freebusyserver && $this->freebusyserver != $server) {
            $redirect = $this->freebusyserver . $path;
            Horde::logMessage(sprintf("URL %s indicates remote free/busy server since we only offer %s. Redirecting.", 
                                      $this->freebusyserver, $server), __FILE__,
                              __LINE__, PEAR_LOG_ERR);
            if ($do_redirect) {
                header("Location: $redirect");
            } else {
                header("X-Redirect-To: $redirect");
                $redirect = 'https://' . urlencode($this->user) . ':' . urlencode(Auth::getCredential('password'))
                    . '@' . $this->freebusyserver . $path;
                if (!@readfile($redirect)) {
                    $message = sprintf(_("Unable to read free/busy information from %s"), 
                                       'https://' . urlencode($this->user) . ':XXX'
                                       . '@' . $this->freebusyserver . $_SERVER['REQUEST_URI']);
                    return PEAR::raiseError($message);
                }
            }
            exit;
        }
    }

    /**
     * Check if we are in an authenticated situation.
     *
     * @return boolean|PEAR_Error True if successful.
     */
    function authenticated()
    {
        global $conf;

        if (empty($this->user)) {
            header('WWW-Authenticate: Basic realm="Kolab Freebusy"');
            return PEAR::raiseError(_("Please authenticate!"));
        }

        if (!$this->_authenticated) {
            return PEAR::raiseError(sprintf(_("Invalid authentication for user %s!"), 
                                            $this->user));
        }
        return true;
    }

    /**
     * Parse the current user accessing the page and try to
     * authenticate the user.
     */
    function _parseUser()
    {
        global $conf;

        $this->user = Auth::getAuth();

        if (empty($this->user)) {
            $this->user = isset($_SERVER['PHP_AUTH_USER'])?$_SERVER['PHP_AUTH_USER']:false;
            $pass = isset($_SERVER['PHP_AUTH_PW'])?$_SERVER['PHP_AUTH_PW']:false;
        } else {
            $this->_authenticated = true;
            return;
        }

        // This part allows you to use the PHP scripts with CGI rather than as
        // an apache module. This will of course slow down things but on the
        // other hand it allows you to reduce the memory footprint of the 
        // apache server. The default is to use PHP as a module and the CGI 
        // version requires specific Apache configuration.
        //
        // The line you need to add to your configuration of the /freebusy 
        // location of your server looks like this:
        //
        //    RewriteRule .* - [E=REMOTE_USER:%{HTTP:Authorization}]
        //
        // The complete section will probably look like this then:
        //
        //  <IfModule mod_rewrite.c>
        //    RewriteEngine On
        //    # FreeBusy list handling
        //    RewriteBase /freebusy
        //    RewriteRule .* - [E=REMOTE_USER:%{HTTP:Authorization}]
        //    RewriteRule ^([^/]+)\.ifb       freebusy.php?uid=$1		    [L]
        //    RewriteRule ^([^/]+)\.vfb       freebusy.php?uid=$1		    [L]
        //    RewriteRule ^([^/]+)\.xfb       freebusy.php?uid=$1&extended=1        [L]
        //    RewriteRule ^trigger/(.+)\.pfb  pfb.php?folder=$1&cache=0             [L]
        //    RewriteRule ^(.+)\.pfb          pfb.php?folder=$1&cache=1             [L]
        //    RewriteRule ^(.+)\.pxfb         pfb.php?folder=$1&cache=1&extended=1  [L]
        //  </IfModule>
        if (empty($this->user) && isset($_ENV['REDIRECT_REDIRECT_REMOTE_USER'])) {
            $a = base64_decode(substr($_ENV['REDIRECT_REDIRECT_REMOTE_USER'], 6)) ;
            if ((strlen($a) != 0) && (strcasecmp($a, ':') == 0)) {
                list($this->user, $pass) = explode(':', $a, 2);
            }
        }

        if (!empty($this->user)) {
            /* Load the authentication libraries */
            require_once 'Horde/Auth.php';
            require_once 'Horde/Secret.php';

            $auth = &Auth::singleton(isset($conf['auth']['driver'])?$conf['auth']['driver']:'kolab');
            if (!$this->_authenticated) {
                $this->_authenticated = $auth->authenticate($this->user, array('password' => $pass), false);
            }
            if ($this->_authenticated) {
                @session_start();
                $_SESSION['__auth'] = array(
                    'authenticated' => true,
                    'userId' => $this->user,
                    'timestamp' => time(),
                    'remote_addr' => isset($_SERVER['REMOTE_ADDR']) ? $_SERVER['REMOTE_ADDR'] : null,
                );
                Auth::setCredential('password', $pass);
            }
        }
    }

    /**
     * Process both the user accessing the page as well as the
     * owner of the requested free/busy information.
     *
     * @return boolean|PEAR_Error True if successful.
     */
    function _process() 
    {
        global $conf;

        require_once 'Horde/Kolab/Server.php';

        /* Connect to the Kolab user database */
        $db = &Horde_Kolab_Server::singleton(array('uid' => $conf['kolab']['ldap']['phpdn']));
        // TODO: Remove once Kolab_Server has been fixed to always return the base dn
        $db->fetch();

        /* Retrieve the server configuration */
        $server = $db->fetch(sprintf('k=kolab,%s',
				     $db->getBaseUid()),
			     KOLAB_OBJECT_SERVER);
        if (is_a($server, 'PEAR_Error')) {
            return $server;
        }
        $this->server_object = $server;

        /* Fetch the user calling us */
        $udn = $db->uidForIdOrMail($this->user);
        if (is_a($udn, 'PEAR_Error')) {
            return $udn;
        }
        if ($udn) {
            $user = $db->fetch($udn, KOLAB_OBJECT_USER);
            if (is_a($user, 'PEAR_Error')) {
                return $user;
            }
            $this->user_object = $user;
        }

        if ($this->user_object && $this->user_object->exists()) {
            $mail = $this->user_object->get(KOLAB_ATTR_MAIL);
            if (is_a($mail, 'PEAR_Error')) {
                return $mail;
            }
            if ($mail) {
                $this->user = $mail;
            }
        }

        /* Fetch the owner of the free/busy data */
        $odn = $db->uidForMailOrIdOrAlias($this->owner);
        if (is_a($odn, 'PEAR_Error')) {
            return $odn;
        }
        if (!$odn) {
            $idx = strpos($this->user, '@');
            if($idx !== false) {
                $domain = substr($this->user, $idx+1);
                Horde::logMessage(sprintf("Trying to append %s to %s", 
                                          $domain, $this->owner),
                                  __FILE__, __LINE__, PEAR_LOG_DEBUG);
                $odn = $odn = $db->uidForIdOrMail($this->owner . '@' . $domain);
            }
        }

        if ($odn) {
            $owner = $db->fetch($odn, KOLAB_OBJECT_USER);
            if (is_a($owner, 'PEAR_Error')) {
                return $owner;
            }
            $this->owner_object = &$owner;
        }

        if (!empty($this->owner_object)) {
            if ($this->owner_object->exists()) {
                $this->owner = $this->owner_object->get(KOLAB_ATTR_MAIL);

                $freebusyserver = $this->owner_object->getServer('freebusy');
                if (!is_a($freebusyserver, 'PEAR_Error')) {
                    $this->freebusyserver = $freebusyserver;
                }
            }
        } else {
            return PEAR::raiseError(_("Unable to determine owner of the free/busy data!"));
        }

        /* Mangle the folder request into an IMAP folder name */
        $this->imap_folder = $this->_getImapFolder();

        return true;
    }

    /**
     * Calculate the correct IMAP folder name to access based on the
     * combination of user and owner.
     *
     * @return string The IMAP folder we should access.
     */
    function _getImapFolder() 
    {
        $userdom = false;
        $ownerdom = false;
        if (ereg( '(.*)@(.*)', $this->user, $regs)) {
            // Regular user
            $user = $regs[1];
            $userdom  = $regs[2];
        } else {
            $user = $this->user;
        }

        if(ereg( '(.*)@(.*)', $this->owner, $regs)) {
            // Regular owner
            $owner = $regs[1];
            $ownerdom = $regs[2];
        } else {
            $owner = $this->owner;
        }

        $fldrcomp = array();
        if ($user == $owner) {
            $fldrcomp[] = 'INBOX';
        } else {
            $fldrcomp[] = 'user';
            $fldrcomp[] = $owner;
        }

        if (!empty($this->folder)) {
            $fldrcomp[] = $this->folder;
        }

        $folder = join('/', $fldrcomp);
        if ($ownerdom && !$userdom) {
            $folder .= '@' . $ownerdom;
        }
        return $folder;
    }

}

