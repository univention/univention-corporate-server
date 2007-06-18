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
// $Id: Protocol.php,v 1.1.2.1 2005/09/29 08:06:03 steuwer Exp $

require_once 'PEAR.php';
require_once 'Net/Socket.php';


define('NET_NNTP_PROTOCOL_DEFAULT_HOST', 'localhost');
define('NET_NNTP_PROTOCOL_DEFAULT_PORT', '119');

/**
 * The Net_NNTP_Protocol class implements the NNTP standard acording to
 * RFX 977, RFC 2980, RFC 850/1036, and RFC 822/2822
 *
 * @version 0.0.1
 * @author Heino H. Gehlsen <heino@gehlsen.dk>
 */
class Net_NNTP_Protocol extends PEAR
{
    // {{{ properties

    /**
     * The socket resource being used to connect to the IMAP server.
     *
     * @var resource
     * @access private
     */
    var $_socket = null;

    /**
     *
     *
     * @var resource
     * @access private
     */
    var $_currentStatusResponse = null;

    // }}}
    // {{{ constructor
	    
    /**
     *
     */
    function Net_NNTP_Protocol() {
	parent::PEAR();
	
	$this->_socket = new Net_Socket();
    }

    // }}}
    // {{{ Connect()

    /**
     * Connect to the server
     *
     * @param optional string $host The adress of the NNTP-server to connect to, defaults to 'localhost'.
     * @param optional int $port The port number to connect to, defaults to 119.
     *
     * @return mixed (bool) true on success or (object) pear_error on failure
     * @access public
     */
    function connect($host = NET_NNTP_PROTOCOL_DEFAULT_HOST, $port = NET_NNTP_PROTOCOL_DEFAULT_PORT)
    {
        if ($this->isConnected() ) {
	    return PEAR::throwError('Already connected, disconnect first!', null);
	}

	// Open Connection
	$R = @$this->_socket->connect($host, $port, false, 15);
	if ($this->isError($R)) {
	    return PEAR::throwError('Could not connect to the server', null, $R->getMessage());
	}

	// Retrive the server's initial response.
	$response = $this->_getStatusResponse();
	if (PEAR::isError($response)) {
	    return $response;
        }

        switch ($response) {
	    case 200: // Posting allowed
		// TODO: Set some variable
	        return true;
	        break;
	    case 201: // Posting NOT allowed
		// TODO: Set some variable
	        return true;
	        break;
	    case 502: // 'access restriction or permission denied'
		return PEAR::throwError('Server refused connection', $response, $this->currentStatusResponse());
		break;
	    default:
		return PEAR::throwError('Unidentified response code', $response, $this->currentStatusResponse());
	}
    }

    // }}}
    // {{{ disconnect()

    /**
     * alias for cmdQuit()
     *
     * @access public
     */
    function disconnect()
    {
	return $this->cmdQuit();
    }

    // }}}
    // {{{ cmdQuit()

    /**
     * Close connection to the server
     *
     * @access public
     */
    function cmdQuit()
    {
	// Tell the server to close the connection
	$response = $this->_sendCommand('QUIT');
        if (PEAR::isError($response)) {
            return $response;
	}
	
        switch ($response) {
	    case 205: // RFC977: 'closing connection - goodbye!'
		// If socket is still open, close it.
		if ($this->isConnected()) {
    	    	    $this->_socket->disconnect();
		}
		return true;
		break;
	    default:
		return PEAR::throwError('Unidentified response code', $response, $this->currentStatusResponse());
	}

    }

    // }}}

    /**
     * The authentication process i not yet standarized but used any way
     * (http://www.mibsoftware.com/userkt/nntpext/index.html).
     */
     
    // {{{ cmdAuthinfo()

