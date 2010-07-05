<?php
/**
 * $Horde: framework/Kolab_Filter/lib/Horde/Kolab/Filter/Content.php,v 1.4.2.8 2009-11-29 10:43:57 wrobel Exp $
 *
 * @package Kolab_Filter
 */

/** Load the basic filter definition */
require_once dirname(__FILE__) . '/Base.php';

/** Load the Transport library */
require_once dirname(__FILE__) . '/Transport.php';

define('RM_STATE_READING_HEADER', 1 );
define('RM_STATE_READING_FROM',   2 );
define('RM_STATE_READING_SUBJECT',3 );
define('RM_STATE_READING_SENDER', 4 );
define('RM_STATE_READING_BODY',   5 );

/**
 * A Kolab Server filter for outgoing mails.
 *
 * $Horde: framework/Kolab_Filter/lib/Horde/Kolab/Filter/Content.php,v 1.4.2.8 2009-11-29 10:43:57 wrobel Exp $
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
class Horde_Kolab_Filter_Content extends Horde_Kolab_Filter_Base
{
    /**
     * Handle the message.
     *
     * @param int    $inh  The file handle pointing to the message.
     * @param string $transport  The name of the transport driver.
     *
     * @return mixed A PEAR_Error in case of an error, nothing otherwise.
     */
    function _parse($inh, $transport)
    {
        global $conf;

        $result = $this->init();
        if (is_a($result, 'PEAR_Error')) {
            return $result;
        }

        if (isset($conf['kolab']['filter']['verify_from_header'])) {
            $verify_from_header = $conf['kolab']['filter']['verify_from_header'];
        } else {
            $verify_from_header = false;
        }

        if (isset($conf['kolab']['filter']['allow_sender_header'])) {
            $allow_sender_header = $conf['kolab']['filter']['allow_sender_header'];
        } else {
            $allow_sender_header = false;
        }

        if (isset($conf['kolab']['filter']['allow_outlook_ical_forward'])) {
            $allow_outlook_ical_forward = $conf['kolab']['filter']['allow_outlook_ical_forward'];
        } else {
            $allow_outlook_ical_forward = true;
        }

        if (empty($transport)) {
            $transport = 'smtp';
        }

        $ical = false;
        $from = false;
        $subject = false;
        $senderok = true;
        $rewrittenfrom = false;
        $state = RM_STATE_READING_HEADER;

        while (!feof($inh) && $state != RM_STATE_READING_BODY) {

            $buffer = fgets($inh, 8192);
            $line = rtrim($buffer, "\r\n");

            if ($line == '') {
                /* Done with headers */
                $state = RM_STATE_READING_BODY;
                if ($from && $verify_from_header) {
                    $rc = $this->_verify_sender($this->_sasl_username, $this->_sender, 
                                                $from, $this->_client_address);
                    if (is_a($rc, 'PEAR_Error')) {
                        return $rc;
                    } else if ($rc === true) {
                        /* All OK, do nothing */
                    } else if ($rc === false) {
                        /* Reject! */
                        $senderok = false;
                    } else if (is_string($rc)) {
                        /* Rewrite from */
                        if (strpos($from, $rc) === false) {
                            Horde::logMessage(sprintf("Rewriting '%s' to '%s'",
                                                      $from, $rc), 
                                              __FILE__, __LINE__, PEAR_LOG_DEBUG);
                            $rewrittenfrom = "From: $rc\r\n";
                        }
                    }
                }
            } else {
                if ($line[0] != ' ' && $line[0] != "\t") {
                    $state = RM_STATE_READING_HEADER;
                }
                switch( $state ) {
                case RM_STATE_READING_HEADER:
                    if ($allow_sender_header &&
                        eregi('^Sender: (.*)', $line, $regs)) {
                        $from = $regs[1];
                        $state = RM_STATE_READING_SENDER;
                    } else if (!$from && eregi('^From: (.*)', $line, $regs)) {
                        $from = $regs[1];
                        $state = RM_STATE_READING_FROM;
                    } else if (eregi('^Subject: (.*)', $line, $regs)) {
                        $subject = $regs[1];
                        $state = RM_STATE_READING_SUBJECT;
                    } else if (eregi('^Content-Type: text/calendar', $line)) {
                        Horde::logMessage("Found iCal data in message",
                                          __FILE__, __LINE__, PEAR_LOG_DEBUG);
                        $ical = true;
                    } else if (eregi('^Message-ID: (.*)', $line, $regs)) {
                        $this->_id = $regs[1];
                    }
                    break;
                case RM_STATE_READING_FROM:
                    $from .= $line;
                    break;
                case RM_STATE_READING_SENDER:
                    $from .= $line;
                    break;
                case RM_STATE_READING_SUBJECT:
                    $subject .= $line;
                    break;
                }
            }
            if (@fwrite($this->_tmpfh, $buffer) === false) {
                $msg = $php_errormsg;
                return PEAR::raiseError(sprintf("Error: Could not write to %s: %s",
                                                $this->_tmpfile, $msg),
                                        OUT_LOG | EX_IOERR);
            }
        }
        while (!feof($inh)) {
            $buffer = fread($inh, 8192);
            if (@fwrite($this->_tmpfh, $buffer) === false) {
                $msg = $php_errormsg;
                return PEAR::raiseError(sprintf("Error: Could not write to %s: %s",
                                                $this->_tmpfile, $msg),
                                        OUT_LOG | EX_IOERR);
            }
        }

        if (@fclose($this->_tmpfh) === false) {
            $msg = $php_errormsg;
            return PEAR::raiseError(sprintf("Error: Failed closing %s: %s",
                                            $this->_tmpfile, $msg),
                                    OUT_LOG | EX_IOERR);
        }

        if (!$senderok) {
            if ($ical && $allow_outlook_ical_forward ) {
                require_once(dirname(__FILE__) . '/Outlook.php');
                $rc = Kolab_Filter_Outlook::embedICal($this->_fqhostname,
                                                      $this->_sender,
                                                      $this->_recipients,
                                                      $from, $subject,
                                                      $this->_tmpfile,
                                                      $transport);
                if (is_a($rc, 'PEAR_Error')) {
                    return $rc;
                } else if ($rc === true) {
                    return;
                }
            } else {
                return PEAR::raiseError(sprintf("Invalid From: header. %s looks like a forged sender",
                                                $from),
                                        OUT_LOG | OUT_STDOUT | EX_NOPERM);
            }
        }

        $result = $this->_deliver($rewrittenfrom, $transport);
        if (is_a($result, 'PEAR_Error')) {
            return $result;
        }
    }

    /**
     * Deliver the message.
     *
     * @param string $transport  The name of the transport driver.
     *
     * @return mixed A PEAR_Error in case of an error, nothing otherwise.
     */
    function _deliver($rewrittenfrom, $transport)
    {
        global $conf;

        if (isset($conf['kolab']['filter']['smtp_host'])) {
            $host = $conf['kolab']['filter']['smtp_host'];
        } else {
            $host = 'localhost';
        }
        if (isset($conf['kolab']['filter']['smtp_port'])) {
            $port = $conf['kolab']['filter']['smtp_port'];
        } else {
            $port = 10025;
        }

        $transport = &Horde_Kolab_Filter_Transport::factory($transport, 
                                               array('host' => $host, 
                                                     'port' => $port));

        $tmpf = @fopen($this->_tmpfile, 'r');
        if (!$tmpf) {
            $msg = $php_errormsg;
            return PEAR::raiseError(sprintf("Error: Could not open %s for writing: %s",
                                            $this->_tmpfile, $msg),
                                    OUT_LOG | EX_IOERR);
        }

        $result = $transport->start($this->_sender, $this->_recipients);
        if (is_a($result, 'PEAR_Error')) {
            return $result;
        }

        $state = RM_STATE_READING_HEADER;
        while (!feof($tmpf) && $state != RM_STATE_READING_BODY) {
            $buffer = fgets($tmpf, 8192);
            if ($rewrittenfrom) {
                if (eregi( '^From: (.*)', $buffer)) {
                    $result = $transport->data($rewrittenfrom);
                    if (is_a($result, 'PEAR_Error')) {
                        return $result;
                    }
                    $state = RM_STATE_READING_FROM;
                    continue;
                } else if ($state == RM_STATE_READING_FROM &&
                           ($buffer[0] == ' ' || $buffer[0] == "\t")) {
                    /* Folded From header, ignore */
                    continue;
                }
            }
            if (rtrim($buffer, "\r\n") == '') {
                $state = RM_STATE_READING_BODY;
            } else if ($buffer[0] != ' ' && $buffer[0] != "\t")  {
                $state = RM_STATE_READING_HEADER;
            }
            $result = $transport->data($buffer);
            if (is_a($result, 'PEAR_Error')) {
                return $result;
            }
        }
        while (!feof($tmpf)) {
            $buffer = fread($tmpf, 8192);
            $len = strlen($buffer);

            /* We can't tolerate that the buffer breaks the data
             * between \r and \n, so we try to avoid that. The limit
             * of 100 reads is to battle abuse
             */
            while ($buffer{$len-1} == "\r" && $len < 8192 + 100) {
                $buffer .= fread($tmpf,1);
                $len++;
            }
            $result = $transport->data($buffer);
            if (is_a($result, 'PEAR_Error')) {
                return $result;
            }
        }
        return $transport->end();
    }

    /**
     * Check that the From header is not trying to impersonate a valid
     * user that is not $sasluser.
     *
     * @param string $sasluser    The current, authenticated user.
     * @param string $sender      Sender address
     * @param string $fromhdr     From header
     * @param string $client_addr Client IP
     *
     * @return mixed A PEAR_Error in case of an error, true if From
     *               can be accepted, false if From must be rejected,
     *               or a string with a corrected From header that
     *               makes From acceptable
     */
    function _verify_sender($sasluser, $sender, $fromhdr, $client_addr) {

        global $conf;

        if (isset($conf['kolab']['filter']['email_domain'])) {
            $domains = $conf['kolab']['filter']['email_domain'];
        } else {
            $domains = 'localhost';
        }

        if (!is_array($domains)) {
            $domains = array($domains);
        }

        if (isset($conf['kolab']['filter']['local_addr'])) {
            $local_addr = $conf['kolab']['filter']['local_addr'];
        } else {
            $local_addr = '127.0.0.1';
        }

        if (empty($client_addr)) {
            $client_addr = $local_addr;
        }

        if (isset($conf['kolab']['filter']['verify_subdomains'])) {
            $verify_subdomains = $conf['kolab']['filter']['verify_subdomains'];
        } else {
            $verify_subdomains = true;
        }

        if (isset($conf['kolab']['filter']['reject_forged_from_header'])) {
            $reject_forged_from_header = $conf['kolab']['filter']['reject_forged_from_header'];
        } else {
            $reject_forged_from_header = false;
        }

        if (isset($conf['kolab']['filter']['kolabhosts'])) {
            $kolabhosts = $conf['kolab']['filter']['kolabhosts'];
        } else {
            $kolabhosts = 'localhost';
        }

        if (isset($conf['kolab']['filter']['privileged_networks'])) {
            $privnetworks = $conf['kolab']['filter']['privileged_networks'];
        } else {
            $privnetworks = '127.0.0.0/8';
        }

        /* Allow anything from localhost and
         * fellow Kolab-hosts 
         */
        if ($client_addr == $local_addr) {
            return true;
        }

        $kolabhosts = split(',', $kolabhosts);
        $kolabhosts = array_map('gethostbyname', $kolabhosts );

        $privnetworks = split(',', $privnetworks);

        if (array_search($client_addr, $kolabhosts) !== false) {
            return true;
        }

        foreach ($privnetworks as $network) {

            $iplong = ip2long($client_addr);
            $cidr = explode("/", $network);
            $netiplong = ip2long($cidr[0]);
            if (count($cidr) == 2) {
                $iplong = $iplong & (0xffffffff << 32 - $cidr[1]);
                $netiplong = $netiplong & (0xffffffff << 32 - $cidr[1]);
            }

            if ($iplong == $netiplong) {
                return true;
            }
        }

        if ($sasluser) {
            /* Load the Server library */
            require_once 'Horde/Kolab/Server.php';

            $server = &Horde_Kolab_Server::singleton();
            if (is_a($server, 'PEAR_Error')) {
                $server->code = OUT_LOG | EX_TEMPFAIL;
                return $server;
            }

            $allowed_addrs = $server->addrsForIdOrMail($sasluser);
            if (is_a($allowed_addrs, 'PEAR_Error')) {
                $allowed_addrs->code = OUT_LOG | EX_NOUSER;
                return $allowed_addrs;
            }
        } else {
            $allowed_addrs = false;
        }

        if ($sasluser) {
            if (isset($conf['kolab']['filter']['untrusted_subject_insert'])) {
                $fmt = $conf['kolab']['filter']['untrusted_subject_insert'];
            } else {
                $fmt = _("(UNTRUSTED, sender is <%s>)");
            }
        } else {
            if (isset($conf['kolab']['filter']['unauthenticated_subject_insert'])) {
                $fmt = $conf['kolab']['filter']['unauthenticated_subject_insert'];
            } else {
                $fmt = _("(UNTRUSTED, sender <%s> is not authenticated)");
            }
        }

        $adrs = imap_rfc822_parse_adrlist($fromhdr, $domains[0]);

        foreach ($adrs as $adr) {
            $from = $adr->mailbox . '@' . $adr->host;
            $fromdom = $adr->host;

            if ($sasluser) {
                if (!in_array(strtolower($from), $allowed_addrs)) {
                    Horde::logMessage(sprintf("%s is not an allowed From address for %s", 
                                              $from, $sasluser), __FILE__, __LINE__, PEAR_LOG_DEBUG);
                    return false;
                }
            } else {
                foreach ($domains as $domain) {
                    if (strtolower($fromdom) == $domain 
                        || ($verify_subdomains
                            && substr($fromdom, -strlen($domain)-1) == ".$domain")) {
                        if ($reject_forged_from_header) {
                            Horde::logMessage(sprintf("%s is not an allowed From address for unauthenticated users.", 
                                                      $from), __FILE__, __LINE__, PEAR_LOG_DEBUG);
                            return false;
                        } else {
                            require_once 'Horde/String.php';
                            require_once 'Horde/MIME.php';

                            /* Rewrite */
                            Horde::logMessage(sprintf("%s is not an allowed From address for unauthenticated users, rewriting.", 
                                                      $from), __FILE__, __LINE__, PEAR_LOG_DEBUG);

                            if (property_exists($adr, 'personal')) {
                                $name = str_replace(array("\\", '"'), 
                                                    array("\\\\",'\"'), 
                                                    MIME::decode($adr->personal, 'utf-8'));
                            } else {
                                $name = '';
                            }

                            $untrusted = sprintf($fmt, $sender, $from, $name);

                            // Is this test really correct?  Is $fromhdr a _decoded_ string?
                            // If not comparing with the unencoded $untrusted is wrong.
                            // sw - 20091125
                            if (strpos( $fromhdr, $untrusted )===false) {
                                $new_from = '"' . MIME::encode($untrusted) . '"';
                                return  $new_from . ' <' . $from . '>';
                            } else {
                                return true;
                            }
                        }
                    }
                }
            }
        }

        /* All seems OK */
        return true;
    }
}

?>
