<?php
//
// +----------------------------------------------------------------------+
// | PHP Version 4                                                        |
// +----------------------------------------------------------------------+
// | Copyright (c) 1997-2003 The PHP Group                                |
// +----------------------------------------------------------------------+
// | This source file is subject to version 2.0 of the PHP license,       |
// | that is bundled with this package in the file LICENSE, and is        |
// | available at through the world-wide-web at                           |
// | http://www.php.net/license/2_02.txt.                                 |
// | If you did not receive a copy of the PHP license and are unable to   |
// | obtain it through the world-wide-web, please send a note to          |
// | license@php.net so we can mail you a copy immediately.               |
// +----------------------------------------------------------------------+
// | Authors: Martin Kaltoft   <martin@nitro.dk>                          |
// |          Tomas V.V.Cox    <cox@idecnet.com>                          |
// |          Heino H. Gehlsen <heino@gehlsen.dk>                         |
// +----------------------------------------------------------------------+
//
// $Id: NNTP.php,v 1.1.2.1 2005/09/29 08:06:03 steuwer Exp $

require_once 'Net/NNTP/Protocol.php';


/* NNTP Authentication modes */
define('NET_NNTP_AUTHORIGINAL', 'original');
define('NET_NNTP_AUTHSIMPLE',   'simple');
define('NET_NNTP_AUTHGENERIC',  'generic');
 
// Deprecated due to naming
define('PEAR_NNTP_AUTHORIGINAL', NET_NNTP_AUTHORIGINAL);
define('PEAR_NNTP_AUTHSIMPLE',   NET_NNTP_AUTHSIMPLE);
define('PEAR_NNTP_AUTHGENERIC',  NET_NNTP_AUTHGENERIC);


/**
 * The Net_NNTP class is an almost 100 % backward compatible 
 * frontend class to the Net_NNTP_Protocol class.
 * 
 * ATTENTION!!!
 * This class should NOT be used in new projects. It is meant
 * as a drop in replacement to the outdated v0.2, and uses 
 * excatly the same protocol implementation as the new 
 * Net_NNTP_Realtime class, but has a lot of deprecated 
 * methods etc. While this class is still maintained, it is
 * officially dead...
 *
 * @author Martin Kaltoft   <martin@nitro.dk>
 * @author Tomas V.V.Cox    <cox@idecnet.com>
 * @author Heino H. Gehlsen <heino@gehlsen.dk>
 */

class Net_NNTP extends Net_NNTP_Protocol
{
    // {{{ properties

    /**
     * @var int
     * @access public
     * @deprecated use last() instead
     */
    var $max;

    /**
     * @var int
     * @access public
     * @deprecated use first() instead
     */
    var $min;

    /**
     * Used for storing information about the currently selected group
     *
     * @var array
     * @access private
     * @since 0.3
     */
    var $_currentGroup = null;

    // }}}
    // {{{ constructor

    /**
     * Constructor
     */
    function Net_NNTP()
    {
	parent::Net_NNTP_Protocol();
    }

    // }}}
    // {{{ connect()

    /**
     * Connect to the newsserver.
     *
     * The function currently allows automatic authentication via the three last parameters, 
     * but this feature is to be considered depresated (use connectAuthenticated instead)
     *
     * In the future, this function will just be inherrited from the parent,
     * and thus the last three parameters will no longer be used to authenticate.
     *
     * @param optional string $host The adress of the NNTP-server to connect to.
     * @param optional int $port The port to connect to.
     * @param optional string $user Deprecated!
     * @param optional string $pass Deprecated!
     * @param optional string $authmode Deprecated!
     *
     * @return mixed (bool) true on success or (object) pear_error on failure
     * @access public
     * @see Net_NNTP::quit()
     * @see Net_NNTP::connectAuthenticated()
     * @see Net_NNTP::authenticate()
     */
    function connect($host = NET_NNTP_PROTOCOL_DEFAULT_HOST,
                     $port = NET_NNTP_PROTOCOL_DEFAULT_PORT,
                     $user = null,
                     $pass = null,
                     $authmode = NET_NNTP_AUTHORIGINAL)
    {
	// Currently this function just 'forwards' to connectAuthenticated().
	return $this->connectAuthenticated($user, $pass, $host, $port, $authmode);
    }