    /**
     * Authenticates the user using the original method
     *
     * @param string $user The username to authenticate as.
     * @param string $pass The password to authenticate with.
     *
     * @return mixed (bool) true on success or (object) pear_error on failure 
     * @access private
     */
    function cmdAuthinfo($user, $pass)
    {
	// Send the username
        $response = $this->_sendCommand('AUTHINFO user '.$user);
        if (PEAR::isError($response)) {
            return $response;
	}

	// Send the password, if the server asks
	if (($response == 381) && ($pass !== null)) {
	    // Send the password
            $response = $this->_sendCommand('AUTHINFO pass '.$pass);
	    if (PEAR::isError($response)) {
        	return $response;
	    }
	}

        switch ($response) {
	    case 281: // RFC2980: 'Authentication accepted'
	        return true;
	        break;
	    case 381: // RFC2980: 'More authentication information required'
	        return PEAR::throwError('Authentication uncompleted', $response, $this->currentStatusResponse());
	        break;
	    case 482: // RFC2980: 'Authentication rejected'
		return PEAR::throwError('Authentication rejected', $response, $this->currentStatusResponse());
		break;
	    case 502: // RFC2980: 'No permission'
		return PEAR::throwError('Authentication rejected', $response, $this->currentStatusResponse());
		break;
//	    case 500:
//	    case 501:
//	    	return PEAR::throwError('Authentication failed', $response, $this->currentStatusResponse());
//	    	break;
	    default:
		return PEAR::throwError('Unexpected authentication error!', $response, $this->currentStatusResponse());
	}
    }
	
    // }}}
    // {{{ cmdAuthinfoSimple()

    /**
     * Authenticates the user using the simple method
     *
     * @param string $user The username to authenticate as.
     * @param string $pass The password to authenticate with.
     *
     * @return mixed (bool) true on success or (object) pear_error on failure 
     * @access private
     */
    function cmdAuthinfoSimple($user, $pass)
    {
        return PEAR::throwError("The auth mode: 'simple' is has not been implemented yet", null);
    }
	
    // }}}
    // {{{ cmdAuthinfoGeneric()

    /**
     * Authenticates the user using the simple method
     *
     * @param string $user The username to authenticate as.
     * @param string $pass The password to authenticate with.
     *
     * @return mixed (bool) true on success or (object) pear_error on failure 
     * @access private
     */
    function cmdAuthinfoGeneric($user, $pass)
    {
        return PEAR::throwError("The auth mode: 'generic' is has not been implemented yet", null);
    }
	
    // }}}
    // {{{ cmdModeReader()

    /**
     *
     * @return mixed (bool) true when one can post on success or (object) pear_error on failure 
     * @access public
     */
    function cmdModeReader()
    {
        // tell the newsserver we want an article
        $response = $this->_sendCommand('MODE READER');
        if (PEAR::isError($response)) {
            return $response;
        }
	
	switch ($response) {
            case 200: // RFC2980: 'Hello, you can post'
	        break;
	    case 201: // RFC2980: 'Hello, you can't post'
		break;
	    default:
		return PEAR::throwError('Unidentified response code', $response, $this->currentStatusResponse());
	}

    }

    // }}}
    // {{{ cmdArticle()

    /**
     * Get an article from the currently open connection.
     *
     * @param mixed $article Either a message-id or a message-number of the article to fetch. If null or '', then use current article.
     *
     * @return mixed (array) article on success or (object) pear_error on failure 
     * @access public
     */
    function cmdArticle($article)
    {
        // tell the newsserver we want an article
        $response = $this->_sendCommand('ARTICLE '.$article);
        if (PEAR::isError($response)) {
            return $response;
        }
	
	switch ($response) {
	    case 220: // RFC977: 'n <a> article retrieved - head and body follow (n = article number, <a> = message-id)'
	    case 221: // RFC977: 'n <a> article retrieved - head follows'
	    case 222: // RFC977: 'n <a> article retrieved - body follows'
	    case 223: // RFC977: 'n <a> article retrieved - request text separately'
		$data = $this->_getTextResponse();
    		if (PEAR::isError($data)) {
    	    	    return $data;
    		}
		return $data;
		break;
	    case 412: // RFC977: 'no newsgroup has been selected'
		return PEAR::throwError('No newsgroup has been selected', $response, $this->currentStatusResponse());
		break;
	    case 420: // RFC977: 'no current article has been selected'
		return PEAR::throwError('No current article has been selected', $response, $this->currentStatusResponse());
		break;
	    case 423: // RFC977: 'no such article number in this group'
		return PEAR::throwError('No such article number in this group', $response, $this->currentStatusResponse());
		break;
	    case 430: // RFC977: 'no such article found'
		return PEAR::throwError('No such article found', $response, $this->currentStatusResponse());
		break;
	    default:
		return PEAR::throwError('Unidentified response code', $response, $this->currentStatusResponse());
	}

    }

