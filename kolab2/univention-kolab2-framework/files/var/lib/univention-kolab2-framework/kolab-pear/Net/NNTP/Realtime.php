<?php
// +-----------------------------------------------------------------------+
// |                                                                       |
// | Copyright © 2003 Heino H. Gehlsen. All Rights Reserved.               |
// |                  http://www.heino.gehlsen.dk/software/license         |
// |                                                                       |
// +-----------------------------------------------------------------------+
// |                                                                       |
// | This work (including software, documents, or other related items) is  |
// | being provided by the copyright holders under the following license.  |
// | By obtaining, using and/or copying this work, you (the licensee)      |
// | agree that you have read, understood, and will comply with the        |
// | following terms and conditions:                                       |
// |                                                                       |
// | Permission to use, copy, modify, and distribute this software and     |
// | its documentation, with or without modification, for any purpose and  |
// | without fee or royalty is hereby granted, provided that you include   |
// | the following on ALL copies of the software and documentation or      |
// | portions thereof, including modifications, that you make:             |
// |                                                                       |
// | 1. The full text of this NOTICE in a location viewable to users of    |
// |    the redistributed or derivative work.                              |
// |                                                                       |
// | 2. Any pre-existing intellectual property disclaimers, notices, or    |
// |    terms and conditions. If none exist, a short notice of the         |
// |    following form (hypertext is preferred, text is permitted) should  |
// |    be used within the body of any redistributed or derivative code:   |
// |    "Copyright © 2003 Heino H. Gehlsen. All Rights Reserved.           |
// |     http://www.heino.gehlsen.dk/software/license"                     |
// |                                                                       |
// | 3. Notice of any changes or modifications to the files, including     |
// |    the date changes were made. (We recommend you provide URIs to      |
// |    the location from which the code is derived.)                      |
// |                                                                       |
// | THIS SOFTWARE AND DOCUMENTATION IS PROVIDED "AS IS," AND COPYRIGHT    |
// | HOLDERS MAKE NO REPRESENTATIONS OR WARRANTIES, EXPRESS OR IMPLIED,    |
// | INCLUDING BUT NOT LIMITED TO, WARRANTIES OF MERCHANTABILITY OR        |
// | FITNESS FOR ANY PARTICULAR PURPOSE OR THAT THE USE OF THE SOFTWARE    |
// | OR DOCUMENTATION WILL NOT INFRINGE ANY THIRD PARTY PATENTS,           |
// | COPYRIGHTS, TRADEMARKS OR OTHER RIGHTS.                               |
// |                                                                       |
// | COPYRIGHT HOLDERS WILL NOT BE LIABLE FOR ANY DIRECT, INDIRECT,        |
// | SPECIAL OR CONSEQUENTIAL DAMAGES ARISING OUT OF ANY USE OF THE        |
// | SOFTWARE OR DOCUMENTATION.                                            |
// |                                                                       |
// | The name and trademarks of copyright holders may NOT be used in       |
// | advertising or publicity pertaining to the software without specific, |
// | written prior permission. Title to copyright in this software and any |
// | associated documentation will at all times remain with copyright      |
// | holders.                                                              |
// |                                                                       |
// +-----------------------------------------------------------------------+
// |                                                                       |
// | This license is based on the "W3C® SOFTWARE NOTICE AND LICENSE".      |
// | No changes have been made to the "W3C® SOFTWARE NOTICE AND LICENSE",  |
// | except for the references to the copyright holder, which has either   |
// | been changes or removed.                                              |
// |                                                                       |
// +-----------------------------------------------------------------------+
// $Id: Realtime.php,v 1.1.2.1 2005/10/05 14:39:47 steuwer Exp $

require_once 'Net/NNTP/Protocol.php';
require_once 'Net/NNTP/Header.php';
require_once 'Net/NNTP/Message.php';


/* NNTP Authentication modes */
define('NET_NNTP_AUTHORIGINAL', 'original');
define('NET_NNTP_AUTHSIMPLE',   'simple');
define('NET_NNTP_AUTHGENERIC',  'generic');

/**
 * The Net_NNTP_Realtime class is a frontend class to the 
 * Net_NNTP_Protocol class. It does everything in realtime...
 *
 * @author Heino H. Gehlsen <heino@gehlsen.dk>
 */
class Net_NNTP_Realtime extends Net_NNTP_Protocol
{
    // {{{ properties

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
    function Net_NNTP_Realtime()
    {
	parent::Net_NNTP_Protocol();
    }

    // }}}
    // {{{ connect()

