<?php

/* Defines used to determine what kind of field query we are dealing with. */
define('IMP_SEARCH_HEADER', 1);
define('IMP_SEARCH_BODY', 2);
define('IMP_SEARCH_DATE', 3);
define('IMP_SEARCH_TEXT', 4);
define('IMP_SEARCH_SIZE', 5);

/* Defines used to identify the flag input. */
define('IMP_SEARCH_FLAG_NOT', 0);
define('IMP_SEARCH_FLAG_HAS', 1);

/* Defines used to identify whether to show unsubscribed folders. */
define('IMP_SEARCH_SHOW_UNSUBSCRIBED', 0);
define('IMP_SEARCH_SHOW_SUBSCRIBED_ONLY', 1);

/**
 * The IMP_Search:: class contains all code related to mailbox searching
 * in IMP.
 *
 * The class uses the $_SESSION['imp']['search'] variable to store information
 * across page accesses. The format of that entry is as follows:
 *
 * $_SESSION['imp']['search'] = array(
 *     'q' => array(
 *         'id_1' => array(
 *             'query' => IMAP_Search_Query object (serialized),
 *             'folders' => array (List of folders to search),
 *             'uiinfo' => array (Info used by search.php to render page),
 *             'label' => string (Description of search),
 *             'vfolder' => boolean (True if this is a Virtual Folder)
 *         ),
 *         'id_2' => array(
 *             ....
 *         ),
 *         ....
 *     ),
 *     'vtrash_id' => string (The Virtual Trash query ID),
 *     'vinbox_id' => string (The Virtual Inbox query ID)
 * );
 *
 * $Horde: imp/lib/Search.php,v 1.37.10.47 2009-01-06 15:24:04 jan Exp $
 *
 * Copyright 2002-2009 The Horde Project (http://www.horde.org/)
 *
 * See the enclosed file COPYING for license information (GPL). If you
 * did not receive this file, see http://www.fsf.org/copyleft/gpl.html.
 *
 * @author  Michael Slusarz <slusarz@horde.org>
 * @package IMP
 */
class IMP_Search {

    /**
     * The ID of the current search query in use.
     *
     * @var string
     */
    var $_id = null;

    /**
     * Save Virtual Folder information when adding entries?
     *
     * @var boolean
     */
    var $_saveVFolder = true;

    /**
     * Constructor.
     *
     * @param array $params  Available parameters:
     * <pre>
     * 'id'  --  The ID of the search query in use.
     * </pre>
     */
    function IMP_Search($params = array())
    {
        if (!empty($params['id'])) {
            $this->_id = $this->_strip($params['id']);
        }
    }

    /**
     * Set up IMP_Search variables for the current session.
     *
     * @param boolean $no_vf  Don't readd the Virtual Folders.
     */
    function sessionSetup($no_vf = false)
    {
        if (!isset($_SESSION['imp']['search'])) {
            $_SESSION['imp']['search'] = array('q' => array());
        }
        if (!$no_vf) {
            foreach ($this->_getVFolderList() as $key => $val) {
                if (!empty($val['vfolder']) &&
                    !$this->isVTrashFolder($key) &&
                    !$this->isVINBOXFolder($key)) {
                    $this->_updateIMPTree('add', $key, $val['label']);
                    $_SESSION['imp']['search']['q'][$key] = $val;
                }
            }
        }
        $this->createVINBOXFolder();
        $this->createVTrashFolder();
    }

    /**
     * Run a search.
     *
     * @param IMAP_Search_Query &$ob  An optional search query to add (via
     *                                'AND') to the active search.
     * @param string $id              The search query id to use (by default,
     *                                will use the current ID set in the
     *                                object).
     *
     * @return array  The sorted list.
     */
    function runSearch(&$ob, $id = null)
    {
        $id = $this->_strip($id);
        $mbox = '';
        $sorted = array();

        if (empty($_SESSION['imp']['search']['q'][$id])) {
            return $sorted;
        }
        $search = &$_SESSION['imp']['search']['q'][$id];

        $imap_search = &$this->_getIMAPSearch();

        /* Prepare the search query. */
        if (!empty($ob)) {
            $old_query = unserialize($search['query']);
            $query = new IMP_IMAP_Search_Query();
            $query->imapAnd(array($ob, $old_query));
        } else {
            $query = unserialize($search['query']);
        }

        /* How do we want to sort results? */
        $sortpref = IMP::getSort();
        if ($sortpref['by'] == SORTTHREAD) {
            $sortpref['by'] = SORTDATE;
        }

        foreach ($search['folders'] as $val) {
            $results = $imap_search->searchSortMailbox($query, null, $val, $sortpref['by'], $sortpref['dir']);

            if (is_array($results)) {
                foreach ($results as $val2) {
                    $sorted[] = $val2 . IMP_IDX_SEP . $val;
                }
            }
        }

        return $sorted;
    }