    // }}}
    // {{{ cmdHead()

    /**
     * Get the headers of an article from the currently open connection.
     *
     * @param mixed $article Either a message-id or a message-number of the article to fetch the headers from. If null or '', then use current article.
     *
     * @return mixed (array) headers on success or (object) pear_error on failure 
     * @access public
     */
    function cmdHead($article)
    {
        // tell the newsserver we want the header of an article
        $response = $this->_sendCommand('HEAD '.$article);
        if (PEAR::isError($response)) {
            return $response;
        }

	switch ($response) {
	    case 220: // RFC977: 'n <a> article retrieved - head and body follow (n = article number, <a> = message-id)'
	    case 221: // RFC977: 'n <a> article retrieved - head follows'
	    case 222: // RFC977: 'n <a> article retrieved - body follows'
	    case 223: // RFC977: 'n <a> article retrieved - request text separately'
		$data = $this->_getTextResponse();
        	if (PEAR::isError($data)) {
        	    return $data;
        	}
	        return $data;
		break;
	    case 412: // RFC977: 'no newsgroup has been selected'
		return PEAR::throwError('No newsgroup has been selected', $response, $this->currentStatusResponse());
		break;
	    case 420: // RFC977: 'no current article has been selected'
		return PEAR::throwError('No current article has been selected', $response, $this->currentStatusResponse());
		break;
	    case 423: // RFC977: 'no such article number in this group'
		return PEAR::throwError('No such article number in this group', $response, $this->currentStatusResponse());
		break;
	    case 430: // RFC977: 'no such article found'
		return PEAR::throwError('No such article found', $response, $this->currentStatusResponse());
		break;
	    default:
		return PEAR::throwError('Unidentified response code', $response, $this->currentStatusResponse());
	}
    }

    // }}}
    // {{{ cmdBody()

    /**
     * Get the body of an article from the currently open connection.
     *
     * @param mixed $article Either a message-id or a message-number of the article to fetch the body from. If null or '', then use current article.
     *
     * @return mixed (array) body on success or (object) pear_error on failure 
     * @access public
     */
    function cmdBody($article)
    {
        // tell the newsserver we want the body of an article
        $response = $this->_sendCommand('BODY '.$article);
        if (PEAR::isError($response)) {
            return $response;
        }

	switch ($response) {
	    case 220: // RFC977: 'n <a> article retrieved - head and body follow (n = article number, <a> = message-id)'
	    case 221: // RFC977: 'n <a> article retrieved - head follows'
	    case 222: // RFC977: 'n <a> article retrieved - body follows'
	    case 223: // RFC977: 'n <a> article retrieved - request text separately'
		$data = $this->_getTextResponse();
        	if (PEAR::isError($data)) {
        	    return $data;
        	}
	        return $data;
		break;
	    case 412: // RFC977: 'no newsgroup has been selected'
		return PEAR::throwError('No newsgroup has been selected', $response, $this->currentStatusResponse());
		break;
	    case 420: // RFC977: 'no current article has been selected'
		return PEAR::throwError('No current article has been selected', $response, $this->currentStatusResponse());
		break;
	    case 423: // RFC977: 'no such article number in this group'
		return PEAR::throwError('No such article number in this group', $response, $this->currentStatusResponse());
		break;
	    case 430: // RFC977: 'no such article found'
		return PEAR::throwError('No such article found', $response, $this->currentStatusResponse());
		break;
	    default:
		return PEAR::throwError('Unidentified response code', $response, $this->currentStatusResponse());
	}
    }

