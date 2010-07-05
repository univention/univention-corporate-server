<?php

require_once 'Horde/Serialize.php';

/**
 * The IMP_tree class provides a tree view of the mailboxes in an IMAP/POP3
 * repository.  It provides access functions to iterate through this tree and
 * query information about individual mailboxes.
 * In IMP, folders = IMAP mailboxes so the two terms are used interchangably.
 *
 * $Horde: imp/lib/IMAP/Tree.php,v 1.25.2.70 2009-05-15 21:40:01 slusarz Exp $
 *
 * Copyright 2000-2009 The Horde Project (http://www.horde.org/)
 *
 * See the enclosed file COPYING for license information (GPL). If you
 * did not receive this file, see http://www.fsf.org/copyleft/gpl.html.
 *
 * @author  Chuck Hagenbuch <chuck@horde.org>
 * @author  Jon Parise <jon@horde.org>
 * @author  Anil Madhavapeddy <avsm@horde.org>
 * @author  Michael Slusarz <slusarz@horde.org>
 * @package IMP
 */

/* Constants for mailboxElt attributes. */
define('IMPTREE_ELT_NOSELECT', 1);
define('IMPTREE_ELT_NAMESPACE', 2);
define('IMPTREE_ELT_IS_OPEN', 4);
define('IMPTREE_ELT_IS_SUBSCRIBED', 8);
define('IMPTREE_ELT_NOSHOW', 16);
define('IMPTREE_ELT_IS_POLLED', 32);
define('IMPTREE_ELT_NEED_SORT', 64);
define('IMPTREE_ELT_VFOLDER', 128);
define('IMPTREE_ELT_NONIMAP', 256);
define('IMPTREE_ELT_INVISIBLE', 512);

/* The isOpen() expanded mode constants. */
define('IMPTREE_OPEN_NONE', 0);
define('IMPTREE_OPEN_ALL', 1);
define('IMPTREE_OPEN_USER', 2);

/* The manner to which to traverse the tree when calling next(). */
define('IMPTREE_NEXT_SHOWCLOSED', 1);
define('IMPTREE_NEXT_SHOWSUB', 2);

/* The string used to indicate the base of the tree. */
define('IMPTREE_BASE_ELT', '%');

/** Defines used with the output from the build() function. */
define('IMPTREE_SPECIAL_INBOX', 1);
define('IMPTREE_SPECIAL_TRASH', 2);
define('IMPTREE_SPECIAL_DRAFT', 3);
define('IMPTREE_SPECIAL_SPAM', 4);
define('IMPTREE_SPECIAL_SENT', 5);

/** Defines used with folderList(). */
define('IMPTREE_FLIST_CONTAINER', 1);
define('IMPTREE_FLIST_UNSUB', 2);
define('IMPTREE_FLIST_OB', 4);
define('IMPTREE_FLIST_VFOLDER', 8);

/* Add a percent to folder key since it allows us to sort by name but never
 * conflict with an IMAP mailbox of the same name (since '%' is an invalid
 * character in an IMAP mailbox string). */
/** Defines used with virtual folders. */
define('IMPTREE_VFOLDER_LABEL', _("Virtual Folders"));
define('IMPTREE_VFOLDER_KEY', IMPTREE_VFOLDER_LABEL . '%');

/** Defines used with namespace display. */
define('IMPTREE_SHARED_LABEL', _("Shared Folders"));
define('IMPTREE_SHARED_KEY', IMPTREE_SHARED_LABEL . '%');
define('IMPTREE_OTHER_LABEL', _("Other Users' Folders"));
define('IMPTREE_OTHER_KEY', IMPTREE_OTHER_LABEL . '%');

class IMP_Tree {

    /**
     * Array containing the mailbox tree.
     *
     * @var array
     */
    var $_tree;

    /**
     * Location of current element in the tree.
     *
     * @var string
     */
    var $_currparent = null;

    /**
     * Location of current element in the tree.
     *
     * @var integer
     */
    var $_currkey = null;

    /**
     * Location of current element in the tree.
     *
     * @var array
     */
    var $_currstack = array();

    /**
     * Show unsubscribed mailboxes?
     *
     * @var boolean
     */
    var $_showunsub = false;

    /**
     * Parent list.
     *
     * @var array
     */
    var $_parent = array();

    /**
     * The cached list of mailboxes to poll.
     *
     * @var array
     */
    var $_poll = null;

    /**
     * The cached list of expanded folders.
     *
     * @var array
     */
    var $_expanded = null;

    /**
     * Cached list of subscribed mailboxes.
     *
     * @var array
     */
    var $_subscribed = null;

    /**
     * The cached full list of mailboxes on the server.
     *
     * @var array
     */
    var $_fulllist = null;

    /**
     * Tree changed flag.  Set when something in the tree has been altered.
     *
     * @var boolean
     */
    var $_changed = false;

    /**
     * Have we shown unsubscribed folders previously?
     *
     * @var boolean
     */
    var $_unsubview = false;

    /**
     * The IMAP_Sort object.
     *
     * @var IMAP_Sort
     */
    var $_imap_sort = null;

    /**
     * The server string for the current server.
     *
     * @var string
     */
    var $_server = '';

    /**
     * The server string used for the delimiter.
     *
     * @var string
     */
    var $_delimiter = '/';

    /**
     * The list of namespaces to add to the tree.
     *
     * @var array
     */
    var $_namespaces = array();

    /**
     * Used to determine the list of element changes.
     *
     * @var array
     */
    var $_eltdiff = null;

    /**
     * If set, track element changes.
     *
     * @var boolean
     */
    var $_trackdiff = true;

    /**
     * See $open parameter in build().
     *
     * @var boolean
     */
    var $_forceopen = false;

    /**
     * Attempts to return a reference to a concrete IMP_Tree instance.
     *
     * If an IMP_Tree object is currently stored in the local session,
     * recreate that object.  Else, create a new instance.  Ensures that only
     * one IMP_Tree instance is available at any time.
     *
     * This method must be invoked as:<pre>
     *   $imp_tree = &IMP_Tree::singleton();
     * </pre>
     *
     * @return IMP_Tree  The IMP_Tree object or null.
     */
    function &singleton()
    {
        static $instance;

        if (!isset($instance)) {
            if (!empty($_SESSION['imp']['cache']['imp_tree'])) {
                $ptr = &$_SESSION['imp']['cache']['imp_tree'];
                $instance = Horde_Serialize::unserialize($ptr['ob'], $ptr['s']);
            }
            if (empty($instance) || is_a($instance, 'PEAR_Error')) {
                $instance = new IMP_Tree();
            }
            register_shutdown_function(array(&$instance, '_store'));
        }

        return $instance;
    }

    /**
     * Constructor.
     */
    function IMP_Tree()
    {
        $this->_server = IMP::serverString();

        if ($_SESSION['imp']['base_protocol'] != 'pop3') {
            $ptr = reset($_SESSION['imp']['namespace']);
            $this->_delimiter = $ptr['delimiter'];
            $this->_namespaces = (empty($GLOBALS['conf']['user']['allow_folders'])) ? array() : $_SESSION['imp']['namespace'];
        }

        $this->init();
    }

    /**
     * Store a serialized version of ourself in the current session.
     *
     * @access private
     */
    function _store()
    {
        /* We only need to restore the object if the tree has changed. */
        if (empty($this->_changed)) {
            return;
        }

        /* Don't store $_expanded and $_poll - these values are handled
         * by the subclasses.
         * Don't store $_imap_sort or $_eltdiff - these needs to be
         * regenerated for each request.
         * Don't store $_currkey, $_currparent, and $_currstack since the
         * user MUST call reset() before cycling through the tree.
         * Don't store $_subscribed and $_fulllist - - this information is
         * stored in the elements.
         * Reset the $_changed and $_trackdiff flags. */
        $this->_currkey = $this->_currparent = $this->_eltdiff = $this->_expanded = $this->_fulllist = $this->_imap_sort = $this->_poll = $this->_subscribed = null;
        $this->_currstack = array();
        $this->_changed = false;
        $this->_trackdiff = true;

        if (!isset($_SESSION['imp']['cache']['imp_tree'])) {
            $_SESSION['imp']['cache']['imp_tree'] = array(
                's' => (defined('SERIALIZE_LZF') && Horde_Serialize::hasCapability(SERIALIZE_LZF)) ? array(SERIALIZE_LZF, SERIALIZE_BASIC) : array(SERIALIZE_BASIC)
            );
        }

        $ptr = &$_SESSION['imp']['cache']['imp_tree'];
        $ptr['ob'] = Horde_Serialize::serialize($this, array_reverse($ptr['s']));
    }

