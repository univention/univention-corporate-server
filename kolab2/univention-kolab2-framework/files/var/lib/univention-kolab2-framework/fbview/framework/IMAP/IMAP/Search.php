<?php
/**
 * The IMAP_Search:: class performs complex searching of an IMAP mailbox.
 *
 * Classes to help with complex searching of an IMAP mailbox.
 * The built-in PHP search() function only allows IMAPv2 search queries
 * (see RFC 1176).  This library allows more complex searches to be
 * created (e.g. OR searches, searching specific headers).
 *
 * $Horde: framework/IMAP/IMAP/Search.php,v 1.26 2004/04/07 14:43:09 chuck Exp $
 *
 * Copyright 2003-2004 Michael Slusarz <slusarz@bigworm.colorado.edu>
 *
 * See the enclosed file COPYING for license information (GPL). If you
 * did not receive this file, see http://www.fsf.org/copyleft/gpl.html.
 *
 * @author  Michael Slusarz <slusarz@bigworm.colorado.edu>
 * @version $Revision: 1.1.2.1 $
 * @since   Horde 3.0
 * @package Horde_IMAP
 */
class IMAP_Search {

    /**
     * The headers cache.
     *
     * @var array $_headers
     */
    var $_headers = array();

    /**
     * The results cache.
     *
     * @var array $_result
     */
    var $_result = array();

    /**
     * Are we dealing with a POP3 connection?
     *
     * @var boolean $_pop3
     */
    var $_pop3 = false;

    /**
     * Internal flag used by searchMailbox().
     *
     * @var integer $_searchflag
     */
    var $_searchflag = 0;

    /**
     * Returns a reference to the global IMAP_Search object,
     * only creating it if it doesn't already exist.
     *
     * This method must be invoked as:
     *   $imap_search = &IMAP_Search::singleton();
     *
     * @access public
     *
     * @param optional array $params  Any parameters the constructor may need.
     *
     * @return object IMAP_Search  The IMAP_Search instance.
     */
    function &singleton($params = array())
    {
        static $object;

        if (!isset($object)) {
            $object = new IMAP_Search($params);
        }

        return $object;
    }

    /**
     * Constructor
     *
     * @access public
     *
     * @param optional array $params  A hash containing the following entries:
     *                                'pop3' => boolean (using POP3
     *                                                   connection?)
     */
    function IMAP_Search($params = array())
    {
        if (isset($params['pop3'])) {
            $this->_pop3 = $params['pop3'];
        }
    }

    /**
     * Searches messages by ALL headers (rather than the limited set
     * provided by imap_search()).
     *
     * @access public
     *
     * @param object IMAP_Search_Query $query  The search query.
     * @param resource &$imap                  An IMAP resource stream.
     * @param string $mbox                     The name of the mailbox to
     *                                         search. For POP3, this should
     *                                         be empty.
     *
     * @return array  The list of indices that match the search rules in the
     *                current mailbox.
     *                Returns PEAR_Error on error.
     */
    function searchMailbox($query, &$imap, $mbox)
    {
        /* Check for IMAP extension. */
        if (!Util::extensionExists('imap')) {
            Horde::fatal(PEAR::raiseError("This function requires 'imap' to be built into PHP."), __FILE__, __LINE__, false);
        }

        /* Open to the correct mailbox. */
        if (!$this->_pop3) {
            @imap_reopen($imap, $mbox);
        }

        /* Clear the search flag. */
        $this->_searchflag = 0;

        return $this->_searchMailbox($query, $imap, $mbox);
    }

    /**
     * Search the mailbox and sort the results.
     *
     * @access public
     *
     * @param object IMAP_Search_Query $query  The search query.
     * @param resource &$imap                  An IMAP resource stream.
     * @param string $mbox                     The name of the mailbox to
     *                                         search.
     * @param integer $criteria                The criteria to sort by
     *                                         (see imap_sort()).
     * @param optional integer $dir            1 for reverse sorting.
     *
     * @return array  The list of indices that match the search rules in the
     *                current mailbox and sorted.
     *                Returns PEAR_Error on error.
     */
    function searchSortMailbox($query, &$imap, $mbox, $criteria, $dir = 0)
    {
        $indices = $this->searchMailbox($query, $imap, $mbox);
        if (is_a($indices, 'PEAR_Error')) {
            return $indices;
        } else {
            $indices_sort = @imap_sort($imap, $sortby, $sortdir, SE_UID);
            return array_values(array_intersect($indices_sort, $indices));
        }
    }