    /**
     * Run a search query not stored in the current session.  Allows custom
     * queries with custom sorts to be used without affecting cached
     * mailboxes.
     *
     * @since IMP 4.2
     *
     * @param IMAP_Search_Query $ob  The search query.
     *
     * @return array  The sorted list.
     */
    function runSearchQuery($ob, $mailbox, $sortby, $sortdir)
    {
        $imap_search = &$this->_getIMAPSearch();
        return $imap_search->searchSortMailbox($ob, null, $mailbox, $sortby, $sortdir);
    }

    /**
     * Creates the IMAP search query in the IMP session.
     *
     * @param IMAP_Search_Query $query  The search query object.
     * @param array $folders            The list of folders to search.
     * @param array $search             The search array used to build the
     *                                  search UI screen.
     * @param string $label             The label to use for the search
     *                                  results.
     * @param string $id                The query id to use (or else one is
     *                                  automatically generated).
     *
     * @return string  Returns the search query id.
     */
    function createSearchQuery($query, $folders, $search, $label, $id = null)
    {
        $id = (empty($id)) ? base_convert(microtime() . mt_rand(), 16, 36) : $this->_strip($id);
        $_SESSION['imp']['search']['q'][$id] = array(
            'query' => serialize($query),
            'folders' => $folders,
            'uiinfo' => $search,
            'label' => $label,
            'vfolder' => false
        );
        return $id;
    }

    /**
     * Deletes an IMAP search query.
     *
     * @param string $id          The search query id to use (by default, will
     *                            use the current ID set in the object).
     * @param boolean $no_delete  Don't delete the entry in the tree object.
     *
     *
     *
     * @return string  Returns the search query id.
     */
    function deleteSearchQuery($id = null, $no_delete = false)
    {
        $id = $this->_strip($id);
        $is_vfolder = !empty($_SESSION['imp']['search']['q'][$id]['vfolder']);
        unset($_SESSION['imp']['search']['q'][$id]);

        if ($is_vfolder) {
            $vfolders = $this->_getVFolderList();
            unset($vfolders[$id]);
            $this->_saveVFolderList($vfolders);
            if (!$no_delete) {
                $this->_updateIMPTree('delete', $id);
            }
        }
    }

    /**
     * Retrieves the previously stored search UI information.
     *
     * @param string $id  The search query id to use (by default, will use
     *                    the current ID set in the object).
     *
     * @return array  The array necessary to rebuild the search UI page.
     */
    function retrieveUIQuery($id = null)
    {
        $id = $this->_strip($id);
        return (isset($_SESSION['imp']['search']['q'][$id]['uiinfo']))
            ? $_SESSION['imp']['search']['q'][$id]['uiinfo']
            : array();
    }

    /**
     * Generates the label to use for search results.
     *
     * @param string $id  The search query id to use (by default, will use
     *                    the current ID set in the object).
     *
     * @return string  The search results label.
     */
    function getLabel($id = null)
    {
        $id = $this->_strip($id);
        return (isset($_SESSION['imp']['search']['q'][$id]['label']))
            ? $_SESSION['imp']['search']['q'][$id]['label']
            : '';
    }

