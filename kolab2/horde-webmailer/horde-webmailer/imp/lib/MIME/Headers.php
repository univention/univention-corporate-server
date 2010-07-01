<?php
/**
 * @package Horde_MIME
 */

require_once 'Horde/MIME/Headers.php';
require_once IMP_BASE . '/lib/version.php';

/**
 * The description of the IMP program to use in the 'User-Agent:' header.
 */
define('IMP_AGENT_HEADER', 'Internet Messaging Program (IMP) ' . IMP_VERSION);

/**
 * The IMP_Headers:: class contains all functions related to handling the
 * headers of mail messages in IMP.
 *
 * $Horde: imp/lib/MIME/Headers.php,v 1.92.2.41 2009-11-19 19:04:35 slusarz Exp $
 *
 * Copyright 2002-2009 The Horde Project (http://www.horde.org/)
 *
 * See the enclosed file COPYING for license information (GPL). If you
 * did not receive this file, see http://www.fsf.org/copyleft/gpl.html.
 *
 * @author  Michael Slusarz <slusarz@horde.org>
 * @package Horde_MIME
 */
class IMP_Headers extends MIME_Headers {

    /**
     * The User-Agent string to use.
     *
     * @var string
     */
    var $_agent = IMP_AGENT_HEADER;

    /**
     * The header object cache.
     *
     * @var array
     */
    var $_obCache = array();

    /**
     * Returns a reference to a currently open IMAP stream.
     *
     * @see MIME_Headers::_getStream()
     */
    function _getStream()
    {
        $imp_imap = &IMP_IMAP::singleton();
        return $imp_imap->stream();
    }

    /**
     * Parses all of the available mailing list headers.
     */
    function parseAllListHeaders()
    {
        foreach ($this->listHeaders() as $val => $str) {
            $this->parseListHeaders($val);
        }
    }

    /**
     * Parses the information in the mailing list headers.
     *
     * @param string $header  The header to process.
     * @param boolean $raw    Should the raw email be returned instead of
     *                        setting the header value?
     *
     * @return string  The header value (if $raw == true).
     */
    function parseListHeaders($header, $raw = false)
    {
        if (!($data = $this->getValue($header))) {
            return;
        }

        $output = '';

        require_once 'Horde/Text.php';

        /* Split the incoming data by the ',' character. */
        foreach (preg_split("/,/", $data) as $entry) {
            /* Get the data inside of the brackets. If there is no brackets,
             * then return the raw text. */
            if (!preg_match("/\<([^\>]+)\>/", $entry, $matches)) {
                return trim($entry);
            }

            /* Remove all whitespace from between brackets (RFC 2369 [2]). */
            $match = preg_replace("/\s+/", '', $matches[1]);

            /* Determine if there are any comments. */
            preg_match("/(\(.+\))/", $entry, $comments);

            /* RFC 2369 [2] states that we should only show the *FIRST* URL
             * that appears in a header that we can adequately handle. */
            if (stristr($match, 'mailto:') !== false) {
                $match = substr($match, strpos($match, ':') + 1);
                if ($raw) {
                    return $match;
                }
                $output = Horde::link(IMP::composeLink($match)) . $match . '</a>';
                if (!empty($comments[1])) {
                    $output .= '&nbsp;' . $comments[1];
                }
                break;
            } elseif (!$raw) {
                require_once 'Horde/Text/Filter.php';
                if ($url = Text_Filter::filter($match, 'linkurls', array('callback' => 'Horde::externalUrl'))) {
                    $output = $url;
                    if (!empty($comments[1])) {
                        $output .= '&nbsp;' . $comments[1];
                    }
                    break;
                } else {
                    /* Use this entry unless we can find a better one. */
                    $output = $match;
                }
            }
        }

        $this->setValue($header, $output);
    }

    /**
     * Adds any site-specific headers defined in config/header.php to the
     * internal header array.
     */
    function addSiteHeaders()
    {
        static $_header;

        /* Add the 'User-Agent' header. */
        $this->addAgentHeader();

        /* Tack on any site-specific headers. */
        if (is_callable(array('Horde', 'loadConfiguration'))) {
            $result = Horde::loadConfiguration('header.php', array('_header'));
            if (!is_a($result, 'PEAR_Error')) {
                extract($result);
            }
        } else {
            require IMP_BASE . '/config/header.php';
            $result = true;
        }

        if (!is_a($result, 'PEAR_Error')) {
            foreach ($_header as $key => $val) {
                $this->addHeader(trim($key), trim($val));
            }
        }
    }

