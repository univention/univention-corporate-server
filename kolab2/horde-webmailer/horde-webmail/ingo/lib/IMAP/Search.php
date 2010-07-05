<?php

require_once 'Horde/IMAP/Search.php';

/**
 * The Ingo_IMAP_Search:: class extends the IMAP_Search class in order to
 * provide necessary bug fixes to ensure backwards compatibility with Horde
 * 3.0.
 *
 * $Horde: ingo/lib/IMAP/Search.php,v 1.1.2.7 2009-01-06 15:24:36 jan Exp $
 *
 * Copyright 2006-2009 The Horde Project (http://www.horde.org/)
 *
 * See the enclosed file COPYING for license information (GPL). If you
 * did not receive this file, see http://www.fsf.org/copyleft/gpl.html.
 *
 * @author  Michael Slusarz <slusarz@horde.org>
 * @since   Ingo 1.1
 * @package Horde_IMAP
 */
class Ingo_IMAP_Search extends IMAP_Search {

    /**
     * The paramater list.
     *
     * @var array
     */
    var $_params = array();

    /**
     * Returns a reference to the global Ingo_IMAP_Search object, only creating
     * it if it doesn't already exist.
     *
     * @param array $params  The parameter array.  It must contain the
     *                       following elements:
     *                       'imap' - An open IMAP stream resource.
     */
    function &singleton($params = array())
    {
        static $object;

        if (!isset($object)) {
            /* Are we using a POP mailbox? */
            $ob = @imap_check($params['imap']);
            $pop3 = (stristr($ob->Driver, 'pop3') !== false);
            $object = new Ingo_IMAP_Search(array('pop3' => $pop3));
        }

        return $object;
    }

    /**
     * Constructor.
     *
     * @param array $params  See IMAP_Search().
     */
    function Ingo_IMAP_Search($params = array())
    {
        $this->_params = $params;
    }

    /**
     * Searches messages by ALL headers (rather than the limited set provided
     * by imap_search()).
     *
     * @see IMAP_Search::searchMailbox()
     */
    function searchMailbox($query, &$imap, $mbox)
    {
        /* Clear the search flag. */
        $this->_searchflag = 0;

        if (!$this->_params['pop3']) {
            @imap_reopen($imap, $mbox);
        }

        return $this->_searchMailbox($query, $imap, $mbox);
    }

}

/**
 * The Ingo_IMAP_Search_Query:: class extends the IMAP_Search_Query class in
 * order to provide necessary bug fixes to ensure backwards compatibility with
 * Horde 3.0.
 *
 * @author  Michael Slusarz <slusarz@horde.org>
 * @since   Ingo 1.1
 * @package Horde_IMAP
 */
class Ingo_IMAP_Search_Query extends IMAP_Search_Query {

    /**
     * Builds the IMAP search query.
     */
    function build()
    {
        $search = parent::build();
        if (empty($search)) {
            if (!empty($this->_or)) {
                return $search;
            }
            $search = &new stdClass;
            $search->flags = null;
            $search->not = false;
            $search->fullquery = $search->query = 'ALL';
        }
        return $search;
    }
}
