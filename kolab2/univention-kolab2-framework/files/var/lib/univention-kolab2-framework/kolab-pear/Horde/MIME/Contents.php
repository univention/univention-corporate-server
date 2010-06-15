<?php

require_once dirname(__FILE__) . '/Message.php';
require_once dirname(__FILE__) . '/Part.php';
require_once HORDE_BASE . '/config/mime_drivers.php';

/* @constant MIME_CONTENTS_CACHE The name of the URL parameter that holds the MIME_Contents cache identifier. */
define('MIME_CONTENTS_CACHE', 'mimecache');

/**
 * The MIME_Contents:: class contains functions related to handling
 * the output of MIME content.
 *
 * $Horde: framework/MIME/MIME/Contents.php,v 1.111 2004/05/28 08:57:21 jan Exp $
 *
 * Copyright 2002-2004 Michael Slusarz <slusarz@bigworm.colorado.edu>
 *
 * See the enclosed file COPYING for license information (GPL). If you
 * did not receive this file, see http://www.fsf.org/copyleft/gpl.html.
 *
 * @author  Michael Slusarz <slusarz@bigworm.colorado.edu>
 * @version $Revision: 1.1.2.1 $
 * @since   Horde 3.0
 * @package Horde_MIME
 */
class MIME_Contents {

    /**
     * The MIME_Message object for the message.
     *
     * @var object MIME_Message $_message
     */
    var $_message;

    /**
     * The attachments list.
     *
     * @var array $_atc
     */
    var $_atc = array();

    /**
     * The message parts list.
     *
     * @var array $_parts
     */
    var $_parts = array();

    /**
     * The summary parts list.
     *
     * @var array $_summary
     */
    var $_summary = array();

    /**
     * The Cache_session identifier.
     *
     * @var string $_sessionCacheID
     */
    var $_sessionCacheID = null;

    /**
     * The MIME_Viewer object cache.
     *
     * @var array $_viewerCache
     */
    var $_viewerCache = array();

    /**
     * The attachment display type to use.
     *
     * @var string $_displayType
     */
    var $_displayType = '';

    /**
     * The MIME index key to use.
     *
     * @var string $_mimekey
     */
    var $_mimekey = null;

    /**
     * The actionID value for various actions.
     * 'download'  --  Downloading a part/attachment.
     * 'view'      --  Viewing a part/attachment.
     *
     * @var array $_viewID
     */
    var $_viewID = array();

    /**
     * Show the links in the summaries?
     *
     * @var boolean $_links
     */
    var $_links = true;

    /**
     * The base MIME_Contents object.
     *
     * @var object MIME_Contents &$_base
     */
    var $_base = null;

    /**
     * The number of message/rfc822 levels labeled as 'attachments'
     * of the current part.
     *
     * @var integer $_attach822
     */
    var $_attach822 = 0;

    /**
     * Constructor
     *
     * @access public
     *
     * @param object MIME_Message $messageOb  The object to work with.
     * @param optional array $viewID          The actionID values for viewing
     *                                        parts/attachments.
     * @param optional array &$contents       Array containing a single value:
     *                                        a reference to the base object.
     * (This last parameter needs to be handled via an array because PHP <
     *  5.0 doesn't handle optional pointer parameters otherwise.)
     */
    function MIME_Contents($messageOb, $viewID = array(), $contents = array())
    {
        global $prefs;

        $this->_message = $messageOb;
        $this->_viewID = $viewID;
        $this->_displayType = $prefs->getValue('attachment_display');

        /* Create the pointer to the base object. */
        if (!empty($contents)) {
            $ptr = reset($contents);
            $old_ptr = &$ptr->getBaseObjectPtr();
            $this->_base = $old_ptr;
        }
    }

    /**
     * Returns the entire body of the message.
     * You probably want to override this function in any subclass.
     *
     * @access public
     *
     * @return string  The text of the body of the message.
     */
    function getBody()
    {
        return $this->_message->toString();
    }

