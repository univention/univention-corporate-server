<?php
/**
 * The IMP_UI_Mailbox:: class is designed to provide a place to dump common
 * code shared among IMP's various UI views for the mailbox page.
 *
 * $Horde: imp/lib/UI/Mailbox.php,v 1.9.2.7 2009-01-06 15:24:12 jan Exp $
 *
 * Copyright 2006-2009 The Horde Project (http://www.horde.org/)
 *
 * See the enclosed file COPYING for license information (GPL). If you
 * did not receive this file, see http://www.fsf.org/copyleft/gpl.html.
 *
 * @author  Michael Slusarz <slusarz@horde.org>
 * @package IMP
 * @since   IMP 4.2
 */
class IMP_UI_Mailbox {

    /**
     */
    var $_charset;

    /**
     */
    var $_identity;

    /**
     */
    var $_mailbox;

    /**
     */
    var $_c = array();

    /**
     */
    function IMP_UI_Mailbox($mailbox = null, $charset = null, $identity = null)
    {
        $this->_mailbox = $mailbox;
        $this->_charset = $charset;
        $this->_identity = $identity;
    }

    /**
     */
    function getFrom($ob)
    {
        $ret = array('error' => false, 'to' => false);

        if (!isset($this->_c['drafts_sm_folder'])) {
            $this->_c['drafts_sm_folder'] = IMP::isSpecialFolder($this->_mailbox);
        }

        if (isset($ob->from)) {
            $ob->from = stripslashes($ob->from);
            $from_adr = IMP::bareAddress($ob->from);
            $from_ob = IMP::parseAddressList($ob->from);
            if (!is_a($from_ob, 'PEAR_Error')) {
                $from_ob = array_shift($from_ob);
            }
            if ($from_adr === null) {
                $ret['from'] = _("Invalid Address");
                $ret['error'] = true;
            } elseif ($this->_identity->hasAddress($from_adr)) {
                if (isset($ob->to)) {
                    if (strstr($ob->to, 'undisclosed-recipients:')) {
                        $ret['from'] = _("Undisclosed Recipients");
                        $ret['error'] = true;
                    } else {
                        $ob->to = stripslashes($ob->to);
                        $tmp = IMP::parseAddressList($ob->to);
                        if (!is_a($tmp, 'PEAR_Error')) {
                            $tmp = array_shift($tmp);
                        }
                        if (isset($tmp->personal)) {
                            $ret['from'] = MIME::decode($tmp->personal, $this->_charset);
                        } else {
                            $ret['from'] = IMP::bareAddress($ob->to);
                        }
                        $ret['fullfrom'] = MIME::decode($ob->to, $this->_charset);
                        if (empty($ret['from'])) {
                            $ret['from'] = $ret['fullfrom'];
                        }
                    }
                } else {
                    $ret['from'] = _("Undisclosed Recipients");
                    $ret['error'] = true;
                }
                if (!$this->_c['drafts_sm_folder']) {
                    $ret['from'] = _("To") . ': ' . stripslashes(trim($ret['from'], '"'));
                }
                $ret['to'] = true;
            } elseif (isset($from_ob->personal)) {
                $ret['from'] = MIME::decode($from_ob->personal, $this->_charset);
                if (!trim($ret['from'], chr(160) . ' ')) {
                    $ret['from'] = $from_adr;
                }
                if ($this->_c['drafts_sm_folder']) {
                    $ret['from'] = _("From") . ': ' . $ret['from'];
                }
                $ret['fullfrom'] = MIME::decode($ob->from, $this->_charset);
            } else {
                if (!isset($from_ob->host) ||
                    (strstr($from_ob->host, 'SYNTAX-ERROR') !== false)) {
                    $ret['from'] = (!empty($from_adr)) ? $from_adr : _("Unknown Recipient");
                    $ret['error'] = true;
                } else {
                    $ret['from'] = $from_adr;
                    $ret['fullfrom'] = MIME::decode($ob->from, $this->_charset);
                }
            }
        } else {
            $ret['from'] = _("Invalid Address");
            $ret['error'] = true;
        }

        $ret['from'] = stripslashes(trim($ret['from'], '"'));
        if (!isset($ret['fullfrom'])) {
            $ret['fullfrom'] = $ret['from'];
        }

        return $ret;
    }

