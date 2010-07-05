<?php

$block_name = _("Contact Search");

/**
 * This is an implementation of the Horde_Block API that allows searching of
 * address books from the portal.
 *
 * $Horde: turba/lib/Block/minisearch.php,v 1.17.2.7 2008-05-20 12:21:13 selsky Exp $
 *
 * @package Horde_Block
 */
class Horde_Block_turba_minisearch extends Horde_Block {

    var $_app = 'turba';

    /**
     * The title to go in this block.
     *
     * @return string  The title text.
     */
    function _title()
    {
        return Horde::link(Horde::url($GLOBALS['registry']->getInitialPage(),
                                      true))
            . _("Contact Search") . '</a>';
    }

    /**
     * The content to go in this block.
     *
     * @return string  The block content.
     */
    function _content()
    {
        require_once dirname(__FILE__) . '/../base.php';

        if ($GLOBALS['browser']->hasFeature('iframes')) {
            Horde::addScriptFile('prototype.js', 'turba', true);
            return Util::bufferOutput(
                'include',
                TURBA_TEMPLATES . '/block/minisearch.inc');
        } else {
            return '<em>' . _("A browser that supports iframes is required")
                . '</em>';
        }
    }

}