    /**
     * Builds a string containing a list of addresses.
     *
     * @param string $field    The address field to parse.
     * @param integer $addURL  The self URL.
     * @param boolean $set     Set the associated header with the return
     *                         string?
     * @param boolean $link    Link each address to the compose screen?
     *
     * @return string  String containing the formatted address list.
     */
    function buildAddressLinks($field, $addURL, $set = false, $link = true)
    {
        global $prefs, $registry;

        $add_link = null;

        /* Make sure this is a valid object address field. */
        $array = $this->getOb($field);
        if (empty($array) || !is_array($array)) {
            return null;
        }

        /* Set up the add address icon link if contact manager is
         * available. */
        if ($link && $prefs->getValue('add_source')) {
            $add_link = $registry->link('contacts/add', array('source' => $prefs->getValue('add_source')));
            if (is_a($add_link, 'PEAR_Error')) {
                if ($registry->hasMethod('contacts/import')) {
                    $add_link = Util::addParameter($addURL, 'actionID', 'add_address');
                } else {
                    $add_link = null;
                }
            }
        }

        $addr_array = array();

        foreach ($this->getAddressesFromObject($array) as $ob) {
            if (isset($ob->groupname)) {
                $group_array = array();
                foreach ($ob->addresses as $ad) {
                    if (empty($ad->address) || empty($ad->inner)) {
                        continue;
                    }

                    $ret = htmlspecialchars($ad->display);

                    /* If this is an incomplete e-mail address, don't link to
                     * anything. */
                    if (stristr($ad->host, 'UNKNOWN') === false) {
                        if ($link) {
                            $ret = Horde::link(IMP::composeLink(array('to' => $ad->address)), sprintf(_("New Message to %s"), $ad->inner)) . htmlspecialchars($ad->display) . '</a>';
                        }

                        /* Append the add address icon to every address if contact
                         * manager is available. */
                        if ($add_link) {
                            $curr_link = Util::addParameter($add_link, array('name' => $ad->personal, 'address' => $ad->inner));
                            $ret .= Horde::link($curr_link, sprintf(_("Add %s to my Address Book"), $ad->inner)) .
                                Horde::img('addressbook_add.png', sprintf(_("Add %s to my Address Book"), $ad->inner)) . '</a>';
                        }
                    }

                    $group_array[] = $ret;
                }

                $addr_array[] = htmlspecialchars($ob->groupname) . ':' . (count($group_array) ? ' ' . implode(', ', $group_array) : '');
            } elseif (!empty($ob->address) && !empty($ob->inner)) {
                $ret = htmlspecialchars($ob->display);

                /* If this is an incomplete e-mail address, don't link to
                 * anything. */
                if (stristr($ob->host, 'UNKNOWN') === false) {
                    if ($link) {
                        $ret = Horde::link(IMP::composeLink(array('to' => $ob->address)), sprintf(_("New Message to %s"), $ob->inner)) . htmlspecialchars($ob->display) . '</a>';
                    }

                    /* Append the add address icon to every address if contact
                     * manager is available. */
                    if ($add_link) {
                        $curr_link = Util::addParameter($add_link, array('name' => $ob->personal, 'address' => $ob->inner));
                        $ret .= Horde::link($curr_link, sprintf(_("Add %s to my Address Book"), $ob->inner)) .
                            Horde::img('addressbook_add.png', sprintf(_("Add %s to my Address Book"), $ob->inner)) . '</a>';
                    }
                }

                $addr_array[] = $ret;
            }
        }

        /* If left with an empty address list ($ret), inform the user that the
         * recipient list is purposely "undisclosed". */
        if (empty($addr_array)) {
            $ret = _("Undisclosed Recipients");
        } else {
            /* Build the address line. */
            $addr_count = count($addr_array);
            $ret = '<span class="nowrap">' . implode(',</span> <span class="nowrap">', $addr_array) . '</span>';
            if ($link && $addr_count > 15) {
                Horde::addScriptFile('prototype.js', 'imp', true);

                $ret = '<span>' .
                    '<span onclick="[ this, this.next(), this.next(1) ].invoke(\'toggle\')" class="widget largeaddrlist">' . sprintf(_("[Show Addresses - %d recipients]"), $addr_count) . '</span>' .
                    '<span onclick="[ this, this.previous(), this.next() ].invoke(\'toggle\')" class="widget largeaddrlist" style="display:none">' . _("[Hide Addresses]") . '</span>' .
                    '<span style="display:none">' .
                    $ret . '</span></span>';
            }
        }

        /* Set the header value, if requested. */
        if (!empty($set)) {
            $this->setValue($field, $ret);
        }

        return $ret;
    }