    // }}}
    // {{{ connectAuthenticated()

    /**
     * Connect to the newsserver, and authenticate. If no user/pass is specified, just connect.
     *
     * @param optional string $user The user name to authenticate with
     * @param optional string $pass The password
     * @param optional string $host The adress of the NNTP-server to connect to.
     * @param optional int $port The port to connect to.
     * @param optional string $authmode The authentication mode
     *
     * @return mixed (bool) true on success or (object) pear_error on failure
     * @access public
     * @since 0.3
     * @see Net_NNTP::connect()
     * @see Net_NNTP::authenticate()
     * @see Net_NNTP::quit()
     */
    function connectAuthenticated($user = null,
            			  $pass = null,
            			  $host = NET_NNTP_PROTOCOL_DEFAULT_HOST,
                		  $port = NET_NNTP_PROTOCOL_DEFAULT_PORT,
                		  $authmode = NET_NNTP_AUTHORIGINAL)
    {
	// Until connect() is changed, connect() is called directly from the parent...
	$R = parent::connect($host, $port);
	if (PEAR::isError($R)) {
	    return $R;
	}

	// Authenticate if username is given
	if ($user != null) {
    	    $R = $this->authenticate($user, $pass, $authmode);
    	    if (PEAR::isError($R)) {
    		return $R;
    	    }
	}

        return true;
    }

    // }}}
    // {{{ quit()

    /**
     * Close connection to the newsserver
     *
     * @access public
     * @see Net_NNTP::connect()
     */
    function quit()
    {
        return $this->cmdQuit();
    }

    // }}}
    // {{{ prepareConnection()

    /**
     * Connect to the newsserver, and issue a GROUP command
     * Once connection is prepared, we can only fetch articles from one group
     * at a time, to fetch from another group, a new connection has to be made.
     *
     * This is to avoid the GROUP command for every article, as it is very
     * ressource intensive on the newsserver especially when used for
     * groups with many articles.
     *
     * @param string $host The adress of the NNTP-server to connect to.
     * @param optional int $port the port-number to connect to, defaults to 119.
     * @param string $newsgroup The name of the newsgroup to use.
     * @param optional string $user The user name to authenticate with
     * @param optional string $pass The password
     * @param optional string $authmode The authentication mode
     *
     * @return mixed (bool) true on success or (object) pear_error on failure
     * @access public
     *
     * @deprecated Use connect() or connectAuthenticated() instead
     */
    function prepareConnection($host,
                                $port = 119,
                                $newsgroup,
                                $user = null,
                                $pass = null,
                                $authmode = NET_NNTP_AUTHORIGINAL)
    {
        /* connect to the server */
        $R = $this->connect($host, $port, $user, $pass, $authmode);
        if ($this->isError($R)) {
            return $R;
        }

        /* issue a GROUP command */
        $R = $this->selectGroup($newsgroup);
        if ($this->isError($R)) {
            return $R;
        }

        return true;
    }

    // }}}
    // {{{ authenticate()

