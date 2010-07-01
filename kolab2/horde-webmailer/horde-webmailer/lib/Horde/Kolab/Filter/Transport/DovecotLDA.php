<?PHP
/**
 * $Horde: framework/Kolab_Filter/lib/Horde/Kolab/Filter/Transport/DovecotLDA.php,v 1.4.2.1 2009-02-20 22:37:15 wrobel Exp $
 *
 * @package Kolab_Filter
 */

/**
 * Defines a transport mechanism for delivering mails to the dovecot
 * IMAP server.
 *
 * $Horde: framework/Kolab_Filter/lib/Horde/Kolab/Filter/Transport/DovecotLDA.php,v 1.4.2.1 2009-02-20 22:37:15 wrobel Exp $
 *
 * Copyright 2008 Intevation GmbH
 *
 * See the enclosed file COPYING for license information (LGPL). If you
 * did not receive this file, see http://www.gnu.org/licenses/old-licenses/lgpl-2.1.html.
 *
 * @author  Sascha Wilde <wilde@intevation.de>
 * @package Kolab_Filter
 */
class Dovecot_LDA
{
    /**
     * The mail sender.
     *
     * @var string
     */
    var $_envelopeSender;

    /**
     * The mail recipient.
     *
     * @var string
     */
    var $_envelopeTo = array();

    /**
     * Transport status.
     *
     * @var int
     */
    var $_status;

    /**
     * The data that should be sent.
     *
     * @var array
     */
    var $_data;

    /**
     * File handle for delivery.
     *
     * @var int
     */
    var $_deliver_fh;

    function Dovecot_LDA()
    {
        $this->_envelopeTo = false;
        $this->_status = 220;
    }

    /**
     * Pretends to connect to Dovecot which is not necessary.
     *
     * @return boolean|PEAR_Error Always true.
     */
    function connect()
    {
        global $conf;

        if (!isset($conf['kolab']['filter']['dovecot_deliver'])) {
            return PEAR::raiseError('Path to the dovecot delivery tool missing!');
        }
        return true;
    }

    /**
     * Pretends to disconnect from Dovecot which is not necessary.
     *
     * @return boolean Always true.
     */
    function disconnect()
    {
        return true;
    }


    /**
     * Set the mail sender.
     *
     * @return boolean Always true.
     */
    function mailFrom($sender)
    {
        $this->_envelopeSender = $sender;
        $this->_status = 250;
        return true;
    }

    /**
     * Add a mail recipient.
     *
     * @return boolean Always true.
     */
    function rcptTo($rcpt)
    {
        $this->_envelopeTo[] = $rcpt;
        $this->_status = 250;
        return true;
    }

    /**
     * Receive commands.
     *
     * @param string $cmd The command.
     *
     * @return boolean|PEAR_Error True if the command succeeded.
     */
    function _put($cmd)
    {
        if ($cmd == "DATA") {
            $this->_status = 354;
        } else {
            $this->_status = 500;
            return PEAR::raiseError('Dovecot LDA Backend received an unknown command.');
        }
        return true;
    }

    /**
     * Check the current response code.
     *
     * @param string $code The response to parse.
     *
     * @return boolean|PEAR_Error True if the current status matches
     * the expectation.
     */
    function _parseResponse($code)
    {
        if ($code) {
            if ($this->_status == $code) {
                return true;
            } else {
                return PEAR::raiseError(sprintf("Dovecot LDA status is %s though %s was expected!.",
                                                $this->_status, $code));
            }
        } else {
            return $this->status;
        }
    }

    /**
     * Send actual mail data.
     *
     * @param string $data The data to write.
     *
     * @return boolean|PEAR_Error True if successful.
     */
    function _send($data)
    {
        $errors = array();
        if ($data == ".\r\n" or $data == "\r\n.\r\n") {
            foreach ($this->_envelopeTo as $recipient) {
                $result = $this->_start_deliver($recipient);
                if (is_a($result, 'PEAR_Error')) {
                    $errors[] = $result;
                    continue;
                }

                $result = $this->_deliver();
                if (is_a($result, 'PEAR_Error')) {
                    $errors[] = $result;
                    continue;
                }

                $result = $this->_stop_deliver();
                if (is_a($result, 'PEAR_Error')) {
                    $errors[] = $result;
                    continue;
                }
            }
            if (empty($errors)) {
                $this->_status = 250;
            } else {
                $this->_status = 500;
                $msg = '';
                foreach ($errors as $error) {
                    $msg[] = $error->getMessage();
                }
                return PEAR::raiseError(sprintf("Dovecot delivery failed: %s",
                                                join(', ', $msg)));
            }
        } else {
            $this->_data[] = $data;
        }
        return true;
    }


    /**
     * Start the delivery process for a recipient.
     *
     * @param string $recipient The recipient of the message.
     *
     * @return boolean|PEAR_Error True if successful.
     */
    function _start_deliver($recipient)
    {
        global $conf;

        Horde::logMessage(sprintf("Starting Dovecot delivery process with UID %d, GID %d (sender=%s, recipient=%s) ...",
                                  getmyuid(), getmygid(),
                                  $this->_envelopeSender, $recipient),
                          __FILE__, __LINE__, PEAR_LOG_DEBUG);

        $deliver = $conf['kolab']['filter']['dovecot_deliver'];

        $this->_deliver_fh = popen($deliver . ' -f ' . $this->_envelopeSender .
                                   ' -d ' . $recipient, "w");
        if ($this->_deliver_fh === false) {
            return PEAR::raiseError('Failed to connect to the dovecot delivery tool!');
        }
        return true;
    }

    /**
     * End the delivery process for a recipient.
     *
     * @return boolean|PEAR_Error True if successful.
     */
    function _stop_deliver()
    {
        Horde::logMessage("Stoping Dovecot delivery process ...",
                          __FILE__, __LINE__, PEAR_LOG_DEBUG);
        $retval = pclose($this->_deliver_fh);
        Horde::logMessage(sprintf("... return value was %d\n", $retval),
                          __FILE__, __LINE__, PEAR_LOG_DEBUG);
        if ($retval != 0) {
            return PEAR::raiseError('Dovecot LDA Backend delivery process signaled an error.');
        }
        return true;
    }

    /**
     * Write data to the deliver process.
     *
     * @return boolean|PEAR_Error True if successful.
     */
    function _deliver()
    {
        foreach ($this->_data as $line) {
            if (!fwrite($this->_deliver_fh, $line)) {
                return PEAR::raiseError('Dovecot LDA Backend failed writing to the deliver process.');
            }
        }
        return true;
    }
}