    /**
     * Obtains the list of virtual folders for the current user.
     *
     * @access private
     *
     * @return array  The list of virtual folders.
     */
    function _getVFolderList()
    {
        $vfolder = $GLOBALS['prefs']->getValue('vfolder');
        if (empty($vfolder)) {
            return array();
        }

        $old_error = error_reporting(0);
        $vfolder = unserialize($vfolder);
        error_reporting($old_error);

        if (!is_array($vfolder)) {
            $vfolder = array();
        }

        // BC: Convert old (IMP < 4.2.1) style w/separate flag entry to new
        // style where flags are part of the fields to query.
        if (!empty($vfolder)) {
            $entry = reset($vfolder);
            if (isset($entry['uiinfo']['flag'])) {
                $lookup = array(
                    1 => 'seen',
                    2 => 'answered',
                    3 => 'flagged',
                    4 => 'deleted'
                );
                while (list($k, $v) = each($vfolder)) {
                    $u = &$v['uiinfo'];
                    if (!empty($u['flag'])) {
                        foreach ($u['flag'] as $key => $val) {
                            if (($val == 0) || ($val == 1)) {
                                $u['field'][] = (($val == 1) ? 'un' : '') . $lookup[$key];
                                ++$u['field_end'];
                            }
                        }
                    }
                    unset($u['flag']);
                    $v['query'] = serialize($this->createQuery($u));
                    $vfolder[$k] = $v;
                }
                $this->_saveVFolderList($vfolder);
            }
        }

        return $vfolder;
    }

    /**
     * Saves the list of virtual folders for the current user.
     *
     * @access private
     *
     * @param array  The virtual folder list.
     */
    function _saveVFolderList($vfolder)
    {
        $GLOBALS['prefs']->setValue('vfolder', serialize($vfolder));
    }

    /**
     * Add a virtual folder for the current user.
     *
     * @param IMAP_Search_Query $query  The search query object.
     * @param array $folders            The list of folders to search.
     * @param array $search             The search array used to build the
     *                                  search UI screen.
     * @param string $label             The label to use for the search
     *                                  results.
     * @param string $id                The virtual folder id.
     *
     * @return string  The virtual folder ID.
     */
    function addVFolder($query, $folders, $search, $label, $id = null)
    {
        $id = $this->createSearchQuery($query, $folders, $search, $label, $id);
        $_SESSION['imp']['search']['q'][$id]['vfolder'] = true;
        if ($this->_saveVFolder) {
            $vfolders = $this->_getVFolderList();
            $vfolders[$id] = $_SESSION['imp']['search']['q'][$id];
            $this->_saveVFolderList($vfolders);
        }
        $this->_updateIMPTree('add', $id, $label);
        return $id;
    }

    /**
     * Add a virtual trash folder for the current user.
     */
    function createVTrashFolder()
    {
        /* Delete the current Virtual Trash folder, if it exists. */
        $vtrash_id = $GLOBALS['prefs']->getValue('vtrash_id');
        if (!empty($vtrash_id)) {
            $this->deleteSearchQuery($vtrash_id, true);
        }

        if (!$GLOBALS['prefs']->getValue('use_vtrash')) {
            return;
        }

        /* Create Virtual Trash with new folder list. */
        require_once IMP_BASE . '/lib/Folder.php';
        $imp_folder = &IMP_Folder::singleton();
        $fl = $imp_folder->flist_IMP();
        $flist = array();
        foreach ($fl as $mbox) {
            if (!empty($mbox['val'])) {
                $flist[] = $mbox['val'];
            }
        }
        array_unshift($flist, 'INBOX');

        require_once IMP_BASE . '/lib/IMAP/Search.php';
        $query = new IMP_IMAP_Search_Query();
        $query->deleted(true);
        $label = _("Virtual Trash");

        $this->_saveVFolder = false;
        if (empty($vtrash_id)) {
            $vtrash_id = $this->addVFolder($query, $flist, array(), $label);
            $GLOBALS['prefs']->setValue('vtrash_id', $vtrash_id);
        } else {
            $this->addVFolder($query, $flist, array(), $label, $vtrash_id);
        }
        $this->_saveVFolder = true;
        $_SESSION['imp']['search']['vtrash_id'] = $vtrash_id;
    }

    /**
     * Determines whether a virtual folder ID is the Virtual Trash Folder.
     *
     * @param string $id  The search query id to use (by default, will use
     *                    the current ID set in the object).
     *
     * @return boolean  True if the virutal folder ID is the Virtual Trash
     *                  folder.
     */
    function isVTrashFolder($id = null)
    {
        $id = $this->_strip($id);
        $vtrash_id = $GLOBALS['prefs']->getValue('vtrash_id');
        return (!empty($vtrash_id) && ($id == $vtrash_id));
    }

