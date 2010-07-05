<?php
/**
 * The IMAP_Search:: class performs complex searching of an IMAP mailbox.
 *
 * Classes to help with complex searching of an IMAP mailbox.  The built-in
 * PHP search() function only allows IMAPv2 search queries (see RFC 1176).
 * This library allows more complex searches to be created (e.g. OR searches,
 * searching specific headers).
 *
 * $Horde: framework/IMAP/IMAP/Search.php,v 1.29.10.32 2009-01-06 15:23:11 jan Exp $
 *
 * Copyright 2003-2009 The Horde Project (http://www.horde.org/)
 *
 * See the enclosed file COPYING for license information (GPL). If you
 * did not receive this file, see http://www.fsf.org/copyleft/gpl.html.
 *
 * @author  Michael Slusarz <slusarz@horde.org>
 * @since   Horde 3.0
 * @package Horde_IMAP
 */
class IMAP_Search {

    /**
     * The headers cache.
     *
     * @var array
     */
    var $_headers = array();

    /**
     * The results cache.
     *
     * @var array
     */
    var $_result = array();

    /**
     * The paramater list.
     *
     * @var array
     */
    var $_params = array();

    /**
     * The charset of the search values.
     *
     * @var string
     */
    var $_charset;

    /**
     * Internal flag used by searchMailbox().
     *
     * @var integer
     */
    var $_searchflag = 0;

    /**
     * Returns a reference to the global IMAP_Search object, only creating it
     * if it doesn't already exist.
     *
     * This method must be invoked as:<code>
     *   $imap_search = &IMAP_Search::singleton();</code>
     *
     * @param array $params  Any parameters the constructor may need.
     *
     * @return IMAP_Search  The IMAP_Search instance.
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
     * Constructor.
     *
     * @param array $params  A hash containing the following entries:<pre>
     *                       'pop3' => boolean (using POP3 connection?)
     *                       'charset' => string (charset of search values)
     *                       'no_imap_search' => true if the IMAP server does
     *                                           not support the charset in
     *                                           the search command
     *                       </pre>
     */
    function IMAP_Search($params = array())
    {
        $this->_params = $params;
    }

    /**
     * Searches messages by ALL headers (rather than the limited set provided
     * by imap_search()).
     *
     * @param IMAP_Search_Query $query  The search query.
     * @param resource $imap            An IMAP resource stream.
     * @param string $mbox              The name of the mailbox to search. For
     *                                  POP3, this should be empty.
     *
     * @return array  The list of indices that match the search rules in the
     *                current mailbox.
     *                Returns PEAR_Error on error.
     */
    function searchMailbox($query, $imap, $mbox)
    {
        /* Check for IMAP extension. */
        if (!Util::extensionExists('imap')) {
            Horde::fatal(PEAR::raiseError("This function requires 'imap' to be built into PHP."), __FILE__, __LINE__, false);
        }

        /* Open to the correct mailbox. */
        // TODO: Remove for Horde 4.0
        if (!$this->_params['pop3']) {
            $old_error = error_reporting(0);
            $res = imap_reopen($imap, $mbox, OP_READONLY);
            error_reporting($old_error);
            if (!$res) {
                return array();
            }
        }

        /* Clear the search flag. */
        $this->_searchflag = 0;

        return $this->_searchMailbox($query, $imap, $mbox);
    }

    /**
     * Searches the mailbox and sorts the results.
     *
     * @param IMAP_Search_Query $query  The search query.
     * @param resource $imap            An IMAP resource stream.
     * @param string $mbox              The name of the mailbox to search.
     * @param integer $sortby           The criteria to sort by (see
     *                                  imap_sort()).
     * @param integer $sortdir          1 for reverse sorting.
     *
     * @return array  The list of indices that match the search rules in the
     *                current mailbox and sorted.
     *                Returns PEAR_Error on error.
     */
    function searchSortMailbox($query, $imap, $mbox, $sortby, $sortdir = 0)
    {
        $indices = $this->searchMailbox($query, $imap, $mbox);
        if (is_a($indices, 'PEAR_Error')) {
            return $indices;
        } else {
            $old_error = error_reporting(0);
            $indices_sort = imap_sort($imap, $sortby, $sortdir, SE_UID);
            error_reporting($old_error);
            return array_values(array_intersect($indices_sort, $indices));
        }
    }