    // }}}
    // {{{ cmdPost()

    /**
     * Post an article to a newsgroup.
     *
     * Among the aditional headers you might think of adding could be:
     * "NNTP-Posting-Host: <ip-of-author>", which should contain the IP-adress
     * of the author of the post, so the message can be traced back to him.
     * "Organization: <org>" which contain the name of the organization
     * the post originates from.
     *
     * @param string $newsgroup The newsgroup to post to.
     * @param string $subject The subject of the post.
     * @param string $body The body of the post itself.
     * @param string $from Name + email-adress of sender.
     * @param optional string $aditional Aditional headers to send.
     *
     * @return mixed (bool) true on success or (object) pear_error on failure
     * @access public
     */
    function cmdPost($newsgroup, $subject, $body, $from, $aditional = '')
    {
        // tell the newsserver we want to post an article
	$response = $this->_sendCommand('POST');
	if (PEAR::isError($response)) {
	    return $response;
        }

	if ($response == 340) { // RFC977: 'send article to be posted. End with <CR-LF>.<CR-LF>'

	    // should be presented in the format specified by RFC850
	    
            $this->_socket->write("Newsgroups: $newsgroup\r\n");
            $this->_socket->write("Subject: $subject\r\n");
    	    $this->_socket->write("From: $from\r\n");
            $this->_socket->write("X-poster: PEAR::Net_NNTP\r\n");
            $this->_socket->write("$aditional\r\n");
            $this->_socket->write("\r\n");
            $this->_socket->write("$body\r\n");
            $this->_socket->write(".\r\n");

	    // Retrive server's response.
	    $response = $this->_getStatusResponse();
	    if (PEAR::isError($response)) {
		return $response;
    	    }
	}

	switch ($response) {
    	    case 240: // RFC977: 'article posted ok'
		return true;
		break;
    	    case 340: // RFC977: 'send article to be posted. End with <CR-LF>.<CR-LF>'
		// This should not happen here!
		return PEAR::throwError('Unknown error during post', $response, $this->currentStatusResponse());
		break;
    	    case 440: // RFC977: 'posting not allowed'
		return PEAR::throwError('Posting not allowed', $response, $this->currentStatusResponse());
		break;
    	    case 441: // RFC977: 'posting failed'
		return PEAR::throwError('Posting failed', $response, $this->currentStatusResponse());
		break;
	    default:
		return PEAR::throwError('Unidentified response code', $response, $this->currentStatusResponse());
	}
    }

    // }}}
    // {{{ cmdGroup()

    /**
     * Selects a news group (issue a GROUP command to the server)
     *
     * @param string $newsgroup The newsgroup name
     *
     * @return mixed (array) groupinfo on success or (object) pear_error on failure
     * @access public
     */
    function cmdGroup($newsgroup)
    {
        $response = $this->_sendCommand('GROUP '.$newsgroup);
        if (PEAR::isError($response)) {
            return $response;
        }

	switch ($response) {
    	    case 211: // RFC977: 'n f l s group selected'
    		$response_arr = split(' ', trim($this->currentStatusResponse()));
    		$response_arr['count'] =& $response_arr[0];
	        $response_arr['first'] =& $response_arr[1];
		$response_arr['last']  =& $response_arr[2];
		$response_arr['group'] =& $response_arr[3];
		return $response_arr;
		break;
	    case 411: // RFC977: 'no such news group'
		return PEAR::throwError('No such news group', $response, $this->currentStatusResponse());
		break;
	    default:
		return PEAR::throwError('Unidentified response code', $response, $this->currentStatusResponse());
	}
	
    }

    // }}}
    // {{{ cmdList()

