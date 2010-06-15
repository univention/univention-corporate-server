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
 */
if (!defined('LATT_HASCHILDREN')) {
    @define('LATT_REFERRAL', 16);
    @define('LATT_HASCHILDREN', 32);
    @define('LATT_HASNOCHILDREN', 64);
}

/* Start at 128 for our local bitmasks to allow for the c-client LATT_*
   constants. */
/** @const IMAPTREE_ELT_HAS_CHILDREN */  define('IMAPTREE_ELT_HAS_CHILDREN', 128);
/** @const IMAPTREE_ELT_IS_OPEN */       define('IMAPTREE_ELT_IS_OPEN', 256);
/** @const IMAPTREE_ELT_IS_SUBSCRIBED */ define('IMAPTREE_ELT_IS_SUBSCRIBED', 512);
/** @const IMAPTREE_ELT_IS_DISCOVERED */ define('IMAPTREE_ELT_IS_DISCOVERED', 1024);
/** @const IMAPTREE_ELT_IS_POLLED */     define('IMAPTREE_ELT_IS_POLLED', 2048);

/* The isOpen() expanded mode constants. */
/** @const IMAPTREE_OPEN_NONE */ define('IMAPTREE_OPEN_NONE', 0);
/** @const IMAPTREE_OPEN_ALL */  define('IMAPTREE_OPEN_ALL', 1);
/** @const IMAPTREE_OPEN_USER */ define('IMAPTREE_OPEN_USER', 2);

/* Which mode of IMAP access are we using. */
/** @const IMAPTREE_MODE_MAIL */ define('IMAPTREE_MODE_MAIL', 0);
/** @const IMAPTREE_MODE_NEWS */ define('IMAPTREE_MODE_NEWS', 1);

/**
 * The IMAP_Tree class provides a tree view of the folders supported with
 * the PHP imap extension (IMAP/POP3/NNTP repositories).  It provides access
 * functions to iterate through this tree and query information about
 * individual mailboxes/folders.
 *
 * $Horde: framework/IMAP/IMAP/Tree.php,v 1.18 2004/04/28 17:41:23 chuck Exp $
 *
 * Copyright 2000-2004 Chuck Hagenbuch <chuck@horde.org>
 * Copyright 2000-2004 Jon Parise <jon@horde.org>
 * Copyright 2000-2004 Anil Madhavapeddy <avsm@horde.org>
 * Copyright 2003-2004 Michael Slusarz <slusarz@bigworm.colorado.edu>
 *
 * See the enclosed file COPYING for license information (GPL). If you
 * did not receive this file, see http://www.fsf.org/copyleft/gpl.html.
 *
 * @author  Chuck Hagenbuch <chuck@horde.org>
 * @author  Jon Parise <jon@horde.org>
 * @author  Anil Madhavapeddy <avsm@horde.org>
 * @author  Michael Slusarz <slusarz@bigworm.colorado.edu>
 * @version $Revision: 1.1.2.1 $
 * @since   Horde 3.0
 * @package Horde_IMAP
 */
class IMAP_Tree {

    /**
     * Associative array containing the mailbox tree.
     *
     * @var array $_tree
     */
    var $_tree;

    /**
     * Location of current element in the tree.
     *
     * @var string $_currparent
     * @var integer $_currkey
     * @var array $_currstack
     */
    var $_currparent = null;
    var $_currkey = null;
    var $_currstack = array();

    /**
     * Key of first (top?) element in the tree (for traversal).
     *
     * @var string $_first
     */
    var $_first = '';

    /**
     * Show unsubscribed mailboxes?
     *
     * @var boolean $_showunsub
     */
    var $_showunsub = false;

    /**
     * The prefix without a trailing delimiter.
     *
     * @var string $_prefixnodelim
     */
    var $_prefixnodelim = '';

    /**
     * Parent list.
     *
     * @var array $_sortcache
     */
    var $_parent = array();

    /**
     * The cached list of mailboxes to poll.
     *
     * @var array $_poll
     */
    var $_poll = null;

    /**
     * The cached list of expanded folders.
     *
     * @var array $_expanded
     */
    var $_expanded = null;

    /**
     * Cached list of subscribed mailboxes.
     *
     * @var array $_subscribed
     */
    var $_subscribed = null;

    /**
     * Cached list of unsubscribed mailboxes.
     *
     * @var array $_unsubscribed
     */
    var $_unsubscribed = null;