    /**
     * Returns the list of mailboxes on the server.
     *
     * @access private
     *
     * @param boolean $showunsub  Show unsubscribed mailboxes?
     *
     * @return array  A list of mailbox names.
     *                The server string has been removed from the name.
     */
    function _getList($showunsub)
    {
        if ($showunsub && !is_null($this->_fulllist)) {
            return $this->_fulllist;
        } elseif (!$showunsub && !is_null($this->_subscribed)) {
            return array_keys($this->_subscribed);
        }

        /* INBOX must always appear. */
        $names = array('INBOX' => 1);

        $imp_imap = &IMP_IMAP::singleton();

        $old_error = error_reporting(0);
        foreach ($this->_namespaces as $key => $val) {
            $newboxes = call_user_func_array($showunsub ? 'imap_list' : 'imap_lsub', array($imp_imap->stream(), $this->_server, $key . '*'));
            if (is_array($newboxes)) {
                foreach ($newboxes as $box) {
                    /* Strip off server string. */
                    $names[$this->_convertName(substr($box, strpos($box, '}') + 1))] = 1;
                }
            }
        }
        error_reporting($old_error);

        // Cached mailbox lists.
        if ($showunsub) {
            $this->_fulllist = array_keys($names);
            return $this->_fulllist;
        } else {
            // Need to compare to full list to remove non-existent mailboxes
            // See RFC 3501 [6.3.9]
            $names = array_intersect($this->_getList(true), array_keys($names));
            $this->_subscribed = array_flip($names);
            return $names;
        }
    }

    /**
     * Make a single mailbox tree element.
     * An element consists of the following items (we use single letters here
     * to save in session storage space):
     *   'a'  --  Attributes
     *   'c'  --  Level count
     *   'l'  --  Label
     *   'p'  --  Parent node
     *   'v'  --  Value
     *
     * @access private
     *
     * @param string $name         The mailbox name.
     * @param integer $attributes  The mailbox's attributes.
     *
     * @return array  See above format.
     */
    function _makeElt($name, $attributes = 0)
    {
        $elt = array(
            'a' => $attributes,
            'c' => 0,
            'p' => IMPTREE_BASE_ELT,
            'v' => $name
        );

        /* Set subscribed values. We know the folder is subscribed, without
         * query of the IMAP server, in the following situations:
         * + Folder is INBOX.
         * + We are adding while in subscribe-only mode.
         * + Subscriptions are turned off. */
        if (!$this->isSubscribed($elt)) {
            if (!$this->_showunsub ||
                ($elt['v'] == 'INBOX') ||
                !$GLOBALS['prefs']->getValue('subscribe')) {
                $this->_setSubscribed($elt, true);
            } else {
                $this->_initSubscribed();
                $this->_setSubscribed($elt, isset($this->_subscribed[$elt['v']]));
            }
        }

        /* Check for polled status. */
        $this->_initPollList();
        $this->_setPolled($elt, isset($this->_poll[$elt['v']]));

        /* Check for open status. */
        switch ($GLOBALS['prefs']->getValue('nav_expanded')) {
        case IMPTREE_OPEN_NONE:
            $open = false;
            break;

        case IMPTREE_OPEN_ALL:
            $open = true;
            break;

        case IMPTREE_OPEN_USER:
            $this->_initExpandedList();
            $open = !empty($this->_expanded[$elt['v']]);
            break;
        }
        $this->_setOpen($elt, $open);

        /* Computed values. */
        $ns_info = $this->_getNamespace($elt['v']);
        $tmp = explode(is_null($ns_info) ? $this->_delimiter : $ns_info['delimiter'], $elt['v']);
        $elt['c'] = count($tmp) - 1;

        /* Convert 'INBOX' to localized name. */
        $elt['l'] = ($elt['v'] == 'INBOX') ? _("Inbox") : String::convertCharset($tmp[$elt['c']], 'UTF7-IMAP');

        if ($_SESSION['imp']['base_protocol'] != 'pop3') {
            if (!empty($GLOBALS['conf']['hooks']['display_folder'])) {
                $this->_setInvisible($elt, !Horde::callHook('_imp_hook_display_folder', array($elt['v']), 'imp'));
            }

            if ($elt['c'] != 0) {
                $elt['p'] = implode(is_null($ns_info) ? $this->_delimiter : $ns_info['delimiter'], array_slice($tmp, 0, $elt['c']));
            }

            if (!is_null($ns_info)) {
                switch ($ns_info['type']) {
                case 'personal':
                    /* Strip personal namespace. */
                    if (!empty($ns_info['name']) && ($elt['c'] != 0)) {
                        --$elt['c'];
                        if (strpos($elt['p'], $ns_info['delimiter']) === false) {
                            $elt['p'] = IMPTREE_BASE_ELT;
                        } elseif (strpos($elt['v'], $ns_info['name'] . 'INBOX' . $ns_info['delimiter']) === 0) {
                            $elt['p'] = 'INBOX';
                        }
                    }
                    break;

                case 'other':
                case 'shared':
                    if (substr($ns_info['name'], 0, -1 * strlen($ns_info['delimiter'])) == $elt['v']) {
                        $elt['a'] = IMPTREE_ELT_NOSELECT | IMPTREE_ELT_NAMESPACE;
                    }

                    if ($GLOBALS['prefs']->getValue('tree_view')) {
                        $name = ($ns_info['type'] == 'other') ? IMPTREE_OTHER_KEY : IMPTREE_SHARED_KEY;
                        if ($elt['c'] == 0) {
                            $elt['p'] = $name;
                            ++$elt['c'];
                        } elseif ($this->_tree[$name] && IMPTREE_ELT_NOSHOW) {
                            if ($elt['c'] == 1) {
                                $elt['p'] = $name;
                            }
                        } else {
                            ++$elt['c'];
                        }
                    }
                    break;
                }
            }
        }

        return $elt;
    }

    /**
     * Initalize the tree.
     */
    function init()
    {
        $initmode = (($_SESSION['imp']['base_protocol'] == 'pop3') ||
                     !$GLOBALS['prefs']->getValue('subscribe') ||
                     $_SESSION['imp']['showunsub'])
            ? 'unsub' : 'sub';

        /* Reset class variables to the defaults. */
        $this->_changed = true;
        $this->_currkey = $this->_currparent = $this->_subscribed = null;
        $this->_currstack = $this->_tree = $this->_parent = array();
        $this->_showunsub = $this->_unsubview = ($initmode == 'unsub');

        /* Create a placeholder element to the base of the tree list so we can
         * keep track of whether the base level needs to be sorted. */
        $this->_tree[IMPTREE_BASE_ELT] = array(
            'a' => IMPTREE_ELT_NEED_SORT,
            'v' => IMPTREE_BASE_ELT
        );

        if (empty($GLOBALS['conf']['user']['allow_folders']) ||
            ($_SESSION['imp']['base_protocol'] == 'pop3')) {
            $this->_insertElt($this->_makeElt('INBOX', IMPTREE_ELT_IS_SUBSCRIBED));
            return;
        }

        /* Add namespace elements. */
        foreach ($this->_namespaces as $key => $val) {
            if ($val['type'] != 'personal' &&
                $GLOBALS['prefs']->getValue('tree_view')) {
                $elt = $this->_makeElt(
                    ($val['type'] == 'other') ? IMPTREE_OTHER_KEY : IMPTREE_SHARED_KEY,
                    IMPTREE_ELT_NOSELECT | IMPTREE_ELT_NAMESPACE | IMPTREE_ELT_NONIMAP | IMPTREE_ELT_NOSHOW
                );
                $elt['l'] = ($val['type'] == 'other')
                    ? IMPTREE_OTHER_LABEL : IMPTREE_SHARED_LABEL;

                foreach ($this->_namespaces as $val2) {
                    if (($val2['type'] == $val['type']) &&
                        ($val2['name'] != $val['name'])) {
                        $elt['a'] &= ~IMPTREE_ELT_NOSHOW;
                        break;
                    }
                }

                $this->_insertElt($elt);
            }
        }

        /* Create the list (INBOX and all other hierarchies). */
        $this->insert($this->_getList($this->_showunsub));

        /* Add virtual folders to the tree. */
        $this->insertVFolders($GLOBALS['imp_search']->listQueries(true));
    }