    /**
     * Internal function to search the mailbox.
     *
     * @access private
     */
    function _searchMailbox($query, &$imap, $mbox)
    {
        $indices = array();

        /* Do the simple searches that imap_search() can handle. */
        if (($ob = $query->build())) {
            if ($ob->not) {
                if (!($indices1 = @imap_search($imap, $ob->flags, SE_UID))) {
                    $indices1 = array();
                }
                if (!($indices2 = @imap_search($imap, $ob->query, SE_UID))) {
                    $indices2 = array();
                }
                $indices = array_diff($indices1, $indices2);
            } else {
                if (!($indices = @imap_search($imap, $ob->fullquery, SE_UID))) {
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
            $overview = @imap_fetch_overview($imap, implode(',', $indices), FT_UID);
            $func = create_function('$a', 'return ($a ' . $sizeOb->sizeop . ' ' . $sizeOb->size . ');');
            $result = array();
            foreach ($overview as $val) {
                if ($func($val->size)) {
                    $result[] = $val->uid;
                }
            }
            $indices = array_values(array_intersect($indices, $result));
        }

        /* Process AND searches now. */
        $indices = $this->_doAndOrSearch($query->andSearch(), $imap, $mbox, 'and', $indices);

        /* Process OR searches now. */
        $indices = $this->_doAndOrSearch($query->orSearch(), $imap, $mbox, 'or', $indices);

        return $indices;
    }

    /**
     * Internal function to search the mailbox.
     *
     * @access private
     */
    function _doAndOrSearch($query, &$imap, $mbox, $mode, $indices,
                            $base = false)
    {
        if (empty($query)) {
            return $indices;
        }

        foreach ($query as $val) {
            if (is_a($val, 'IMAP_Search_Query')) {
                $result = $this->_searchMailbox($val, $imap, $mbox);
                if ($mode == 'and') {
                    /* If the result is empty in an AND search, we know that
                       the entire AND search will be empty so return
                       immediately. */
                    if (empty($result)) {
                        return array();
                    }

                    /* If we have reached this point, and have not performed
                       a search yet, we must use the results as the indices
                       list. Without this check, the indices list will always
                       be empty if an AND search is the first search. */
                    if (empty($indices) && ($this->_searchflag == 1)) {
                        $indices = $result;
                        $this->_searchflag = 2;
                    } else {
                        $indices = array_values(array_intersect($indices, $result));
                    }
                } elseif (!empty($result)) {
                    $indices = array_unique(array_merge($indices, $result));
                }
            } else {
                $indices = $this->_doAndOrSearch($val, $imap, $mbox, $mode, $indices);
            }
        }

        return $indices;
    }

    /**
     * Use a PHP based functions to perform the search.
     *
     * @access private
     *
     * @param array $imap_query  The search query.
     * @param string $flags      Any additional flags.
     * @param resource &$imap    An IMAP resource stream.
     * @param string $mbox       The name of the search mailbox.
     *
     * @return array  The list of indices that match.
     */
    function _searchPHP($imap_query, $flags, &$imap, $mbox)
    {
        $indices = array();

        if (empty($flags)) {
            $flags = 'ALL';
        }

        if ($this->_pop3) {
            $mbox = 'POP3';
        }

        $cache_key = $mbox . '|' . $flags;

        /* We have to use parseMIMEHeaders() to get each header and see if
           any field matches. Use imap_search() to get the list of message
           indices or return empty list if no search results. */
        if (!isset($this->_result[$cache_key])) {
            $this->_result[$cache_key] = @imap_search($imap, $flags, SE_UID);
        }

        /* If empty message list, return now. */
        if (empty($this->_result[$cache_key])) {
            return array();
        }

        include_once 'Horde/MIME/Structure.php';

        if (!isset($this->_headers[$mbox])) {
            $this->_headers[$mbox] = array();
        }

        /* Get the header/query to search for. */
        $query = reset($imap_query);
        $key = strtolower(key($imap_query));

        foreach ($this->_result[$cache_key] as $index) {
            if (!isset($this->_headers[$mbox][$index])) {
                $this->_headers[$mbox][$index] = MIME_Structure::parseMIMEHeaders(@imap_fetchheader($imap, $index, FT_UID), null, true);
            }
            $h = &$this->_headers[$mbox][$index];

            /* We need to do a case insensitive search on text because,
               for example, e-mail addresses may not be caught correctly
               (filtering for example@example.com will not catch
                exAmple@example.com). */
            if (isset($h[$key]) &&
                (stristr($h[$key], strval($query)) !== false)) {
                $indices[] = $index;
            }
        }

        return $indices;
    }

}

/**
 * The IMAP_Search_Object:: class is used to formulate queries to be used
 * with the IMAP_Search:: class.
 *
 * @author  Michael Slusarz <slusarz@bigworm.colorado.edu>
 * @version $Revision: 1.1.2.1 $
 * @since   Horde 3.0
 * @package Horde_IMAP
 */
class IMAP_Search_Query {

    var $_and = array();
    var $_extendedSearch = array();
    var $_flags = array();
    var $_not = false;
    var $_or = array();
    var $_query = null;
    var $_size = null;
    var $_sizeop = null;

    function IMAP_Search_Query()
    {
    }

    /**
     * Return any extended searches.
     */
    function extendedSearch()
    {
        return $this->_extendedSearch;
    }

    /**
     * Return the parameters for a size search.
     */
    function sizeSearch()
    {
        if (is_null($this->_size)) {
            return null;
        }
        $ob = &new stdClass;
        $ob->size = $this->_size;
        $ob->sizeop = $this->_sizeop;

        return $ob;
    }

    /**
     * Return any AND searches.
     */
    function andSearch()
    {
        return $this->_and;
    }

    /**
     * Return any OR searches.
     */
    function orSearch()
    {
        return $this->_or;
    }

    /**
     * Return the flags.
     */
    function flags()
    {
        return ((empty($this->_flags)) ? '' : implode(' ', $this->_flags));
    }

    /**
     * Build the IMAP search query.
     */
    function build()
    {
        $search = &new stdClass;

        $search->not = $this->_not;
        $search->flags = $this->flags();

        if (empty($this->_query)) {
            if (empty($search->flags)) {
                return '';
            }
            $search->query = 'ALL';
            $search->not = false;
        } else {
            if ($search->not && empty($search->flags)) {
                $search->flags = 'ALL';
            }
            $search->query = $this->_query;
        }
        $search->fullquery = $search->flags . ' ' . $search->query;

        return $search;
    }

    /* IMAP search modifiers. */
    function _modifiers($ob, $cmd)
    {
        if (is_a($ob, 'IMAP_Search_Query')) {
            $ob = array($ob);
        }
        array_push($this->$cmd, $ob);
    }

    function imapAnd($ob)
    {
        $this->_modifiers($ob, '_and');
    }

    function imapOr($ob)
    {
        $this->_modifiers($ob, '_or');
    }

    /* IMAP Search Flags. */
    /* There is no need to support the KEYWORD/UNKEYWORD query since the
       individual keywords have identical functionality. */
    function _imapFlags($flag, $cmd) {
        $cmd = ($flag) ? $cmd : 'UN' . $cmd;
        $this->_flags[] = $cmd;
    }

    function answered($flag)
    {
        $this->_imapFlags($flag, 'ANSWERED');
    }

    function deleted($flag)
    {
        $this->_imapFlags($flag, 'DELETED');
    }

    function flagged($flag)
    {
        $this->_imapFlags($flag, 'FLAGGED');
    }

    function seen($flag)
    {
        $this->_imapFlags($flag, 'SEEN');
    }

    function recent($flag)
    {
        $this->_imapFlags(true, (($flag) ? 'RECENT' : 'OLD'));
    }

    function imapNew()
    {
        $this->_imapFlags(true, 'NEW');
    }

    /* IMAP Header Search. */
    function header($header, $query, $not = false) {
        $header = ucfirst(rtrim($header, ':'));
        $stdHdrs = array('To', 'Cc', 'From', 'Subject');
        if ($query != '') {
            if (in_array($header, $stdHdrs)) {
                $this->_query = String::upper($header) . ' "' . addslashes($query) . '"';
            } else {
                $this->_extendedSearch[$header] = $query;
            }
            $this->_not = $not;
        }
    }

    /* IMAP Date Search. */
    function _imapDate($day, $month, $year, $cmd)
    {
        $this->_query = $cmd . ' ' . date("d-M-y", mktime(0, 0, 0, $month, $day, $year));
    }

    function before($day, $month, $year)
    {
        $this->_imapDate($day, $month, $year, 'BEFORE');
    }

    function since($day, $month, $year)
    {
        $this->_imapDate($day, $month, $year, 'SINCE');
    }

    function on($day, $month, $year)
    {
        $this->_imapDate($day, $month, $year, 'ON');
    }

    /* IMAP Text searches. */
    function body($query, $not = false)
    {
        $this->_query = 'BODY "' . $query . '"';
        $this->_not = $not;
    }

    function text($query, $not = false)
    {
        $this->_query = 'TEXT "' . $query . '"';
        $this->_not = $not;
    }

    /* IMAP Size searches. */
    function size($size, $operator)
    {
        $this->_size = $size;
        $this->_sizeop = $operator;
    }

}