    /**
     * Returns the raw text for one section of the message.
     * You probably want to override this function in any subclass.
     *
     * @access public
     *
     * @param string $id  The ID of the MIME_Part.
     *
     * @return string  The text of the part.
     */
    function getBodyPart($id)
    {
        if (($part = &$this->getMIMEPart($id))) {
            return $part->getContents();
        } else {
            return '';
        }
    }

    /**
     * Returns the MIME_Message object for the mail message.
     *
     * @access public
     *
     * @return object MIME_Message  A MIME_Message object.
     */
    function getMIMEMessage()
    {
        return $this->_message;
    }

    /**
     * Fetch a part of a MIME message.
     *
     * @access public
     *
     * @param integer $id  The MIME index of the part requested.
     *
     * @return object MIME_Part  The raw MIME part asked for.
     */
    function &getMIMEPart($id)
    {
        $mime = $this->_message->getPart($id);
        return $mime;
    }

    /**
     * Rebuild the MIME_Part structure of a message.
     * You probably want to override this function in any subclass.
     *
     * @access public
     *
     * @return object MIME_Message  A MIME_Message object with all of the body
     *                              text stored in the individual MIME_Parts.
     */
    function rebuildMessage()
    {
        return $this->_message;
    }

    /**
     * Fetch part of a MIME message.
     *
     * @access public
     *
     * @param integer $id            The MIME ID of the part requested.
     * @param optional boolean $all  If this is a header part, should we
     *                               return all text in the body?
     *
     * @return object MIME_Part  The MIME_Part.
     */
    function &getRawMIMEPart($id, $all = false)
    {
        $mime_part = &$this->getMIMEPart($id);
        if (!is_a($mime_part, 'MIME_Part')) {
            return;
        }

        /* If all text is requested, change the ID now. */
        if ($all && $mime_part->getInformation('header')) {
            $id = substr($id, 0, strrpos($id, '.'));
        }

        /* Only set contents if there is currently none in the MIME Part. */
        if (!$mime_part->getContents()) {
            $mime_part->setContents($this->getBodyPart($id));
        }

        return $mime_part;
    }

    /**
     * Fetch part of a MIME message and decode it, if it is base_64 or
     * qprint encoded.
     *
     * @access public
     *
     * @param integer $id            The MIME ID of the part requested.
     * @param optional boolean $all  If this is a header part, should we
     *                               return all text in the body?
     *
     * @return object MIME_Part  The MIME_Part with its contents decoded.
     */
    function &getDecodedMIMEPart($id, $all = false)
    {
        if (($mime_part = &$this->getRawMIMEPart($id, $all))) {
            $mime_part->transferDecodeContents();
            return $mime_part;
        } else {
            return;
        }
    }

    /**
     * Return the attachment list (HTML table format).
     *
     * @access public
     *
     * @return string  The list of attachments formatted into HTML.
     */
    function getAttachments()
    {
        $msg = '';

        foreach ($this->_atc as $key => $val) {
            $msg .= $this->_arrayToTableRow($this->_atc[$key]);
        }

        return $msg;
    }

