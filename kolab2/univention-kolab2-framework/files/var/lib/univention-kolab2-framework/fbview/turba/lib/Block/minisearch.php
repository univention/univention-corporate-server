<?php
/**
 * Turba_Minisearch_Block:: Implementation of the Horde_Block API to
 * allows searching of addressbooks from the portal.
 *
 * $Horde: turba/lib/Block/minisearch.php,v 1.10 2004/05/28 11:14:01 jan Exp $
 *
 * @package Horde_Block
 */
class Horde_Block_Turba_minisearch extends Horde_Block {

    var $_app = 'turba';

    /**
     * The title to go in this block.
     *
     * @return string   The title text.
     */
    function _title()
    {
        global $registry;

        $html  = Horde::link(Horde::url($registry->getInitialPage(), true), $registry->getParam('name'), 'header') . $registry->getParam('name') . '</a> :: ';
        $html .= Horde::link(Horde::applicationUrl('add.php', true), _("New Contact"), 'smallheader') . Horde::img('add.gif', _("New Contact"), 'hspace="5"', Horde::url($registry->getParam('graphics'), true, -1)) . _("New Contact") . '</a>';

        return $html;
    }

    /**
     * The content to go in this block.
     *
     * @return string   The content
     */
    function _content()
    {
        global $browser, $registry, $prefs;
        require_once dirname(__FILE__) . '/../base.php';

        if ($browser->hasFeature('iframes')) {
            $html = Util::bufferOutput('include', TURBA_TEMPLATES . '/block/minisearch.inc');
        } else {
            $html = '<i>' . _("A browser that supports iFrames is required") . '</i>';
        }

        return $html;
    }

}
