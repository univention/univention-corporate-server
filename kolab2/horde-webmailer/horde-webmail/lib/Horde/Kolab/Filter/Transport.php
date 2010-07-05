<?php
/**
 * $Horde: framework/Kolab_Filter/lib/Horde/Kolab/Filter/Transport.php,v 1.4.2.3 2009-11-24 13:53:40 wrobel Exp $
 *
 * @package Kolab_Filter
 */

/**
 * Provides a delivery mechanism for a mail message.
 *
 * $Horde: framework/Kolab_Filter/lib/Horde/Kolab/Filter/Transport.php,v 1.4.2.3 2009-11-24 13:53:40 wrobel Exp $
 *
 * Copyright 2004-2008 Klarälvdalens Datakonsult AB
 *
 * See the enclosed file COPYING for license information (LGPL). If you
 * did not receive this file, see http://www.gnu.org/licenses/old-licenses/lgpl-2.1.html.
 *
 * @author  Steffen Hansen <steffen@klaralvdalens-datakonsult.se>
 * @author  Gunnar Wrobel <wrobel@pardus.de>
 * @package Kolab_Filter
 */
class Horde_Kolab_Filter_Transport 
{
    /**
     * The connection parameters for the transport.
     *
     * @var array
     */
    var $_params;

    /**
     * The transport class delivering the message.
     *
     * @var mixed
     */
    var $_transport;

    /**
     * Internal marker to indicate if we received a new line.
     *
     * @var boolean
     */
    var $_got_newline;

    /**
     * Constructor.
     */
    function Horde_Kolab_Filter_Transport($params)
    {
        $this->_params = $params;
        $this->_transport = false;
    }

    /**
     * Attempts to return a concrete Horde_Kolab_Filter_Transport instance based on $driver.
     *
     * @param string $driver The type of the concrete Horde_Kolab_Filter_Transport
     *                       subclass to return.  The class name is
     *                       based on the Horde_Kolab_Filter_Transport driver
     *                       ($driver).  The code is dynamically
     *                       included.
     *
     * @param array $params  A hash containing any additional
     *                       configuration or connection parameters a
     *                       subclass might need.
     *
     * @return Horde_Kolab_Filter_Transport|boolean The newly created concrete
     *                                 Horde_Kolab_Filter_Transport instance, or
     *                                 false on an error.
     */
    function &factory($driver, $params = array())
    {
        $class = 'Horde_Kolab_Filter_Transport_' . $driver;
        if (!class_exists($class)) {
            include dirname(__FILE__) . '/Transport/' . $driver . '.php';
        }
        if (class_exists($class)) {
            $transport = &new $class($params);
            return $transport;
        }
        return PEAR::raiseError(sprintf('No such class \"%s\"', $class),
                                OUT_LOG | EX_SOFTWARE);
    }

    /**
     * Create the transport class.
     */
    function createTransport() {
        $this->_transport = $this->_createTransport();
    }

    /**
     * Starts transporting the message.
     *
     * @param string $sender The message sender.
     * @param array $recips  The recipients of the message.
     *
     * @return boolean|PEAR_Error True on success, a PEAR_Error otherwise.
     */
    function start($sender, $recips)
    {
        $this->createTransport();

        $myclass = get_class($this->_transport);
        $this->_got_newline = true;

        $result = $this->_transport->connect();
        if (is_a($result, 'PEAR_Error')) {
            $result->code = OUT_LOG | EX_UNAVAILABLE;
            return $result;
        }

        if (isset($this->_params['user']) && isset($this->_params['pass']) ) {
            $this->_transport->auth($this->_params['user'], $this->_params['pass'], 'PLAIN');
        }

        $result = $this->_transport->mailFrom($sender);
        if (is_a($result, 'PEAR_Error')) {
            $resp = $this->_transport->getResponse();
            $error = PEAR::raiseError(sprintf('Failed to set sender: %s, code=%s',
                                              $resp[1], $resp[0]), $resp[0]);
            return $this->rewriteCode($error);
        }

        if (!is_array($recips)) {
            $recips = array($recips);
        }

        $reciperrors = array();
        foreach ($recips as $recip) {
            $result = $this->_transport->rcptTo($recip);
            if (is_a($result, 'PEAR_Error')) {
                $resp = $this->_transport->getResponse();
                $reciperrors[] = PEAR::raiseError(sprintf('Failed to set recipient: %s, code=%s',
                                                          $resp[1], $resp[0]), $resp[0]);
            }
        }

        if (count($reciperrors) == count($recips)) {
            /* OK, all failed, just give up */
            if (count($reciperrors) == 1) {
                /* Only one failure, just return that */
                return $this->rewriteCode($reciperrors[0]);
            }
            /* Multiple errors */
            $error = $this->createErrorObject($reciperrors,
                                              'Delivery to all recipients failed!');
            return $this->rewriteCode($error);
        }

        $result = $this->_transport->_put('DATA');
        if (is_a($result, 'PEAR_Error')) {
            $resp = $this->_transport->getResponse();
            $error = PEAR::raiseError(sprintf('Failed to send DATA: %s, code=%s',
                                              $resp[1], $resp[0]), $resp[0]);
            return $this->rewriteCode($error);
        }

        $result = $this->_transport->_parseResponse(354);
        if (is_a($result, 'PEAR_Error')) {
            return $this->rewriteCode($result);
        }

        if (!empty($reciperrors)) {
            return $this->createErrorObject($reciperrors,
                                            'Delivery to some recipients failed!');
        }
        return true;
    }