    /**
     * Expand a mail folder.
     *
     * @param string $folder      The folder name to expand.
     * @param boolean $expandall  Expand all folders under this one?
     */
    function expand($folder, $expandall = false)
    {
        $folder = $this->_convertName($folder);

        if (!isset($this->_tree[$folder])) {
            return;
        }
        $elt = &$this->_tree[$folder];

        if ($this->hasChildren($elt)) {
            if (!$this->isOpen($elt)) {
                $this->_changed = true;
                $this->_setOpen($elt, true);
            }

            /* Expand all children beneath this one. */
            if ($expandall && !empty($this->_parent[$folder])) {
                foreach ($this->_parent[$folder] as $val) {
                    $this->expand($this->_tree[$val]['v'], true);
                }
            }
        }
    }

    /**
     * Collapse a mail folder.
     *
     * @param string $folder  The folder name to collapse.
     */
    function collapse($folder)
    {
        $folder = $this->_convertName($folder);

        if (!isset($this->_tree[$folder])) {
            return;
        }

        if ($this->isOpen($this->_tree[$folder])) {
            $this->_changed = true;
            $this->_setOpen($this->_tree[$folder], false);
        }
    }

    /**
     * Sets the internal array pointer to the next element, and returns the
     * next object.
     *
     * @param integer $mask  A mask with the following elements:
     * <pre>
     * IMPTREE_NEXT_SHOWCLOSED - Don't ignore closed elements.
     * IMPTREE_NEXT_SHOWSUB - Only show subscribed elements.
     * </pre>
     *
     * @return mixed  Returns the next element or false if the element doesn't
     *                exist.
     */
    function next($mask = 0)
    {
        do {
            $res = $this->_next($mask);
        } while (is_null($res));
        return $res;
    }

    /**
     * Private helper function to avoid recursion issues (see Bug #7420).
     *
     * @access private
     *
     * @param integer $mask  See next().
     *
     * @return mixed  Returns the next element, false if the element doesn't
     *                exist, or null if the current element is not active.
     */
    function _next($mask = 0)
    {
        if (is_null($this->_currkey) && is_null($this->_currparent)) {
            return false;
        }

        $curr = $this->current();

        $old_showunsub = $this->_showunsub;
        if ($mask & IMPTREE_NEXT_SHOWSUB) {
            $this->_showunsub = false;
        }

        if ($this->_activeElt($curr) &&
            (($mask & IMPTREE_NEXT_SHOWCLOSED) || $this->isOpen($curr)) &&
            ($this->_currparent != $curr['v'])) {
            /* If the current element is open, and children exist, move into
             * it. */
            $this->_currstack[] = array('k' => $this->_currkey, 'p' => $this->_currparent);
            $this->_currkey = 0;
            $this->_currparent = $curr['v'];
            $this->_sortLevel($curr['v']);

            $curr = $this->current();
            if ($GLOBALS['prefs']->getValue('tree_view') &&
                $this->isNamespace($curr) &&
                !$this->_isNonIMAPElt($curr) &&
                ($this->_tree[$curr['p']] && IMPTREE_ELT_NOSHOW)) {
                $this->next($mask);
            }
        } else {
            /* Else, increment within the current subfolder. */
            $this->_currkey++;
        }

        $curr = $this->current();
        if (!$curr) {
            if (empty($this->_currstack)) {
                $this->_currkey = $this->_currparent = null;
                $this->_showunsub = $old_showunsub;
                return false;
            } else {
                do {
                    $old = array_pop($this->_currstack);
                    $this->_currkey = $old['k'] + 1;
                    $this->_currparent = $old['p'];
                } while ((($curr = $this->current()) == false) &&
                         count($this->_currstack));
            }
        }

        $res = $this->_activeElt($curr);
        $this->_showunsub = $old_showunsub;
        return ($res) ? $curr : null;
    }

    /**
     * Set internal pointer to the head of the tree.
     * This MUST be called before you can traverse the tree with next().
     *
     * @return mixed  Returns the element at the head of the tree or false
     *                if the element doesn't exist.
     */
    function reset()
    {
        $this->_currkey = 0;
        $this->_currparent = IMPTREE_BASE_ELT;
        $this->_currstack = array();
        $this->_sortLevel($this->_currparent);
        return $this->current();
    }

    /**
     * Return the current tree element.
     *
     * @return array  The current tree element or false if there is no
     *                element.
     */
    function current()
    {
        return (!isset($this->_parent[$this->_currparent][$this->_currkey]))
            ? false
            : $this->_tree[$this->_parent[$this->_currparent][$this->_currkey]];
    }

    /**
     * Determines if there are more elements in the current tree level.
     *
     * @return boolean  True if there are more elements, false if this is the
     *                  last element.
     */
    function peek()
    {
        for ($i = ($this->_currkey + 1); ; ++$i) {
            if (!isset($this->_parent[$this->_currparent][$i])) {
                return false;
            }
            if ($this->_activeElt($this->_tree[$this->_parent[$this->_currparent][$i]])) {
                return true;
            }
        }
    }

    /**
     * Returns the requested element.
     *
     * @param string $name  The name of the tree element.
     *
     * @return array  Returns the requested element or false if not found.
     */
    function get($name)
    {
        $name = $this->_convertName($name);
        return (isset($this->_tree[$name])) ? $this->_tree[$name] : false;
    }

    /**
     * Insert a folder/mailbox into the tree.
     *
     * @param mixed $id  The name of the folder (or a list of folder names)
     *                   to add.
     */
    function insert($id)
    {
        if (is_array($id)) {
            /* We want to add from the BASE of the tree up for efficiency
             * sake. */
            $this->_sortList($id);
        } else {
            $id = array($id);
        }

        foreach ($id as $val) {
            if (isset($this->_tree[$val]) &&
                !$this->isContainer($this->_tree[$val])) {
                continue;
            }

            $ns_info = $this->_getNamespace($val);
            if (is_null($ns_info)) {
                if (strpos($val, IMPTREE_VFOLDER_KEY . $this->_delimiter) === 0) {
                    $elt = $this->_makeElt(IMPTREE_VFOLDER_KEY, IMPTREE_ELT_VFOLDER | IMPTREE_ELT_NOSELECT | IMPTREE_ELT_NONIMAP);
                    $elt['l'] = IMPTREE_VFOLDER_LABEL;
                    $this->_insertElt($elt);
                }

                $elt = $this->_makeElt($val, IMPTREE_ELT_VFOLDER | IMPTREE_ELT_IS_SUBSCRIBED);
                $elt['l'] = $elt['v'] = String::substr($val, String::length(IMPTREE_VFOLDER_KEY) + String::length($this->_delimiter));
                $this->_insertElt($elt);
            } else {
                /* Break apart the name via the delimiter and go step by
                 * step through the name to make sure all subfolders exist
                 * in the tree. */
                $parts = explode($ns_info['delimiter'], $val);
                $parts[0] = $this->_convertName($parts[0]);
                $parts_count = count($parts);
                for ($i = 0; $i < $parts_count; ++$i) {
                    $part = implode($ns_info['delimiter'], array_slice($parts, 0, $i + 1));

                    if (isset($this->_tree[$part])) {
                        if (($part == $val) &&
                            $this->isContainer($this->_tree[$part])) {
                            $this->_setContainer($this->_tree[$part], false);
                        }
                    } else {
                        $this->_insertElt(($part == $val) ? $this->_makeElt($part) : $this->_makeElt($part, IMPTREE_ELT_NOSELECT));
                    }
                }
            }
        }
    }

