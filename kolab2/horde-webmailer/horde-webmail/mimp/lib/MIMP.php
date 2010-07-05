<?php
/**
 * MIMP Base Class.
 *
 * $Horde: mimp/lib/MIMP.php,v 1.69.2.7 2009-01-06 15:24:53 jan Exp $
 *
 * Copyright 1999-2009 The Horde Project (http://www.horde.org/)
 *
 * See the enclosed file COPYING for license information (GPL). If you
 * did not receive this file, see http://www.fsf.org/copyleft/gpl.html.
 *
 * @author  Chuck Hagenbuch <chuck@horde.org>
 * @package MIMP
 */
class MIMP {

    /**
     * Take a Horde_Mobile_card and add global MIMP menu items.
     *
     * @param Horde_Mobile_linkset &$menu  The menu linkset, with page-specific
     *                                     options already filled in.
     * @param string $page                 The current page ('compose',
     *                                     'folders', 'mailbox', 'message').
     */
    function addMIMPMenu(&$menu, $page)
    {
        $items = array();
        if (!in_array($page, array('mailbox', 'message')) ||
            ($GLOBALS['imp_mbox']['mailbox'] != 'INBOX')) {
            $items[MIMP::generateMIMPUrl('mailbox.php', 'INBOX')] = _("Inbox");
        }
        if ($page != 'compose') {
            $items[Util::addParameter(Horde::url(MIMP_WEBROOT . 'compose.php'), 'u', base_convert(microtime() . mt_rand(), 10, 36))] = _("New Message");
        }
        if ($page != 'folders') {
            $items[Horde::url(MIMP_WEBROOT . 'folders.php')] = _("Folders");
        }
        // @TODO - Options for mobile browsers
        // if ($options_link = Horde::getServiceLink('options', 'mimp')) {
        //     $items[Util::addParameter($options_link, 'mobile', 1, false)] = _("Options");
        // }
        $logout_link = IMP::getLogoutUrl();
        if (!empty($logout_link)) {
            $items[Auth::addLogoutParameters($logout_link, AUTH_REASON_LOGOUT)] = _("Log out");
        }

        foreach ($items as $link => $label) {
            $menu->add(new Horde_Mobile_link($label, $link));
        }

        if (is_readable(MIMP_BASE . '/config/menu.php')) {
            include MIMP_BASE . '/config/menu.php';
            if (isset($_menu) && is_array($_menu)) {
                foreach ($_menu as $menuitem) {
                    if ($menuitem == 'separator') {
                        continue;
                    }
                    $menu->add(new Horde_Mobile_link($menuitem['text'], $menuitem['url']));
                }
            }
        }
    }

    /**
     * Generates a URL with necessary mailbox/index information for MIMP.
     *
     * @param string $page      Page name to link to.
     * @param string $mailbox   The base mailbox to use on the linked page.
     * @param string $index     The index to use on the linked page.
     * @param string $tmailbox  The mailbox associated with $index.
     *
     * @return string  URL to $page with any necessary mailbox information
     *                 added to the parameter list of the URL.
     */
    function generateMIMPUrl($page, $mailbox, $index = null, $tmailbox = null)
    {
        return Util::addParameter(Horde::url(MIMP_WEBROOT . $page), IMP::getIMPMboxParameters($mailbox, $index, $tmailbox));
    }

    /**
     * Returns the appropriate link to call the message composition screen.
     *
     * @since MIMP 1.1
     *
     * @param mixed $args   List of arguments to pass to compose.php. If this
     *                      is passed in as a string, it will be parsed as a
     *                      toaddress?subject=foo&cc=ccaddress (mailto-style)
     *                      string.
     * @param array $extra  Hash of extra, non-standard arguments to pass to
     *                      compose.php.
     *
     * @return string  The link to the message composition screen.
     */
    function composeLink($args = array(), $extra = array())
    {
        return Util::addParameter(Horde::url(MIMP_WEBROOT . 'compose.php'), IMP::composeLinkArgs($args, $extra));
    }

}