    /**
     * Return the message list (HTML table format).
     *
     * @access public
     *
     * @param optional boolean $oneframe  Should the output be designed
     *                                    for display in a single frame?
     *
     * @return string  The message formatted into HTML.
     */
    function getMessage($oneframe = false)
    {
        $msg = '';
        $msgCount = count($this->_parts);
        $partDisplayed = false;

        if ($oneframe) {
            $msg .= '<style type="text/css">.onefr {border: 1px solid #000000; background-color: lightgrey; padding: 1px}</style>' . "\n";
        }

        foreach ($this->_parts as $key => $value) {
            if (isset($this->_summary[$key]) &&
                ((($msgCount == 1) && empty($value)) || ($msgCount > 1))) {
                $msg .= '<tr><td align="left">';
                if ($oneframe) {
                    $msg .= '<table class="onefr">';
                    $summary = $this->_summary[$key];
                    $summary = array_merge(array_splice($summary, 0, 1), array_splice($summary, 1));
                    $msg .= $this->_arrayToTableRow($summary);
                } else {
                    $msg .= '<table>';
                    $msg .= $this->_arrayToTableRow($this->_summary[$key]);
                }
                $msg .= '</table><div style="font-size: 1px;">&nbsp;<br /></div></td></tr>';
            }
            if (!empty($value)) {
                $msg .= '<tr><td class="text" align="left">' . $value . '</td></tr>';
                $partDisplayed = true;
            }
        }

        if (!$partDisplayed) {
            $msg .= '<tr><td class="text" align="left"><i>' . _("There are no parts that can be displayed inline.") . '</i></td></tr>';
        }

        return $msg;
    }

    /**
     * Expands an array into a table row.
     *
     * @access private
     *
     * @param array $array  The array to expand.
     *
     * @return string  The array expanded to a HTML table row.
     */
    function _arrayToTableRow($array)
    {
        $text = '<tr valign="middle">';

        foreach ($array as $elem) {
            if (!empty($elem)) {
                $text .= "<td>$elem&nbsp;</td>\n";
            }
        }

        return $text . "</tr>\n";
    }

    /**
     * Returns the data for a specific MIME index.
     *
     * @access public
     *
     * @param string $id     The MIME index.
     * @param string $field  The field to return (message, atc, summary)
     *
     * @return string  The text currently set for that index.
     */
    function getIndex($id, $field)
    {
        $field = '_' . $field;
        if (is_array($this->$field) && array_key_exists($id, $this->$field)) {
            $entry = $this->$field;
            return $entry[$id];
        } else {
            return null;
        }
    }

    /**
     * Removes the message text and summary for a specific MIME index.
     *
     * @access public
     *
     * @param string $id  The MIME index.
     */
    function removeIndex($id)
    {
        unset($this->_parts[$id]);
        unset($this->_summary[$id]);
        unset($this->_atc[$id]);
    }

    /**
     * Determine if we can (and know how to) inline a MIME Part.
     *
     * @param object MIME_Part &$mime_part  A MIME_Part object.
     *
     * @return boolean  True if part can be inlined.
     *                  False if it cannot.
     */
    function canDisplayInline(&$mime_part)
    {
        /* First check: The MIME headers allow the part to be inlined. */
        if ($mime_part->getDisposition() != 'inline') {
            return;
        }

        /* Second check (save the most expensive for last):
         * Check to see if the driver is set to inline. */
        $viewer = &$this->getMIMEViewer($mime_part);
        return (is_a($viewer, 'MIME_Viewer') && $viewer->canDisplayInline());
    }

    /**
     * Get MIME_Viewer object.
     *
     * @access public
     *
     * @param object MIME_Part &$mime_part  A MIME_Part object.
     *
     * @return object MIME_Viewer  The MIME_Viewer object.
     *                             Return false on error.
     */
    function &getMIMEViewer(&$mime_part)
    {
        /* Make sure we have a MIME_Part to process. */
        if (empty($mime_part)) {
            return false;
        }

        require_once dirname(__FILE__) . '/Viewer.php';

        $key = $mime_part->getUniqueID() . '|' . $mime_part->getType();
        if (!isset($this->_viewerCache[$key])) {
            $this->_viewerCache[$key] = &MIME_Viewer::factory($mime_part);
        }

        return $this->_viewerCache[$key];
    }

    /**
     * Get the MIME Content-Type output by a MIME_Viewer for a particular
     * MIME_Part.
     *
     * @access public
     *
     * @param object MIME_Part &$mime_part  A MIME_Part object.
     *
     * @return string  The MIME type output by the MIME_Viewer.
     *                 Return false on error.
     */
    function getMIMEViewerType(&$mime_part)
    {
        if (($viewer = &$this->getMIMEViewer($mime_part))) {
            $type = $viewer->getType();
            $charset = $mime_part->getCharset(true);
            if ($charset) {
                $type .= '; charset=' . $charset;
            }
            return $type;
        } else {
            return false;
        }
    }