    /**
     * Insert an element into the tree.
     *
     * @access private
     *
     * @param array $elt  The element to insert. The key in the tree is the
     *                    'v' (value) element of the element.
     */
    function _insertElt($elt)
    {
        if (!strlen($elt['l']) || isset($this->_tree[$elt['v']])) {
            return;
        }

        // UW fix - it may return both 'foo' and 'foo/' as folder names.
        // Only add one of these (without the namespace character) to
        // the tree.  See Ticket #5764.
        $ns_info = $this->_getNamespace($elt['v']);
        if (isset($this->_tree[rtrim($elt['v'], is_null($ns_info) ? $this->_delimiter : $ns_info['delimiter'])])) {
            return;
        }

        $this->_changed = true;

        /* Set the parent array to the value in $elt['p']. */
        if (empty($this->_parent[$elt['p']])) {
            $this->_parent[$elt['p']] = array();
            // This is a case where it is possible that the parent element has
            // changed (it now has children) but we can't catch it via the
            // bitflag (since hasChildren() is dynamically determined).
            if ($this->_trackdiff && !is_null($this->_eltdiff)) {
                $this->_eltdiff['c'][$elt['p']] = 1;
            }
        }
        $this->_parent[$elt['p']][] = $elt['v'];
        $this->_tree[$elt['v']] = $elt;

        if ($this->_trackdiff && !is_null($this->_eltdiff)) {
            $this->_eltdiff['a'][$elt['v']] = 1;
        }

        /* Make sure we are sorted correctly. */
        if (count($this->_parent[$elt['p']]) > 1) {
            $this->_setNeedSort($this->_tree[$elt['p']], true);
        }
    }

    /**
     * Delete an element from the tree.
     *
     * @param mixed $id  The element name or an array of element names.
     *
     * @return boolean  Return true on success, false on error.
     */
    function delete($id)
    {
        if (is_array($id)) {
            /* We want to delete from the TOP of the tree down to ensure that
             * parents have an accurate view of what children are left. */
            $this->_sortList($id);
            $id = array_reverse($id);

            $success = true;
            foreach ($id as $val) {
                $currsuccess = $this->delete($val);
                if (!$currsuccess) {
                    $success = false;
                }
            }
            return $success;
        } else {
            $id = $this->_convertName($id, true);
        }

        $vfolder_base = ($id == IMPTREE_VFOLDER_LABEL);
        $search_id = $GLOBALS['imp_search']->createSearchID($id);

        if ($vfolder_base ||
            (isset($this->_tree[$search_id]) &&
             $this->isVFolder($this->_tree[$search_id]))) {
            if (!$vfolder_base) {
                $id = $search_id;

            }
            $parent = $this->_tree[$id]['p'];
            unset($this->_tree[$id]);

            /* Delete the entry from the parent tree. */
            $key = array_search($id, $this->_parent[$parent]);
            unset($this->_parent[$parent][$key]);

            /* Rebuild the parent tree. */
            if (!$vfolder_base && empty($this->_parent[$parent])) {
                $this->delete($parent);
            } else {
                $this->_parent[$parent] = array_values($this->_parent[$parent]);
            }
            $this->_changed = true;

            return true;
        }

        $ns_info = $this->_getNamespace($id);

        if (($id == 'INBOX') ||
            !isset($this->_tree[$id]) ||
            ($id == $ns_info['name'])) {
            return false;
        }

        $this->_changed = true;

        $elt = &$this->_tree[$id];

        /* Delete the entry from the folder list cache(s). */
        foreach (array('_subscribed', '_fulllist') as $var) {
            if (!is_null($this->$var)) {
                $this->$var = array_values(array_diff($this->$var, array($id)));
            }
        }

        /* Do not delete from tree if there are child elements - instead,
         * convert to a container element. */
        if ($this->hasChildren($elt)) {
            $this->_setContainer($elt, true);
            return true;
        }

        $parent = $elt['p'];

        /* Delete the tree entry. */
        unset($this->_tree[$id]);

        /* Delete the entry from the parent tree. */
        $key = array_search($id, $this->_parent[$parent]);
        unset($this->_parent[$parent][$key]);

        if (!is_null($this->_eltdiff)) {
            $this->_eltdiff['d'][$id] = 1;
        }

        if (empty($this->_parent[$parent])) {
            /* This folder is now completely empty (no children).  If the
             * folder is a container only, we should delete the folder from
             * the tree. */
            unset($this->_parent[$parent]);
            if (isset($this->_tree[$parent])) {
                if ($this->isContainer($this->_tree[$parent]) &&
                    !$this->isNamespace($this->_tree[$parent])) {
                    $this->delete($parent);
                } else {
                    $this->_modifyExpandedList($parent, 'remove');
                    $this->_setOpen($this->_tree[$parent], false);
                    /* This is a case where it is possible that the parent
                     * element has changed (it no longer has children) but
                     * we can't catch it via the bitflag (since hasChildren()
                     * is dynamically determined). */
                    if (!is_null($this->_eltdiff)) {
                        $this->_eltdiff['c'][$parent] = 1;
                    }
                }
            }
        } else {
            /* Rebuild the parent tree. */
            $this->_parent[$parent] = array_values($this->_parent[$parent]);
        }

        /* Remove the mailbox from the expanded folders list. */
        $this->_modifyExpandedList($id, 'remove');

        /* Remove the mailbox from the nav_poll list. */
        $this->removePollList($id);

        return true;
    }

    /**
     * Subscribe an element to the tree.
     *
     * @param mixed $id  The element name or an array of element names.
     */
    function subscribe($id)
    {
        if (!is_array($id)) {
            $id = array($id);
        }

        foreach ($id as $val) {
            $val = $this->_convertName($val);
            if (isset($this->_tree[$val])) {
                $this->_changed = true;
                $this->_setSubscribed($this->_tree[$val], true);
                $this->_setContainer($this->_tree[$val], false);
            }
        }
    }

    /**
     * Unsubscribe an element from the tree.
     *
     * @param mixed $id  The element name or an array of element names.
     */
    function unsubscribe($id)
    {
        if (!is_array($id)) {
            $id = array($id);
        } else {
            /* We want to delete from the TOP of the tree down to ensure that
             * parents have an accurate view of what children are left. */
            $this->_sortList($id);
            $id = array_reverse($id);
        }

        foreach ($id as $val) {
            $val = $this->_convertName($val);

            /* INBOX can never be unsubscribed to. */
            if (isset($this->_tree[$val]) && ($val != 'INBOX')) {
                $this->_changed = $this->_unsubview = true;

                $elt = &$this->_tree[$val];

                /* Do not delete from tree if there are child elements -
                 * instead, convert to a container element. */
                if (!$this->_showunsub && $this->hasChildren($elt)) {
                    $this->_setContainer($elt, true);
                }

                /* Set as unsubscribed, add to unsubscribed list, and remove
                 * from subscribed list. */
                $this->_setSubscribed($elt, false);
            }
        }
    }

    /**
     * Set an attribute for an element.
     *
     * @access private
     *
     * @param array &$elt     The tree element.
     * @param integer $const  The constant to set/remove from the bitmask.
     * @param boolean $bool   Should the attribute be set?
     */
    function _setAttribute(&$elt, $const, $bool)
    {
        if ($bool) {
            $elt['a'] |= $const;
        } else {
            $elt['a'] &= ~$const;
        }
    }