    /**
     * Fetches a list of all avaible newsgroups
     *
     * @return mixed (array) nested array with informations about existing newsgroups on success or (object) pear_error on failure
     * @access public
     */
    function cmdList()
    {
        $response = $this->_sendCommand('LIST');
        if (PEAR::isError($response)){
            return $response;
        }

	switch ($response) {
    	    case 215: // RFC977: 'list of newsgroups follows'
		$data = $this->_getTextResponse();
    		if (PEAR::isError($data)) {
    		    return $data;
    		}
    		foreach($data as $line) {
    		    $arr = explode(' ', trim($line));
    		    $arr['group']    =& $arr[0];
    		    $arr['last']     =& $arr[1];
    		    $arr['first']    =& $arr[2];
    		    $arr['posting' ] = (bool) ($arr[3] == 'y');
    		    $groups[$arr[0]] = $arr;
    		}
	        return $groups;
		break;
	    default:
		return PEAR::throwError('Unidentified response code', $response, $this->currentStatusResponse());
	}
    }

    // }}}
    // {{{ cmdListNewsgroups()

    /**
     * Fetches a list of (all) avaible newsgroup descriptions.
     *
     * @param string $wildmat Wildmat of the groups, that is to be listed, defaults to '';
     *
     * @return mixed (array) nested array with description of existing newsgroups on success or (object) pear_error on failure
     * @access public
     */
    function cmdListNewsgroups($wildmat = '')
    {
        $response = $this->_sendCommand('LIST NEWSGROUPS '.$wildmat);
        if (PEAR::isError($response)){
            return $response;
        }

	switch ($response) {
	    case 215: // RFC2980: 'information follows'
		$data = $this->_getTextResponse();
	        if (PEAR::isError($data)) {
	            return $data;
	        }

	        foreach($data as $line) {
	            preg_match("/^(.*?)\s(.*?$)/", trim($line), $matches);
	            $groups[$matches[1]] = (string) $matches[2];
	        }

	        return $groups;
		break;
	    case 503: // RFC2980: 'program error, function not performed'
		return PEAR::throwError('Internal server error, function not performed', $response, $this->currentStatusResponse());
		break;
	    default:
		return PEAR::throwError('Unidentified response code', $response, $this->currentStatusResponse());
	}

    }

    // }}}
    /**
     * Fetches a list of (all) avaible newsgroup descriptions.
     * Depresated as of RFC2980.
     *
     * @param string $wildmat Wildmat of the groups, that is to be listed, defaults to '*';
     *
     * @return mixed (array) nested array with description of existing newsgroups on success or (object) pear_error on failure
     * @access public
     */
    function cmdXGTitle($wildmat = '*')
    {
        $response = $this->_sendCommand('XGTITLE '.$wildmat);
        if (PEAR::isError($response)){
            return $response;
        }

	switch ($response) {
	    case 282: // RFC2980: 'list of groups and descriptions follows'
		$data = $this->_getTextResponse();
	        if (PEAR::isError($data)) {
	            return $data;
	        }

	        foreach($data as $line) {
	            preg_match("/^(.*?)\s(.*?$)/", trim($line), $matches);
	            $groups[$matches[1]] = (string) $matches[2];
	        }

	        return $groups;
		break;
		  
	    case 481: // RFC2980: 'Groups and descriptions unavailable'
		return PEAR::throwError('Groups and descriptions unavailable', $response, $this->currentStatusResponse());
		break;
	    default:
		return PEAR::throwError('Unidentified response code', $response, $this->currentStatusResponse());
	}

    }

    // }}}
    // {{{ cmdNewgroups()

    /**
     * Fetches a list of all newsgroups created since a specified date.
     *
     * @param int $time Last time you checked for groups (timestamp).
     *
     * @return mixed (array) nested array with informations about existing newsgroups on success or (object) pear_error on failure
     * @access public
     */
    function cmdNewgroups($time)
    {
        $response = $this->_sendCommand('NEWGROUPS '.date('ymd His', $time));
        if (PEAR::isError($response)){
            return $response;
        }

	switch ($response) {
	    case 231: // REF977: 'list of new newsgroups follows'
		$groups = array();
	        foreach($this->_getTextResponse() as $line) {
		    $arr = explode(' ', $line);
		    $groups[$arr[0]]['group'] = $arr[0];
		    $groups[$arr[0]]['last'] = $arr[1];
		    $groups[$arr[0]]['first'] = $arr[2];
		    $groups[$arr[0]]['posting'] = $arr[3];
		}
		return $groups;
		break;
	    default:
		return PEAR::throwError('Unidentified response code', $response, $this->currentStatusResponse());
	}
    }

