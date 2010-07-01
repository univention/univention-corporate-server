<?php
/* Constants for mailboxElt attributes.
 * All versions of c-client (c-client/mail.h) define these constants:
 *   LATT_NOINFERIORS (long) 0x1 = 1
 *   LATT_NOSELECT (long) 0x2 = 2
 *   LATT_MARKED (long) 0x4 = 4
 *   LATT_UNMARKED (long) 0x8 = 8
 *
 * Newer versions of c-client (imap-2002 and greater) define these constants:
 *   LATT_REFERRAL (long) 0x10 = 16
 *   LATT_HASCHILDREN (long) 0x20 = 32
 *   LATT_HASNOCHILDREN (long) 0x40 = 64
 * ...but these constant names do not appear in PHP until PHP 4.3.5 and 5.0.
 *
 * Also, no need to define LATT_REFERRAL at the present time since we don't use
 * it anywhere.
 */
if (!defined('LATT_HASCHILDREN')) {
//    @define('LATT_REFERRAL', 16);
    @define('LATT_HASCHILDREN', 32);
    @define('LATT_HASNOCHILDREN', 64);
}

/* Start at 128 for our local bitmasks to allow for the c-client LATT_*
   constants. */
define('IMAPTREE_ELT_HAS_CHILDREN', 128); // DEPRECATED
define('IMAPTREE_ELT_IS_OPEN', 256);
define('IMAPTREE_ELT_IS_SUBSCRIBED', 512);
define('IMAPTREE_ELT_IS_DISCOVERED', 1024);
define('IMAPTREE_ELT_IS_POLLED', 2048);
define('IMAPTREE_ELT_NEED_SORT', 4096);
// '8192' is used by IMP 4.x so do not use it here
// TODO: Renumber to 128 in Horde 4.0
define('IMAPTREE_ELT_NAMESPACE', 16384);

/* The isOpen() expanded mode constants. */
define('IMAPTREE_OPEN_NONE', 0);
define('IMAPTREE_OPEN_ALL', 1);
define('IMAPTREE_OPEN_USER', 2);

/* Which mode of IMAP access are we using. */
define('IMAPTREE_MODE_MAIL', 0);
define('IMAPTREE_MODE_NEWS', 1);

/* The initalization mode to use when creating the tree. */
define('IMAPTREE_INIT_SUB', 1);
define('IMAPTREE_INIT_UNSUB', 2);
define('IMAPTREE_INIT_FETCHALL', 4);

/* The manner to which to traverse the tree when calling next(). */
define('IMAPTREE_NEXT_SHOWCLOSED', 1);
define('IMAPTREE_NEXT_SHOWSUB', 2);

/* The string used to indicate the base of the tree. */
define('IMAPTREE_BASE_ELT', null);

/**
 * The IMAP_Tree class provides a tree view of the folders supported with
 * the PHP imap extension (IMAP/POP3/NNTP repositories).  It provides access
 * functions to iterate through this tree and query information about
 * individual mailboxes/folders.
 *
 * $Horde: framework/IMAP/IMAP/Tree.php,v 1.48.2.47 2009-01-06 15:23:11 jan Exp $
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
 * @since   Horde 3.0
 * @package Horde_IMAP
 */
class IMAP_Tree {

    /**
     * Associative array containing the mailbox tree.
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
     * Cached list of unsubscribed mailboxes.
     *
     * @var array
     */
    var $_unsubscribed = null;

    /**
     * Init mode flag.
     *
     * @var integer
     */
    var $_initmode = 0;

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
     * Insert an element in the tree that doesn't appear on the IMAP server.
     * If set, IMAP_Tree:: will call _getNonIMAPElt() to obtain the element
     * to add to the tree.
     *
     * @var boolean
     */
    var $_nonimapelt = false;

    /**
     * The name to use when storing the object in the session.
     *
     * @var string
     */
    var $_cachename;

    /**
     * The application that generated this tree.
     * THIS SHOULD BE SET IN EVERY SUBCLASS CONSTRUCTOR.
     *
     * @var string
     */
    var $_app = null;

    /**
     * The server string for the current server.
     * THIS SHOULD BE SET IN EVERY SUBCLASS CONSTRUCTOR.
     *
     * @var string
     */
    var $_server = '';

    /**
     * Should we use 'mail' mode or 'news' mode?
     * THIS SHOULD BE SET IN EVERY SUBCLASS CONSTRUCTOR.
     *
     * @var integer
     */
    var $_mode = null;

    /**
     * The list of namespaces to add to the tree.
     *
     * @var array
     */
    var $_namespaces;

    /**
     * Does the IMAP server support the children extension?
     *
     * @var boolean
     */
    var $_childrensupport = null;

    /**
     * Used to determine the list of element changes.
     *
     * @var array
     */
    var $_eltdiff = null;

    /**
     * Attempts to return a reference to a concrete IMAP_Tree instance.
     *
     * If an IMAP_Tree object is currently stored in the local session,
     * recreate that object.  Else, if $create is true, will create a new
     * instance.  Ensures that only one IMAP_Tree instance is available
     * at any time.
     *
     * This method must be invoked as:<pre>
     *   $imap_tree = &IMAP_Tree::singleton($app, $classname, [$create[, $unsub]]);</pre>
     *
     * @param string $app        The current application name.
     * @param string $classname  The class name to use when instantiating a new
     *                           object.
     * @param boolean $create    Create a new IMAP_Tree if it doesn't exist in
     *                           the session?
     * @param integer $init      The initialization mode to use.
     * @param string $cachename  The name to use when storing in the session.
     *
     * @return IMAP_Tree  The IMAP_Tree object or null.
     */
    function &singleton($app, $classname, $create = false,
                        $init = IMAPTREE_INIT_SUB, $cachename = 'imaptree')
    {
        static $instance = array();

        if (isset($instance[$app])) {
            return $instance[$app];
        }

        if (!empty($_SESSION[$app][$cachename])) {
            require_once 'Horde/SessionObjects.php';
            $cacheSess = &Horde_SessionObjects::singleton();
            $instance[$app] = &$cacheSess->query($_SESSION[$app][$cachename]);
            register_shutdown_function(array(&$instance[$app], '_store'));
        } elseif ($create) {
            $instance[$app] = &new $classname($init, $cachename);
        }

        return $instance[$app];
    }