    /**
     * Init mode flag.  If true we are in initialization mode.
     *
     * @var boolean $_initmode
     */
    var $_initmode = false;

    /**
     * Tree changed flag.  Set when something in the tree has been altered.
     *
     * @var boolean $_changed
     */
    var $_changed = false;

    /**
     * Does this server support the LATT_HASCHILDREN/LATT_HASNOCHILDREN
     * constants?
     *
     * @var boolean $_children
     */
    var $_children = null;

    /**
     * Have we shown unsubscribed folders previously?
     *
     * @var boolean $_unsubview
     */
    var $_unsubview = false;

    /**
     * Cached results of hasChildren().
     *
     * @var array $_hasChildrenCache
     */
    var $_hasChildrenCache = array();

    /**
     * The IMAP_Sort object.
     *
     * @var object IMAP_Sort $_imap_sort
     */
    var $_imap_sort = null;

    /**
     * The application that generated this tree.
     * THIS SHOULD BE SET IN EVERY SUBCLASS CONSTRUCTOR.
     *
     * @var string $_app
     */
    var $_app = null;

    /**
     * The server string for the current server.
     * THIS SHOULD BE SET IN EVERY SUBCLASS CONSTRUCTOR.
     *
     * @var string $_server
     */
    var $_server = '';

    /**
     * The server string used for the delimiter.
     * THIS SHOULD BE SET IN EVERY SUBCLASS CONSTRUCTOR.
     *
     * @var string $_delimiter
     */
    var $_delimiter = '/';

    /**
     * Where we start listing folders.
     * THIS SHOULD BE SET IN EVERY SUBCLASS CONSTRUCTOR.
     *
     * @var string $_prefix
     */
    var $_prefix = '';

    /**
     * Should dotfiles be shown?
     * THIS SHOULD BE SET IN EVERY SUBCLASS CONSTRUCTOR.
     *
     * @var boolean $_dotfiles
     */
    var $_dotfiles = false;

    /**
     * Should we use 'mail' mode or 'news' mode?
     * THIS SHOULD BE SET IN EVERY SUBCLASS CONSTRUCTOR.
     *
     * @var integer $_mode
     */
    var $_mode = null;

    /**
     * Attempts to return a reference to a concrete IMAP_Tree instance.
     * If an IMAP_Tree object is currently stored in the local session,
     * recreate that object.  Else, if $create is true, will create a new
     * instance.  Ensures that only one IMAP_Tree instance is available
     * at any time.
     *
     * This method must be invoked as:
     *   $imap_tree = &IMAP_Tree::singleton([$create[, $unsub]]);
     *
     * @access public
     *
     * @param string $app               The current application name.
     * @param string $classname         The class name to use when
     *                                  instantiating a new object.
     * @param optional boolean $create  Create a new IMAP_Tree if it doesn't
     *                                  exist in the session?
     * @param optional boolean $unsub   If creating a new object, init
     *                                  unsubscribed folders?
     *
     * @return object IMAP_Tree  The IMAP_Tree object or null.
     */
    function &singleton($app, $classname, $create = false, $unsub = false)
    {
        static $instance = array();

        if (isset($instance[$app])) {
            return $instance[$app];
        }

        if (!empty($_SESSION[$app]['imaptree'])) {
            require_once 'Horde/SessionObjects.php';
            $cacheSess = &Horde_SessionObjects::singleton();
            $instance[$app] = $cacheSess->query($_SESSION[$app]['imaptree']);
            register_shutdown_function(array(&$instance[$app], '_store'));
        } elseif ($create) {
            $instance[$app] = new $classname($unsub);
        }

        return $instance[$app];
    }

    /**
     * Constructor.
     *
     * @access public
     *
     * @param optional boolean $unsub  When initializing, show unsubscribed
     *                                 folders?
     */
    function IMAP_Tree($unsub = false)
    {
        register_shutdown_function(array(&$this, '_store'));
        $this->init($unsub);
    }