    // }}}
    // {{{ cmdListOverviewFmt()

    /**
     * Returns a list of avaible headers which are send from newsserver to client for every news message
     *
     * @return mixed (array) of header names on success or (object) pear_error on failure
     * @access public
     */
    function cmdListOverviewFmt()
    {
	$response = $this->_sendCommand('LIST OVERVIEW.FMT');
        if (PEAR::isError($response)){
            return $response;
        }

	switch ($response) {
	    case 215: // RFC2980: 'information follows'
		$data = $this->_getTextResponse();
	        if (PEAR::isError($data)) {
	            return $data;
	        }

	        $format = array('number');
	        // XXX Use the splitHeaders() algorithm for supporting
	        //     multiline headers?
	        foreach ($data as $line) {
	            $line = current(explode(':', trim($line)));
	            $format[] = $line;
	        }
	        return $format;
		break;
	    case 503: // RFC2980: 'program error, function not performed'
		return PEAR::throwError('Internal server error, function not performed', $response, $this->currentStatusResponse());
		break;
	    default:
		return PEAR::throwError('Unidentified response code', $response, $this->currentStatusResponse());
	}
    }

    // }}}
    // {{{ cmdXOver()

    /**
     * Fetch message header from message number $first until $last
     *
     * The format of the returned array is:
     * $messages[message_id][header_name]
     *
     * @param integer $first first article to fetch
     * @param integer $last  last article to fetch
     *
     * @return mixed (array) nested array of message and there headers on success or (object) pear_error on failure
     * @access public
     */
    function cmdXOver($first, $last)
    {
        $format = $this->cmdListOverviewFmt();
        if (PEAR::isError($format)){
            return $formt;
        }

        $response = $this->_sendCommand('XOVER '.$first.'-'.$last);
        if (PEAR::isError($response)){
            return $response;
        }

	switch ($response) {
	    case 224: // RFC2980: 'Overview information follows'
		$data = $this->_getTextResponse();
	        if (PEAR::isError($data)) {
	            return $data;
	        }
		$messages = array();
	        foreach($data as $line) {
	            $i=0;
	            foreach(explode("\t", trim($line)) as $line) {
	                $message[$format[$i++]] = $line;
	            }
	            $messages[$message['Message-ID']] = $message;
	        }
        	return $messages;
		break;
	    case 412: // RFC2980: 'No news group current selected'
		return PEAR::throwError('No news group current selected', $response, $this->currentStatusResponse());
		break;
	    case 420: // RFC2980: 'No article(s) selected'
		return PEAR::throwError('No article(s) selected', $response, $this->currentStatusResponse());
		break;
	    case 502: // RFC2980: 'no permission'
		return PEAR::throwError('No permission', $response, $this->currentStatusResponse());
		break;
	    default:
		return PEAR::throwError('Unidentified response code', $response, $this->currentStatusResponse());
	}
    }
    
    // }}}
    // {{{ cmdXROver()

