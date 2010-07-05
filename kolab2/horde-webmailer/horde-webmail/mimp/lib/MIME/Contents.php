<?php

require_once IMP_BASE . '/lib/MIME/Contents.php';

/**
 * The MIMP_Contents:: class extends the IMP_Contents:: class and contains
 * all functions related to handling the content and output of mail messages
 * in MIMP.
 *
 * $Horde: mimp/lib/MIME/Contents.php,v 1.48.2.4 2009-01-06 15:24:53 jan Exp $
 *
 * Copyright 2002-2009 The Horde Project (http://www.horde.org/)
 *
 * See the enclosed file COPYING for license information (GPL). If you
 * did not receive this file, see http://www.fsf.org/copyleft/gpl.html.
 *
 * @author  Michael Slusarz <slusarz@horde.org>
 * @package MIMP
 */
class MIMP_Contents extends IMP_Contents {

    /**
     * Attempts to return a reference to a concrete MIMP_Contents instance.
     * If an MIMP_Contents object is currently stored in the local cache,
     * recreate that object.  Else, create a new instance.
     * Ensures that only one MIMP_Contents instance for any given message is
     * available at any one time.
     *
     * This method must be invoked as:
     *   $mimp_contents = &MIMP_Contents::singleton($in);
     *
     * @param mixed $in  Either an index string or a MIME_Message object.
     *
     * @return MIMP_Contents  The MIMP_Contents object or null.
     */
    function &singleton($in)
    {
        static $instance = array();

        $signature = MIMP_Contents::_createCacheID($in);
        if (isset($instance[$signature])) {
            return $instance[$signature];
        }

        $instance[$signature] = new MIMP_Contents($in);
        return $instance[$signature];
    }

    /**
     * Return the attachment list, in Horde_Mobile:: objects for
     * header listing.
     *
     * @param Horde_Mobile_block $hb  The Horde_Mobile_block object to add to.
     */
    function getAttachments(&$hb)
    {
        $msg = '';

        foreach (array_keys($this->_atc) as $key) {
            $part = $this->_message->getPart($key);
            if ($part !== false) {
                $hb->add(new Horde_Mobile_text(_("Attachment") . ': ', array('b')));
                $t = &$hb->add(new Horde_Mobile_text(sprintf('%s (%s KB)', $part->getName(true, true), $part->getSize()) . "\n"));
                $t->set('linebreaks', true);
            }
        }
    }

    /**
     * Return all viewable message parts (plain text, for
     * Horde_Mobile:: to deal with).
     *
     * @return string  The full message.
     */
    function getMessage()
    {
        $msg = '';
        $partDisplayed = false;

        foreach ($this->_parts as $key => $value) {
            if (!empty($value)) {
                if ($msg) {
                    $msg .= "\n\n";
                }
                $msg .= $value;
                $partDisplayed = true;
            }
        }

        if (!$partDisplayed) {
            $msg .= _("There are no parts that can be displayed inline.");
        }

        return $msg;
    }

    /**
     * Returns an array summarizing a part of a MIME message.
     *
     * @param MIME_Part &$mime_part  The MIME_Part to summarize.
     * @param boolean $guess         Is this a temporary guessed-type part?
     *
     * @return array  See MIME_Contents::partSummary().
     *                Ignores guessed parts.
     */
    function partSummary(&$mime_part, $guess = false)
    {
        if ($guess) {
            return array();
        } else {
            $summary = parent::partSummary($mime_part);
            array_walk($summary, 'strip_tags');
            return $summary;
        }
    }

    /**
     * Render a MIME Part.
     *
     * @param MIME_Part &$mime_part  A MIME_Part object.
     *
     * @return string  The rendered data.
     */
    function renderMIMEPart(&$mime_part)
    {
        $this->_setContents($mime_part);
        return parent::renderMIMEPart($mime_part);
    }

    /**
     * Render MIME Part data.
     *
     * @access private
     *
     * @param MIME_Part &$mime_part  A MIME_Part object.
     * @param boolean $attachment    Render MIME Part attachment info?
     *
     * @return string  The rendered data.
     */
    function _renderMIMEPart(&$mime_part, $attachment = false)
    {
        /* Get the MIME_Viewer object for this MIME part */
        $viewer = &$this->getMIMEViewer($mime_part);
        if (!is_a($viewer, 'MIME_Viewer')) {
            return '';
        }

        $mime_part->transferDecodeContents();

        /* If this is a text/* part, AND the text is in a different
         * character set than the browser, convert to the current
         * character set. */
        $charset = $mime_part->getCharset();
        if ($charset) {
            $charset_upper = String::upper($charset);
            if ($charset_upper != 'US-ASCII') {
                $default_charset = String::upper(NLS::getCharset());
                if ($charset_upper != $default_charset) {
                    $mime_part->setContents(String::convertCharset($mime_part->getContents(), $charset, $default_charset));
                }
            }
        }

        $viewer->setMIMEPart($mime_part);
        $params = array(&$this);
        if ($attachment) {
            return $viewer->renderAttachmentInfo($params);
        } else {
            return $viewer->render($params);
        }
    }

    /**
     * Build the message deciding what MIME Parts to show.
     *
     * @return boolean  False on error.
     */
    function buildMessage()
    {
        $status = $GLOBALS['registry']->pushApp('mimp');
        $ret = parent::buildMessage();
        if ($status) {
            $GLOBALS['registry']->popApp('mimp');
        }
        return $ret;
    }

    /**
     * Prints out the status message for a given MIME Part.
     *
     * @param mixed $msg      The message(s) to output.
     * @param string $img     NOT USED.
     * @param boolean $print  NOT USED.
     * @param string $class   NOT USED.
     *
     * @return string  The formatted status message string.
     */
    function formatStatusMsg($msg, $img = null, $printable = true,
                             $class = null)
    {
        if (!is_array($msg)) {
            $msg = array($msg);
        }
        return implode("\n", $msg) . "\n\n";
    }

}