    /**
     * Auth process (not yet standarized but used any way)
     * http://www.mibsoftware.com/userkt/nntpext/index.html
     *
     * @param string $user The user name
     * @param optional string $pass The password if needed
     * @param optional string $mode Authinfo type: original, simple, generic
     *
     * @return mixed (bool) true on success or (object) pear_error on failure
     * @access public
     * @since 0.3
     * @see Net_NNTP::connect()
     */
    function authenticate($user, $pass, $mode = NET_NNTP_AUTHORIGINAL)
    {
        // Username is a must...
        if ($user == null) {
            return $this->throwError('No username supplied', null);
        }

        // Use selected authentication method
        switch ($mode) {
            case NET_NNTP_AUTHORIGINAL:
                return $this->cmdAuthinfo($user, $pass);
                break;
            case NET_NNTP_AUTHSIMPLE:
                return $this->cmdAuthinfoSimple($user, $pass);
                break;
            case NET_NNTP_AUTHGENERIC:
                return $this->cmdAuthinfoGeneric($user, $pass);
                break;
            default:
                return $this->throwError("The auth mode: '$mode' is unknown", null);
        }
    }

    // }}}
    // {{{ isConnected()

    /**
     * Test whether we are connected or not.
     *
     * @return bool true or false
     * @access public
     * @see Net_NNTP::connect()
     * @see Net_NNTP::quit()
     */
    function isConnected()
    {
        return parent::isConnected();
    }

    // }}}
    // {{{ selectGroup()

    /**
     * Selects a news group (issue a GROUP command to the server)
     *
     * @param string $newsgroup The newsgroup name
     *
     * @return mixed (array) Groups info on success or (object) pear_error on failure
     * @access public
     * @see group()
     * @see count()
     * @see first()
     * @see last()
     */
    function selectGroup($newsgroup)
    {
        $response_arr = $this->cmdGroup($newsgroup);
    	if (PEAR::isError($response_arr)) {
	    return $response_arr;
	}

	$this->_currentGroup = $response_arr;

	// Deprecated / historical				  	
	$response_arr['min'] =& $response_arr['first'];
	$response_arr['max'] =& $response_arr['last'];
	$this->min =& $response_arr['min'];
	$this->max =& $response_arr['max'];

	return $response_arr;
    }

    // }}}
    // {{{ getGroups()

    /**
     * Fetches a list of all avaible newsgroups
     *
     * @return mixed (array) nested array with informations about existing newsgroups on success or (object) pear_error on failure
     * @access public
     */
    function getGroups()
    {
	// Get groups
	$groups = $this->cmdList();
	if (PEAR::isError($groups)) {
	    return $groups;
	}

	// Deprecated / historical
	foreach (array_keys($groups) as $k) {
    	    $groups[$k]['posting_allowed'] =& $groups[$k][3];
	}

	// Get group descriptions
	$descriptions = $this->cmdListNewsgroups();
	if (PEAR::isError($descriptions)) {
	    return $descriptions;
	}
	
	// Set known descriptions for groups
	if (count($descriptions) > 0) {
    	    foreach ($descriptions as $k=>$v) {
		$groups[$k]['desc'] = $v;
	    }
	}

	return $groups;
    }

    // }}}
    // {{{ getOverview()

    /**
     * Fetch message header from message number $first to $last
     *
     * The format of the returned array is:
     * $messages[message_id][header_name]
     *
     * @param integer $first first article to fetch
     * @param integer $last  last article to fetch
     *
     * @return mixed (array) nested array of message and there headers on success or (object) pear_error on failure
     * @access public
     * @see Net_NNTP::getOverviewFormat()
     * @see Net_NNTP::getReferencesOverview()
     */
    function getOverview($first, $last)
    {
	$overview = $this->cmdXOver($first, $last);
	if (PEAR::isError($overview)) {
	    return $overview;
	}

	return $overview;
    }

    // }}}
    // {{{ getOverviewFormat()

    /**
     * Returns a list of avaible headers which are send from newsserver to client for every news message
     *
     * @return mixed (array) header names on success or (object) pear_error on failure
     * @access public
     * @see Net_NNTP::getOverview()
     */
    function getOverviewFormat()
    {
	return $this->cmdListOverviewFMT();
    }

    // }}}
    // {{{ getOverviewFmt()

