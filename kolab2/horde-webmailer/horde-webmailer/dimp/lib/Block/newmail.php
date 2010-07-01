<?php
/**
 * $Horde: dimp/lib/Block/newmail.php,v 1.11.2.6 2009-01-06 15:22:38 jan Exp $
 *
 * Copyright 2007-2009 The Horde Project (http://www.horde.org/)
 *
 * See the enclosed file COPYING for license information (GPL). If you
 * did not receive this file, see http://www.fsf.org/copyleft/gpl.html.
 *
 * @package Horde_Block
 * @author  Michael Slusarz <slusarz@curecanti.org>
 */

class Horde_Block_dimp_newmail extends Horde_Block {

    var $_app = 'dimp';

    function _content()
    {
        $GLOBALS['authentication'] = 'none';
        $GLOBALS['load_imp'] = true;
        require_once $GLOBALS['registry']->get('fileroot', 'dimp') . '/lib/base.php';

        if (!IMP::checkAuthentication(true)) {
            return '';
        }

        /* Filter on INBOX display, if requested. */
        if ($GLOBALS['prefs']->getValue('filter_on_display')) {
            require_once IMP_BASE . '/lib/Filter.php';
            IMP_Filter::filter('INBOX');
        }

        require_once IMP_BASE . '/lib/IMAP/Search.php';
        $query = new IMP_IMAP_Search_Query();
        $query->seen(false);
        $ids = $GLOBALS['imp_search']->runSearchQuery($query, IMP::serverString('INBOX'), SORTARRIVAL, 1);

        $html = '<table cellspacing="0" width="100%">';
        if (empty($ids)) {
            $html .= '<tr><td><em>' . _("No unread messages") . '</em></td></tr>';
        } else {
            require_once IMP_BASE . '/lib/IMAP/MessageCache.php';
            require_once IMP_BASE . '/lib/UI/Mailbox.php';
            require_once 'Horde/Identity.php';
            require_once 'Horde/Text.php';

            $charset = NLS::getCharset();
            $identity = &Identity::singleton(array('imp', 'imp'));
            $imp_ui = new IMP_UI_Mailbox('INBOX', $charset, $identity);
            $shown = empty($this->_params['msgs_shown']) ? 2 : $this->_params['msgs_shown'];

            $msg_cache = &IMP_MessageCache::singleton();
            $overview = $msg_cache->retrieve('INBOX', array_slice($ids, 0, $shown), 1);
            foreach ($overview as $ob) {
                $date = $imp_ui->getDate((isset($ob->date)) ? $ob->date : null);
                $from_res = $imp_ui->getFrom($ob);
                $subject = (empty($ob->subject)) ? _("[No Subject]") : $imp_ui->getSubject($ob->subject);

                $html .= '<tr style="cursor:pointer" class="text" onclick="DimpBase.go(\'msg:INBOX:' . $ob->uid . '\');return false;"><td>' .
                    '<strong>' . htmlspecialchars($from_res['from'], ENT_QUOTES, $charset) . '</strong><br />' .
                    str_replace('&nbsp;', '&#160;', Text::htmlSpaces($subject)) . '</td>' .
                    '<td>' . htmlspecialchars($date, ENT_QUOTES, $charset) . '</td></tr>';
            }

            $more_msgs = count($ids) - $shown;
            if ($more_msgs == 1) {
                $text = _("1 more unseen message...");
            } elseif ($more_msgs > 1) {
                $text = sprintf(_("%s more unseen messages..."), $more_msgs);
            } else {
                $text = _("Go to your Inbox...");
            }
            $html .= '<tr><td colspan="2" style="cursor:pointer" align="right" onclick="DimpBase.go(\'folder:INBOX\');return false;">' . $text . '</td></tr>';
        }
        $html .= '</table>';

        return $html;
    }

}