    /**
     * Internal wrapper method to imap_search that allows charset aware
     * searches if available.
     *
     * @access private
     */
    function _imapSearch($imap, $criteria)
    {
        $old_error = error_reporting(0);

        if (!empty($this->_params['charset'])) {
            if (empty($this->_params['no_imap_charset']) &&
                version_compare(PHP_VERSION, '4.3.3', '>=')) {
                $res = imap_search($imap, $criteria, SE_UID, $this->_params['charset']);
                error_reporting($old_error);
                return $res;
            } else {
                $criteria = String::convertCharset($criteria, $this->_params['charset'], 'US-ASCII');
            }
        }

        $res = imap_search($imap, $criteria, SE_UID);
        error_reporting($old_error);
        return $res;
    }

    /**
     * Internal function to search the mailbox.
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
            $old_error = error_reporting(0);
            $overview = imap_fetch_overview($imap, implode(',', $indices), FT_UID);
            error_reporting($old_error);

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

    /**
     * Internal function to search the mailbox.
     *
     * @access private
     */
    function _doAndOrSearch($query, $imap, $mbox, $mode, $indices,
                            $base = false)
    {
        if (empty($query)) {
            return $indices;
        }

        foreach ($query as $val) {
            if (is_a($val, 'IMAP_Search_Query')) {
                $prevsearch = (empty($indices) && ($this->_searchflag == 0));
                $result = $this->_searchMailbox($val, $imap, $mbox);
                if ($mode == 'and') {
                    /* If the result is empty in an AND search, we know that
                       the entire AND search will be empty so return
                       immediately. */
                    if (empty($result)) {
                        return array();
                    }

                    /* If we have reached this point, and have not performed a
                       search yet, we must use the results as the indices
                       list. Without this check, the indices list will always
                       be empty if an AND search is the first search. */
                    if ($prevsearch) {
                        $indices = $result;
                        $this->_searchflag = 1;
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
     * Uses PHP based functions to perform the search.
     *
     * @access private
     *
     * @param stdClass $imap_query  Search query.
     * @param string $flags         Any additional flags.
     * @param resource $imap        An IMAP resource stream.
     * @param string $mbox          The name of the search mailbox.
     *
     * @return array  The list of indices that match.
     */
    function _searchPHP($imap_query, $flags, $imap, $mbox)
    {
        $indices = array();

        if (empty($flags)) {
            $flags = 'ALL';
        }

        if (!empty($this->_params['pop3'])) {
            $mbox = 'POP3';
        }

        $cache_key = $mbox . '|' . $flags;

        /* We have to use parseMIMEHeaders() to get each header and see if any
         * field matches. Use imap_search() to get the list of message indices
         * or return empty list if no search results. */
        if (!isset($this->_result[$cache_key])) {
            $old_error = error_reporting(0);
            $this->_result[$cache_key] = imap_search($imap, $flags, SE_UID);
            error_reporting($old_error);
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
        $query = reset($imap_query->query);
        $key = strtolower(key($imap_query->query));

        foreach ($this->_result[$cache_key] as $index) {
            if (!isset($this->_headers[$mbox][$index])) {
                $old_error = error_reporting(0);
                $this->_headers[$mbox][$index] = MIME_Structure::parseMIMEHeaders(imap_fetchheader($imap, $index, FT_UID), null, true);
                error_reporting($old_error);
            }
            $h = &$this->_headers[$mbox][$index];

            /* We need to do a case insensitive search on text because, for
             * example, e-mail addresses may not be caught correctly
             * (filtering for example@example.com will not catch
             * exAmple@example.com). */
            $match_success = false;
            if (isset($h[$key])) {
                $hdr_array = (is_array($h[$key])) ? $h[$key] : array($h[$key]);
                foreach ($hdr_array as $val) {
                    if (stristr($val, strval($query)) !== false) {
                        $match_success = true;
                        break;
                    }
                }
            }
            if (($imap_query->not && !$match_success) ||
                (!$imap_query->not && $match_success)) {
                $indices[] = $index;
            }
        }

        return $indices;
    }

}

/**
 * The IMAP_Search_Object:: class is used to formulate queries to be used with
 * the IMAP_Search:: class.
 *
 * @author  Michael Slusarz <slusarz@horde.org>
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

    /**
     * Returns any extended searches.
     */
    function extendedSearch()
    {
        if (!empty($this->_extendedSearch)) {
            $search = new stdClass;
            $search->not = $this->_not;
            $search->query = $this->_extendedSearch;
            return $search;
        } else {
            return null;
        }
    }

    /**
     * Returns the parameters for a size search.
     */
    function sizeSearch()
    {
        if (is_null($this->_size)) {
            return null;
        }
        $ob = new stdClass;
        $ob->size = (float)$this->_size;
        $ob->sizeop = $this->_sizeop;

        return $ob;
    }

    /**
     * Returns any AND searches.
     */
    function andSearch()
    {
        return $this->_and;
    }

    /**
     * Returns any OR searches.
     */
    function orSearch()
    {
        return $this->_or;
    }

    /**
     * Returns the flags.
     */
    function flags()
    {
        return ((empty($this->_flags)) ? '' : implode(' ', $this->_flags));
    }

    /**
     * Builds the IMAP search query.
     */
    function build()
    {
        $search = new stdClass;

        $search->not = $this->_not;
        $search->flags = $this->flags();

        if (empty($this->_query)) {
            if (!empty($this->_or)) {
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
        $search->fullquery = (!empty($search->flags) ? $search->flags . ' ' : '') . $search->query;

        return $search;
    }

    /**
     * IMAP search modifiers.
     */
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

    /**
     * IMAP Search Flags.
     *
     * There is no need to support the KEYWORD/UNKEYWORD query since
     * the individual keywords have identical functionality.
     */
    function _imapFlags($flag, $cmd)
    {
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

    /**
     * IMAP Header Search.
     */
    function header($header, $query, $not = false)
    {
        $header = ucfirst(rtrim($header, ':'));
        $stdHdrs = array('To', 'Cc', 'From', 'Subject');
        if ($query != '') {
            if (in_array($header, $stdHdrs)) {
                $this->_query = String::upper($header) . ' "' . str_replace('"', '\"', $query) . '"';
            } else {
                $this->_extendedSearch[$header] = $query;
            }
            $this->_not = $not;
        }
    }

    /**
     * IMAP Date Search.
     */
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

    /**
     * IMAP Text searches.
     */
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

    /**
     * IMAP Size searches.
     */
    function size($size, $operator)
    {
        $this->_size = $size;
        $this->_sizeop = $operator;
    }

    /**
     * Determines whether this query matches a pre-parsed message
     *
     * Note: This is not completely implemented.
     *
     * @param object $parsedMessage  The return value from
     *                               Mail_mimeDecode::decode()
     * @return bool  whether the message matches
     */
    function matches(&$parsedMessage)
    {
        $result = $this->_matchesQuery($parsedMessage);
        if (!empty($this->_or)) {
            $result = $this->_recursiveMatch($this->_or, '||', $parsedMessage);
        }
        if (!empty($this->_and)) {
            $result = $this->_recursiveMatch($this->_and, '&&', $parsedMessage);
        }
        if ($this->_not) {
            $result = !$result;
        }
        return $result;
    }

    function _recursiveMatch(&$list, $operator, &$parsedMessage)
    {
        switch ($operator) {
        case '||':
            $result = false;
            break;

        case '&&':
            $result = true;
            break;
        }
        foreach (array_keys($list) as $i) {
            if (is_object($list[$i])) {
                $result1 = $list[$i]->matches($parsedMessage);
            } else {
                $result1 = $this->_recursiveMatch($list[$i], $operator,
                                                  $parsedMessage);
            }
            switch ($operator) {
            case '||':
                $result = $result || $result1;
                break;

            case '&&':
                $result = $result && $result1;
                break;
            }
        }
        return $result;
    }

    function _matchesQuery(&$parsedMessage)
    {
        if (empty($this->_query)) {
            return false;
        }

        if (preg_match('/^FROM "(.*)"$/', $this->_query, $m)) {
            if (empty($parsedMessage->headers)) {
                return false;
            }
            if (empty($parsedMessage->headers['from'])) {
                return false;
            }
            if (strpos(strtolower($parsedMessage->headers['from']),
                       strtolower($m[1])) !== false) {
                return true;
            }
        }

        return false;
    }

}
