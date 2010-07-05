<?php

require_once 'Horde/IMAP/Thread.php';

/**
 * The IMP_Thread class extends the IMAP_Thread class to include a function
 * to generate the thread tree images.  This class is necessary to ensure
 * backwards compatibility with Horde 3.0.
 *
 * For the next (mythical) release of Horde 4.x, this code should be merged
 * into the IMAP_Thread class.
 *
 * $Horde: imp/lib/IMAP/Thread.php,v 1.5.2.8 2009-01-06 15:24:05 jan Exp $
 *
 * Copyright 2005-2009 The Horde Project (http://www.horde.org/)
 *
 * See the enclosed file COPYING for license information (GPL). If you
 * did not receive this file, see http://www.fsf.org/copyleft/gpl.html.
 *
 * @author  Michael Slusarz <slusarz@horde.org>
 * @since   IMP 4.1
 * @package IMP
 */
class IMP_Thread extends IMAP_Thread {

    /**
     * Images used and their internal representations.
     *
     * @var array
     */
    var $_imglist = array(
        '0' => 'blank.png',
        '1' => 'line.png',
        '2' => 'join.png',
        '3' => 'joinbottom-down.png',
        '4' => 'joinbottom.png'
    );

    /**
     * Generate the thread representation for the given index list in the
     * internal format (a string with each character representing the graphic
     * to be displayed from $_imglist).
     *
     * @param array $indices    The list of indices to create a tree for.
     * @param boolean $sortdir  True for newest first, false for oldest first.
     *
     * @return array  An array with the index as the key and the interal
     *                thread representation as the value.
     */
    function getThreadTreeOb($indices, $sortdir)
    {
        $container = $last_level = $last_thread = null;
        $tree = array();

        if ($sortdir) {
            $indices = array_reverse($indices);
        }

        /* If starting in the middle of a thread, the threadLevel tree needs
         * to be built from the bottom of the current thread. */
        $first = reset($indices);
        $indentBase = $this->getThreadBase($first);
        if (!empty($indentBase) && $indentBase != $first) {
            reset($this->_lookup);
            while (key($this->_lookup) != $indentBase) {
                next($this->_lookup);
            }
            while (($key = key($this->_lookup)) != $first) {
                $threadLevel[$this->getThreadIndent($key)] = $this->lastInLevel($key);
                next($this->_lookup);
            }
        }

        foreach ($indices as $val) {
            $tree[$val] = '';

            $indentBase = $this->getThreadBase($val);
            if (empty($indentBase)) {
                continue;
            }

            $lines = '';
            $indentLevel = $this->getThreadIndent($val);
            $lastinlevel = $this->lastInLevel($val);

            if ($lastinlevel && ($indentBase == $val)) {
                continue;
            }

            if ($lastinlevel) {
                $join_img = ($sortdir) ? 3 : 4;
            } elseif (($indentLevel == 1) && ($indentBase == $val)) {
                $join_img = ($sortdir) ? 4 : 3;
                $container = $val;
            } else {
                $join_img = 2;
            }
            $threadLevel[$indentLevel] = $lastinlevel;
            $line = '';
            for ($i = ($container == $indentBase) ? 1 : 2; $i < $indentLevel; ++$i) {
                $line .= (!isset($threadLevel[$i]) || ($threadLevel[$i])) ? 0 : 1;
            }
            $tree[$val] = $line . $join_img;
        }

        return $tree;
    }

    /**
     * Generate the thread representation image for the given index list.
     *
     * @param array $indices    The list of indices to create a tree for.
     * @param boolean $sortdir  True for newest first, false for oldest first.
     *
     * @return array  An array with the index as the key and the thread image
     *                representation as the value.
     */
    function getThreadImageTree($indices, $sortdir)
    {
        $tree = array();
        $imgs = $this->getImageUrls(false);
        foreach ($this->getThreadTreeOb($indices, $sortdir) as $k => $v) {
            $tree[$k] = '';
            for ($i = 0, $length = strlen($v); $i < $length; ++$i) {
                $tree[$k] .= $imgs[$v[$i]];
            }
        }
        return $tree;
    }

    /**
     * Get potential image URLs that may be used to display a thread.
     * This function may be called statically, i.e.:
     *   IMP_Thread::getImageUrls();
     *
     * @since IMP 4.2
     *
     * @param ids $ids  Add unique DOM ID to each image?
     *
     * @return array  An array with the image code as a key and the image url
     *                as the value.
     */
    function getImageUrls($ids = true)
    {
        $graphicsdir = $GLOBALS['registry']->getImageDir('horde');
        $args = array();

        $vars = get_class_vars('IMP_Thread');
        foreach ($vars['_imglist'] as $key => $val) {
            if ($ids) {
                $args['id'] = 'thread_img_' . $key;
            }
            $out[$key] = Horde::img('tree/' . (($key != 0 && !empty($GLOBALS['nls']['rtl'][$GLOBALS['language']])) ? ('rev-' . $val) : $val), '', $args, $graphicsdir);
        }

        return $out;
    }

}