    /**
     * Store a serialized version of ourself in the current IMP session.
     *
     * @access private
     */
    function _store()
    {
        /* We only need to restore the object if the tree has changed. */
        if (!empty($this->_changed)) {
            /* Don't store $_expanded and $_poll - these values are handled
             * by the subclasses.
             * Don't store $_subscribed and $_unsubscribed - this information
             * is stored in the attributes ('a') parameter.
             * Don't store $_hasChildrenCache and $_imap_sort - these need to
             * be regenerated for each request.
             * Reset the $_changed flag. */
            $this->_expanded = $this->_imap_sort = $this->_poll = $this->_subscribed = $this->_unsubscribed = null;
            $this->_hasChildrenCache = array();
            $this->_changed = false;

            require_once 'Horde/SessionObjects.php';
            $cacheSess = &Horde_SessionObjects::singleton();

            /* Reuse old session ID if possible. */
            if (isset($_SESSION[$this->_app]['imaptree'])) {
                $cacheSess->overwrite($_SESSION[$this->_app]['imaptree'], $this, false);
            } else {
                if (!isset($_SESSION[$this->_app])) {
                    $_SESSION[$this->_app] = array();
                }
                $_SESSION[$this->_app]['imaptree'] = $cacheSess->storeOid($this, false);
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
        $newboxes = call_user_func(($this->_showunsub) ? 'imap_getmailboxes' : 'imap_getsubscribed', $this->_getStream(), $this->_server, $path);

        $unique = array();

        if (is_array($newboxes)) {
            $found = array();
            foreach ($newboxes as $box) {
                if (!empty($box->name) && empty($found[$box->name])) {
                    $found[$box->name] = true;

                    /* Strip off server string. */
                    $box = $this->_removeServerString($box);
                    $unique[$box->name] = $box;
                }
            }
        }

        return $unique;
    }

    /**
     * Get information about a specific mailbox.
     *
     * @access private
     *
     * @param string $path  The mailbox to query.
     *
     * @return stdClass  See imap_getmailboxes().  The server string has
     *                   already been removed from the 'name' parameter.
     */
    function _getMailbox($path)
    {
        $box = (!$this->_showunsub && (($this->_mode == IMAPTREE_MODE_NEWS) || $path != 'INBOX')) ? @imap_getsubscribed($this->_getStream(), $this->_server, $path) : @imap_getmailboxes($this->_getStream(), $this->_server, $path);

        if (empty($box)) {
            return false;
        } else {
            $box = $box[0];

            /* Do a version check to see if this version of c-client supports
             * the LATT_HASCHILDREN/HASNOCHILDREN constants. */
            if (is_null($this->_children)) {
                $this->_children = (bool) (($box->attributes & LATT_HASCHILDREN) || ($box->attributes & LATT_HASNOCHILDREN));
            }

            return $this->_removeServerString($box);
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
     * @param object stdClass $ob  The object returned by imap_getmailboxes().
     *
     * @return array  See format above.
     */
    function _makeMailboxTreeElt($ob)
    {
        $elt = array();
        $elt['a'] = $ob->attributes;
        $elt['p'] = null;
        $elt['v'] = $ob->name;

        /* Set subscribed values. Make sure the INBOX is always subscribed
         * to (if working with mail) so there is always at least 1 viewable
         * element. */
        if (($this->_mode == IMAPTREE_MODE_MAIL) && ($ob->name == 'INBOX')) {
            $this->_initSubscribed();
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
        $tmp = explode($this->_delimiter, $elt['v']);
        $elt['c'] = count($tmp) - 1;
        if (!empty($elt['c'])) {
            $elt['p'] = implode($this->_delimiter, array_slice($tmp, 0, $elt['c']));
            if (($this->_mode == IMAPTREE_MODE_MAIL) &&
                $elt['p'] == $this->_prefixnodelim) {
                $elt['p'] = 'INBOX';
            }
        }
        $elt['l'] = $tmp[$elt['c']];
        $elt['l'] = String::convertCharset($elt['l'], 'UTF7-IMAP');

        return $elt;
    }

    /**
     * Initalize the list at the top level of the hierarchy.
     *
     * @access public
     *
     * @param boolean $unsub  Show unsubscribed mailboxes?
     */
    function init($unsub)
    {
        /* Reset all class variables to the defaults. */
        $this->_changed = true;
        $this->_currkey = null;
        $this->_currparent = null;
        $this->_currstack = array();
        $this->_first = null;
        $this->_tree = array();
        $this->_parent = array();
        $this->_showunsub = $this->_unsubview = $unsub;

        /* Get the prefix without trailing delimiter, since we use it so
         * often. */
        $this->_prefixnodelim = $this->noTrailingDelimiter($this->_prefix);

        /* Set initialization mode. */
        $this->_initmode = true;

        /* Get the initial list of mailboxes from the subclass. */
        $boxes = $this->_init();

        /* Create the list (INBOX and any other hierarchies). */
        $this->_addLevel($boxes);

        /* End initialization mode. */
        $this->_initmode = false;
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
     * Make sure there is no trailing delimiter on the element name.
     *
     * @access public
     *
     * @param string $name  The element name.
     *
     * @return string  The element name with any trailing delimiter stripped
     *                 off.
     */
    function noTrailingDelimiter($name)
    {
        if (substr($name, -1) == $this->_delimiter) {
            $name = substr($name, 0, strlen($name) - 1);
        }

        return $name;
    }

    /**
     * Expand a mail folder.
     *
     * @access public
     *
     * @param string $folder               The folder name to expand.
     * @param optional boolean $expandall  Expand all folders under this one?
     */
    function expand($folder, $expandall = false)
    {
        if (!isset($this->_tree[$folder])) {
            return;
        }

        $this->_changed = true;

        /* Merge in next level of information. */
        if (!$this->isDiscovered($this->_tree[$folder])) {
            $info = $this->_childrenInfo($folder, true, true);
            if ($info['haschildren']) {
                if ($this->_initmode) {
                    if ($this->isOpen($this->_tree[$folder])) {
                        $this->_addLevel($info['list']);
                    }
                } else {
                    $this->_addLevel($info['list']);
                    $this->_setOpen($this->_tree[$folder], true);
                }
            }
        }

        $this->_setDiscovered($this->_tree[$folder], true);

        if ($this->hasChildren($this->_tree[$folder])) {
            $this->_setOpen($this->_tree[$folder], true);

            /* Expand all children beneath this one. */
            if ($expandall && !empty($this->_parent[$folder])) {
                foreach ($this->_parent[$folder] as $val) {
                    $this->expand($val, true);
                }
            }
        }
    }

    /**
     * Collapse a mail folder.
     *
     * @access public
     *
     * @param string $folder  The folder name to collapse.
     */
    function collapse($folder)
    {
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
     * @access public
     *
     * @return mixed  Returns the next element or false if the element doesn't
     *                exist.
     */
    function next()
    {
        if (is_null($this->_currkey) && is_null($this->_currparent)) {
            return false;
        }

        $this->_changed = true;

        $curr = $this->current();

        if (($this->_showunsub ||
             $this->isSubscribed($curr) ||
             ($this->isContainer($curr) &&
              $this->hasChildren($curr, true))) &&
            $this->isOpen($curr)) {
            /* If the current element is open, move into it. */
            array_push($this->_currstack, array('k' => $this->_currkey, 'p' => $this->_currparent));
            $this->_currkey = 0;
            $this->_currparent = $curr['value'];
        } else {
            /* Else, increment within the current subfolder. */
            $this->_currkey++;
        }

        /* If the pointer doesn't point to an element, try to move back to
           the previous subfolder.  If there is no previous subfolder,
           return false. */
        $curr = $this->current();
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

        if (!$this->_showunsub &&
            !$this->isSubscribed($curr) &&
            (!$this->isContainer($curr) ||
             !$this->hasChildren($curr, true))) {
            /* Skip this entry if:
             * 1. We are not showing all elements
             * 2. We are not subscribed to this element
             * 3. It is not a container -OR-, if it is a container, if there
             *    are no viewable elements underneath it. */
            return $this->next();
        }

        return $curr;
    }

    /**
     * Set internal pointer to the head of the tree.
     *
     * @access public
     *
     * @return mixed  Returns the element at the head of the tree or false
     *                if the element doesn't exist.
     */
    function reset()
    {
        $this->_changed = true;

        foreach ($this->_parent as $key => $val) {
            $key2 = array_search($this->_first, $val);
            if ($key2 !== null) {
                $this->_currkey = $key2;
                $this->_currparent = $key;
                $this->_currstack = array();
                break;
            }
        }

        return $this->current();
    }

    /**
     * Return the current tree element.
     *
     * @access public
     *
     * @return array  The current tree element or false if there is no
     *                element.
     */
    function current()
    {
        if (!isset($this->_parent[$this->_currparent][$this->_currkey])) {
            return false;
        }

        return $this->_addaliases($this->_tree[$this->_parent[$this->_currparent][$this->_currkey]]);
    }

    /**
     * Determines if there are more elements in the current tree level.
     *
     * @access public
     *
     * @return boolean  True if there are more elements, false if this is the
     *                  last element.
     */
    function peek()
    {
        return (isset($this->_parent[$this->_currparent][($this->_currkey + 1)]));
    }

    /**
     * Adds aliases to a tree element and returns the resulting array.
     *
     * @access private
     *
     * @param array $elt  A tree element.
     *
     * @return array  A tree element with the aliases added.
     */
    function _addaliases($elt)
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
     * @access public
     *
     * @param string $name  The name of the tree element.
     *
     * @return array  Returns the requested element or false if not found.
     */
    function get($name)
    {
        if (isset($this->_tree[$name])) {
            return $this->_addaliases($this->_tree[$name]);
        } else {
            return false;
        }
    }

    /**
     * Insert a folder/mailbox into the tree.
     *
     * @access public
     *
     * @param mixed $id  The name of the folder (or a list of folder names)
     *                   to add (must be present on the mail server).
     *
     * @return boolean  True on success, false on error.
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

        $success = true;
        foreach ($id as $val) {
            $currsuccess = $this->_insert($val, 1);
            if (!$currsuccess) {
                $success = false;
            }
        }

        return $success;
    }

    /**
     * Insert a folder/mailbox into the tree.
     *
     * @access private
     *
     * @param string $id    The name of the folder to add (must be present on
     *                      the mail server).
     * @param integer $pos  Current delimiter position.
     *
     * @return boolean  True on success, false on error.
     */
    function _insert($id, $pos)
    {
        $this->_changed = true;

        /* Break apart the name via the delimiter and go step by step through
         * the name to make sure all subfolders exist in the tree. */
        $parts = explode($this->_delimiter, $id);
        $begin = implode($this->_delimiter, array_slice($parts, 0, $pos));
        $more = (count($parts) > $pos);
        
        if (isset($this->_tree[$begin])) {
            if (!$more) {
                $this->_setContainer($this->_tree[$begin], false);
            }
        } elseif ($begin != $this->_prefixnodelim) {
            $ob = $this->_getMailbox($begin);
            $elt = $this->_makeMailboxTreeElt($ob);

            if ($this->_insertElt($elt)) {
                /* We know that the parent folder has children. */
                if (isset($this->_tree[$elt['p']])) {
                    $this->_setChildren($this->_tree[$elt['p']], true);
                }

                /* Make sure we are sorted correctly. */
                if (count($this->_parent[$elt['p']]) > 1) {
                    $this->_sortList($this->_parent[$elt['p']]);
                }
            }
        }

        if ($more) {
            return $this->_insert($id, ++$pos);
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
           %/% lists; also filter out dotfiles if requested. */
        if (!isset($this->_tree[$elt['v']]) &&
            ($this->_dotfiles ||
             (strlen($elt['l']) && $elt['l'][0] != '.') ||
             ($this->_prefixnodelim == $elt['l']))) {
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
     * @access public
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
        }

        if ((($this->_mode == IMAPTREE_MODE_MAIL) && ($id == 'INBOX')) ||
            !isset($this->_tree[$id]) ||
            ($id == $this->_prefixnodelim)) {
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

        /* Delete the tree entry. */
        unset($this->_tree[$id]);

        /* Delete the entry from the parent tree. */
        $key = array_search($id, $this->_parent[$parent]);
        unset($this->_parent[$parent][$key]);

        if (empty($this->_parent[$parent])) {
            /* This folder is now completely empty (no children).  If the
             * folder is a container only, we should delete the folder from
             * the tree. */
            unset($this->_parent[$parent]);
            if (isset($this->_tree[$parent])) {
                $this->_setChildren($this->_tree[$parent], false);
                if ($this->isContainer($this->_tree[$parent])) {
                    $this->delete($parent);
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
     * @access public
     *
     * @param mixed $id  The element name or an array of element names.
     */
    function subscribe($id)
    {
        if (!is_array($id)) {
            $id = array($id);
        }

        foreach ($id as $val) {
            if (isset($this->_tree[$val])) {
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
     * @access public
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
            /* The INBOX can never be unsubscribed to (if in mail mode). */
            if (isset($this->_tree[$val]) &&
                (($this->_mode != IMAPTREE_MODE_MAIL) || ($val != 'INBOX'))) { 
                $elt = &$this->_tree[$val];

                /* Do not delete from tree if there are child elements -
                 * instead, convert to a container element. */
                if ($this->hasChildren($elt)) {
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
     * @param array $list               A list of stdClass objects in the
     *                                  format retuned from
     *                                  imap_getmailboxes().
     * @param optional boolean $expand  Expand subfolders?
     */
    function _addLevel($list, $expand = true)
    {
        foreach ($list as $key => $val) {
            $elt = $this->_makeMailboxTreeElt($val);
            if ($key != $this->_prefix) {
                /* We need to convert $parent to a string because, if there
                 * is no parent (NULL), this is stored as the empty string in
                 * the parent array. */
                $parent = strval($elt['p']);
                if ($this->_insertElt($elt) && empty($this->_first)) {
                    $this->_first = $elt['l'];
                }
            }
            if ($expand) {
                if ($this->isOpen($elt)) {
                    $this->expand($elt['v']);
                } else {
                    $this->_childrenInfo($elt['v'], false, true);
                }
            }
        }


        /* Sort the list. */
        if (isset($parent) && !empty($this->_parent[$parent])) {
            $this->_sortList($this->_parent[$parent]);
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
     * Does the element have any children?
     *
     * @access public
     *
     * @param array $elt                  A tree element.
     * @param optional boolean $viewable  Only return true if this element
     *                                    has viewable children?
     *
     * @return integer  Non-zero if the element has children.
     */
    function hasChildren($elt, $viewable = false)
    {
        $ret = (($elt['a'] & IMAPTREE_ELT_HAS_CHILDREN) ||
                ($this->_children && ($elt['a'] & LATT_HASCHILDREN)));

        if (!$viewable || !$ret) {
            return $ret;
        }

        /* If we are viewing all elements (subscribed and unsubscribed)
         * -OR- we are viewing only unsubscribed but we have not viewed
         * unsubscribed elements yet, we know that their must be viewable
         * children so return true. */
        if ($this->_showunsub || !$this->_unsubview) {
            return true;
        }

        /* Cache results from below since, most likely if we get this far,
         * this code will be accessed several times in the current request. */
        if (isset($this->_hasChildrenCache[$elt['v']])) {
            return $this->_hasChildrenCache[$elt['v']];
        }

        $retvalue = false;
        if (!$this->isDiscovered($elt) ||
            ($this->hasChildren($elt) &&
             empty($this->_parent[$elt['v']]))) {
            $info = $this->_childrenInfo($elt['v']);
            $retvalue = (!empty($info['haschildren']));
        } else { 
            foreach ($this->_parent[$elt['v']] as $val) {
                if (isset($this->_tree[$val])) {
                    if ($this->isSubscribed($this->_tree[$val]) ||
                        $this->hasChildren($this->_tree[$val], true)) {
                        $retvalue = true;
                        break;
                    }
                }
            }
        }

        $this->_hasChildrenCache[$elt['v']] = $retvalue;

        return $retvalue;
    }

    /**
     * Set the children attribute for an element.
     *
     * @access private
     *
     * @param array &$elt    A tree element.
     * @param boolean $bool  TODO
     */
    function _setChildren(&$elt, $bool)
    {
        $this->_setAttribute($elt, IMAPTREE_ELT_HAS_CHILDREN, $bool);
        if ($this->_children) {
            $this->_setAttribute($elt, LATT_HASCHILDREN, $bool);
            $this->_setAttribute($elt, LATT_HASNOCHILDREN, !$bool);
        }
    }

    /**
     * Has the tree element been discovered?
     *
     * @access public
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
     * @access public
     *
     * @param array $elt  A tree element.
     *
     * @return integer  True if the element is open.
     */
    function isOpen($elt)
    {
        if (empty($this->_initmode)) {
            return $elt['a'] & IMAPTREE_ELT_IS_OPEN;
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
     * @access public
     *
     * @param array $elt  A tree element.
     *
     * @return integer  True if the element is a container.
     */
    function isContainer($elt)
    {
        return $elt['a'] & LATT_NOSELECT;
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
     * @access public
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
     * Return the prefix.
     *
     * @access public
     *
     * @return string  The prefix where folders are begin to be listed.
     */
    function getPrefix()
    {
        return $this->_prefix;
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
        $ob->name = substr($ob->name, strpos($ob->name, '}') + 1);
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
     * @access public
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
     * @access public
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
     * @access public
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
     * @access public
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
     * Initialize the list of subscribed mailboxes.
     *
     * @access private
     */
    function _initSubscribed()
    {
        if (is_null($this->_subscribed)) {
            $this->_subscribed = array();
            /* INBOX is always subscribed to if we are in mail mode. */
            if ($this->_mode == IMAPTREE_MODE_MAIL) {
                $this->_subscribed['INBOX'] = 1;
            }
            $sublist = @imap_lsub($this->_getStream(), $this->_server, $this->_prefix . '*');
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
        if (is_null($this->_subscribed)) {
            $this->_initSubscribed();
            $this->_unsubscribed = array();

            /* Get list of all mailboxes. */
            $all_list = @imap_list($this->_getStream(), $this->_server, $this->_prefix . '*');
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
     *
     * @access public
     */
    function expandAll()
    {
        foreach ($this->_parent[null] as $val) {
            $this->expand($val, true);
        }
    }

    /**
     * Should we collapse all elements?
     *
     * @access public
     */
    function collapseAll()
    {
        foreach ($this->_tree as $val) {
            $this->collapse($val['v']);
        }
    }

    /**
     * Return the list of mailboxes in the next level.
     *
     * @access private
     *
     * @param string $id              The current mailbox.
     * @param optional boolean $list  Should we return the list of mailboxes,
     *                                even if we can use the LATT_HASCHILDREN
     *                                constant?
     * @param optional boolean $set   Should we set the has children flag?
     *
     * @return array  A list of mailbox objects or the empty list.
     *                See _getList() for format.
     */
    function _childrenInfo($id, $list = false, $set = false)
    {
        $info = array('haschildren' => false, 'list' => array());
        $tried = false;

        if (isset($this->_tree[$id]['a'])) {
            if ($this->hasChildren($this->_tree[$id]['a'])) {
                $info['haschildren'] = true;
                $tried = true;
            }
        }

        if (!$tried || ($info['haschildren'] && $list)) {
            if (($this->_mode == IMAPTREE_MODE_MAIL) && ($id == 'INBOX')) { 
                if (empty($this->_prefix)) {
                    $query = '%' . $this->_delimiter . '%';
                } else {
                    $query = $this->_prefix . '%';
                }
            } else {
                $query = $this->noTrailingDelimiter($id) . $this->_delimiter . '%';
            }

            $info['list'] = $this->_getList($query);
            if (!$info['haschildren']) {
                $info['haschildren'] = count($info['list']);
            }
        }

        if ($set && isset($this->_tree[$id])) {
            $this->_setChildren($this->_tree[$id], $info['haschildren']);
        }

        return $info;
    }

    /**
     * Switch subscribed/unsubscribed viewing.
     *
     * @access public
     *
     * @param boolean $unsub  Show unsubscribed elements?
     */
    function showUnsubscribed($unsub)
    {
        if ($unsub === $this->_showunsub) {
            return;
        }

        $this->_showunsub = $unsub;

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

        $this->_initmode = true;
        $this->insert(array_keys($this->_unsubscribed));
        $this->_initmode = false;
    }

    /**
     * Returns a reference to a currently open IMAP stream.
     * THIS METHOD MUST BE DEFINED IN ALL SUBCLASSES.
     *
     * @abstract
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
     * Get information about new/unseen/total messages for the given
     * element.
     *
     * @access public
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

        $sts = @imap_status($this->_getStream(), $this->_server . $name, SA_MESSAGES | SA_UNSEEN | SA_RECENT);
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
     * @param array &$mbox           The list of mailboxes to sort.
     * @param optional boolean $key  Are the list of mailbox names in the key
     *                               field of $mbox?
     */
    function _sortList(&$mbox, $key = false)
    {
        if (is_null($this->_imap_sort)) {
            require_once 'Horde/IMAP/Sort.php';
            $this->_imap_sort = &new IMAP_Sort($this->_delimiter);
        }

        if ($key) {
            $this->_imap_sort->sortMailboxesByKey($mbox, ($this->_mode == IMAPTREE_MODE_MAIL));
        } else {
            $this->_imap_sort->sortMailboxes($mbox, ($this->_mode == IMAPTREE_MODE_MAIL));
        }
    }

}