    /**
     * Add a virtual INBOX folder for the current user.
     */
    function createVINBOXFolder()
    {
        /* Initialize IMP_Tree. */
        require_once IMP_BASE . '/lib/IMAP/Tree.php';
        $imptree = &IMP_Tree::singleton();

        /* Delete the current Virtual Inbox folder, if it exists. */
        $vinbox_id = $GLOBALS['prefs']->getValue('vinbox_id');
        if (!empty($vinbox_id)) {
            $this->deleteSearchQuery($vinbox_id, true);
        }

        if (!$GLOBALS['prefs']->getValue('use_vinbox')) {
            return;
        }

        /* Create Virtual INBOX with nav_poll list. Filter out any nav_poll
         * entries that don't exist. Sort the list also. */
        $flist = $imptree->getPollList(true, true);

        require_once IMP_BASE . '/lib/IMAP/Search.php';
        $query = new IMP_IMAP_Search_Query();
        $query->seen(false);
        $query->deleted(false);
        $label = _("Virtual INBOX");

        $this->_saveVFolder = false;
        if (empty($vinbox_id)) {
            $vinbox_id = $this->addVFolder($query, $flist, array(), $label);
            $GLOBALS['prefs']->setValue('vinbox_id', $vinbox_id);
        } else {
            $this->addVFolder($query, $flist, array(), $label, $vinbox_id);
        }
        $this->_saveVFolder = true;
        $_SESSION['imp']['search']['vinbox_id'] = $vinbox_id;
    }

    /**
     * Determines whether a virtual folder ID is the Virtual INBOX Folder.
     *
     * @param string $id  The search query id to use (by default, will use
     *                    the current ID set in the object).
     *
     * @return boolean  True if the virutal folder ID is the Virtual INBOX
     *                  folder.
     */
    function isVINBOXFolder($id = null)
    {
        $id = $this->_strip($id);
        $vinbox_id = $GLOBALS['prefs']->getValue('vinbox_id');
        return (!empty($vinbox_id) && ($id == $vinbox_id));
    }

    /**
     * Is the current active folder an editable Virtual Folder?
     *
     * @param string $id  The search query id to use (by default, will use
     *                    the current ID set in the object).
     *
     * @return boolean  True if the current folder is both a virtual folder
     *                  and can be edited.
     */
    function isEditableVFolder($id = null)
    {
        $id = $this->_strip($id);
        return ($this->isVFolder($id) && !$this->isVTrashFolder($id) && !$this->isVINBOXFolder($id));
    }

    /**
     * Return a list of IDs and query labels, sorted by the label.
     *
     * @param boolean $vfolder  If true, only return Virtual Folders?
     *
     * @return array  An array with the folder IDs as the key and the labels
     *                as the value.
     */
    function listQueries($vfolder = false)
    {
        $vfolders = array();

        if (empty($_SESSION['imp']['search']['q'])) {
            return $vfolders;
        }

        foreach ($_SESSION['imp']['search']['q'] as $key => $val) {
            if (!$vfolder || !empty($val['vfolder'])) {
                $vfolders[$key] = $this->getLabel($key);
            }
        }
        natcasesort($vfolders);

        return $vfolders;
    }

    /**
     * Get the list of searchable folders for the given search query.
     *
     * @param string $id  The search query id to use (by default, will use
     *                    the current ID set in the object).
     *
     * @return array  The list of searchable folders.
     */
    function getSearchFolders($id = null)
    {
        $id = $this->_strip($id);
        return (isset($_SESSION['imp']['search']['q'][$id]['folders'])) ? $_SESSION['imp']['search']['q'][$id]['folders'] : array();
    }

    /**
     * Return a list of search queries valid only for the current session
     * (i.e. no virtual folders).
     *
     * @return array  Keys are the search ids, values are a textual
     *                description of the search.
     */
    function getSearchQueries()
    {
        $retarray = array();

        foreach ($_SESSION['imp']['search']['q'] as $key => $val) {
            if (!$this->isVFolder($key) &&
                ($text = $this->searchQueryText($key))) {
                $retarray[$key] = $text;
            }
        }

        return array_reverse($retarray, true);
    }