    /**
     * Connect to the NNTP-server.
     *
     * @param optional string $host The adress of the NNTP-server to connect to.
     * @param optional int $port The port to connect to.
     *
     * @return mixed (bool) true on success or (object) pear_error on failure
     * @access public
     * @see Net_NNTP::quit()
     * @see Net_NNTP::authenticate()
     * @see Net_NNTP::connectAuthenticated()
     */
    function connect($host = NET_NNTP_PROTOCOL_DEFAULT_HOST,
                     $port = NET_NNTP_PROTOCOL_DEFAULT_PORT)
    {
	return parent::connect($host, $port);
    }

    // }}}
    // {{{ connectAuthenticated()

    /**
     * Connect to the NNTP-server, and authenticate using given username and password.
     *
     * @param optional string $user The username.
     * @param optional string $pass The password.
     * @param optional string $host The IP-address of the NNTP-server to connect to.
     * @param optional int $port The port to connect to.
     * @param optional string $authmode The authentication mode.
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
	$R = $this->connect($host, $port);
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
    // {{{ authenticate()

    /**
     * Authenticate
     * 
     * Auth process (not yet standarized but used any way)
     * http://www.mibsoftware.com/userkt/nntpext/index.html
     *
     * @param string $user The username
     * @param optional string $pass The password
     * @param optional string $mode The authentication mode (original, simple, generic).
     *
     * @return mixed (bool) true on success or (object) pear_error on failure
     * @access public
     * @see Net_NNTP::connect()
     * @see Net_NNTP::connectAuthenticated()
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
     * Test whether a connection is currently open.
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
     * Selects a newsgroup
     *
     * @param string $newsgroup Newsgroup name
     *
     * @return mixed (array) Info about the newsgroup on success or (object) pear_error on failure
     * @access public
     * @see Net_NNTP::group()
     * @see Net_NNTP::first()
     * @see Net_NNTP::last()
     * @see Net_NNTP::count()
     * @see Net_NNTP::getGroups()
     */
    function selectGroup($newsgroup)
    {
        $response_arr = $this->cmdGroup($newsgroup);
    	if (PEAR::isError($response_arr)) {
	    return $response_arr;
	}

	// Store group info in the object
	$this->_currentGroup = $response_arr;

	return $response_arr;
    }

    // }}}
    // {{{ getGroups()

    /**
     * Fetches a list of all avaible newsgroups
     *
     * @return mixed (array) nested array with informations about existing newsgroups on success or (object) pear_error on failure
     * @access public
     * @see Net_NNTP::selectGroup()
     * @see Net_NNTP::getDescriptions()
     */
    function getGroups()
    {
	// Get groups
	$groups = $this->cmdList();
	if (PEAR::isError($groups)) {
	    return $groups;
	}

	return $groups;
    }

    // }}}
    // {{{ getDescriptions()

    /**
     * Fetches a list of all avaible newsgroup descriptions.
     *
     * @return mixed (array) nested array with description of existing newsgroups on success or (object) pear_error on failure
     * @access public
     * @see Net_NNTP::getGroups()
     */
    function getDescriptions()
    {

	// Get group descriptions
	$descriptions = $this->cmdListNewsgroups();
	if (PEAR::isError($descriptions)) {
	    return $descriptions;
	}
	
	return $descriptions;
    }

    // }}}
    // {{{ getOverview()

    /**
     * Fetch message header fields from message number $first to $last
     *
     * The format of the returned array is:
     * $messages[message_id][header_name]
     *
     * @param integer $first first article to fetch
     * @param integer $last  last article to fetch
     *
     * @return mixed (array) nested array of message and their headers on success or (object) pear_error on failure
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
    // {{{ getOverviewFmt()

    /**
     * Returns a list of avaible headers which are send from NNTP-server to the client for every news message
     *
     * @return mixed (array) header names on success or (object) pear_error on failure
     * @access public
     * @see Net_NNTP::getOverview()
     */
    function getOverviewFormat()
    {
	return $this->cmdListOverviewFmt();
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
     * "NNTP-Posting-Host: <ip-of-author>", which should contain the IP-address
     * of the author of the post, so the message can be traced back to him.
     * Or "Organization: <org>" which contain the name of the organization
     * the post originates from)
     *
     * @param string $newsgroups The newsgroup to post to.
     * @param string $subject The subject of the post.
     * @param string $body The body of the post itself.
     * @param string $from Name + email-adress of sender.
     * @param optional string $aditional Aditional headers to send.
     *
     * @return mixed (string) server response on success or (object) pear_error on failure
     * @access public
     */
    function post($newsgroups, $subject, $body, $from, $aditional = '')
    {
	return $this->cmdPost($newsgroups, $subject, $body, $from, $aditional);
    }

    // }}}
    // {{{ getArticle()

