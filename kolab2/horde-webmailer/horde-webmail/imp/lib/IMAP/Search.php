<?php

require_once 'Horde/IMAP/Search.php';

/**
 * The IMP_IMAP_Search:: class extends the IMAP_Search class in order to
 * provide necessary bug fixes to ensure backwards compatibility with Horde
 * 3.0.
 *
 * $Horde: imp/lib/IMAP/Search.php,v 1.5.2.6 2009-01-06 15:24:05 jan Exp $
 *
 * Copyright 2006-2009 The Horde Project (http://www.horde.org/)
 *
 * See the enclosed file COPYING for license information (GPL). If you
 * did not receive this file, see http://www.fsf.org/copyleft/gpl.html.
 *
 * @author  Michael Slusarz <slusarz@horde.org>
 * @since   IMP 4.1
 * @package Horde_IMAP
 */
class IMP_IMAP_Search extends IMAP_Search {

    /**
     * Returns a reference to the global IMP_IMAP_Search object, only creating
     * it if it doesn't already exist.
     *
     * @see IMAP_Search::singleton()
     */
    function &singleton($params = array())
    {
        static $object;

        if (!isset($object)) {
            $object = new IMP_IMAP_Search($params);
        }

        return $object;
    }

    /**
     * Searches messages by ALL headers (rather than the limited set provided
     * by imap_search()).
     *
     * @see IMAP_Search::searchMailbox(). $imap does not needed to be passed
     *      in.
     */
    function searchMailbox($query, $imap, $mbox)
    {
        /* Clear the search flag. */
        $this->_searchflag = 0;

        $imp_imap = &IMP_IMAP::singleton();
        if (!$imp_imap->changeMbox($mbox, IMP_IMAP_AUTO)) {
            return array();
        }
        $stream = $imp_imap->stream();

        return $this->_searchMailbox($query, $stream, $mbox);
    }

    /**
     * Searches a mailbox and sorts the results.
     *
     * @see IMAP_Search::searchSortMailbox(). $imap does not needed to be
     *      passed in.
     */
    function searchSortMailbox($query, $imap, $mbox, $sortby, $sortdir = 0)
    {
        $imp_imap = &IMP_IMAP::singleton();
        $stream = $imp_imap->stream();
        return parent::searchSortMailbox($query, $stream, $mbox, $sortby, $sortdir);
    }

    /**
     * Internal function to search the mailbox.
     * Uses cached results of overview data for size searches.
     *
     * @access private
     */
    function _searchMailbox($query, $imap, $mbox)
    {
        $indices = array();

        $this->_searchflag = 0;

        /* Do the simple searches that imap_search() can handle. */
        if (($ob = $query->build())) {
            if ($ob->not) {
                if (!($indices1 = $this->_imapSearch($imap, $ob->flags))) {
                    $indices1 = array();
                }
                if (!($indices2 = $this->_imapSearch($imap, $ob->query))) {
                    $indices2 = array();
                }
                $indices = array_diff($indices1, $indices2);
            } else {
                if (!($indices = $this->_imapSearch($imap, $ob->fullquery))) {
                    $indices = array();
                }
            }

            /* Set the search flag. */
            if ($this->_searchflag == 0) {
                $this->_searchflag = 1;
            }
        }

        /* Process extended searches. */
        if (($extended = $query->extendedSearch())) {
            $result = $this->_searchPHP($extended, $query->flags(), $imap, $mbox);
            /* Set the search flag. */
            if ($this->_searchflag == 0) {
                $indices = $result;
                $this->_searchflag = 1;
            } else {
                $indices = array_values(array_intersect($indices, $result));
            }
        }

        /* Process size searches. */
        if (($sizeOb = $query->sizeSearch())) {
            // Changes from framework version
            require_once IMP_BASE . '/lib/IMAP/MessageCache.php';
            $msg_cache = &IMP_MessageCache::singleton();
            $overview = $msg_cache->retrieve($mbox, $indices, 1);
            // End changes from framework version

            $result = array();
            foreach ($overview as $val) {
                switch ($sizeOb->sizeop) {
                case '<':
                    if ($val->size < $sizeOb->size) {
                        $result[] = $val->uid;
                    }
                    break;

                case '>':
                    if ($val->size > $sizeOb->size) {
                        $result[] = $val->uid;
                    }
                    break;
                }
            }
            if ($this->_searchflag == 0) {
                $this->_searchflag = 1;
            }
            $indices = array_values(array_intersect($indices, $result));
        }

        /* Process AND searches now. */
        $indices = $this->_doAndOrSearch($query->andSearch(), $imap, $mbox,
                                         'and', $indices);

        /* Process OR searches now. */
        $indices = $this->_doAndOrSearch($query->orSearch(), $imap, $mbox,
                                         'or', $indices);

        return $indices;
    }


}

/**
 * The IMP_IMAP_Search_Query:: class extends the IMAP_Search_Query class in
 * order to provide necessary bug fixes to ensure backwards compatibility with
 * Horde 3.0.
 *
 * @author  Michael Slusarz <slusarz@horde.org>
 * @since   IMP 4.1
 * @package Horde_IMAP
 */
class IMP_IMAP_Search_Query extends IMAP_Search_Query {

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
            $search = new stdClass;
            $search->flags = null;
            $search->not = false;
            $search->fullquery = $search->query = 'ALL';
        }
        return $search;
    }
}