    /**
     * Return search query text representation for a given search ID.
     *
     * @since IMP 4.2
     *
     * @param string $id  The search query id to use (by default, will use
     *                    the current ID set in the object).
     *
     * @return array  The textual description of the search.
     */
    function searchQueryText($id = null)
    {
        $id = $this->_strip($id);
        if (empty($_SESSION['imp']['search']['q'][$id])) {
            return '';
        } elseif ($this->isVINBOXFolder($id) || $this->isVTrashFolder($id)) {
            return $_SESSION['imp']['search']['q'][$id]['label'];
        } elseif (empty($_SESSION['imp']['search']['q'][$id]['uiinfo'])) {
            unset($_SESSION['imp']['search']['q'][$id]);
            return '';
        }

        $flagfields = $this->flagFields();
        $searchfields = $this->searchFields();
        $val = $_SESSION['imp']['search']['q'][$id];

        $text = '';
        if (!empty($val['uiinfo']['field'])) {
            $text = _("Search") . ' ';
            $text_array = array();
            foreach ($val['uiinfo']['field'] as $key2 => $val2) {
                if (isset($flagfields[$val2])) {
                    $text_array[] = $flagfields[$val2]['label'];
                } else {
                    switch ($searchfields[$val2]['type']) {
                    case IMP_SEARCH_DATE:
                        $text_array[] = sprintf("%s '%s'", $searchfields[$val2]['label'], strftime("%x", mktime(0, 0, 0, $val['uiinfo']['date'][$key2]['month'], $val['uiinfo']['date'][$key2]['day'], $val['uiinfo']['date'][$key2]['year'])));
                        break;

                    case IMP_SEARCH_SIZE:
                        $text_array[] = $searchfields[$val2]['label'] . ' ' . ($val['uiinfo']['text'][$key2] / 1024);
                        break;

                    default:
                        $text_array[] = sprintf("%s for '%s'", $searchfields[$val2]['label'], ((!empty($val['uiinfo']['text_not'][$key2])) ? _("not") . ' ' : '') . $val['uiinfo']['text'][$key2]);
                        break;
                    }
                }
            }
            $text .= implode(' ' . (($val['uiinfo']['match'] == 'and') ? _("and") : _("or")) . ' ', $text_array);
        }

        return $text . ' ' . _("in") . ' ' . implode(', ', $val['uiinfo']['folders']);
    }

    /**
     * Returns a link to edit a given search query.
     *
     * @param string $id  The search query id to use (by default, will use
     *                    the current ID set in the object).
     *
     * @return string  The URL to the search page.
     */
    function editURL($id = null)
    {
        $id = $this->_strip($id);
        return Util::addParameter(Horde::applicationUrl('search.php'), array('edit_query' => $id));
    }

    /**
     * Returns a link to delete a given search query.
     *
     * @param string $id  The search query id to use (by default, will use
     *                    the current ID set in the object).
     *
     * @return string  The URL to allow deletion of the search query.
     */
    function deleteURL($id = null)
    {
        $id = $this->_strip($id);
        return Util::addParameter(Horde::applicationUrl('folders.php'),
                                  array('actionID' => 'delete_search_query',
                                        'folders_token' => IMP::getRequestToken('imp.folders'),
                                        'queryid' => $id,
                                  ));
    }

    /**
     * Is the given mailbox a search mailbox?
     *
     * @param string $id  The search query id to use (by default, will use
     *                    the current ID set in the object).
     *
     * @return boolean  Whether the given mailbox name is a search mailbox.
     */
    function isSearchMbox($id = null)
    {
        return ($id === null) ? !empty($this->_id) : isset($_SESSION['imp']['search']['q'][$this->_strip($id)]);
    }

    /**
     * Is the given mailbox a virtual folder?
     *
     * @param string $id  The search query id to use (by default, will use
     *                    the current ID set in the object).
     *
     * @return boolean  Whether the given mailbox name is a virtual folder.
     */
    function isVFolder($id = null)
    {
        $id = $this->_strip($id);
        return (!empty($_SESSION['imp']['search']['q'][$id]['vfolder']));
    }

    /**
     * Get the ID for the search mailbox, if we are currently in a search
     * mailbox.
     *
     * @return mixed  The search ID if in a mailbox, else false.
     */
    function searchMboxID()
    {
        return ($this->_id !== null) ? $this->_id : false;
    }