    /**
     * Does the element have any active children?
     *
     * @param array $elt  A tree element.
     *
     * @return boolean  True if the element has active children.
     */
    function hasChildren($elt)
    {
        if (isset($this->_parent[$elt['v']])) {
            if ($this->_showunsub) {
                return true;
            }

            foreach ($this->_parent[$elt['v']] as $val) {
                $child = &$this->_tree[$val];
                if ($this->isSubscribed($child) ||
                    $this->hasChildren($this->_tree[$val])) {
                    return true;
                }
            }
        }

        return false;
    }

    /**
     * Is the tree element open?
     *
     * @param array $elt  A tree element.
     *
     * @return integer  True if the element is open.
     */
    function isOpen($elt)
    {
        return (($elt['a'] & IMPTREE_ELT_IS_OPEN) && $this->hasChildren($elt));
    }

    /**
     * Set the open attribute for an element.
     *
     * @access private
     *
     * @param array &$elt    A tree element.
     * @param boolean $bool  The setting.
     */
    function _setOpen(&$elt, $bool)
    {
        $this->_setAttribute($elt, IMPTREE_ELT_IS_OPEN, $bool);
        $this->_modifyExpandedList($elt['v'], $bool ? 'add' : 'remove');
    }

    /**
     * Is this element a container only, not a mailbox (meaning you can
     * not open it)?
     *
     * @param array $elt  A tree element.
     *
     * @return integer  True if the element is a container.
     */
    function isContainer($elt)
    {
        return (($elt['a'] & IMPTREE_ELT_NOSELECT) ||
                (!$this->_showunsub &&
                 !$this->isSubscribed($elt) &&
                 $this->hasChildren($elt)));
    }

    /**
     * Set the element as a container?
     *
     * @access private
     *
     * @param array &$elt    A tree element.
     * @param boolean $bool  Is the element a container?
     */
    function _setContainer(&$elt, $bool)
    {
        $this->_setAttribute($elt, IMPTREE_ELT_NOSELECT, $bool);
    }

    /**
     * Is the user subscribed to this element?
     *
     * @param array $elt  A tree element.
     *
     * @return integer  True if the user is subscribed to the element.
     */
    function isSubscribed($elt)
    {
        return $elt['a'] & IMPTREE_ELT_IS_SUBSCRIBED;
    }

    /**
     * Set the subscription status for an element.
     *
     * @access private
     *
     * @param array &$elt    A tree element.
     * @param boolean $bool  Is the element subscribed to?
     */
    function _setSubscribed(&$elt, $bool)
    {
        $this->_setAttribute($elt, IMPTREE_ELT_IS_SUBSCRIBED, $bool);
        if (!is_null($this->_subscribed)) {
            if ($bool) {
                $this->_subscribed[$elt['v']] = 1;
            } else {
                unset($this->_subscribed[$elt['v']]);
            }
        }
    }

    /**
     * Is the element a namespace container?
     *
     * @param array $elt  A tree element.
     *
     * @return integer  True if the element is a namespace container.
     */
    function isNamespace($elt)
    {
        return $elt['a'] & IMPTREE_ELT_NAMESPACE;
    }

    /**
     * Is the element a non-IMAP element?
     *
     * @param array $elt  A tree element.
     *
     * @return integer  True if the element is a non-IMAP element.
     */
    function _isNonIMAPElt($elt)
    {
        return $elt['a'] & IMPTREE_ELT_NONIMAP;
    }

    /**
     * Initialize the expanded folder list.
     *
     * @access private
     */
    function _initExpandedList()
    {
        if (is_null($this->_expanded)) {
            $serialized = $GLOBALS['prefs']->getValue('expanded_folders');
            $this->_expanded = ($serialized) ? unserialize($serialized) : array();
        }
    }

    /**
     * Add/remove an element to the expanded list.
     *
     * @access private
     *
     * @param string $id      The element name to add/remove.
     * @param string $action  Either 'add' or 'remove';
     */
    function _modifyExpandedList($id, $action)
    {
        $this->_initExpandedList();
        if ($action == 'add') {
            $this->_expanded[$id] = true;
        } else {
            unset($this->_expanded[$id]);
        }
        $GLOBALS['prefs']->setValue('expanded_folders', serialize($this->_expanded));
    }

    /**
     * Initializes and returns the list of mailboxes to poll.
     *
     * @param boolean $prune  Prune non-existant folders from list?
     * @param boolean $sort   Sort the directory list?
     *
     * @return array  The list of mailboxes to poll.
     */
    function getPollList($prune = false, $sort = false)
    {
        $this->_initPollList();

        $plist = ($prune) ? array_values(array_intersect(array_keys($this->_poll), $this->folderList())) : $this->_poll;
        if ($sort) {
            require_once IMP_BASE . '/lib/IMAP/Sort.php';
            $ns_new = $this->_getNamespace(null);
            $imap_sort = new IMP_IMAP_Sort($ns_new['delimiter']);
            $imap_sort->sortMailboxes($plist);
        }

        return $plist;
    }

    /**
     * Init the poll list.  Called once per session.
     *
     * @access private
     */
    function _initPollList()
    {
        if (is_null($this->_poll)) {
            /* We ALWAYS poll the INBOX. */
            $this->_poll = array('INBOX' => 1);

            /* Add the list of polled mailboxes from the prefs. */
            if ($GLOBALS['prefs']->getValue('nav_poll_all')) {
                $navPollList = array_flip($this->_getList(true));
            } else {
                $old_error = error_reporting(0);
                $navPollList = unserialize($GLOBALS['prefs']->getValue('nav_poll'));
                error_reporting($old_error);
            }
            if ($navPollList) {
                $this->_poll += $navPollList;
            }
        }
    }

    /**
     * Add element to the poll list.
     *
     * @param mixed $id  The element name or a list of element names to add.
     */
    function addPollList($id)
    {
        if (!is_array($id)) {
            $id = array($id);
        }

        if (!empty($id) && !$GLOBALS['prefs']->isLocked('nav_poll')) {
            require_once IMP_BASE . '/lib/Folder.php';
            $imp_folder = &IMP_Folder::singleton();
            $this->getPollList();
            foreach ($id as $val) {
                if (!$this->isSubscribed($this->_tree[$val])) {
                    $imp_folder->subscribe(array($val));
                }
                $this->_poll[$val] = true;
                $this->_setPolled($this->_tree[$val], true);
            }
            $GLOBALS['prefs']->setValue('nav_poll', serialize($this->_poll));
            $this->_changed = true;
        }
    }

    /**
     * Remove element from the poll list.
     *
     * @param string $id  The folder/mailbox or a list of folders/mailboxes
     *                    to remove.
     */
    function removePollList($id)
    {
        if (!is_array($id)) {
            $id = array($id);
        }

        $removed = false;

        if (!$GLOBALS['prefs']->isLocked('nav_poll')) {
            $this->getPollList();
            foreach ($id as $val) {
                if ($val != 'INBOX') {
                    unset($this->_poll[$val]);
                    if (isset($this->_tree[$val])) {
                        $this->_setPolled($this->_tree[$val], false);
                    }
                    $removed = true;
                }
            }
            if ($removed) {
                $GLOBALS['prefs']->setValue('nav_poll', serialize($this->_poll));
                $this->_changed = true;
            }
        }
    }

    /**
     * Does the user want to poll this mailbox for new/unseen messages?
     *
     * @param array $elt  A tree element.
     *
     * @return integer  True if the user wants to poll the element.
     */
    function isPolled($elt)
    {
        return ($GLOBALS['prefs']->getValue('nav_poll_all')) ? true : ($elt['a'] & IMPTREE_ELT_IS_POLLED);
    }

    /**
     * Set the polled attribute for an element.
     *
     * @access private
     *
     * @param array &$elt    A tree element.
     * @param boolean $bool  The setting.
     */
    function _setPolled(&$elt, $bool)
    {
        $this->_setAttribute($elt, IMPTREE_ELT_IS_POLLED, $bool);
    }

