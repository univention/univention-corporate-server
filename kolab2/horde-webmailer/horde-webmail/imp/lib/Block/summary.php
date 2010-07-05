<?php

$block_name = _("Folder Summary");

/**
 * $Horde: imp/lib/Block/summary.php,v 1.54.2.11 2007-12-20 13:59:25 jan Exp $
 *
 * @package Horde_Block
 */
class Horde_Block_imp_summary extends Horde_Block {

    /**
     * Whether this block has changing content.
     */
    var $updateable = true;

    var $_app = 'imp';

    function _title()
    {
        return Horde::link(Horde::url($GLOBALS['registry']->getInitialPage(), true)) . $GLOBALS['registry']->get('name') . '</a>';
    }

    function _params()
    {
        return array('show_unread' => array('type' => 'boolean',
                                            'name' => _("Only display folders with unread messages in them?"),
                                            'default' => 0),
                     'show_total' => array('type' => 'boolean',
                                           'name' => _("Show total number of mails in folder?"),
                                           'default' => 0)
                     );
    }

    function _content()
    {
        global $notification, $prefs, $registry;

        $GLOBALS['authentication'] = 'none';
        require dirname(__FILE__) . '/../base.php';

        $html = '<table cellspacing="0" width="100%">';

        if (!IMP::checkAuthentication(true)) {
            return $html . '<tr><td class="text">' . Horde::link(Horde::applicationUrl('index.php', true), sprintf(_("Log in to %s"), $registry->applications['imp']['name'])) . sprintf(_("Log in to %s"), $registry->applications['imp']['name']) . '</a></td></tr></table>';
        }

        /* Filter on INBOX display, if requested. */
        if ($prefs->getValue('filter_on_display')) {
            require_once IMP_BASE . '/lib/Filter.php';
            IMP_Filter::filter('INBOX');
        }

        /* Get list of mailboxes to poll. */
        require_once IMP_BASE . '/lib/IMAP/Tree.php';
        $imptree = &IMP_Tree::singleton();
        $folders = $imptree->getPollList(true, true);

        /* Quota info, if available. */
        $quota_msg = Util::bufferOutput(array('IMP', 'quota'));
        if (!empty($quota_msg)) {
            $html .= '<tr><td colspan="3">' . $quota_msg . '</td></tr>';
        }

        $newmsgs = array();
        $anyUnseen = false;

        foreach ($folders as $folder) {
            if (($folder == 'INBOX') ||
                ($_SESSION['imp']['base_protocol'] != 'pop3')) {
                $info = $imptree->getElementInfo($folder);
                if (!empty($info)) {
                    if (empty($this->_params['show_unread']) ||
                        !empty($info['unseen'])) {
                        if (!empty($info['newmsg'])) {
                            $newmsgs[$folder] = $info['newmsg'];
                        }
                        $url = Util::addParameter(Horde::applicationUrl('mailbox.php', true), array('no_newmail_popup' => 1, 'mailbox' => $folder));
                        $html .= '<tr style="cursor:pointer" class="text" onclick="self.location=\'' . $url . '\'"><td>';
                        if (!empty($info['unseen'])) {
                            $html .= '<strong>';
                            $anyUnseen = true;
                        }
                        $html .= Horde::link($url) . IMP::displayFolder($folder) . '</a>';
                        if (!empty($info['unseen'])) {
                            $html .= '</strong>';
                        }
                        $html .= '</td><td>' .
                            (!empty($info['unseen']) ? '<strong>' . $info['unseen'] . '</strong>' : '0') .
                            (!empty($this->_params['show_total']) ? '</td><td>(' . $info['messages'] . ')' : '') .
                            '</td></tr>';
                    }
                }
            }
        }

        $html .= '</table>';

        /* Check to see if user wants new mail notification, but only
         * if the user is logged into IMP. */
        if ($prefs->getValue('nav_popup')) {
            // Always include these scripts so they'll be there if
            // there's new mail in later dynamic updates.
            Horde::addScriptFile('prototype.js', 'imp', true);
            Horde::addScriptFile('effects.js', 'imp', true);
            Horde::addScriptFile('redbox.js', 'imp', true);
        }

        if (!empty($newmsgs)) {
            /* Reopen the mailbox R/W so we ensure the 'recent' flags are
             * cleared from the current mailbox. */
            $imp_imap = &IMP_IMAP::singleton();
            foreach ($newmsgs as $mbox => $nm) {
                $imp_imap->changeMbox($mbox);
            }

            if ($prefs->getValue('nav_popup')) {
                $alert = IMP::getNewMessagePopup($newmsgs);
                if (!Util::getFormData('httpclient')) {
                    $alert = 'document.observe("dom:loaded", function() { ' . $alert . ' });';
                }
                $notification->push($alert, 'javascript');
                $html .= Util::bufferOutput(array($notification, 'notify'), array('listeners' => 'javascript'));
            }

            if (class_exists('Notification_Listener_audio')
                && ($sound = $prefs->getValue('nav_audio'))) {
                $notification->push($registry->getImageDir() .
                                    '/audio/' . $sound, 'audio');
                $html .= Util::bufferOutput(array($notification, 'notify'), array('listeners' => 'audio'));
            }
        } elseif (!empty($this->_params['show_unread'])) {
            if (count($folders) == 0) {
                $html .= _("No folders are being checked for new mail.");
            } elseif (!$anyUnseen) {
                $html .= '<em>' . _("No folders with unseen messages") . '</em>';
            } elseif ($prefs->getValue('nav_popup')) {
                $html .= '<em>' . _("No folders with new messages") . '</em>';
            }
        }

        return $html;
    }

}