    /**
     * Constructor.
     *
     * @param integer $init      The initialization mode to use.
     * @param string $cachename  The name to use when storing in the session.
     */
    function IMAP_Tree($init = IMAPTREE_INIT_SUB, $cachename = 'imaptree')
    {
        register_shutdown_function(array(&$this, '_store'));
        $this->_cachename = $cachename;
        $this->init($init);
    }

    /**
     * Store a serialized version of ourself in the current session.
     *
     * @access private
     */
    function _store()
    {
        /* We only need to restore the object if the tree has changed. */
        if (!empty($this->_changed)) {
            /* Don't store $_expanded and $_poll - these values are handled
             * by the subclasses.
             * Don't store $_imap_sort or $_eltdiff - this needs to be
             * regenerated for each request.
             * Don't store $_currkey, $_currparent, and $_currStack since the
             * user MUST call reset() before cycling through the tree.
             * Reset the $_changed flag. */
            $this->_currkey = $this->_currparent = $this->_eltdiff = $this->_expanded = $this->_imap_sort = $this->_poll = null;
            $this->_currStack = array();
            $this->_changed = false;

            require_once 'Horde/SessionObjects.php';
            $cacheSess = &Horde_SessionObjects::singleton();

            /* Reuse old session ID if possible. */
            if (isset($_SESSION[$this->_app][$this->_cachename])) {
                $cacheSess->overwrite($_SESSION[$this->_app][$this->_cachename], $this, false);
            } else {
                if (!isset($_SESSION[$this->_app])) {
                    $_SESSION[$this->_app] = array();
                }
                $_SESSION[$this->_app][$this->_cachename] = $cacheSess->storeOid($this, false);
            }
        }
    }