    /**
     * Returns the key to use for a particular MIME_Part.
     *
     * @access private
     *
     * @param object MIME_Part &$mime_part  A MIME_Part object.
     * @param optional boolean $override    Respect the MIME key override
     *                                      value?
     *
     * @return string  The unique identifier of the MIME_Part.
     *                 Returns false if no key found.
     */
    function _getMIMEKey(&$mime_part, $override = true)
    {
        $id = $this->getMIMEKeyOverride();

        if ($override && !is_null($id)) {
            return $id;
        } else {
            $id = $mime_part->getMIMEId();
            if (is_null($id)) {
                return false;
            } else {
                return $id;
            }
        }
    }

    /**
     * Gets the MIME key override.
     *
     * @access public
     *
     * @return string  The MIME key override - null if no override.
     */
    function getMIMEKeyOverride()
    {
        return $this->_mimekey;
    }

    /**
     * Sets an override for the MIME key.
     *
     * @access public
     *
     * @param optional string $mimekey
     */
    function setMIMEKeyOverride($mimekey = null)
    {
        $this->_mimekey = $mimekey;
    }

    /**
     * Should we display links for the summaries?
     *
     * @access public
     *
     * @param optional boolean $show  Show the summary links?
     */
    function showSummaryLinks($show = null)
    {
        if (!is_null($show)) {
            $this->_links = $show;
        }

        return $this->_links;
    }

    /**
     * Render a MIME Part.
     *
     * @access public
     *
     * @param object MIME_Part &$mime_part  A MIME_Part object.
     *
     * @return string  The rendered data.
     */
    function renderMIMEPart(&$mime_part)
    {
        return $this->_renderMIMEPart($mime_part, false);
    }

    /**
     * Render MIME Part attachment info.
     *
     * @access public
     *
     * @param object MIME_Part &$mime_part  A MIME_Part object.
     *
     * @return string  The rendered data.
     */
    function renderMIMEAttachmentInfo(&$mime_part)
    {
        return $this->_renderMIMEPart($mime_part, true);
    }

    /**
     * Render MIME Part data.
     *
     * @access private
     *
     * @param object MIME_Part &$mime_part  A MIME_Part object.
     * @param optional boolean $attachment  Render MIME Part attachment info?
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

        $msg = '';

        $mime_part->transferDecodeContents();

        /* If this is a text/* part, AND the text is in a different character
         * set than the browser, convert to the current character set.
         * Additionally, if the browser does not support UTF-8, give the
         * user a link to open the part in a new window with the correct
         * character set. */
        $charset = $mime_part->getCharset();
        if ($charset) {
            $charset_upper = String::upper($charset);
            if (($charset_upper != 'US-ASCII') &&
                !$this->viewAsAttachment()) {
                $default_charset = String::upper(NLS::getCharset());
                if ($charset_upper != $default_charset) {
                    $mime_part->setContents(String::convertCharset($mime_part->getContents(), $charset, $default_charset));
                    if ($default_charset != 'UTF-8') {
                        $status = array(
                            sprintf(_("This message was written in a character set (%s) other than your own."), htmlspecialchars($charset)),
                            sprintf(_("If it is not displayed correctly, %s to open it in a new window."), $this->linkViewJS($mime_part, 'view_attach', _("click here")))
                        );
                        $msg = $this->formatStatusMsg($status, null, false) . '<p />' . $msg;
                    }
                }
            }
        }

        $viewer->setMIMEPart($mime_part);
        $params = array(&$this);
        if ($attachment) {
            $msg .= $viewer->renderAttachmentInfo($params);
        } else {
            $msg .= $viewer->render($params);
        }