    /**
     * Strip the identifying label from a mailbox ID.
     *
     * @access private
     *
     * @param string $id  The mailbox query ID.
     *
     * @return string  The virtual folder ID, with any IMP specific identifying
     *                 information stripped off.
     */
    function _strip($id)
    {
        return ($id === null) ? $this->_id : ((strpos($id, IMP_SEARCH_MBOX) === 0) ? substr($id, strlen(IMP_SEARCH_MBOX)) : $id);
    }

    /**
     * Create the canonical search ID for a given search query.
     *
     * @since IMP 4.1.2
     *
     * @access public
     *
     * @param string $id  The mailbox query ID.
     *
     * @return string  The canonical search query ID.
     */
    function createSearchID($id)
    {
        return IMP_SEARCH_MBOX . $this->_strip($id);
    }

    /**
     * Return the base search fields.
     *
     * @return array  The base search fields.
     */
    function searchFields()
    {
        return array(
            'from' => array(
                'label' => _("From"),
                'type' => IMP_SEARCH_HEADER,
                'not' => true
            ),
            'to' => array(
                'label' => _("To"),
                'type' => IMP_SEARCH_HEADER,
                'not' => true
            ),
            'cc' => array(
                'label' => _("Cc"),
                'type' => IMP_SEARCH_HEADER,
                'not' => true
            ),
            'bcc' => array(
                'label' => _("Bcc"),
                'type' => IMP_SEARCH_HEADER,
                'not' => true
            ),
            'subject' => array(
                'label' => _("Subject"),
                'type' => IMP_SEARCH_HEADER,
                'not' => true
            ),
            'body' => array(
               'label' => _("Body"),
               'type' => IMP_SEARCH_BODY,
                'not' => true
            ),
            'text' => array(
               'label' => _("Entire Message"),
               'type' => IMP_SEARCH_TEXT,
                'not' => true
            ),
            'date_on' => array(
                'label' => _("Date ="),
                'type' => IMP_SEARCH_DATE,
                'not' => true
            ),
            'date_until' => array(
                'label' => _("Date <"),
                'type' => IMP_SEARCH_DATE,
                'not' => true
            ),
            'date_since' => array(
                'label' => _("Date >="),
                'type' => IMP_SEARCH_DATE,
                'not' => true
            ),
            // Displayed in KB, but stored internally in bytes
            'size_smaller' => array(
                'label' => _("Size (KB) <"),
                'type' => IMP_SEARCH_SIZE,
                'not' => false
            ),
            // Displayed in KB, but stored internally in bytes
            'size_larger' => array(
                'label' => _("Size (KB) >"),
                'type' => IMP_SEARCH_SIZE,
                'not' => false
            ),
        );
    }

    /**
     * Return the base flag fields.
     *
     * @since IMP 4.2.1
     *
     * @return array  The base flag fields.
     */
    function flagFields()
    {
        return array(
            'seen' => array(
                'flag' => 'seen',
                'label' => _("Seen messages"),
                'type' => IMP_SEARCH_FLAG_HAS
            ),
            'unseen' => array(
                'flag' => 'seen',
                'label' => _("Unseen messages"),
                'type' => IMP_SEARCH_FLAG_NOT
            ),
            'answered' => array(
                'flag' => 'answered',
                'label' => _("Answered messages"),
                'type' => IMP_SEARCH_FLAG_HAS
            ),
            'unanswered' => array(
                'flag' => 'answered',
                'label' => _("Unanswered messages"),
                'type' => IMP_SEARCH_FLAG_NOT
            ),
            'flagged' => array(
                'flag' => 'flagged',
                'label' => _("Flagged messages"),
                'type' => IMP_SEARCH_FLAG_HAS
            ),
            'unflagged' => array(
                'flag' => 'flagged',
                'label' => _("Unflagged messages"),
                'type' => IMP_SEARCH_FLAG_NOT
            ),
            'deleted' => array(
                'flag' => 'deleted',
                'label' => _("Deleted messages"),
                'type' => IMP_SEARCH_FLAG_HAS
            ),
            'undeleted' => array(
                'flag' => 'deleted',
                'label' => _("Undeleted messages"),
                'type' => IMP_SEARCH_FLAG_NOT
            ),
        );
    }