    /**
     * Is the element invisible?
     *
     * @since IMP 4.3.4
     *
     * @param array $elt  A tree element.
     *
     * @return integer  True if the element is marked as invisible.
     */
    function isInvisible($elt)
    {
        return $elt['a'] & IMPTREE_ELT_INVISIBLE;
    }

    /**
     * Set the invisible attribute for an element.
     *
     * @access private
     * @since IMP 4.3.4
     *
     * @param array &$elt    A tree element.
     * @param boolean $bool  The setting.
     */
    function _setInvisible(&$elt, $bool)
    {
        $this->_setAttribute($elt, IMPTREE_ELT_INVISIBLE, $bool);
    }

    /**
     * Flag the element as needing its children to be sorted.
     *
     * @access private
     *
     * @param array &$elt    A tree element.
     * @param boolean $bool  The setting.
     */
    function _setNeedSort(&$elt, $bool)
    {
        $this->_setAttribute($elt, IMPTREE_ELT_NEED_SORT, $bool);
    }

    /**
     * Does this element's children need sorting?
     *
     * @param array $elt  A tree element.
     *
     * @return integer  True if the children need to be sorted.
     */
    function _needSort($elt)
    {
        return (($elt['a'] & IMPTREE_ELT_NEED_SORT) && (count($this->_parent[$elt['v']]) > 1));
    }

    /**
     * Initialize the list of subscribed mailboxes.
     *
     * @access private
     */
    function _initSubscribed()
    {
        if (is_null($this->_subscribed)) {
            $this->_getList(false);
        }
    }

    /**
     * Should we expand all elements?
     */
    function expandAll()
    {
        foreach ($this->_parent[IMPTREE_BASE_ELT] as $val) {
            $this->expand($val, true);
        }
    }

    /**
     * Should we collapse all elements?
     */
    function collapseAll()
    {
        foreach ($this->_tree as $key => $val) {
            if ($key !== IMPTREE_BASE_ELT) {
                $this->collapse($val['v']);
            }
        }
    }

    /**
     * Switch subscribed/unsubscribed viewing.
     *
     * @param boolean $unsub  Show unsubscribed elements?
     */
    function showUnsubscribed($unsub)
    {
        if ((bool)$unsub === $this->_showunsub) {
            return;
        }

        $this->_showunsub = $unsub;
        $this->_changed = true;

        /* If we are switching from unsubscribed to subscribed, no need
         * to do anything (we just ignore unsubscribed stuff). */
        if ($unsub === false) {
            return;
        }

        /* If we are switching from subscribed to unsubscribed, we need
         * to add all unsubscribed elements that live in currently
         * discovered items. */
        $this->_unsubview = true;
        $this->_trackdiff = false;
        $this->insert($this->_getList(true));
        $this->_trackdiff = true;
    }

    /**
     * Get information about new/unseen/total messages for the given element.
     *
     * @param string $name  The element name.
     *
     * @return array  Array with the following fields:
     * <pre>
     * 'messages'  --  Number of total messages.
     * 'newmsg'    --  Number of new messages.
     * 'unseen'    --  Number of unseen messages.
     * </pre>
     */
    function getElementInfo($name)
    {
        $status = array();

        require_once IMP_BASE . '/lib/IMAP/Cache.php';
        $imap_cache = &IMP_IMAP_Cache::singleton();
        $sts = $imap_cache->getStatus(null, $name);
        if (!empty($sts)) {
            $status = array(
                'messages' => $sts->messages,
                'unseen' => (isset($sts->unseen) ? $sts->unseen : 0),
                'newmsg' => (isset($sts->recent) ? $sts->recent : 0)
            );
        }

        return $status;
    }

    /**
     * Sorts a list of mailboxes.
     *
     * @access private
     *
     * @param array &$mbox   The list of mailboxes to sort.
     * @param boolean $base  Are we sorting a list of mailboxes in the base
     *                       of the tree.
     */
    function _sortList(&$mbox, $base = false)
    {
        if (is_null($this->_imap_sort)) {
            require_once 'Horde/IMAP/Sort.php';
            $this->_imap_sort = &new IMAP_Sort($this->_delimiter);
        }

        if ($base) {
            $basesort = array();
            foreach ($mbox as $val) {
                $basesort[$val] = ($val == 'INBOX') ? 'INBOX' : $this->_tree[$val]['l'];
            }
            $this->_imap_sort->sortMailboxes($basesort, true, true, true);
            $mbox = array_keys($basesort);
        } else {
            $this->_imap_sort->sortMailboxes($mbox, true);
        }

        if ($base) {
            for ($i = 0, $count = count($mbox); $i < $count; ++$i) {
                if ($this->_isNonIMAPElt($this->_tree[$mbox[$i]])) {
                    /* Already sorted by name - simply move to the end of
                     * the array. */
                    $mbox[] = $mbox[$i];
                    unset($mbox[$i]);
                }
            }
            $mbox = array_values($mbox);
        }
    }

    /**
     * Is the given element an "active" element (i.e. an element that should
     * be worked with given the current viewing parameters).
     *
     * @access private
     *
     * @param array $elt  A tree element.
     *
     * @return boolean  True if it is an active element.
     */
    function _activeElt($elt)
    {
        return (!$this->isInvisible($elt) &&
                ($this->_showunsub ||
                 ($this->isSubscribed($elt) && !$this->isContainer($elt)) ||
                 $this->hasChildren($elt)));
    }

    /**
     * Convert a mailbox name to the correct, internal name (i.e. make sure
     * INBOX is always capitalized for IMAP servers).
     *
     * @access private
     *
     * @param string $name  The mailbox name.
     *
     * @return string  The converted name.
     */
    function _convertName($name)
    {
        return (strcasecmp($name, 'INBOX') == 0) ? 'INBOX' : $name;
    }

    /**
     * Get namespace info for a full folder path.
     *
     * @access private
     *
     * @param string $mailbox  The folder path.
     *
     * @return mixed  The namespace info for the folder path or null if the
     *                path doesn't exist.
     */
    function _getNamespace($mailbox)
    {
        if (!in_array($mailbox, array(IMPTREE_OTHER_KEY, IMPTREE_SHARED_KEY, IMPTREE_VFOLDER_KEY)) &&
            (strpos($mailbox, IMPTREE_VFOLDER_KEY . $this->_delimiter) !== 0)) {
            return IMP::getNamespace($mailbox);
        }
        return null;
    }

    /**
     * Set the start point for determining element differences via eltDiff().
     *
     * @since IMP 4.1
     */
    function eltDiffStart()
    {
        $this->_eltdiff = array('a' => array(), 'c' => array(), 'd' => array());
    }

    /**
     * Return the list of elements that have changed since nodeDiffStart()
     * was last called.
     *
     * @since IMP 4.1
     *
     * @return array  Returns false if no changes have occurred, or an array
     *                with the following keys:
     * <pre>
     * 'a' => A list of elements that have been added.
     * 'c' => A list of elements that have been changed.
     * 'd' => A list of elements that have been deleted.
     * </pre>
     */
    function eltDiff()
    {
        if (is_null($this->_eltdiff) || !$this->_changed) {
            return false;
        }

        $ret = array(
            'a' => array_keys($this->_eltdiff['a']),
            'c' => array_keys($this->_eltdiff['c']),
            'd' => array_keys($this->_eltdiff['d'])
        );

        $this->_eltdiff = null;

        return $ret;
    }