    /**
     * Return the list of addresses for a header object.
     *
     * @TODO Merge back to Horde_Mime_Headers with the changes to support
     * groups.
     *
     * @param array $obs  An array of header objects (See imap_headerinfo()
     *                    for the object structure).
     *
     * @return array  An array of objects.
     * <pre>
     * Object elements:
     * 'address'   -  Full address
     * 'display'   -  A displayable version of the address
     * 'host'      -  Host name
     * 'inner'     -  Trimmed, bare address
     * 'personal'  -  Personal string
     * </pre>
     */
    function getAddressesFromObject($obs)
    {
        $retArray = array();

        if (!is_array($obs) || empty($obs)) {
            return $retArray;
        }

        foreach ($obs as $ob) {
            if (isset($ob->groupname)) {
                $newOb = new stdClass;
                $newOb->addresses = $this->getAddressesFromObject($ob->addresses);
                $newOb->groupname = $ob->groupname;

                $retArray[] = $newOb;
                continue;
            }

            /* Ensure we're working with initialized values. */
            $ob->personal = (isset($ob->personal)) ? stripslashes(trim(MIME::decode($ob->personal), '"')) : '';

            if (isset($ob->mailbox)) {
                /* Don't process invalid addresses. */
                if (strpos($ob->mailbox, 'UNEXPECTED_DATA_AFTER_ADDRESS') !== false ||
                    strpos($ob->mailbox, 'INVALID_ADDRESS') !== false) {
                    continue;
                }
            } else {
                $ob->mailbox = '';
            }

            if (!isset($ob->host)) {
                $ob->host = '';
            }

            $inner = MIME::trimEmailAddress(MIME::rfc822WriteAddress($ob->mailbox, $ob->host, ''));

            /* Generate the new object. */
            $newOb = new stdClass;
            $newOb->address = MIME::addrObject2String($ob, array('undisclosed-recipients@', 'Undisclosed recipients@'));
            $newOb->display = (empty($ob->personal) ? '' : $ob->personal . ' <') . $inner . (empty($ob->personal) ? '' : '>');
            $newOb->host = $ob->host;
            $newOb->inner = $inner;
            $newOb->personal = $ob->personal;

            $retArray[] = $newOb;
        }

        return $retArray;
    }

    /**
     * Adds the local time string to the date header.
     *
     * @param string $date  The date string.
     *
     * @return string  The date string with the local time added on.
     */
    function addLocalTime($date)
    {
        if (empty($date)) {
            $ltime = false;
        } else {
            $date = preg_replace('/\s+\(\w+\)$/', '', $date);
            $ltime = strtotime($date);
        }
        if ($ltime !== false && $ltime !== -1) {
            $date_str = strftime($GLOBALS['prefs']->getValue('date_format'), $ltime);
            $time_str = strftime($GLOBALS['prefs']->getValue('time_format'), $ltime);
            $tz = strftime('%Z');
            if ((date('Y') != @date('Y', $ltime)) ||
                (date('M') != @date('M', $ltime)) ||
                (date('d') != @date('d', $ltime))) {
                /* Not today, use the date. */
                $date .= sprintf(' <small>[%s %s %s]</small>', $date_str, $time_str, $tz);
            } else {
                /* Else, it's today, use the time only. */
                $date .= sprintf(' <small>[%s %s]</small>', $time_str, $tz);
            }
        }

        return $date;
    }

    /**
     * Returns a header from the header object.
     *
     * @todo Move to framework for Horde 4.0.
     *
     * @param string $field  The header to return as an object.
     *
     * @return mixed  The field requested.
     */
    function getOb($field)
    {
        if (!isset($this->_obCache[$field])) {
            $ob = IMP::parseAddressList($this->getValue($field));
            if (is_a($ob, 'PEAR_Error')) {
                $ob = array();
            }
            $this->_obCache[$field] = $ob;
        }
        return $this->_obCache[$field];
    }

    /**
     * Explicitly sets the User-Agent string.
     *
     * @todo Move to framework for Horde 4.0.
     * @since IMP 4.2
     *
     * @param string $useragent  The User-Agent string to use.
     */
    function setUserAgent($useragent)
    {
        $this->_agent = $useragent;
    }

    /**
     * Determines the X-Priority of the message based on the headers.
     *
     * @since IMP 4.2
     *
     * @return string  'high', 'low', or 'normal'.
     */
    function getXpriority()
    {
        if (($priority = $this->getValue('x-priority')) &&
            preg_match('/\s*(\d+)\s*/', $priority, $matches)) {
            if (in_array($matches[1], array(1, 2))) {
                return 'high';
            } elseif (in_array($matches[1], array(4, 5))) {
                return 'low';
            }
        }

        return 'normal';
    }

    /**
     * Returns e-mail information for a mailing list.
     *
     * @since IMP 4.2
     *
     * @return array  An array with 2 elements: 'exists' and 'reply_list'.
     */
    function getListInformation()
    {
        $ret = array('exists' => false, 'reply_list' => null);

        if ($this->listHeadersExist()) {
            $ret['exists'] = true;

            /* See if the List-Post header provides an e-mail address for the
             * list. */
            if ($this->getValue('list-post')) {
                $ret['reply_list'] = $this->parseListHeaders('list-post', true);
            }
        }

        return $ret;
    }

}