    /**
     * Returns a list of avaible headers which are send from newsserver to client for every news message
     *
     * @return mixed (array) header names on success or (object) pear_error on failure
     * @access public
     * @deprecated use getOverviewFormat() instead
     */
    function getOverviewFmt()
    {
	return $this->getOverviewFormat();
    }

    // }}}
    // {{{ getReferencesOverview()

    /**
     * Fetch a list of each message's reference header.
     *
     * @param integer $first first article to fetch
     * @param integer $last  last article to fetch
     *
     * @return mixed (array) nested array of references on success or (object) pear_error on failure
     *
     * @return mixed (array) nested array of message and there headers on success or (object) pear_error on failure
     * @access public
     * @see Net_NNTP::getOverview()
     */
    function getReferencesOverview($first, $last)
    {
	$overview = $this->cmdXROver($first, $last);
	if (PEAR::isError($overview)) {
	    return $overview;
	}
	
	return $overview;
    }

    // }}}
    // {{{ post()

    /**
     * Post an article to a number of newsgroups.
     *
     * (Among the aditional headers you might think of adding could be:
     * "NNTP-Posting-Host: <ip-of-author>", which should contain the IP-adress
     * of the author of the post, so the message can be traced back to him.
     * Or "Organization: <org>" which contain the name of the organization
     * the post originates from)
     *
     * @param string $subject The subject of the post.
     * @param string $newsgroup The newsgroup to post to.
     * @param string $from Name + email-adress of sender.
     * @param string $body The body of the post itself.
     * @param optional string $aditional Aditional headers to send.
     *
     * @return mixed (string) server response on success or (object) pear_error on failure
     * @access public
     */
    function post($subject, $newsgroup, $from, $body, $aditional = '')
    {
	return $this->cmdPost($newsgroup, $subject, $body, $from, $aditional);
    }

    // }}}
    // {{{ getArticleRaw()

    /**
     * Get an article (raw data)
     *
     * @param mixed $article Either the message-id or the message-number on the server of the article to fetch.
     * @param bool  $implode When true the result array is imploded to a string, defaults to true.
     *
     * @return mixed (array/string) The headers on success or (object) pear_error on failure
     * @access public
     * @since 0.3
     * @see getHeaderRaw()
     * @see getBodyRaw()
     */
    function getArticleRaw($article, $implode = true)
    {
        $data = $this->cmdArticle($article);
        if (PEAR::isError($data)) {
	    return $data;
	}
	if ($implode == true) {
	    $data = implode("\r\n", $data);
	}
	return $data;
    }

    // }}}
    // {{{ getArticle()

    /**
     * Get an article (deprecated)
     *
     * @param mixed $article Either the message-id or the message-number on the server of the article to fetch.
     *
     * @return mixed (string) The headers on success or (object) pear_error on failure
     * @access public
     * @deprecated Use getArticleRaw() instead
     */
    function getArticle($article)
    {
	return $this->getArticleRaw($article);
    }

    // }}}
    // {{{ getHeaderRaw()

    /**
     * Get the headers of an article (raw data)
     *
     * @param mixed $article Either the (string) message-id or the (int) message-number on the server of the article to fetch.
     * @param bool  $implode When true the result array is imploded to a string, defaults to true.
     *
     * @return mixed (array/string) headers on success or (object) pear_error on failure
     * @access public
     * @since 0.3
     * @see getArticleRaw()
     * @see getBodyRaw()
     */
    function getHeaderRaw($article, $implode = true)
    {
        $data = $this->cmdHead($article);
        if (PEAR::isError($data)) {
	    return $data;
	}
	if ($implode == true) {
	    $data = implode("\r\n", $data);
	}
	return $data;
    }

    // }}}
    // {{{ getHeaders()

    /**
     * Get the headers of an article (deprecated)
     *
     * @param mixed $article Either the (string) message-id or the (int) message-number on the server of the article to fetch.
     *
     * @return mixed (string) headers on success or (object) pear_error on failure
     * @access public
     * @deprecated Use getHeaderRaw() instead
     */
    function getHeaders($article)
    {
        return $this->getHeaderRaw($article);
    }