    /**
     */
    function getSize($size)
    {
        if ($size > 1024) {
            if (!isset($this->_c['localeinfo'])) {
                $this->_c['localeinfo'] = NLS::getLocaleInfo();
            }
            $size = $size / 1024;
            if ($size > 1024) {
                return sprintf(_("%s MB"), number_format($size / 1024, 1, $this->_c['localeinfo']['decimal_point'], $this->_c['localeinfo']['thousands_sep']));
            } else {
                return sprintf(_("%s KB"), number_format($size, 0, $this->_c['localeinfo']['decimal_point'], $this->_c['localeinfo']['thousands_sep']));
            }
        } else {
            return $size;
        }
    }

    /**
     */
    function getAttachmentAltList()
    {
        return array(
            'signed' => _("Message is signed"),
            'encrypted' => _("Message is encrypted"),
            'attachment' => _("Message has attachments")
        );
    }

    /**
     */
    function getAttachmentAlt($attachment)
    {
        $list = $this->getAttachmentAltList();
        return (isset($list[$attachment])) ? $list[$attachment] : $list['attachment'];
    }

    /**
     */
    function getAttachmentType($structure)
    {
        if ($structure->getPrimaryType() == 'multipart') {
            switch ($structure->getSubType()) {
            case 'signed':
                return 'signed';

            case 'encrypted':
                return 'encrypted';

            case 'alternative':
            case 'related':
                /* Treat this as no attachments. */
                break;

            default:
                return 'attachment';
            }
        } elseif ($structure->getType() == 'application/pkcs7-mime') {
             return 'encrypted';
        }

        return '';
    }

    /**
     */
    function getDate($date)
    {
        if (!isset($this->_c['curr_time'])) {
            $this->_c['curr_time'] = time();
            $this->_c['curr_time'] -= $this->_c['curr_time'] % 60;
        }

        /* Formats the header date string nicely. */
        if (!empty($date)) {
            $date = preg_replace('/\s+\(\w+\)$/', '', $date);
            $udate = strtotime($date, $this->_c['curr_time']);
        }

        if (empty($date)) {
            return _("Unknown Date");
        } elseif (empty($udate) || ($udate === -1)) {
            if (substr($date, -3) != ' UT') {
                return _("Unknown Date");
            }
            $udate = strtotime($date . 'C', $this->_c['curr_time']);
            if (empty($udate) || ($udate === -1)) {
                return _("Unknown Date");
            }
        }

        if (!isset($this->_c['today_start'])) {
            $ltime_val = localtime();
            $this->_c['today_start'] = mktime(0, 0, 0, $ltime_val[4] + 1, $ltime_val[3], 1900 + $ltime_val[5]);
            $this->_c['today_end'] = $this->_c['today_start'] + 86400;
            $this->_c['datefmt'] = $GLOBALS['prefs']->getValue('date_format');
            $this->_c['timefmt'] = $GLOBALS['prefs']->getValue('time_format');
        }

        if (($udate < $this->_c['today_start']) ||
            ($udate > $this->_c['today_end'])) {
            /* Not today, use the date. */
            return strftime($this->_c['datefmt'], $udate);
        }

        /* Else, it's today, use the time. */
        return strftime($this->_c['timefmt'], $udate);
    }

    /**
     */
    function getSubject($subject)
    {
        $subject = MIME::decode($subject, $this->_charset);
        if (!empty($subject)) {
            $subject = strtr($subject, "\t", ' ');
        }
        return IMP::filterText($subject);
    }

}