    /**
     * Fetch message references from message number $first to $last
     *
     * @param integer $first first article to fetch
     * @param integer $last  last article to fetch
     *
     * @return mixed (array) assoc. array of message references on success or (object) pear_error on failure
     * @access public
     */
    function cmdXROver($first, $last)
    {
        $response = $this->_sendCommand('XROVER '.$first.'-'.$last);
        if (PEAR::isError($response)){
            return $response;
        }

	switch ($response) {
	    case 224: // RFC2980: 'Overview information follows'
		$data = $this->_getTextResponse();
	        if (PEAR::isError($data)) {
	            return $data;
	        }

	        foreach($data as $line) {

	            $references = preg_split("/ +/", trim($line), -1, PREG_SPLIT_NO_EMPTY);

	            $id = array_shift($references);

	            $messages[$id] = $references;
	        }
        	return $messages;
		break;
	    case 412: // RFC2980: 'No news group current selected'
		return PEAR::throwError('No news group current selected', $response, $this->currentStatusResponse());
		break;
	    case 420: // RFC2980: 'No article(s) selected'
		return PEAR::throwError('No article(s) selected', $response, $this->currentStatusResponse());
		break;
	    case 502: // RFC2980: 'no permission'
		return PEAR::throwError('No permission', $response, $this->currentStatusResponse());
		break;
	    default:
		return PEAR::throwError('Unidentified response code', $response, $this->currentStatusResponse());
	}
    }

    // }}}
    // {{{ cmdListgroup()

    /**
     *
     * @param string $newsgroup 
     *
     * @return mixed (array) on success or (object) pear_error on failure
     */
    function cmdListgroup($newsgroup)
    {
        $response = $this->_sendCommand('LISTGROUP '.$newsgroup);
        if (PEAR::isError($response)){
            return $response;
        }

	switch ($response) {
	    case 211: // RFC2980: 'list of article numbers follow'
		$data = $this->_getTextResponse();
	        if (PEAR::isError($data)) {
	            return $data;
	        }
	        return $data;
		break;
	    case 412: // RFC2980: 'Not currently in newsgroup'
		return PEAR::throwError('Not currently in newsgroup', $response, $this->currentStatusResponse());
		break;
	    case 502: // RFC2980: 'no permission'
		return PEAR::throwError('No permission', $response, $this->currentStatusResponse());
		break;
	    default:
		return PEAR::throwError('Unidentified response code', $response, $this->currentStatusResponse());
	}
    }

    // }}}
    // {{{ cmdNewnews()

    /**
     *
     */
    function cmdNewnews($time, $newsgroups = '*')
    {
	// TODO: the lenght of the request string may not exceed 510 chars
	
        $response = $this->_sendCommand('NEWNEWS '.$newsgroups.' '.date('ymd His', $time));
        if (PEAR::isError($response)){
            return $response;
        }

	switch ($response) {
	    case 230: // RFC977: 'list of new articles by message-id follows'
		$messages = array();
        	foreach($this->_getTextResponse() as $line) {
		    $messages[] = $line;
		}
		return $messages;
		break;
	    default:
		return PEAR::throwError('Unidentified response code', $response, $this->currentStatusResponse());
	}
    }

    // }}}
    // {{{ cmdDate()

    /**
     * Get the date from the newsserver format of returned date
     *
     * @param bool $timestap when false function returns string, and when true function returns int/timestamp.
     *
     * @return mixed (string) 'YYYYMMDDhhmmss' / (int) timestamp on success or (object) pear_error on failure
     * @access public
     */
    function cmdDate($timestamp = false)
    {
        $response = $this->_sendCommand('DATE');
        if (PEAR::isError($response)){
            return $response;
        }

	switch ($response) {
	    case 111: // RFC2980: 'YYYYMMDDhhmmss'
                $d = $this->currentStatusResponse();
		if ($timestamp === false) {
		    return (string) $d;	    
		} else {
	    	    return (int) strtotime(substr($d, 0, 8).' '.$d[8].$d[9].':'.$d[10].$d[11].':'.$d[12].$d[13]);
		}
		break;
	    default:
		return PEAR::throwError('Unidentified response code', $response, $this->currentStatusResponse());
	}
    }
    // }}}
    // {{{ isConnected()

    /**
     * Test whether we are connected or not.
     *
     * @return bool true or false
     *
     * @access public
     */
    function isConnected()
    {
	return (is_resource($this->_socket->fp) && !feof($this->_socket->fp));
    }

    // }}}
    // {{{ setDebug()