    /**
     * Inserts virtual folders into the tree.
     *
     * @param array $id_list  An array with the folder IDs to add as the key
     *                        and the labels as the value.
     */
    function insertVFolders($id_list)
    {
        if (empty($id_list) ||
            empty($GLOBALS['conf']['user']['allow_folders'])) {
            return;
        }

        $adds = $id = array();

        foreach ($id_list as $key => $val) {
            $id[$GLOBALS['imp_search']->createSearchID($key)] = $val;
        }

        foreach (array_keys($id) as $key) {
            $id_key = IMPTREE_VFOLDER_KEY . $this->_delimiter . $key;
            if (!isset($this->_tree[$id_key])) {
                $adds[] = $id_key;
            }
        }

        if (empty($adds)) {
            return;
        }

        $this->insert($adds);

        foreach ($id as $key => $val) {
            $this->_tree[$key]['l'] = $val;
        }

        /* Sort the Virtual Folder list in the object, if necessary. */
        if ($this->_needSort($this->_tree[IMPTREE_VFOLDER_KEY])) {
            $vsort = array();
            foreach ($this->_parent[IMPTREE_VFOLDER_KEY] as $val) {
                $vsort[$val] = $this->_tree[$val]['l'];
            }
            natcasesort($vsort);
            $this->_parent[IMPTREE_VFOLDER_KEY] = array_keys($vsort);
            $this->_setNeedSort($this->_tree[IMPTREE_VFOLDER_KEY], false);
            $this->_changed = true;
        }
    }

    /**
     * Builds a list of folders, suitable to render a folder tree.
     *
     * @param integer $mask  The mask to pass to next().
     * @param boolean $open  If using the base folder icons, display a
     *                       different icon whether the folder is opened or
     *                       closed.
     *
     * @return array  An array with three elements: the folder list, the total
     *                number of new messages, and a list with folder names
     *                suitable for user interaction.
     *                The folder list array contains the following added
     *                entries on top of the entries provided by element():
     * <pre>
     * 'display' - The mailbox name run through IMP::displayFolder().
     * 'peek' - See peek().
     * </pre>
     */
    function build($mask = 0, $open = true)
    {
        $displayNames = $newmsgs = $rows = array();
        $this->_forceopen = $open;

        /* Start iterating through the list of mailboxes, displaying them. */
        $mailbox = $this->reset();
        do {
            $row = $this->element($mailbox['v']);

            $row['display'] = ($this->_isNonIMAPElt($mailbox)) ? $mailbox['l'] : IMP::displayFolder($mailbox['v']);
            $row['peek'] = $this->peek();

            if (!empty($row['newmsg'])) {
                $newmsgs[$row['value']] = $row['newmsg'];
            }

            /* Hide folder prefixes from the user. */
            if ($row['level'] >= 0) {
                $rows[] = $row;
                $displayNames[] = addslashes($row['display']);
            }
        } while (($mailbox = $this->next($mask)));

        $this->_forceopen = false;

        return array($rows, $newmsgs, $displayNames);
    }

    /**
     * Get any custom icon configured for the given element.
     *
     * @params array $elt  A tree element.
     *
     * @return array  An array with the 'icon', 'icondir', and 'alt'
     *                information for the element, or false if no icon
     *                available.
     */
    function getCustomIcon($elt)
    {
        static $mbox_icons;

        if (isset($mbox_icons) && !$mbox_icons) {
            return false;
        }

        /* Call the mailbox icon hook, if requested. */
        if (empty($GLOBALS['conf']['hooks']['mbox_icon'])) {
            $mbox_icons = false;
            return false;
        }

        if (!isset($mbox_icons)) {
            $mbox_icons = Horde::callHook('_imp_hook_mbox_icons', array(),
                                          'imp', false);
            if (!$mbox_icons) {
                return false;
            }
        }

        if (isset($mbox_icons[$elt['v']])) {
            return array('icon' => $mbox_icons[$elt['v']]['icon'], 'icondir' => $mbox_icons[$elt['v']]['icondir'], 'alt' => $mbox_icons[$elt['v']]['alt']);
        }

        return false;
    }

    /**
     * Returns whether this element is a virtual folder.
     *
     * @param array $elt  A tree element.
     *
     * @return integer  True if the element is a virtual folder.
     */
    function isVFolder($elt)
    {
        return $elt['a'] & IMPTREE_ELT_VFOLDER;
    }

    /**
     * Rename a current folder.
     *
     * @since IMP 4.1
     *
     * @param array $old  The old folder names.
     * @param array $new  The new folder names.
     */
    function rename($old, $new)
    {
        foreach ($old as $key => $val) {
            $polled = (isset($this->_tree[$val])) ? $this->isPolled($this->_tree[$val]) : false;
            if ($this->delete($val)) {
                $this->insert($new[$key]);
                if ($polled) {
                    $this->addPollList($new[$key]);
                }
            }
        }
    }

    /**
     * Returns a list of all IMAP mailboxes in the tree.
     *
     * @since IMP 4.1
     *
     * @param integer $mask  A mask with the following elements:
     * <pre>
     * IMPTREE_FLIST_CONTAINER - Show container elements.
     * IMPTREE_FLIST_UNSUB - Show unsubscribed elements.
     * IMPTREE_FLIST_OB - Return full tree object.
     * IMPTREE_FLIST_VFOLDER - Show Virtual Folders. (since IMP 4.2.1)
     * </pre>
     * @param string $base  Return all mailboxes below this element. (since
     *                      IMP 4.2.1)
     *
     * @return array  An array of IMAP mailbox names.
     */
    function folderList($mask = 0, $base = null)
    {
        $baseindex = null;
        $ret_array = array();

        $diff_unsub = (($mask & IMPTREE_FLIST_UNSUB) != $this->_showunsub) ? $this->_showunsub : null;
        $this->showUnsubscribed($mask & IMPTREE_FLIST_UNSUB);

        $mailbox = $this->reset();

        // Search to base element.
        if (!is_null($base)) {
            while ($mailbox && $mailbox['v'] != $base) {
                $mailbox = $this->next(IMPTREE_NEXT_SHOWCLOSED);
            }
            if ($mailbox) {
                $baseindex = count($this->_currstack);
                $baseparent = $this->_currparent;
                $basekey = $this->_currkey;
                $mailbox = $this->next(IMPTREE_NEXT_SHOWCLOSED);
            }
        }

        if ($mailbox) {
            do {
                if (!is_null($baseindex) &&
                    (!isset($this->_currstack[$baseindex]) ||
                     ($this->_currstack[$baseindex]['k'] != $basekey) ||
                     ($this->_currstack[$baseindex]['p'] != $baseparent))) {
                    break;
                }

                if ((($mask & IMPTREE_FLIST_CONTAINER) ||
                     !$this->isContainer($mailbox)) &&
                    (($mask & IMPTREE_FLIST_VFOLDER) ||
                     !$this->isVFolder($mailbox))) {
                    $ret_array[] = ($mask & IMPTREE_FLIST_OB) ? $mailbox : $mailbox['v'];
                }
            } while (($mailbox = $this->next(IMPTREE_NEXT_SHOWCLOSED)));
        }

        if (!is_null($diff_unsub)) {
            $this->showUnsubscribed($diff_unsub);
        }

        return $ret_array;
    }

    /**
     * Is the mailbox open in the sidebar?
     *
     * @since IMP 4.1.1
     *
     * @param array $mbox  A mailbox name.
     *
     * @return integer  True if the mailbox is open in the sidebar.
     */
    function isOpenSidebar($mbox)
    {
        switch ($GLOBALS['prefs']->getValue('nav_expanded_sidebar')) {
        case IMPTREE_OPEN_USER:
            $this->_initExpandedList();
            return !empty($this->_expanded[$mbox]);
            break;

        case IMPTREE_OPEN_ALL:
            return true;
            break;

        case IMPTREE_OPEN_NONE:
        default:
            return false;
            break;
        }
    }

    /**
     * Init frequently used element() data.
     *
     * @access private
     */
    function _initElement()
    {
        global $prefs, $registry;

        /* Initialize the user's identities. */
        require_once 'Horde/Identity.php';
        $identity = &Identity::singleton(array('imp', 'imp'));

        return array(
            'trash' => IMP::folderPref($prefs->getValue('trash_folder'), true),
            'draft' => IMP::folderPref($prefs->getValue('drafts_folder'), true),
            'spam' => IMP::folderPref($prefs->getValue('spam_folder'), true),
            'sent' => $identity->getAllSentmailFolders(),
            'image_dir' => $registry->getImageDir(),
        );
    }