    /**
     * Returns a list of folders/mailboxes matching a certain path.
     *
     * @access private
     *
     * @param string $path  The mailbox path.
     *
     * @return array  A list of mailbox_objects whose name matched $path.
     *                The server string has been removed from the name.
     */
    function _getList($path)
    {
        $unique = array();

        if (!$this->_showunsub) {
            $this->_initSubscribed();
        }
        $newboxes = @imap_getmailboxes($this->_getStream(), $this->_server, $path);
        if (is_array($newboxes)) {
            foreach ($newboxes as $box) {
                if ($this->_showunsub ||
                    !isset($this->_subscribed[$box->name])) {
                    /* Strip off server string. */
                    $box = $this->_removeServerString($box);
                    if ($box->name && !isset($unique[$box->name])) {
                        $unique[$box->name] = $box;
                    }
                }
            }
        }

        return $unique;
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
     * @param object stdClass $ob  The object returned by imap_getmailboxes().
     *
     * @return array  See format above.
     */
    function _makeMailboxTreeElt($ob)
    {
        $elt['a'] = $ob->attributes;
        $elt['c'] = 0;
        $elt['p'] = IMAPTREE_BASE_ELT;
        $elt['v'] = $ob->name;

        /* Set subscribed values. Make sure INBOX is always subscribed
         * to (if working with mail) so there is always at least 1
         * viewable element. */
        if ($elt['v'] == 'INBOX') {
            $this->_setSubscribed($elt, true);
        } elseif (!$this->isSubscribed($elt)) {
            $this->_initSubscribed();
            $this->_setSubscribed($elt, isset($this->_subscribed[$elt['v']]));
        }

        /* Check for polled status. */
        if (!$this->isPolled($elt)) {
            $this->getPollList();
            $this->_setPolled($elt, isset($this->_poll[$elt['v']]));
        }

        /* Check for open status. */
        $this->_setOpen($elt, $this->isOpen($elt));

        /* Computed values. */
        $ns_info = $this->_getNamespace($elt['v']);
        $tmp = explode((is_null($ns_info)) ? $this->_delimiter : $ns_info['delimiter'], $elt['v']);
        $elt['c'] = count($tmp) - 1;
        $label = $elt['c'];
        if (!empty($elt['c']) &&
            !preg_match("/\{.*pop3.*\}/", $ob->fullServerPath)) {
            $elt['p'] = implode((is_null($ns_info)) ? $this->_delimiter : $ns_info['delimiter'], array_slice($tmp, 0, $elt['c']));
            /* Strip personal namespace. */
            if (!is_null($ns_info) &&
                !empty($ns_info['name']) &&
                ($ns_info['type'] == 'personal')) {
                $elt['c']--;
                if (strpos($elt['p'], $ns_info['delimiter']) === false) {
                    $elt['p'] = IMAPTREE_BASE_ELT;
                } elseif (strpos($elt['v'], $ns_info['name'] . 'INBOX' . $ns_info['delimiter']) === 0) {
                    $elt['p'] = 'INBOX';
                }
            }
        }
        $elt['l'] = String::convertCharset($tmp[$label], 'UTF7-IMAP');

        return $elt;
    }

    /**
     * Initalize the list at the top level of the hierarchy.
     *
     * @param integer $init  The initialization mode.
     */
    function init($init)
    {
        /* Reset all class variables to the defaults. */
        $this->_changed = true;
        $this->_currkey = null;
        $this->_currparent = null;
        $this->_currstack = array();
        $this->_tree = array();
        $this->_parent = array();
        $this->_showunsub = $this->_unsubview = ($init & IMAPTREE_INIT_UNSUB);
        $this->_subscribed = null;
        $this->_unsubscribed = null;

        /* Set initialization mode. */
        $this->_initmode = $init;

        /* Get the initial list of mailboxes from the subclass. */
        $boxes = $this->_init();

        /* Create a placeholder element to the base of the tree list so we can
         * keep track of whether the base level needs to be sorted. */
        $this->_tree[IMAPTREE_BASE_ELT] = array('a' => IMAPTREE_ELT_IS_DISCOVERED);

        /* Check to make sure all namespace elements are in the tree. */
        /* TODO: Remove namespaces availability check in Horde 4.0 */
        if ($this->_namespaces) {
            foreach ($this->_namespaces as $key => $val) {
                if ($val['type'] != 'personal') {
                    $name = substr($key, 0, -1 * strlen($val['delimiter']));
                    if (!isset($this->_tree[$val['name']])) {
                        $ob = &new stdClass;
                        $ob->delimiter = $val['delimiter'];
                        $ob->attributes = LATT_NOSELECT | IMAPTREE_ELT_NAMESPACE;
                        /* $ob->fullServerPath is not completely set here. */
                        $ob->fullServerPath = $ob->name = $name;
                        $elt = $this->_makeMailboxTreeElt($ob);
                        $this->_insertElt($elt);
                    }
                }
            }
        }

        /* Create the list (INBOX and any other hierarchies). */
        $this->_addLevel($boxes);

        /* End initialization mode. */
        $this->_initmode = 0;
    }

    /**
     * Subclass specific initialization tasks.
     * THIS METHOD MUST BE DEFINED IN ALL SUBCLASSES.
     *
     * @abstract
     *
     * @access private
     *
     * @return array  The initial list of elements to add to the tree.
     */
    function _init()
    {
        return array();
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

        $this->_changed = true;

        /* Merge in next level of information. */
        if ($this->hasChildren($this->_tree[$folder])) {
            if (!$this->isDiscovered($this->_tree[$folder])) {
                $info = $this->_childrenInfo($folder);
                if (!empty($info)) {
                    if ($this->_initmode) {
                        if (($this->_initmode & IMAPTREE_INIT_FETCHALL) ||
                            $this->isOpen($this->_tree[$folder])) {
                            $this->_addLevel($info);
                        }
                    } else {
                        $this->_addLevel($info);
                        $this->_setOpen($this->_tree[$folder], true);
                    }
                }
            } else {
                if (!($this->_initmode & IMAPTREE_INIT_FETCHALL)) {
                    $this->_setOpen($this->_tree[$folder], true);
                }

                /* Expand all children beneath this one. */
                if ($expandall && !empty($this->_parent[$folder])) {
                    foreach ($this->_parent[$folder] as $val) {
                        $this->expand($this->_tree[$val]['v'], true);
                    }
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

        $this->_changed = true;

        /* Set the folder attributes to not expanded. */
        $this->_setOpen($this->_tree[$folder], false);
    }

    /**
     * Sets the internal array pointer to the next element, and returns the
     * next object.
     *
     * @param integer $mask  A mask with the following elements:
     * <pre>
     * IMAPTREE_NEXT_SHOWCLOSED - Don't ignore closed elements.
     * IMAPTREE_NEXT_SHOWSUB - Only show subscribed elements.
     * </pre>
     *
     * @return mixed  Returns the next element or false if the element doesn't
     *                exist.
     */
    function next($mask = 0)
    {
        if (is_null($this->_currkey) && is_null($this->_currparent)) {
            return false;
        }

        $curr = $this->current();

        $old_showunsub = $this->_showunsub;
        if ($mask & IMAPTREE_NEXT_SHOWSUB) {
            $this->_showunsub = false;
        }

        if ($this->_activeElt($curr) &&
            (($mask & IMAPTREE_NEXT_SHOWCLOSED) || $this->isOpen($curr)) &&
            ($this->_currparent != $curr['v'])) {
            /* If the current element is open, and children exist, move into
             * it. */
            $this->_currstack[] = array('k' => $this->_currkey, 'p' => $this->_currparent);
            $this->_currkey = 0;
            $this->_currparent = $curr['v'];
            if ($this->_needSort($this->_tree[$curr['v']])) {
                $this->_sortList($this->_parent[$curr['v']], is_null($curr['v']));
                $this->_setNeedSort($this->_tree[$curr['v']], false);
                $this->_changed = true;
            }
        } else {
            /* Else, increment within the current subfolder. */
            $this->_currkey++;
        }

        /* If the pointer doesn't point to an element, try to move back to
           the previous subfolder.  If there is no previous subfolder,
           return false. */
        $curr = $this->current();
        if (!$curr &&
            ($mask & IMAPTREE_NEXT_SHOWCLOSED) &&
            !$this->isDiscovered($this->_tree[$this->_currparent]) &&
            $this->hasChildren($this->_tree[$this->_currparent])) {
            $this->_addLevel($this->_childrenInfo($this->_tree[$this->_currparent]['v']));
            $curr = $this->current();
        }

        $this->_showunsub = $old_showunsub;

        if (!$curr) {
            if (empty($this->_currstack)) {
                $this->_currkey = null;
                $this->_currparent = null;
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

        if (!$this->_activeElt($curr)) {
            /* Skip this entry if:
             * 1. We are not showing all elements
             * 2. We are not subscribed to this element
             * 3. It is not a container -OR-, if it is a container, if there
             *    are no viewable elements underneath it.
             * 4. This is an empty namespace element. */
            return $this->next($mask);
        }

        return $curr;
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
        $this->_currparent = IMAPTREE_BASE_ELT;
        $this->_currstack = array();

        if ($this->_needSort($this->_tree[$this->_currparent])) {
            $this->_sortList($this->_parent[$this->_currparent], is_null($this->_currparent));
            $this->_setNeedSort($this->_tree[$this->_currparent], false);
            $this->_changed = true;
        }

        /* When resetting in news mode, the first element may not be
         * viewable (unlike mail mode, where the first element is INBOX and
         * is always viewable).  Therefore, we need to search for the first
         * viewable item and that will be the base of the viewable tree. */
        if ($this->_mode == IMAPTREE_MODE_NEWS) {
            $curr = $this->current();
            if (!$this->_activeElt($curr)) {
                $this->next();
            }
        }

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
        if (!isset($this->_parent[$this->_currparent][$this->_currkey])) {
            return false;
        }

        return $this->_addAliases($this->_tree[$this->_parent[$this->_currparent][$this->_currkey]]);
    }

    /**
     * Determines if there are more elements in the current tree level.
     *
     * @return boolean  True if there are more elements, false if this is the
     *                  last element.
     */
    function peek()
    {
        for ($i = ($this->_currkey + 1); ; $i++) {
            if (!isset($this->_parent[$this->_currparent][$i])) {
                return false;
            }
            if ($this->_activeElt($this->_addAliases($this->_tree[$this->_parent[$this->_currparent][$i]]))) {
                return true;
            }
        }
    }

    /**
     * Adds aliases to a tree element and returns the resulting array.
     *
     * @access protected
     *
     * @param array $elt  A tree element.
     *
     * @return array  A tree element with the aliases added.
     */
    function _addAliases($elt)
    {
        $elt['label'] = $elt['l'];
        $elt['level'] = $elt['c'];
        $elt['parent'] = $elt['p'];
        $elt['value'] = $elt['v'];

        return $elt;
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

        if (isset($this->_tree[$name])) {
            return $this->_addAliases($this->_tree[$name]);
        } else {
            return false;
        }
    }

    /**
     * Insert a folder/mailbox into the tree.
     *
     * @param mixed $id  The name of the folder (or a list of folder names)
     *                   to add (must be present on the mail server).
     *
     * @return boolean  True on success, false on error.
     */
    function insert($id)
    {
        if ($this->_mode == IMAPTREE_MODE_NEWS) {
            return false;
        }

        if (is_array($id)) {
            if (!$this->_nonimapelt) {
                /* We want to add from the BASE of the tree up for efficiency
                 * sake. */
                $this->_sortList($id);
            }
        } else {
            $id = array($id);
        }

        $adds = array();

        foreach ($id as $val) {
            $ns_info = $this->_getNamespace($val);
            if (is_null($ns_info) || $this->_nonimapelt) {
                $adds[] = $val;
            } else {
                /* Break apart the name via the delimiter and go step by step
                 * through the name to make sure all subfolders exist in the
                 * tree. */
                $parts = explode($ns_info['delimiter'], $val);
                $parts[0] = $this->_convertName($parts[0]);
                for ($i = 0; $i < count($parts); $i++) {
                    $adds[] = implode($ns_info['delimiter'], array_slice($parts, 0, $i + 1));
                }
            }
        }

        foreach (array_unique($adds) as $id) {
            if (isset($this->_tree[$id])) {
                continue;
            }

            $this->_changed = true;

            if ($this->_nonimapelt) {
                $elt = $this->_getNonIMAPElt($id);
            } else {
                $ob = $this->_getList($id);
                $elt = $this->_makeMailboxTreeElt(reset($ob));
                if (!$this->isSubscribed($elt)) {
                    $tmp = @imap_lsub($this->_getStream(), $this->_server, $elt['v']);
                    if (!empty($tmp)) {
                        $this->_setSubscribed($elt, true);
                    }
                }
            }

            if ($this->_insertElt($elt)) {
                /* We know that the parent folder has children. */
                if (isset($this->_tree[$elt['p']])) {
                    $this->_setChildren($this->_tree[$elt['p']], true);
                }

                /* Make sure we are sorted correctly. */
                if (count($this->_parent[$elt['p']]) > 1) {
                    $this->_setNeedSort($this->_tree[$elt['p']], true);
                }

                /* Add to subscribed/unsubscribed list. */
                if ($this->isSubscribed($elt) &&
                    !is_null($this->_subscribed)) {
                    $this->_subscribed[$elt['v']] = 1;
                } elseif (!$this->isSubscribed($elt) &&
                          !is_null($this->_unsubscribed)) {
                    $this->_unsubscribed[$elt['v']] = 1;
                }
            }
        }

        return true;
    }

    /**
     * Insert an element into the tree.
     *
     * @access private
     *
     * @param array $elt  The element to insert. The key in the tree is the
     *                    'v' (value) element of the element.
     *
     * @return boolean  True if added to the tree.
     */
    function _insertElt($elt)
    {
        /* Don't include the parent directories that UW passes back in
           %/% lists. */
        if (strlen($elt['l']) &&
            (!isset($this->_tree[$elt['v']]) ||
             $this->isContainer($this->_tree[$elt['v']])) &&
            /* TODO: Remove dotfiles filter in next major release. */
            ($this->_dotfiles || ($elt['l'][0] != '.'))) {
            /* Set the parent array to the value in $elt['p']. */
            if (empty($this->_parent[$elt['p']])) {
                $this->_parent[$elt['p']] = array();
            }
            $this->_parent[$elt['p']][] = $elt['v'];
            $this->_tree[$elt['v']] = $elt;
            return true;
        } else {
            return false;
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

        $ns_info = $this->_getNamespace($id);

        if (($id == 'INBOX') ||
            !isset($this->_tree[$id]) ||
            ($id == $ns_info['name'])) {
            return false;
        }

        $this->_changed = true;

        $elt = &$this->_tree[$id];

        /* Do not delete from tree if there are child elements - instead,
         * convert to a container element. */
        if ($this->hasChildren($elt)) {
            $this->_setContainer($elt, true);
            return true;
        }

        $parent = $elt['p'];

        /* Delete the tree entries. */
        unset($this->_tree[$id]);
        unset($this->_subscribed[$id]);
        unset($this->_unsubscribed[$id]);

        /* Delete the entry from the parent tree. */
        $key = array_search($id, $this->_parent[$parent]);
        unset($this->_parent[$parent][$key]);

        if (empty($this->_parent[$parent])) {
            /* This folder is now completely empty (no children).  If the
             * folder is a container only, we should delete the folder from
             * the tree. */
            unset($this->_parent[$parent]);
            if (isset($this->_tree[$parent])) {
                $this->_setChildren($this->_tree[$parent], null);
                if ($this->isContainer($this->_tree[$parent]) &&
                    !$this->isNamespace($this->_tree[$parent])) {
                    $this->delete($parent);
                } elseif (!$this->hasChildren($this->_tree[$parent])) {
                    $this->_removeExpandedList($parent);
                    $this->_setChildren($this->_tree[$parent], false);
                    $this->_setOpen($this->_tree[$parent], false);
                }
            }
        } else {
            /* Rebuild the parent tree. */
            $this->_parent[$parent] = array_values($this->_parent[$parent]);
        }

        /* Remove the mailbox from the expanded folders list. */
        $this->_removeExpandedList($id);

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
                if (!is_null($this->_subscribed)) {
                    $this->_subscribed[$val] = 1;
                }
                unset($this->_unsubscribed[$val]);
            } else {
                $this->insert($val);
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

            /* INBOX can never be unsubscribed to (if in mail mode). */
            if (isset($this->_tree[$val]) && ($val != 'INBOX')) {
                $this->_changed = true;
                $this->_unsubview = true;

                $elt = &$this->_tree[$val];

                /* Do not delete from tree if there are child elements -
                 * instead, convert to a container element. */
                if (!$this->_showunsub && $this->hasChildren($elt)) {
                    $this->_setContainer($elt, true);
                }

                /* Set as unsubscribed, add to unsubscribed list, and remove
                 * from subscribed list. */
                $this->_setSubscribed($elt, false);
                if (!is_null($this->_unsubscribed)) {
                    $this->_unsubscribed[$val] = 1;
                }
                unset($this->_subscribed[$val]);
            }
        }
    }

    /**
     * Add another level of hierarchy to the tree.
     *
     * @access private
     *
     * @param array $list  A list of stdClass objects in the format returned
     *                     from imap_getmailboxes().
     */
    function _addLevel($list)
    {
        $expandall = ($this->_initmode & IMAPTREE_INIT_FETCHALL);

        foreach ($list as $val) {
            $elt = $this->_makeMailboxTreeElt($val);

            $parent = $elt['p'];
            $this->_insertElt($elt);
            $this->_changed = true;

            if ($expandall || $this->isOpen($elt)) {
                $this->expand($elt['v']);
            }
        }

        /* Sort the list. */
        if (!empty($list) &&
            !empty($this->_parent[$parent])) {
            $this->_setDiscovered($this->_tree[$parent], true);
            if (count($this->_parent[$parent]) > 1) {
                $this->_setNeedSort($this->_tree[$parent], true);
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
        static $hasChildrenCache = array();

        $is_ns = $this->isNamespace($elt);

        /* Don't do the following if we are dealing with a namespace
         * container. */
        if (!$is_ns) {
            /* Not all IMAP servers support the HASCHILDREN flag (like UW!) so
             * we need to skip this check if the IMAP server doesn't set
             * either HASCHILDREN or HASNOCHILDREN. */
            if (!empty($this->_childrensupport) ||
                (is_null($this->_childrensupport) &&
                 ($elt['a'] & LATT_HASCHILDREN) ||
                 ($elt['a'] & LATT_HASNOCHILDREN))) {
                $ret = ($elt['a'] & LATT_HASCHILDREN);

                /* CHECK: If we are viewing all folders, and there is a folder
                 * listed as expanded but it does not contain any children,
                 * then we should remove it from the expanded list since it
                 * doesn't exist anymore. */
                if ($this->_showunsub && !$ret) {
                    $this->_initExpandedList();
                    if (!empty($this->_expanded[$elt['v']])) {
                        $this->_removeExpandedList($elt['v']);
                        $this->_setOpen($this->_tree[$elt['v']], false);
                    }
                }

                if (!$ret) {
                    return false;
                }

                /* If we are viewing all elements (subscribed and unsubscribed)
                 * and we reach this point we know that there must be viewable
                 * children so return true. */
                if ($this->_showunsub) {
                    return true;
                }
            }
        }

        /* Cache results from below since, most likely if we get this far,
         * this code will be accessed several times in the current request. */
        if (isset($hasChildrenCache[$elt['v']])) {
            return $hasChildrenCache[$elt['v']];
        }

        /* If we reach this point, then we are either in subscribe-only mode
         * or we are dealing with a namespace container. Check for the
         * existence of any subscribed mailboxes below the current node. */
        $this->_initSubscribed();
        $folder_list = $this->_subscribed;
        if ($this->_showunsub) {
            $this->_initUnsubscribed();
            $folder_list += $this->_unsubscribed;
        }
        $ns_info = $this->_getNamespace($elt['v']);
        if (!is_null($ns_info)) {
            $search_str = $elt['v'] . $ns_info['delimiter'];
            if (($elt['v'] == 'INBOX') &&
                ($ns_info['name'] == ('INBOX' . $ns_info['delimiter']))) {
                $search_str .= $ns_info['name'];
            }
            foreach (array_keys($folder_list) as $val) {
                if (strpos($val, $search_str) === 0) {
                    $this->_hasChildrenCache[$elt['v']] = true;
                    return true;
                }
            }
        }

        /* Do one final check if this is a namespace container - if we get
         * this far, and are viewing all folders, then we know we have no
         * children so make sure the element is not set to expanded/open. */
        if ($is_ns && $this->_showunsub) {
            $this->_initExpandedList();
            if (!empty($this->_expanded[$elt['v']])) {
                $this->_removeExpandedList($elt['v']);
                $this->_setOpen($this->_tree[$elt['v']], false);
            }
        }

        $hasChildrenCache[$elt['v']] = false;
        return false;
    }

    /**
     * Set the children attribute for an element.
     *
     * @access private
     *
     * @param array &$elt  A tree element.
     * @param mixed $bool  The setting. If null, clears the flag.
     */
    function _setChildren(&$elt, $bool)
    {
        if (is_null($bool)) {
            $this->_setAttribute($elt, LATT_HASCHILDREN, false);
            $this->_setAttribute($elt, LATT_HASNOCHILDREN, false);
        } else {
            $this->_setAttribute($elt, LATT_HASCHILDREN, $bool);
            $this->_setAttribute($elt, LATT_HASNOCHILDREN, !$bool);
        }
    }

    /**
     * Has the tree element been discovered?
     *
     * @param array $elt  A tree element.
     *
     * @return integer  Non-zero if the element has been discovered.
     */
    function isDiscovered($elt)
    {
        return $elt['a'] & IMAPTREE_ELT_IS_DISCOVERED;
    }

    /**
     * Set the discovered attribute for an element.
     *
     * @access private
     *
     * @param array &$elt    A tree element.
     * @param boolean $bool  The setting.
     */
    function _setDiscovered(&$elt, $bool)
    {
        $this->_setAttribute($elt, IMAPTREE_ELT_IS_DISCOVERED, $bool);
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
        if (!$this->_initmode) {
            return (($elt['a'] & IMAPTREE_ELT_IS_OPEN) && $this->hasChildren($elt));
        } else {
            switch ($this->_getInitExpandedMode()) {
            case IMAPTREE_OPEN_NONE:
                return false;
                break;

            case IMAPTREE_OPEN_ALL:
                return true;
                break;

            case IMAPTREE_OPEN_USER:
                $this->_initExpandedList();
                return !empty($this->_expanded[$elt['v']]);
                break;
            }
        }
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
        $this->_setAttribute($elt, IMAPTREE_ELT_IS_OPEN, $bool);
        if (!$this->_initmode) {
            $this->_initExpandedList();
            if ($bool) {
                $this->_addExpandedList($elt['v']);
            } else {
                $this->_removeExpandedList($elt['v']);
            }
        }
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
        return (($elt['a'] & LATT_NOSELECT) ||
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
        $this->_setAttribute($elt, LATT_NOSELECT, $bool);
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
        return $elt['a'] & IMAPTREE_ELT_IS_SUBSCRIBED;
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
        $this->_setAttribute($elt, IMAPTREE_ELT_IS_SUBSCRIBED, $bool);
    }

    /**
     * Is the element a namespace container?
     *
     * @param array $elt  A tree element.
     *
     * @return integer  True if the element is a namespace container?
     */
    function isNamespace($elt)
    {
        return $elt['a'] & IMAPTREE_ELT_NAMESPACE;
    }

    /**
     * Remove the server string from the 'name' parameter.
     *
     * @access private
     *
     * @param object stdClass $ob  An object returned from
     *                             imap_getmailboxes().
     *
     * @return stdClass  The object returned with the server string stripped
     *                   from the 'name' parameter.
     */
    function _removeServerString($ob)
    {
        $ob->fullServerPath = $ob->name;
        $ob->name = $this->_convertName(substr($ob->name, strpos($ob->name, '}') + 1));
        return $ob;
    }

    /**
     * Initialize the expanded folder list.
     * THIS METHOD SHOULD BE DEFINED IN ALL SUBCLASSES.
     *
     * @abstract
     *
     * @access private
     */
    function _initExpandedList()
    {
        $this->_expanded = array();
    }

    /**
     * Add an element to the expanded list.
     * THIS METHOD SHOULD BE DEFINED IN ALL SUBCLASSES.
     *
     * @abstract
     *
     * @access private
     *
     * @param string $id  The element name to remove.
     */
    function _addExpandedList($id)
    {
    }

    /**
     * Remove an element from the expanded list.
     * THIS METHOD SHOULD BE DEFINED IN ALL SUBCLASSES.
     *
     * @abstract
     *
     * @access private
     *
     * @param string $id  The element name to remove.
     */
    function _removeExpandedList($id)
    {
    }

    /**
     * Initialize/get the list of elements to poll.
     * THIS METHOD SHOULD BE DEFINED IN ALL SUBCLASSES.
     *
     * @abstract
     *
     * @return array  The list of elements to poll (name in key field).
     */
    function getPollList()
    {
        $this->_poll = array();
        return $this->_poll;
    }

    /**
     * Add element to the poll list.
     * THIS METHOD SHOULD BE DEFINED IN ALL SUBCLASSES.
     *
     * @abstract
     *
     * @param mixed $id  The element name or a list of element names to add.
     */
    function addPollList($id)
    {
    }

    /**
     * Remove element from the poll list.
     * THIS METHOD SHOULD BE DEFINED IN ALL SUBCLASSES.
     *
     * @abstract
     *
     * @param string $id  The folder/mailbox or a list of folders/mailboxes
     *                    to remove.
     */
    function removePollList($id)
    {
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
        return $elt['a'] & IMAPTREE_ELT_IS_POLLED;
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
        $this->_setAttribute($elt, IMAPTREE_ELT_IS_POLLED, $bool);
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
        $this->_setAttribute($elt, IMAPTREE_ELT_NEED_SORT, $bool);
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
        return $elt['a'] & IMAPTREE_ELT_NEED_SORT;
    }

    /**
     * Initialize the list of subscribed mailboxes.
     *
     * @access private
     */
    function _initSubscribed()
    {
        if (is_null($this->_subscribed)) {
            $this->_changed = true;
            $this->_subscribed = array();
            $sublist = array();

            /* INBOX is always subscribed to if we are in mail mode. */
            if ($this->_mode == IMAPTREE_MODE_MAIL) {
                $this->_subscribed['INBOX'] = 1;
            }

            /* TODO: Remove namespaces availability check in Horde 4.0 */
            if ($this->_namespaces) {
                foreach ($this->_namespaces as $val) {
                    $tmp = @imap_lsub($this->_getStream(), $this->_server, $val['name'] . '*');
                    if (!empty($tmp)) {
                        $sublist = array_merge($sublist, $tmp);
                    }
                }
            } else {
                $sublist = @imap_lsub($this->_getStream(), $this->_server, $this->_prefix . '*');
            }

            if (!empty($sublist)) {
                foreach ($sublist as $val) {
                    $this->_subscribed[substr($val, strpos($val, '}') + 1)] = 1;
                }
            }
        }
    }

    /**
     * Initialize the list of unsubscribed mailboxes.
     *
     * @access private
     */
    function _initUnsubscribed()
    {
        if (is_null($this->_unsubscribed)) {
            $this->_changed = true;
            $this->_initSubscribed();
            $this->_unsubscribed = array();
            $all_list = array();

            /* Get list of all mailboxes. */
            /* TODO: Remove namespaces availability check in Horde 4.0 */
            if ($this->_namespaces) {
                foreach ($this->_namespaces as $val) {
                    $tmp = @imap_list($this->_getStream(), $this->_server, $val['name'] . '*');
                    if (!empty($tmp)) {
                        $all_list = array_merge($all_list, $tmp);
                    }
                }
            } else {
                $all_list = @imap_list($this->_getStream(), $this->_server, $this->_prefix . '*');
            }

            if (!empty($all_list)) {
                /* Find all mailboxes that aren't in the subscribed list. */
                foreach ($all_list as $val) {
                    $val = substr($val, strpos($val, '}') + 1);
                    if (!isset($this->_subscribed[$val])) {
                        $this->_unsubscribed[$val] = 1;
                    }
                }
            }
        }
    }

    /**
     * Should we expand all elements?
     */
    function expandAll()
    {
        foreach ($this->_parent[null] as $val) {
            $this->expand($val, true);
        }
    }

    /**
     * Should we collapse all elements?
     */
    function collapseAll()
    {
        foreach ($this->_tree as $key => $val) {
            if ($key != IMAPTREE_BASE_ELT) {
                $this->collapse($val['v']);
            }
        }

        /* Clear all entries from the expanded list. */
        $this->_initExpandedList();
        foreach ($this->_expanded as $key => $val) {
            $this->_removeExpandedList($key);
        }

    }

    /**
     * Return the list of mailboxes in the next level.
     *
     * @access private
     *
     * @param string $id  The current mailbox.
     *
     * @return array  A list of mailbox objects or the empty list.
     *                See _getList() for format.
     */
    function _childrenInfo($id)
    {
        $info = array();
        $ns_info = $this->_getNamespace($id);

        if (is_null($ns_info)) {
            return $info;
        }

        if (($id == 'INBOX') &&
            ($ns_info['name'] == ('INBOX' . $ns_info['delimiter']))) {
            $search = $id . $ns_info['delimiter'] . $ns_info['name'];
        } else {
            $search = $id . $ns_info['delimiter'];
        }

        $info = $this->_getList($search . '%');

        if (isset($this->_tree[$id])) {
            $this->_setChildren($this->_tree[$id], !empty($info));
        }

        return $info;
    }

    /**
     * Switch subscribed/unsubscribed viewing.
     *
     * @param boolean $unsub  Show unsubscribed elements?
     */
    function showUnsubscribed($unsub)
    {
        if ($unsub === $this->_showunsub) {
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
        $this->_initUnsubscribed();
        if (empty($this->_unsubscribed)) {
            return;
        }

        $this->_initmode = IMAPTREE_INIT_UNSUB;
        $this->insert(array_keys($this->_unsubscribed));
        $this->_initmode = 0;
    }

    /**
     * Returns a reference to a currently open IMAP stream.
     * THIS METHOD MUST BE DEFINED IN ALL SUBCLASSES.
     *
     * @abstract
     * @todo Deprecate in Horde 4.0 - just have the subclass define a $_stream
     *       variable.
     *
     * @access private
     *
     * @return resource  An IMAP resource stream.
     */
    function &_getStream()
    {
        return false;
    }

    /**
     * Returns the currently selected initialization expanded mode.
     * THIS METHOD SHOULD BE DEFINED IN ALL SUBCLASSES.
     *
     * @abstract
     *
     * @access private
     *
     * @return integer  The current initialization expanded mode.
     */
    function _getInitExpandedMode()
    {
        return IMAPTREE_OPEN_NONE;
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

        require_once 'Horde/IMAP/Cache.php';
        $imap_cache = &IMAP_Cache::singleton();
        $sts = $imap_cache->getStatus($this->_getStream(), $this->_server . $name);
        if (!empty($sts)) {
            $status['messages'] = $sts->messages;
            $status['unseen'] = isset($sts->unseen) ? $sts->unseen : 0;
            $status['newmsg'] = isset($sts->recent) ? $sts->recent : 0;
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
            foreach ($mbox as $val) {
                $basesort[$val] = ($val == 'INBOX') ? 'INBOX' : $this->_tree[$val]['l'];
            }
            $this->_imap_sort->sortMailboxes($basesort, ($this->_mode == IMAPTREE_MODE_MAIL), true, true);
            $mbox = array_keys($basesort);
        } else {
            $this->_imap_sort->sortMailboxes($mbox, ($this->_mode == IMAPTREE_MODE_MAIL));
        }
    }

    /**
     * Return a Non-IMAP mailbox element given an element identifier.
     *
     * @abstract
     *
     * @access private
     *
     * @param string $id  The element identifier.
     *
     * @return array  A mailbox element.
     */
    function _getNonIMAPElt($id)
    {
        return array();
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
        if ($this->_showunsub &&
            $this->isNamespace($elt)) {
            return ($this->hasChildren($elt));
        } else {
            return ($this->_showunsub ||
                    ($this->isSubscribed($elt) && !$this->isContainer($elt)) ||
                    $this->hasChildren($elt));
        }
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
        return (($this->_mode == IMAPTREE_MODE_MAIL) && (strcasecmp($name, 'INBOX') == 0)) ? 'INBOX' : $name;
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
        static $namespaceCache = array();

        if (isset($namespaceCache[$mailbox])) {
            return $namespaceCache[$mailbox];
        }

        /* TODO: Remove namespaces availability check in Horde 4.0 */
        if (!empty($this->_namespaces)) {
            foreach ($this->_namespaces as $key => $val) {
                if ((($mailbox . $val['delimiter']) == $key) ||
                    (!empty($key) && (strpos($mailbox, $key) === 0))) {
                    $namespaceCache[$mailbox] = $val;
                    return $val;
                }
            }

            if (isset($this->_namespaces[''])) {
                $namespaceCache[$mailbox] = $this->_namespaces[''];
                return $this->_namespaces[''];
            }

            $namespaceCache[$mailbox] = null;
            return null;
        } else {
            if (substr($this->_prefix, -1) == $this->_delimiter) {
                $name = substr($this->_prefix, 0, strlen($this->_prefix) - 1);
            } else {
                $name = $this->_prefix;
            }
            $namespaceCache[$mailbox] = array('delimiter' => $this->_delimiter, 'name' => $name, 'type' => 'personal');
            return $namespaceCache[$mailbox];
        }
    }

    /**
     * Does the IMAP server support the 'CHILDREN' IMAP extension?
     *
     * @param boolean $support  True if the IMAP server supports the CHILDREN
     *                          extension, false if it doesn't.
     */
    function IMAPchildrenSupport($support)
    {
        $this->_childrensupport = (bool) $support;
    }

    /**
     * Set the start point for determining element differences via eltDiff().
     *
     * @since Horde 3.1
     */
    function eltDiffStart()
    {
        $this->_eltdiff = $this->_tree;
    }

    /**
     * Return the list of elements that have changed since nodeDiffStart()
     * was last called.
     *
     * @since Horde 3.1
     *
     * @return array  An array with the following keys:
     * <pre>
     * 'a' => A list of elements that have been added.
     * 'c' => A list of elements that have been changed.
     * 'd' => A list of elements that have been deleted.
     * </pre>
     *                Returns false if no changes have occurred.
     */
    function eltDiff()
    {
        if (!$this->_changed || !$this->_eltdiff) {
            return false;
        }

        $added = $changed = $deleted = array();

        /* Determine the deleted items. */
        $deleted = array_values(array_diff(array_keys($this->_eltdiff), array_keys($this->_tree)));

        foreach ($this->_tree as $key => $val) {
            if (!isset($this->_eltdiff[$key])) {
                $added[] = $key;
            } elseif ($val != $this->_eltdiff[$key]) {
                $changed[] = $key;
            }
        }

        if (empty($added) && empty($changed) && empty($deleted)) {
            return false;
        } else {
            return array('a' => $added, 'c' => $changed, 'd' => $deleted);
        }
    }

    /**** Deprecated variables/functions. These remain for BC only. ****/

    /**
     * The prefix without a trailing delimiter.
     *
     * @deprecated since Horde 3.1
     * @var string
     */
    var $_prefixnodelim = '';

    /**
     * The server string used for the delimiter.
     * THIS SHOULD BE SET IN EVERY SUBCLASS CONSTRUCTOR.
     *
     * @deprecated since Horde 3.1
     * @var string
     */
    var $_delimiter = '/';

    /**
     * Where we start listing folders.
     * THIS SHOULD BE SET IN EVERY SUBCLASS CONSTRUCTOR.
     *
     * @deprecated since Horde 3.1
     * @var string
     */
    var $_prefix = '';

    /**
     * The location of the first level of folders below the INBOX.
     * THIS SHOULD BE SET IN EVERY SUBCLASS CONSTRUCTOR.
     *
     * @deprecated since Horde 3.1
     * @var string
     */
    var $_namespace = '';

    /**
     * Should dotfiles be shown?
     * THIS SHOULD BE SET IN EVERY SUBCLASS CONSTRUCTOR.
     *
     * @var boolean
     */
    var $_dotfiles = false;

    /**
     * The existence of this function in IMAP_Tree indicates that extended
     * namespace support is available.
     *
     * @return boolean  Returns true.
     */
    function extendedNamespaceSupport()
    {
        return true;
    }

    /**
     * Return the prefix.
     *
     * @deprecated since Horde 3.1
     * @return string  The prefix where folders begin to be listed.
     */
    function getPrefix()
    {
        return $this->_prefix;
    }

    /**
     * Get information about a specific mailbox.
     *
     * @access private
     * @deprecated since Horde 3.1
     *
     * @param string $path  The mailbox to query.
     *
     * @return stdClass  See imap_getmailboxes().  The server string has
     *                   already been removed from the 'name' parameter.
     */
    function _getMailbox($path)
    {
        $box = $this->_getList($path);
        if (empty($box)) {
            return false;
        } else {
            return reset($box);
        }
    }

    /**
     * Make sure there is no trailing delimiter on the element name.
     *
     * @param string $name  The element name.
     * @deprecated since Horde 3.1
     *
     * @return string  The element name with any trailing delimiter stripped
     *                 off.
     */
    function noTrailingDelimiter($name)
    {
        $ns_info = $this->_getNamespace($name);
        if (substr($name, -1) == $ns_info['delimiter']) {
            $name = substr($name, 0, strlen($name) - 1);
        }

        return $name;
    }


}