    // }}}
    // {{{ getBodyRaw()

    /**
     * Get the body of an article (raw data)
     *
     * @param mixed $article Either the message-id or the message-number on the server of the article to fetch.
     * @param bool  $implode When true the result array is imploded to a string, defaults to true.
     *
     * @return mixed (array/string) headers on success or (object) pear_error on failure
     * @access public
     * @since 0.3
     * @see getHeaderRaw()
     * @see getArticleRaw()
     */
    function getBodyRaw($article, $implode = true)
    {
        $data = $this->cmdBody($article);
        if (PEAR::isError($data)) {
	    return $data;
	}
	if ($implode == true) {
	    $data = implode("\r\n", $data);
	}
	return $data;
    }

    // }}}
    // {{{ getBody()

    /**
     * Get the body of an article (deprecated)
     *
     * @param mixed $article Either the message-id or the message-number on the server of the article to fetch.
     *
     * @return mixed (string) headers on success or (object) pear_error on failure
     * @access public
     * @deprecated Use getBodyRaw() instead
     */
    function getBody($article)
    {
	return $this->getBodyRaw($article);
    }

    // }}}
    // {{{ getGroupArticles()

    /**
     * Experimental
     *
     * @access public
     * @since 0.3
     */
    function getGroupArticles($newsgroup)
    {
        return $this->cmdListgroup($newsgroup);
    }

    // }}}
    // {{{ getNewGroups()

    /**
     * Experimental
     *
     * @access public
     * @since 0.3
     */
    function getNewGroups($time)
    {
	switch (gettype($time)) {
	    case 'integer':
		break;
	    case 'string':
		$time = (int) strtotime($time);
		break;
	    default:
	        return $this->throwError('');
	}

	return $this->cmdNewgroups($time);
    }

    // }}}
    // {{{ getNewNews()

    /**
     * Experimental
     *
     * @access public
     * @since 0.3
     */
    function getNewNews($time, $newsgroups = '*')
    {
	switch (gettype($time)) {
	    case 'integer':
		break;
	    case 'string':
		$time = (int) strtotime($time);
		break;
	    default:
	        return $this->throwError('UPS...');
	}

	return $this->cmdNewnews($time, $newsgroups);
    }

    // }}}
    // {{{ getDate()

    /**
     * Get the NNTP-server's internal date
     *
     * Get the date from the newsserver format of returned date:
     *
     * @param optional int $format
     *  - 0: $date - timestamp
     *  - 1: $date['y'] - year
     *       $date['m'] - month
     *       $date['d'] - day
     *
     * @return mixed (mixed) date on success or (object) pear_error on failure
     * @access public
     * @since 0.3
     */
    function getDate($format = 1)
    {
        $date = $this->cmdDate();
        if (PEAR::isError($date)) {
	    return $date;
	}

	switch ($format) {
	    case 1:
	        return array('y' => substr($date, 0, 4), 'm' => substr($date, 4, 2), 'd' => substr($date, 6, 2));
	        break;

	    case 0:
	    default:
	        return $date;
	        break;
	}
    }

    // }}}
    // {{{ date()

    /**
     * @return mixed (array) date on success or (object) pear_error on failure
     * @access public
     *
     * @deprecated Use getDate() instead
     */
    function date()
    {
        return $this->getDate();
    }

    // }}}
    // {{{ count()

    /**
     * Number of articles in currently selected group
     *
     * @return integer count
     * @access public
     * @since 0.3
     * @see Net_NNTP::selectGroup()
     * @see Net_NNTP::group()
     * @see Net_NNTP::first()
     * @see Net_NNTP::last()
     */
    function count()
    {
        return $this->_currentGroup['count'];

    }