    /**
     * Update IMAP_Tree object.
     *
     * @access private
     *
     * @param string $action  Either 'delete' or 'add'.
     * @param string $id      The query ID to update.
     * @param string $label   If $action = 'add', the label to use for the
     *                        query ID.
     */
    function _updateIMPTree($action, $id, $label = null)
    {
        require_once IMP_BASE . '/lib/IMAP/Tree.php';
        $imptree = &IMP_Tree::singleton();

        switch ($action) {
        case 'delete':
            $imptree->delete($id);
            break;

        case 'add':
            $imptree->insertVFolders(array($id => $label));
            break;
        }
    }

    /**
     * Return an IMAP_Search object.
     *
     * @access private
     *
     * @return IMAP_Search  The IMAP_Search object.
     */
    function &_getIMAPSearch()
    {
        $charset = NLS::getCharset();
        $search_params = array('pop3' => ($_SESSION['imp']['base_protocol'] == 'pop3'), 'charset' => $charset);

        /* Check if the IMAP server supports searches in the current
         * charset. */
        if (empty($_SESSION['imp']['imap_server']['search_charset'][$charset])) {
            $search_params['no_imap_charset'] = true;
        }

        require_once IMP_BASE . '/lib/IMAP/Search.php';
        $imap_search = &IMP_IMAP_Search::singleton($search_params);

        return $imap_search;
    }

    /**
     * Creates a search query.
     *
     * @since IMP 4.2.1
     *
     * @param array $uiinfo  An uiinfo array (see imp/search.php).
     *
     * @return IMP_IMAP_Search_Query  A search object.
     */
    function createQuery($search)
    {
        require_once IMP_BASE . '/lib/IMAP/Search.php';
        $query = new IMP_IMAP_Search_Query();

        $search_array = array();
        $search_fields = $this->searchFields();
        $flag_fields = $this->flagFields();

        foreach ($search['field'] as $key => $val) {
            $ob = new IMP_IMAP_Search_Query();

            if (isset($flag_fields[$val])) {
                $ob->$flag_fields[$val]['flag']((bool)$flag_fields[$val]['type']);
                $search_array[] = $ob;
            } else {
                switch ($search_fields[$val]['type']) {
                case IMP_SEARCH_HEADER:
                    if (!empty($search['text'][$key])) {
                        $ob->header($val, $search['text'][$key], $search['text_not'][$key]);
                        $search_array[] = $ob;
                    }
                    break;

                case IMP_SEARCH_BODY:
                    if (!empty($search['text'][$key])) {
                        $ob->body($search['text'][$key], $search['text_not'][$key]);
                        $search_array[] = $ob;
                    }
                    break;

                case IMP_SEARCH_TEXT:
                    if (!empty($search['text'][$key])) {
                        $ob->text($search['text'][$key], $search['text_not'][$key]);
                        $search_array[] = $ob;
                    }
                    break;

                case IMP_SEARCH_DATE:
                    if (!empty($search['date'][$key]['day']) &&
                        !empty($search['date'][$key]['month']) &&
                        !empty($search['date'][$key]['year'])) {
                        if ($val == 'date_on') {
                            $ob->on($search['date'][$key]['day'], $search['date'][$key]['month'], $search['date'][$key]['year']);
                        } elseif ($val == 'date_until') {
                            $ob->before($search['date'][$key]['day'], $search['date'][$key]['month'], $search['date'][$key]['year']);
                        } elseif ($val == 'date_since') {
                            $ob->since($search['date'][$key]['day'], $search['date'][$key]['month'], $search['date'][$key]['year']);
                        }
                        $search_array[] = $ob;
                    }
                    break;

                case IMP_SEARCH_SIZE:
                    if (!empty($search['text'][$key])) {
                        $ob->size(intval($search['text'][$key]), ($val == 'size_larger') ? '>' : '<');
                        $search_array[] = $ob;
                    }
                    break;
                }
            }
        }

        /* Search match. */
        if ($search['match'] == 'and') {
            $query->imapAnd($search_array);
        } elseif ($search['match'] == 'or') {
            $query->imapOr($search_array);
        }

        return $query;
    }

}