    /**
     * Sets the debuging information on or off
     *
     * @param boolean True or false 
     *
     * @return bool previos state
     * @access public
     */
    function setDebug($debug = true)
    {
        $tmp = $this->_debug;
        $this->_debug = $debug;
        return $tmp;
    }

    // }}}
    // {{{ _getStatusResponse()

    /**
     * Get servers statusresponse after a command.
     *
     * @return mixed (int) statuscode on success or (object) pear_error on failure
     * @access private
     */
    function _getStatusResponse()
    {
	// Retrieve a line (terminated by "\r\n") from the server.
	$response = $this->_socket->gets(256);
        if (PEAR::isError($response) ) {
    	    return PEAR::throwError('Failed to read from socket!', null, $response->getMessage());
        }

        if ($this->_debug) {
            echo "S: $response\r\n";
        }

	// Trim the start of the response in case of misplased whitespace (should not be needen!!!)
	$response = ltrim($response);

        $this->_currentStatusResponse = array(
					      (int) substr($response, 0, 3),
	                                      (string) rtrim(substr($response, 4))
					     );

	return $this->_currentStatusResponse[0];
    }
    
    // }}}
    // {{{ currentStatusResponse()

    /**
     *
     *
     * @return string status text
     * @access private
     */
    function currentStatusResponse()
    {
	return $this->_currentStatusResponse[1];
    }
    
    // }}}
    // {{{ _getTextResponse()

    /**
     * Get data until a line with only a '.' in it is read and return data.
     *
     * @return mixed (array) text response on success or (object) pear_error on failure
     * @access private
     */
    function _getTextResponse()
    {
        $data = array();
        $line = '';
	
        // Continue until connection is lost
        while(!$this->_socket->eof()) {

            // Retrieve and append up to 1024 characters from the server.
            $line .= $this->_socket->gets(1024); 
            if (PEAR::isError($line) ) {
                return PEAR::throwError( 'Failed to read from socket!', null, $line->getMessage());
    	    }
	    
            // Continue if the line is not terminated by CRLF
            if (substr($line, -2) != "\r\n" || strlen($line) < 2) {
                continue;
            }

            // Validate recieved line
            if (false) {
                // Lines should/may not be longer than 998+2 chars (RFC2822 2.3)
                if (strlen($line) > 1000) {
                    return PEAR::throwError('Invalid line recieved!', null);
                }
            }

            // Remove CRLF from the end of the line
            $line = substr($line, 0, -2);

            // Check if the line terminates the textresponse
            if ($line == '.') {
                // return all previous lines
                return $data;
                break;
            }

            // If 1st char is '.' it's doubled (NNTP/RFC977 2.4.1)
            if (substr($line, 0, 2) == '..') {
                $line = substr($line, 1);
            }
            
            // Add the line to the array of lines
            $data[] = $line;

            // Reset/empty $line
            $line = '';
        }

    	return PEAR::throwError('Data stream not terminated with period', null);
    }

    // }}}
    // {{{ _sendCommand()

    /**
     * Send a command to the server. A carriage return / linefeed (CRLF) sequence
     * will be appended to each command string before it is sent to the IMAP server.
     *
     * @param string $cmd The command to launch, ie: "ARTICLE 1004853"
     *
     * @return mixed (int) response code on success or (object) pear_error on failure
     * @access private
     */
    function _sendCommand($cmd)
    {
        // NNTP/RFC977 only allows command up to 512 (-2) chars.
        if (!strlen($cmd) > 510) {
            return PEAR::throwError('Failed to write to socket! (Command to long - max 510 chars)');
        }

        // Check if connected
	if (!$this->isConnected()) {
            return PEAR::throwError('Failed to write to socket! (connection lost!)');
        }

	// Send the command
	$R = $this->_socket->writeLine($cmd);
        if ( PEAR::isError($R) ) {
            return PEAR::throwError('Failed to write to socket!', null, $R->getMessage());
        }
	
        if ($this->_debug) {
            echo "C: $cmd\r\n";
        }

	return $this->_getStatusResponse();
    }
    
    // }}}

}

?>