    // }}}
    // {{{ last()

    /**
     * Maximum article number in current group
     *
     * @return integer maximum
     * @access public
     * @since 0.3
     * @see Net_NNTP::selectGroup()
     * @see Net_NNTP::group()
     * @see Net_NNTP::first()
     * @see Net_NNTP::count()
     */
    function last()
    {
	return $this->_currentGroup['last'];
    }

    // }}}
    // {{{ max()

    /**
     * @return integer maximum
     * @access public
     *
     * @deprecated Use last() instead
     */
    function max()
    {
        return $this->last();
    }

    // }}}
    // {{{ first()

    /**
     * Minimum article number in current group
     *
     * @return integer minimum
     * @access public
     * @since 0.3
     * @see Net_NNTP::selectGroup()
     * @see Net_NNTP::group()
     * @see Net_NNTP::last()
     * @see Net_NNTP::count()
     */
    function first()
    {
	return $this->_currentGroup['first'];
    }

    // }}}
    // {{{ min()

    /**
     * @return integer minimum
     * @access public
     *
     * @deprecated Use first() instead
     */
    function min()
    {
        return $this->first();
    }

    // }}}
    // {{{ group()

    /**
     * Currently selected group
     *
     * @return string group
     * @access public
     * @since 0.3
     * @see Net_NNTP::selectGroup()
     * @see Net_NNTP::first()
     * @see Net_NNTP::last()
     * @see Net_NNTP::count()
     */
    function group()
    {
	return $this->_currentGroup['group'];
    }

    // }}}
    // {{{ splitHeaders()

    /**
     * Get the headers of an article from the currently open connection, and parse them into a keyed array.
     *
     * @param mixed $article Either the (string) message-id or the (int) message-number on the server of the article to fetch.
     *
     * @return mixed (array) Assoc array with headers names as key on success or (object) pear_error on failure
     * @access public
     */
    function splitHeaders($article)
    {
	// Retrieve headers
        $headers = $this->getHeaderRaw($article, false);
        if (PEAR::isError($headers)) {
            return $this->throwError($headers);
        }
	
	$return = array();

	// Loop through all header field lines
        foreach ($headers as $field) {
	    // Separate header name and value
	    if (!preg_match('/([\S]+)\:\s*(.*)\s*/', $field, $matches)) {
		// Fail...
	    }
	    $name = $matches[1];
	    $value = $matches[2];
	    unset($matches);

	    // Add header to $return array
    	    if (isset($return[$name]) AND is_array($return[$name])) {
		// The header name has already been used at least two times.
            	$return[$name][] = $value;
            } elseif (isset($return[$name])) {
		// The header name has already been used one time -> change to nedted values.
            	$return[$name] = array($return[$name], $value);
            } else {
		// The header name has not used until now.
        	$return[$name] = $value;
            }
        }

	return $return;
    }

    // }}}
    // {{{ responseCode()

    /**
     * returns the response code of a newsserver command
     *
     * @param string $response newsserver answer
     *
     * @return integer response code
     * @access public
     *
     * @deprecated
     */
    function responseCode($response)
    {
        $parts = explode(' ', ltrim($response), 2);
        return (int) $parts[0];
    }

    // }}}
    // {{{ _getData()

    /**
     * Get data until a line with only a '.' in it is read and return data.
     *
     * @return mixed (string) data on success or (object) pear_error on failure
     * @access private
     *
     * @deprecated Use _getTextResponse() instead
     */
    function _getData()
    {
	return $this->_getTextResponse();
    }

    // }}}
    // {{{ command()

    /**
     * Issue a command to the NNTP server
     *
     * @param string $cmd The command to launch, ie: "ARTICLE 1004853"
     *
     * @return mixed (int) response code on success or (object) pear_error on failure
     * @access public
     */
    function command($cmd)
    {
        return $this->_sendCommand($cmd);
    }

    // }}}

}
?>