    /**
     * Return extended information on an element.
     *
     * @since IMP 4.2
     *
     * @param string $name  The name of the tree element.
     *
     * @return array  Returns the element with extended information, or false
     *                if not found.  The information returned is as follows:
     * <pre>
     * 'alt' - The alt text for the icon.
     * 'base_elt' - The return from get().
     * 'children' - Does the element have children?
     * 'container' - Is this a container element?
     * 'editvfolder' - Can this virtual folder be edited?
     * 'icon' - The name of the icon graphic to use.
     * 'icondir' - The path of the icon directory.
     * 'level' - The deepness level of this element.
     * 'mbox_val' - A html-ized version of 'value'.
     * 'msgs' - The number of total messages in the element (if polled).
     * 'name' - A html-ized version of 'label'.
     * 'newmsg' - The number of new messages in the element (if polled).
     * 'parent' - The parent element value.
     * 'polled' - Show polled information?
     * 'special' - An integer mask indicating if this is a "special" element.
     * 'specialvfolder' - Is this a "special" virtual folder?
     * 'unseen' - The number of unseen messages in the element (if polled).
     * 'user_icon' - Use a user defined icon?
     * 'value' - The value of this element (i.e. element id).
     * 'vfolder' - Is this a virtual folder?
     * </pre>
     */
    function element($mailbox)
    {
        static $elt;

        $mailbox = $this->get($mailbox);
        if (!$mailbox) {
            return false;
        }

        if (!isset($elt)) {
            $elt = $this->_initElement();
        }

        $row = array(
            'base_elt' => $mailbox,
            'children' => $this->hasChildren($mailbox),
            'container' => false,
            'editvfolder' => false,
            'icondir' => $elt['image_dir'],
            'iconopen' => null,
            'level' => $mailbox['c'],
            'mbox_val' => htmlspecialchars($mailbox['v']),
            'name' => htmlspecialchars($mailbox['l']),
            'newmsg' => 0,
            'parent' => $mailbox['p'],
            'polled' => false,
            'special' => 0,
            'specialvfolder' => false,
            'user_icon' => false,
            'value' => $mailbox['v'],
            'vfolder' => false,
        );

        $icon = $this->getCustomIcon($mailbox);

        if (!$this->isContainer($mailbox)) {
            /* We are dealing with mailboxes here.
             * Determine if we need to poll this mailbox for new messages. */
            if ($this->isPolled($mailbox)) {
                /* If we need message information for this folder, update
                 * it now. */
                $msgs_info = $this->getElementInfo($mailbox['v']);
                if (!empty($msgs_info)) {
                    $row['polled'] = true;
                    if (!empty($msgs_info['newmsg'])) {
                        $row['newmsg'] = $msgs_info['newmsg'];
                    }
                    $row['msgs'] = $msgs_info['messages'];
                    $row['unseen'] = $msgs_info['unseen'];
                }
            }


            switch ($mailbox['v']) {
            case 'INBOX':
                $row['icon'] = 'folders/inbox.png';
                $row['alt'] = _("Inbox");
                $row['special'] = IMPTREE_SPECIAL_INBOX;
                break;

            case $elt['trash']:
                if ($GLOBALS['prefs']->getValue('use_vtrash')) {
                    $row['icon'] = ($this->isOpen($mailbox)) ? 'folders/folder_open.png' : 'folders/folder.png';
                    $row['alt'] = _("Mailbox");
                } else {
                    $row['icon'] = 'folders/trash.png';
                    $row['alt'] = _("Trash folder");
                    $row['special'] = IMPTREE_SPECIAL_TRASH;
                }
                break;

            case $elt['draft']:
                $row['icon'] = 'folders/drafts.png';
                $row['alt'] = _("Draft folder");
                $row['special'] = IMPTREE_SPECIAL_DRAFT;
                break;

            case $elt['spam']:
                $row['icon'] = 'folders/spam.png';
                $row['alt'] = _("Spam folder");
                $row['special'] = IMPTREE_SPECIAL_SPAM;
                break;

            default:
                if (in_array($mailbox['v'], $elt['sent'])) {
                    $row['icon'] = 'folders/sent.png';
                    $row['alt'] = _("Sent mail folder");
                    $row['special'] = IMPTREE_SPECIAL_SENT;
                } else {
                    $row['icon'] = ($this->isOpen($mailbox)) ? 'folders/folder_open.png' : 'folders/folder.png';
                    $row['alt'] = _("Mailbox");
                }
                break;
            }

            /* Virtual folders. */
            if ($this->isVFolder($mailbox)) {
                $row['vfolder'] = true;
                $row['editvfolder'] = $GLOBALS['imp_search']->isEditableVFolder($mailbox['v']);
                if ($GLOBALS['imp_search']->isVTrashFolder($mailbox['v'])) {
                    $row['specialvfolder'] = true;
                    $row['icon'] = 'folders/trash.png';
                    $row['alt'] = _("Virtual Trash Folder");
                } elseif ($GLOBALS['imp_search']->isVINBOXFolder($mailbox['v'])) {
                    $row['specialvfolder'] = true;
                    $row['icon'] = 'folders/inbox.png';
                    $row['alt'] = _("Virtual INBOX Folder");
                }
            }
        } else {
            /* We are dealing with folders here. */
            $row['container'] = true;
            if ($this->_forceopen && $this->isOpen($mailbox)) {
                $row['icon'] = 'folders/folder_open.png';
                $row['alt'] = _("Opened Folder");
            } else {
                $row['icon'] = 'folders/folder.png';
                $row['iconopen'] = 'folders/folder_open.png';
                $row['alt'] = ($this->_forceopen) ? _("Closed Folder") : _("Folder");
            }
            if ($this->isVFolder($mailbox)) {
                $row['vfolder'] = true;
            }
        }

        /* Overwrite the icon information now. */
        if (!empty($icon)) {
            $row['icon'] = $icon['icon'];
            $row['icondir'] = $icon['icondir'];
            if (!empty($icon['alt'])) {
                $row['alt'] = $icon['alt'];
            }
            $row['iconopen'] = isset($icon['iconopen']) ? $icon['iconopen'] : null;
            $row['user_icon'] = true;
        }

        return $row;
    }

    /**
     * Sort a level in the tree.
     *
     * @access private
     *
     * @param string $id  The parent folder whose children need to be sorted.
     */
    function _sortLevel($id)
    {
        if ($this->_needSort($this->_tree[$id])) {
            $this->_sortList($this->_parent[$id], ($id === IMPTREE_BASE_ELT));
            $this->_setNeedSort($this->_tree[$id], false);
            $this->_changed = true;
        }
    }

    /**
     * Determines the mailbox name to create given a parent and the new name.
     *
     * @param string $parent  The parent name.
     * @param string $parent  The new mailbox name.
     *
     * @return string  The full path to the new mailbox, or PEAR_Error.
     */
    function createMailboxName($parent, $new)
    {
        $ns_info = (empty($parent)) ? IMP::defaultNamespace() : $this->_getNamespace($parent);
        if (is_null($ns_info)) {
            if ($this->isNamespace($this->_tree[$parent])) {
                $ns_info = $this->_getNamespace($new);
                if (in_array($ns_info['type'], array('other', 'shared'))) {
                    return $new;
                }
            }
            return PEAR::raiseError(_("Cannot directly create mailbox in this folder."), 'horde.error');
        }

        $mbox = $ns_info['name'];
        if (!empty($parent)) {
            $mbox .= substr_replace($parent, '', 0, strlen($ns_info['name']));
            $mbox = rtrim($mbox, $ns_info['delimiter']) . $ns_info['delimiter'];
        }
        return $mbox . $new;
    }

}