    /**
     * Get an article
     *
     * The v0.2 version of the this function (which returned the article as a string) has been renamed to getArticleRaw().
     *
     * @param mixed $article Either the message-id or the message-number on the server of the article to fetch.
     *
     * @return mixed (object) message object on success or (object) pear_error on failure
     * @access public
     * @see Net_NNTP::getArticleRaw()
     * @see Net_NNTP::getHeader()
     * @see Net_NNTP::getBody()
     */
    function getArticle($article)
    {
        $message = $this->getArticleRaw($article, false);
        if (PEAR::isError($message)) {
	    return $data;
	}
	
	$M = Net_NNTP_Message::create($message);
	
	return $M;
    }

    // }}}
    // {{{ getArticleRaw()

    /**
     * Get a article (raw data)
     *
     * @param mixed $article Either the message-id or the message-number on the server of the article to fetch.
     * @param optional bool  $implode When true the result array is imploded to a string, defaults to false.
     *
     * @return mixed (array/string) The article on success or (object) pear_error on failure
     * @access public
     * @see Net_NNTP::getArticle()
     * @see Net_NNTP::getHeaderRaw()
     * @see Net_NNTP::getBodyRaw()
     */
    function getArticleRaw($article, $implode = false)
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
    // {{{ getHeader()

    /**
     * Get the header of an article
     *
     * @param mixed $article Either the (string) message-id or the (int) message-number on the server of the article to fetch.
     *
     * @return mixed (object) header object on success or (object) pear_error on failure
     * @access public
     * @see Net_NNTP::getHeaderRaw()
     * @see Net_NNTP::getArticle()
     * @see Net_NNTP::getBody()
     */
    function getHeader($article)
    {
        $header = $this->getHeaderRaw($article, false);
        if (PEAR::isError($header)) {
	    return $header;
	}

	$H = Net_NNTP_Header::create($header);

	return $H;
    }

    // }}}
    // {{{ getHeaderRaw()

    /**
     * Get the header of an article (raw data)
     *
     * @param mixed $article Either the (string) message-id or the (int) message-number on the server of the article to fetch.
     * @param optional bool $implode When true the result array is imploded to a string, defaults to false.
     *
     * @return mixed (array/string) header fields on success or (object) pear_error on failure
     * @access public
     * @see Net_NNTP::getHeader()
     * @see Net_NNTP::getArticleRaw()
     * @see Net_NNTP::getBodyRaw()
     */
    function getHeaderRaw($article, $implode = false)
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
    // {{{ getBody()

	// Not written yet...

    // }}}
    // {{{ getBodyRaw()

    /**
     * Get the body of an article (raw data)
     *
     * @param mixed $article Either the message-id or the message-number on the server of the article to fetch.
     * @param optional bool $implode When true the result array is imploded to a string, defaults to false.
     *
     * @return mixed (array/string) body on success or (object) pear_error on failure
     * @access public
     * @see Net_NNTP::getBody()
     * @see Net_NNTP::getHeaderRaw()
     * @see Net_NNTP::getArticleRaw()
     */
    function getBodyRaw($article, $implode = false)
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
	        return PEAR::throwError('UPS...');
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
    // {{{ count()

    /**
     * Number of articles in currently selected group
     *
     * @return integer number of article in group
     * @access public
     * @since 0.3
     * @see Net_NNTP::group()
     * @see Net_NNTP::first()
     * @see Net_NNTP::last()
     * @see Net_NNTP::selectGroup()
     */
    function count()
    {
        return $this->_currentGroup['count'];
    }

    // }}}
    // {{{ last()

    /**
     * Maximum article number in currently selected group
     *
     * @return integer number of last article
     * @access public
     * @since 0.3
     * @see Net_NNTP::first()
     * @see Net_NNTP::group()
     * @see Net_NNTP::count()
     * @see Net_NNTP::selectGroup()
     */
    function last()
    {
	return $this->_currentGroup['last'];
    }

    // }}}
    // {{{ first()

    /**
     * Minimum article number in currently selected group
     *
     * @return integer number of first article
     * @access public
     * @since 0.3
     * @see Net_NNTP::last()
     * @see Net_NNTP::group()
     * @see Net_NNTP::count()
     * @see Net_NNTP::selectGroup()
     */
    function first()
    {
	return $this->_currentGroup['first'];
    }

    // }}}
    // {{{ group()

    /**
     * Currently selected group
     *
     * @return string group name
     * @access public
     * @since 0.3
     * @see Net_NNTP::first()
     * @see Net_NNTP::last()
     * @see Net_NNTP::count()
     * @see Net_NNTP::selectGroup()
     */
    function group()
    {
	return $this->_currentGroup['group'];
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