    /**
     * Encapsulate multiple errors in one.
     *
     * @param array  $reciperrors  The errors.
     * @param string $msg          A combined error message.
     *
     * @return PEAR_Error The combined error.
     */
    function createErrorObject($reciperrors, $msg = null)
    {
        /* Return the lowest errorcode to not bounce more
         * than we have to
         */
        if ($msg == null) {
            $msg = 'Delivery to recipients failed.';
        }

        $code = 1000;

        foreach ($reciperrors as $err) {
            if ($err->code < $code) {
                $code = $err->code;
            }
        }
        return new PEAR_Error($msg, $code, null, null, $reciperrors);  
    }

    /**
     * Modified implementation from Net_SMTP that supports dotstuffing
     * even when getting the mail line-by line.
     *
     * @param string $data   Mail message data.
     */
    function quotedataline(&$data)
    {
        /*
         * Change Unix (\n) and Mac (\r) linefeeds into Internet-standard CRLF
         * (\r\n) linefeeds.
         */
        $data = preg_replace(array('/(?<!\r)\n/','/\r(?!\n)/'), "\r\n", $data);

        /*
         * Because a single leading period (.) signifies an end to the data,
         * legitimate leading periods need to be "doubled" (e.g. '..').
         */
        if ($this->_got_newline && !empty($data) && $data[0] == '.') {
            $data = '.'.$data;
        }

        $data = str_replace("\n.", "\n..", $data);
        $len = strlen($data);
        if ($len > 0) {
            $this->_got_newline = ( $data[$len-1] == "\n" );
        }
    }

    /**
     * Send message data.
     *
     * @param string $data The text of the message.
     *
     * @return boolean|PEAR_Error True on success.
     */
    function data($data) {
        $this->quotedataline($data);
        $result = $this->_transport->_send($data);
        if (is_a($result, 'PEAR_Error')) {
            $resp = $this->_transport->getResponse();
            $error = PEAR::raiseError(sprintf('Failed to send message data: %s, code=%s',
                                              $resp[1], $resp[0]), $resp[0]);
            return $this->rewriteCode($error);
        }
        return true;
    }

    /**
     * Finish sending data.
     *
     * @return boolean|PEAR_Error True on success.
     */
    function end() 
    {
        if ($this->_got_newline) {          
            $dot = ".\r\n";
        } else {
            $dot = "\r\n.\r\n";
        }

        $result = $this->_transport->_send($dot);
        if (is_a($result, 'PEAR_Error')) {
            $resp = $this->_transport->getResponse();
            $error = PEAR::raiseError(sprintf('Failed to send message end: %s, code=%s',
                                              $resp[1], $resp[0]), $resp[0]);
            return $this->rewriteCode($error);
        }
        $result = $this->_transport->_parseResponse(250);
        if (is_a($result, 'PEAR_Error')) {
            return $this->rewriteCode($result);
        }
        $this->_transport->disconnect();
        $this->_transport = false;
        return true;
    }

    /**
     * Rewrite the code to something postfix can understand.
     *
     * @param PEAR_error $result The reponse of the transport.
     *
     * @return PEAR_error An error with a rewritten error code.
     */
    function rewriteCode($result) 
    {
        list($resultcode, $resultmessage) = $this->_transport->getResponse();
        if ($resultcode < 500) {
            $code = EX_TEMPFAIL;
        } else {
            $code = EX_UNAVAILABLE;
        }
        $append = sprintf(': %s, original code %s', $resultmessage, $resultcode);
        $result->message = $result->getMessage() . $append;
        $result->code = OUT_LOG | OUT_STDOUT | $code;
        return $result;
    }

}