        return $msg;
    }

    /**
     * Build the message deciding what MIME Parts to show.
     *
     * @access public
     *
     * @return boolean  False on error.
     */
    function buildMessage()
    {
        $this->_atc = array();
        $this->_parts = array();
        $this->_summary = array();

        if (!is_a($this->_message, 'MIME_Message')) {
            return false;
        }

        /* Now display the parts. */
        $mime_part = &$this->_message->getBasePart();
        $this->buildMessagePart($mime_part);

        return true;
    }

    /**
     * Processes a MIME_Part and stores the display information in the internal
     * class variables.
     *
     * @access public
     *
     * @param object MIME_Part &$mime_part  The MIME_Part object to process.
     *
     * @return string  The rendered text.
     */
    function buildMessagePart(&$mime_part)
    {
        $msg = '';

        /* If we can't display the part inline, add it to the attachment
           list. If the MIME ID of the current part is '0', then force a
           render of the part (since it is the base part and, without
           attempting to render, the message will ALWAYS appear empty. */
        if (!$this->canDisplayInline($mime_part) &&
            ($mime_part->getMIMEId() != 0)) {
            /* Not displaying inline; add to the attachments list. */
            if (($this->_displayType == 'list') ||
                ($this->_displayType == 'both')) {
                $this->setSummary($mime_part, 'attachment');
            }
            if (($this->_displayType == 'inline') ||
                ($this->_displayType == 'both')) {
                $this->setSummary($mime_part, 'part');
            }

            /* Check to see if any attachment information can be rendered by
               the MIME_Viewer. */
            $msg = $this->renderMIMEAttachmentInfo($mime_part);
            if (!empty($msg)) {
                $key = $this->_getMIMEKey($mime_part);
                $this->_parts[$key] = $msg;
            }
        } else {
            $msg = $this->renderMIMEPart($mime_part);
            if (!empty($msg)) {
                $key = $this->_getMIMEKey($mime_part);
                if (!$this->_attach822) {
                    $this->_parts[$key] = $msg;
                }
                /* Some MIME_Viewers set the summary by themelves, so only
                 * add to attachment/inline lists if nothing has been set
                 * as of yet. */
                if (!empty($key) && !$this->getIndex($key, 'summary')) {
                    $this->setSummary($mime_part, 'part');
                    if ($this->_attach822 &&
                        (($this->_displayType == 'list') ||
                        ($this->_displayType == 'both'))) {
                        $this->setSummary($mime_part, 'attachment');
                    }
                }
            }
        }

        if ($mime_part->getInformation('header')) {
            /* If this is message/rfc822 part, and it is marked as an
             * attachment, we need to let future calls to buildMessagePart()
             * know that it should mark embedded parts as not viewable
             * inline. */
            $increment_822 = false;
            if (($mime_part->getType() == 'message/rfc822') &&
                ($mime_part->getDisposition() == 'attachment')) {
                $this->_attach822++;
                $increment_822 = true;
            }

            foreach ($mime_part->getParts() as $part) {
                $msg .= $this->buildMessagePart($part);
            }

            if ($increment_822) {
                $this->_attach822--;
            }
        }

        return $msg;
    }

    /**
     * Are we viewing this page as an attachment through view.php?
     * This method can also be called via MIME_Contents::viewAsAttachment().
     *
     * @access public
     *
     * @param optional boolean $popup  If true, also check if we are viewing
     *                                 attachment in popup view window.
     *
     * @return boolean  True if we are viewing this part as an attachment
     *                  through view.php.
     */
    function viewAsAttachment($popup = false)
    {
        if (stristr($_SERVER['PHP_SELF'], 'view.php') &&
            (!$popup || Util::getFormData('popup_view'))) {
            return true;
        } else {
            return false;
        }
    }

    /**
     * Sets a summary entry.
     *
     * @access public
     *
     * @param object MIME_Part &$mime_part  The MIME_Part object.
     * @param string $type                  The summary cache to use.
     */
    function setSummary(&$mime_part, $type)
    {
        if ($type == 'attachment') {
            $cache = &$this->_atc;
        } elseif ($type == 'part') {
            $cache = &$this->_summary;
        } else {
            return;
        }

        $key = $this->_getMIMEKey($mime_part);
        $summary = $this->partSummary($mime_part, null);

        if (!empty($summary)) {
            if (!isset($this->_parts[$key])) {
                $this->_parts[$key] = null;
            }
            $cache[$key] = $summary;
        }
    }

    /**
     * Returns an array summarizing a part of a MIME message.
     *
     * @access public
     *
     * @param object MIME_Part &$mime_part  The MIME_Part to summarize.
     * @param optional boolean $guess       Is this a temporary guessed-type
     *                                      part?
     *
     * @return array  The summary of the part.
     *                [0] = Icon
     *                [1] = IMAP ID
     *                [2] = Description
     *                [3] = MIME Type
     *                [4] = Size
     *                [5] = Download link/icon
     */
    function partSummary(&$mime_part, $guess = false)
    {
        $attachment = ($mime_part->getDisposition() == 'attachment');
        $bytes = $mime_part->getBytes();
        $description = htmlspecialchars($mime_part->getDescription(true, true));
        $summary = array();
        $type = $mime_part->getType();
        $viewer = &$this->getMIMEViewer($mime_part);

        /* Return if we still didn't find a native mime viewer
         * for a guessed mime type. */
        if ($guess && is_a($viewer, 'MIME_Viewer_default')) {
            return $summary;
        }

        /* Get the MIME id index. */
        $id = $this->_getMIMEKey($mime_part);

        /* Icon column. */
        $icon = $viewer->getIcon($type);
        $summary[] = '<img src="' . $icon . '" height="16" width="16" border="0" alt="" />';

        /* Number column. */
        $summary[] = $id;

        /* Name/text part column. */
        if (!$this->_links ||
            (!$attachment && empty($bytes))  ||
            !isset($this->_viewID['view']) ||
            is_a($viewer, 'MIME_Viewer_default')) {
            $summary[] = $description;
        } else {
            $param_array = array();
            if ($guess === true) {
                $param_array['ctype'] = $type;
            }
            $summary[] = $this->linkViewJS($mime_part, $this->_viewID['view'], $description, null, null, $param_array);
        }

        /* MIME type column. */
        if ($guess) {
            $summary[] = '<i>' . sprintf(_("View as %s"), $type) . '</i>';
        } else {
            $summary[] = '[' . $type . ']';
        }

        /* Size Column. */
        $size = $mime_part->getSize(true);
        if (!empty($bytes) &&
            ($mime_part->getCurrentEncoding() == 'base64')) {
            /* From RFC 2045 [6.8]: "...the encoded data are consistently
               only about 33 percent larger than the unencoded data." */
            $size = number_format(($bytes * 0.75) / 1024);
        }
        $summary[] = sprintf(_("%s KB"), $size);

        /* Download column. */
        if (!$this->_links ||
            is_null($size) ||
            !isset($this->_viewID['download'])) {
            $summary[] = null;
        } else {
            global $registry;
            $summary[] = $this->linkView($mime_part, $this->_viewID['download'], Horde::img('download.gif', _("Download"), null, $registry->getParam('graphics', 'horde')), array('jstext' => sprintf(_("Download %s"), $mime_part->getDescription(true, true))), true);
        }

        /* If the MIME Type is application/octet-stream, try to use
           the file extension to determine the actual MIME type. */
        if ($this->_links &&
            !$guess &&
            !is_null($size) &&
            ($type == 'application/octet-stream') ||
            ($type == 'application/base64')) {
            require_once dirname(__FILE__) . '/Magic.php';
            $new_type = MIME_Magic::filenameToMIME($mime_part->getName());
            if ($new_type != 'application/octet-stream') {
                $temp_part = $mime_part;
                $temp_part->setType($new_type);
                $summary = array_map(
                    create_function('$a, $b', 'return empty($b) ? $a : $a . \'<br />\' . $b;'),
                    $summary,
                    $this->partSummary($temp_part, true));
            }
        }

        return $summary;
    }

    /**
     * Return the URL to the view.php page.
     *
     * @access public
     *
     * @param object MIME_Part &$mime_part  The MIME_Part object to view.
     * @param integer $actionID             The ActionID to perform.
     * @param optional array $params        A list of any additional
     *                                      parameters that need to be passed
     *                                      to view.php. (key = name)
     * @param optional boolean $dload       Should we generate a download
     *                                      link?
     *
     * @return string  The URL to view.php.
     */
    function urlView(&$mime_part, $actionID, $params = array(), $dload = false)
    {
        /* Get the MIME ID for this part. */
        if (isset($params['id'])) {
            $id = $params['id'];
        } else {
            $id = $mime_part->getMIMEId();
        }

        /* Add the necessary local parameters. */
        $params['actionID'] = $actionID;
        $params['id'] = $id;
        $params = array_merge($params, $this->cacheIDURLParam());

        if ($dload) {
            $url = Horde::downloadUrl($mime_part->getName(true, true), $params);
        } else {
            $url = Util::addParameter(Horde::applicationUrl('view.php'), $params);
        }

        return $url;
    }

    /**
     * Generate a link to the view.php page.
     *
     * @access public
     *
     * @param object MIME_Part &$mime_part  The MIME_Part object to view.
     * @param integer $actionID             The actionID value.
     * @param string $text                  The link text.
     * @param optional array $params        A list of additional parameters.
     *   'class'       -  The CSS class to use.
     *   'jstext'      -  The JS text to use.
     *   'viewparams'  -  A list of any additional parameters that need to be
     *                    passed to view.php.
     * @param optional boolean $dload       Should we generate a download
     *                                      link?
     *
     * @return string  A HTML href link to view.php.
     */
    function linkView(&$mime_part, $actionID, $text, $params = array(),
                      $dload = false)
    {
        if (!isset($params['class'])) {
            $params['class'] = null;
        }
        if (!isset($params['jstext'])) {
            $params['jstext'] = $text;
        }
        if (!isset($params['viewparams'])) {
            $params['viewparams'] = array();
        }

        if ($dload) {
            $window = null;
        } else {
            $window = 'view_' . abs(crc32(microtime()));
        }

        return Horde::link($this->urlView($mime_part, $actionID, $params['viewparams'], $dload), $params['jstext'], $params['class'], $window) . $text . '</a>';
    }

    /**
     * Generate a javascript link to the view.php page.
     *
     * @access public
     *
     * @param object MIME_Part &$mime_part  The MIME_Part object to view.
     * @param integer $actionID             The ActionID to perform.
     * @param string $text                  The link text.
     * @param optional string $jstext       The Javascript link text.
     * @param optional string $css          The CSS class to use.
     * @param optional array $params        A list of any additional
     *                                      parameters that need to be passed
     *                                      to view.php. (key = name)
     *
     * @return string  A HTML href link to view.php.
     */
    function linkViewJS(&$mime_part, $actionID, $text, $jstext = null,
                        $css = null, $params = array())
    {
        /* If viewing via view.php, we don't want a JS link. */
        if ($this->viewAsAttachment()) {
            return $this->linkView($mime_part, $actionID, $text, $params);
        }

        if (empty($jstext)) {
            $jstext = sprintf(_("View %s"), $mime_part->getDescription(true, true));
        }
        $params['popup_view'] = 1;

        $url = $this->urlView($mime_part, $actionID, $params);

        if (!($id = $mime_part->getMIMEId())) {
            $id = abs(crc32(serialize($mime_part)));
        }

        return Horde::widget('', $jstext, $css, null, "view('" . $url . "', '" . $id . "'); return false;", $text);
    }

    /**
     * Prints out the status message for a given MIME Part.
     *
     * @access public
     *
     * @param string $msg              The message to output.
     * @param optional string $img     An image link to add to the beginning
     *                                 of the message.
     * @param optional boolean $print  Output this message when in a print
     *                                 view?
     *
     * @return string  The formatted status message string.
     */
    function formatStatusMsg($msg, $img = null, $printable = true)
    {
        $text = '';

        if (!is_array($msg)) {
            $msg = array($msg);
        }

        /* If we are viewing as an attachment, don't print italics. */
        if ($this->viewAsAttachment()) {
            return implode("\n", $msg);
        }

        $text = '<table style="padding: 1px; border: 1px dashed #00c; background-color: #eef; font-color: #006">';

        /* If no image, simply print out the message. */
        if (is_null($img)) {
            foreach ($msg as $val) {
                $text .= '<tr><td>' . $val . '</td></tr>' . "\n";
            }
        } else {
            $text .= '<tr><td valign="middle">' . $img . '&nbsp;</td>';
            $text .= '<td>';

            if (count($msg) == 1) {
                $text .= $msg[0];
            } else {
                $text .= '<table>';
                foreach ($msg as $val) {
                    $text .= '<tr><td>' . $val . '</td></tr>' . "\n";
                }
                $text .= '</table>';
            }
            $text .= '</td></tr>' . "\n";
        }

        $text .= '</table><div style="font-size: 1px;">&nbsp;<br /></div>';

        return $text;
    }

    /**
     * Return a pointer to the base object.
     *
     * @access public
     *
     * @return mixed  Returns a pointer to the base object.
     *                Returns false if there is no base object.
     */
    function &getBaseObjectPtr()
    {
        return (is_null($this->_base)) ? $this : $this->_base;
    }

    /**
     * Set the MIME_Contents:: object to be cached.
     *
     * @access private
     *
     * @param string  The cache OID.
     */
    function _addCache()
    {
        if (is_null($this->_sessionCacheID)) {
            $this->_sessionCacheID = $this->_createCacheID();
            register_shutdown_function(array(&$this, '_addCacheShutdown'));
        }

        return $this->_sessionCacheID;
    }

    /**
     * Creates a unique cache ID for this object.
     *
     * @access private
     *
     * @return string  A unique cache ID. 
     */
    function _createCacheID()
    {
        return md5(microtime());
    }

    /**
     * Saves a copy of the MIME_Contents object at the end of a request.
     *
     * @access private
     */
    function _addCacheShutdown()
    {
        require_once 'Horde/SessionObjects.php';
        $cache = &Horde_SessionObjects::singleton();

        /* Don't save the MIME_Viewer cached objects since there is no easy
           way to regenerate them on cache reload. */
        $this->_viewerCache = array();

        $cache->store($this->_sessionCacheID, $this);
    }

    /**
     * Returns the cached MIME_Contents:: object.
     * This function should be called statically e.g.:
     * $ptr = &MIME_Contents::getCache().
     *
     * @access public
     *
     * @param optional string $cacheid  The cache ID to use.  If empty, will
     *                                  use the cache ID located in the URL
     *                                  parameter named MIME_CONTENTS_CACHE.
     *
     * @return object MIME_Contents  Returns the MIME_Contents object, or
     *                               null if it does not exist.
     */
    function &getCache($cacheid = null)
    {
        if (is_null($cacheid)) {
            $cacheid = Util::getFormData(MIME_CONTENTS_CACHE);
        }

        require_once 'Horde/SessionObjects.php';
        $cache = &Horde_SessionObjects::singleton();
        return $ret = &$cache->query($cacheid);
    }

    /**
     * Add the current object to the cache, and return the cache identifier
     * to be used in URLs.
     *
     * @access public
     *
     * @return array  The parameter key/value set to use in URLs.
     */
    function cacheIDURLParam()
    {
        return array(MIME_CONTENTS_CACHE => $this->_addCache());
    }

}
