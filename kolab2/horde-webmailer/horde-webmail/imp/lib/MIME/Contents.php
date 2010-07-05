<?php
/**
 * @package Horde_MIME
 */

require_once 'Horde/MIME/Contents.php';
// TODO: for BC - Remove for Horde 4.0
if (is_callable(array('Horde', 'loadConfiguration'))) {
    $result = Horde::loadConfiguration('mime_drivers.php', array('mime_drivers', 'mime_drivers_map'), 'imp');
    if (!is_a($result, 'PEAR_Error')) {
        extract($result);
    }
} else {
    require IMP_BASE . '/config/mime_drivers.php';
}

/**
 * The IMP_Contents:: class extends the MIME_Contents:: class and contains
 * all functions related to handling the content and output of mail messages
 * in IMP.
 *
 * $Horde: imp/lib/MIME/Contents.php,v 1.153.4.61 2009-01-06 15:24:09 jan Exp $
 *
 * Copyright 2002-2009 The Horde Project (http://www.horde.org/)
 *
 * See the enclosed file COPYING for license information (GPL). If you
 * did not receive this file, see http://www.fsf.org/copyleft/gpl.html.
 *
 * @author  Michael Slusarz <slusarz@horde.org>
 * @package Horde_MIME
 */
class IMP_Contents extends MIME_Contents {

    /**
     * The text of the body of the message.
     *
     * @var string
     */
    var $_body = '';

    /**
     * The MIME part id of the message body.
     *
     * @todo Copied to MIME_Contents but kept here for BC.
     *
     * @var integer
     */
    var $_body_id;

    /**
     * The text of various MIME body parts.
     *
     * @var array
     */
    var $_bodypart = array();

    /**
     * The IMAP index of the message.
     *
     * @var integer
     */
    var $_index;

    /**
     * The mailbox of the current message.
     *
     * @var string
     */
    var $_mailbox;

    /**
     * Should attachment stripping links be generated?
     *
     * @var boolean
     */
    var $_strip = false;

    /**
     * List of all downloadable parts.
     *
     * @todo Copied to MIME_Contents but kept here for BC.
     *
     * @var array
     */
    var $_downloads = null;

    /**
     * Attempts to return a reference to a concrete IMP_Contents instance.
     * If an IMP_Contents object is currently stored in the local cache,
     * recreate that object.  Else, create a new instance.
     * Ensures that only one IMP_Contents instance for any given message is
     * available at any one time.
     *
     * This method must be invoked as:
     *   $imp_contents = &IMP_Contents::singleton($in);
     *
     * @param mixed $in  Either an index string (see IMP_Contents::singleton()
     *                   for the format) or a MIME_Message object.
     *
     * @return IMP_Contents  The IMP_Contents object or null.
     */
    function &singleton($in)
    {
        static $instance = array();

        $sig = IMP_Contents::_createCacheID($in);
        if (isset($instance[$sig])) {
            return $instance[$sig];
        }

        $instance[$sig] = &IMP_Contents::getCache($sig);

        // The returned instance might be a MIMP_Contents object.  If not in
        // MIMP context, then just create a new object instead.
        if (!empty($instance[$sig]) &&
            !is_subclass_of($instance[$sig], 'MIME_Contents')) {
            unset($instance[$sig]);
        }

        if (empty($instance[$sig])) {
            $instance[$sig] = new IMP_Contents($in);
            $message = $instance[$sig]->getMIMEMessage();
            if (is_a($message, 'PEAR_Error')) {
                return $message;
            }
        }

        return $instance[$sig];
    }

    /**
     * Constructor.
     *
     * @param mixed $in  Either an index string (see IMP_Contents::singleton()
     *                   for the format) or a MIME_Message object.
     */
    function IMP_Contents($in)
    {
        if (is_a($in, 'MIME_Message')) {
            $ob = $in;
            $in = null;
        } else {
            list($this->_index, $this->_mailbox) = explode(IMP_IDX_SEP, $in);

            /* Get the MIME_Structure object for the given index. */
            require_once IMP_BASE . '/lib/IMAP/MessageCache.php';
            $msg_cache = &IMP_MessageCache::singleton();
            $ret = $msg_cache->retrieve($this->_mailbox, array($this->_index), 8);
            if (!isset($ret[$this->_index]) || !isset($ret[$this->_index]->structure)) {
                $this->_message = PEAR::raiseError(_("Error displaying message."));
                return;
            }
            $ob = &Util::cloneObject($ret[$this->_index]->structure);
        }

        switch ($GLOBALS['prefs']->getValue('attachment_display')) {
        case 'list':
            $this->_displayType = MIME_CONTENTS_DISPLAY_TYPE_LIST;
            break;

        case 'inline':
            $this->_displayType = MIME_CONTENTS_DISPLAY_TYPE_INLINE;
            break;

        case 'both':
            $this->_displayType = MIME_CONTENTS_DISPLAY_TYPE_BOTH;
            break;
        }

        parent::MIME_Contents($ob, array('download' => 'download_attach', 'view' => 'view_attach'));
    }

    /**
     * Returns the entire body of the message.
     *
     * @return string  The text of the body of the message.
     */
    function getBody()
    {
        if (empty($this->_body)) {
            $imp_imap = &IMP_IMAP::singleton();
            $imp_imap->changeMbox($this->_mailbox, IMP_IMAP_AUTO);
            $this->_body = @imap_body($imp_imap->stream(), $this->_index, FT_UID | FT_PEEK);
        }

        return $this->_body;
    }

    /**
     * Gets the raw text for one section of the message.
     *
     * @param integer $id  The ID of the MIME_Part.
     *
     * @return string  The text of the part.
     */
    function getBodyPart($id)
    {
        if (!isset($this->_bodypart[$id])) {
            $imp_imap = &IMP_IMAP::singleton();
            $imp_imap->changeMbox($this->_mailbox, IMP_IMAP_AUTO);
            $this->_bodypart[$id] = imap_fetchbody($imp_imap->stream(), $this->_index, $id, FT_UID | FT_PEEK);
        }

        return isset($this->_bodypart[$id]) ? $this->_bodypart[$id] : '';
    }

    /**
     * Allow attachments to be stripped by providing a link in summary view?
     *
     * @param boolean $strip         Should the strip links be generated?
     * @param string $message_token  The message token to append to the strip
     *                               URL.
     */
    function setStripLink($strip = false, $message_token = null)
    {
        $this->_strip = $strip;
        $this->_message_token = $message_token;
    }

    /**
     * Returns an array summarizing a part of a MIME message.
     *
     * @param MIME_Part &$mime_part  See MIME_Contents::partSummary().
     * @param boolean $guess         See MIME_Contents::partSummary().
     *
     * @return array  See MIME_Contents::partSummary().
     *                Adds the following key to that return:
     *                [6] = Compressed Download Link
     *                [7] = Image Save link (if allowed)
     *                [8] = Strip Attachment Link (if allowed)
     */
    function partSummary(&$mime_part, $guess = false)
    {
        global $registry;

        $summary = parent::partSummary($mime_part, $guess);

        /* Don't add extra links if not requested or if this is a guessed
           part. */
        if ($guess || !$this->_links) {
            return $summary;
        }

        /* Display the compressed download link only if size is greater
           than 200 KB. */
        if (($mime_part->getBytes() > 204800) &&
            Util::extensionExists('zlib') &&
            ($mime_part->getType() != 'application/zip') &&
            ($mime_part->getType() != 'application/x-zip-compressed')) {
            $summary[] = $this->linkView($mime_part, 'download_attach', Horde::img('compressed.png', _("Download in .zip Format"), null, $registry->getImageDir('horde') . '/mime'), array('jstext' => sprintf(_("Download %s in .zip Format"), $mime_part->getDescription(true, true)), 'viewparams' => array('zip' => 1)), true);
        } else {
            $summary[] = null;
        }

        /* Display the image save link if the required registry calls are
         * present. */
        if (($mime_part->getPrimaryType() == 'image') &&
            $registry->hasMethod('images/selectGalleries') &&
            ($image_app = $registry->hasMethod('images/saveImage'))) {
            Horde::addScriptFile('prototype.js', 'imp', true);
            Horde::addScriptFile('popup.js', 'imp', true);
            $summary[] = Horde::link('#', _("Save Image in Gallery"), null, null, IMP::popupIMPString('saveimage.php', array('index' => ($this->_index . IMP_IDX_SEP . $this->_mailbox), 'id' => $mime_part->getMIMEId()), 450, 200) . "return false;") . '<img src="' . $registry->get('icon', $image_app) . '" alt="' . _("Save Image in Gallery") . '" title="' . _("Save Image in Gallery") . '" /></a>';
        } else {
            $summary[] = null;
        }

        /* Strip the Attachment? */
        if ($this->_strip &&
            !$mime_part->getInformation('rfc822_part')) {
            $url = Horde::selfUrl(true);
            $url = Util::removeParameter($url, array('actionID', 'imapid', 'index'));
            $url = Util::addParameter($url, array('actionID' => 'strip_attachment', 'imapid' => $this->_getMIMEKey($mime_part, false), 'index' => $this->_index, 'message_token' => $this->_message_token));
            $summary[] = Horde::link($url, _("Strip Attachment"), null, null, "return window.confirm('" . addslashes(_("Are you sure you wish to PERMANENTLY delete this attachment?")) . "');") . Horde::img('delete.png', _("Strip Attachment"), null, $registry->getImageDir('horde')) . '</a>';
        } else {
            $summary[] = null;
        }

        return $summary;
    }

    /**
     * Return the URL to the view.php page.
     *
     * @param MIME_Part &$mime_part  See MIME_Contents::urlView().
     * @param integer $actionID      See MIME_Contents::urlView().
     * @param array $params          See MIME_Contents::urlView().
     * @param boolean $dload         See MIME_Contents::urlView().
     * The following parameter names will be overwritten by this function:
     *   id, index, mailbox
     *
     * @return string  The URL to view.php.
     */
    function urlView(&$mime_part, $actionID, $params = array(), $dload = false)
    {
        /* Add the necessary local parameters. */
        $params = array_merge($params, IMP::getIMPMboxParameters($GLOBALS['imp_mbox']['mailbox'], $this->_index, $this->_mailbox));

        /* Should this be a download link? */
        $dload = (($actionID == 'download_attach') ||
                  ($actionID == 'download_render') ||
                  ($actionID == 'save_message'));

        return parent::urlView($mime_part, $actionID, $params, $dload);
    }

    /**
     * Generate a link to the view.php page.
     *
     * @param MIME_Part &$mime_part  See MIME_Contents::linkView().
     * @param integer $actionID      See MIME_Contents::linkView().
     * @param string $text           See MIME_Contents::linkView().
     * @param array $params          See MIME_Contents::linkView().
     *
     * @return string  See MIME_Contents::linkView().
     */
    function linkView(&$mime_part, $actionID, $text, $params = array())
    {
        if ($mime_part->getInformation('actionID')) {
            $actionID = $mime_part->getInformation('actionID');
        }

        /* If this is a 'download_attach or 'download_render' link, we do not
           want to show in a new window. */
        $dload = (($actionID == 'download_attach') ||
                  ($actionID == 'download_render'));

        /* If download attachment, add the 'thismailbox' param. */
        if ($actionID == 'download_attach') {
            $params['viewparams']['thismailbox'] = $this->_mailbox;
        }

        if ($mime_part->getInformation('viewparams')) {
            foreach ($mime_part->getInformation('viewparams') as $key => $val) {
                $params['viewparams'][$key] = $val;
            }
        }

        return parent::linkView($mime_part, $actionID, $text, $params, $dload);
    }

    /**
     * Returns the full message text.
     *
     * @return string  The full message text.
     */
    function fullMessageText()
    {
        $imp_headers = &$this->getHeaderOb();
        return $imp_headers->getHeaderText() . $this->getBody();
    }

    /**
     * Returns the header object.
     *
     * @return IMP_Headers  The IMP_Headers object.
     */
    function &getHeaderOb()
    {
        require_once IMP_BASE . '/lib/IMAP/MessageCache.php';
        $msg_cache = &IMP_MessageCache::singleton();
        $ret = $msg_cache->retrieve($this->_mailbox, array($this->_index), 32);
        $imp_headers = &Util::cloneObject($ret[$this->_index]->header);
        return $imp_headers;
    }

    /**
     * Returns the IMAP index for the current message.
     *
     * @return integer  The message index.
     */
    function getMessageIndex()
    {
        return $this->_index;
    }

    /**
     * Returns the IMAP mailbox for the current message.
     *
     * @since IMP 4.2.1
     *
     * @return string  The message mailbox.
     */
    function getMessageMailbox()
    {
        return $this->_mailbox;
    }

    /**
     * Rebuild the MIME_Part structure of a message from IMAP data.
     * This will store IMAP data in all parts of the message - for example,
     * all data for a multipart/mixed part will be stored in the base part,
     * and each part will contain its own data.  Note that if you want to
     * build a message string from the MIME_Part data after calling
     * rebuildMessage(), you should use IMP_Contents::toString() instead of
     * MIME_Part::toString().
     *
     * @return MIME_Message  A MIME_Message object with all of the body text
     *                       stored in the individual MIME_Parts.
     */
    function rebuildMessage()
    {
        $part = $this->_message->getBasePart();
        $this->_rebuildMessage($part);
        return $this->_message;
    }

    /**
     * Recursive function used to rebuild the MIME_Part structure of a
     * message.
     *
     * @access private
     *
     * @param MIME_Part $part  A MIME_Part object.
     */
    function _rebuildMessage($part)
    {
        $id = $part->getMIMEId();

        $mime_part = $this->getMIMEPart($id);
        $this->_setContents($mime_part, true);
        if ($this->_message->getPart($id) === $this->_message) {
            $this->_message = &$mime_part;
        } else {
            $this->_message->alterPart($id, $mime_part);
        }

        if ($part->getPrimaryType() == 'multipart') {
            /* Recursively process any subparts. */
            $parts = $part->getParts();
            while ($mime = array_shift($parts)) {
                $this->_rebuildMessage($mime);
            }
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
        $viewer = $this->getMIMEViewer($mime_part);
        if (!is_a($viewer, 'PEAR_Error') &&
            $viewer->getConfigParam('limit_inline_size') &&
            ($mime_part->getBytes() > $viewer->getConfigParam('limit_inline_size'))) {
            $text = $this->formatStatusMsg(array(_("This message part cannot be viewed because it is too large."), sprintf(_("Click %s to download the data."), $this->linkView($mime_part, 'download_attach', _("HERE")))));
        } else {
            $this->_setContents($mime_part);
            $text = parent::renderMIMEPart($mime_part);

            /* Convert textual emoticons into graphical ones - but only for
             * text parts. */
            if (($mime_part->getPrimaryType() == 'text') &&
                !$this->viewAsAttachment() &&
                $GLOBALS['prefs']->getValue('emoticons')) {
                require_once 'Horde/Text/Filter.php';
                $text = Text_Filter::filter($text, 'emoticons', array('entities' => true));
            }
        }

        return $text;
    }

    /**
     * Saves a copy of the MIME_Contents object at the end of a request.
     *
     * @access private
     */
    function _addCacheShutdown()
    {
        /* Don't cache bodypart data in the session. */
        $this->_bodypart = array();
        $this->_body = null;

        parent::_addCacheShutdown();
    }

    /**
     * Get the from address of the message.
     *
     * @return string  The from address of the message.
     */
    function getFromAddress()
    {
        $headers = &$this->getHeaderOb();
        return $headers->getFromAddress();
    }

    /**
     * Generate the list of MIME IDs to use for download all.
     *
     * @todo  Copied to MIME_Contents but kept here for BC.
     *
     * @return array  The list of MIME IDs that should be downloaded when
     *                downloading all attachments.
     */
    function getDownloadAllList()
    {
        if (is_array($this->_downloads)) {
            return $this->_downloads;
        }

        $this->_downloads = array();
        $bodyid = $this->findBody();

        /* Here is what we consider 'downloadable':
         * All parts not 'multipart/*' and 'message/*' except for
         *  'message/rfc822'
         * All parts that are not PGP or S/MIME signature information
         * NOT the body part (if one exists)
         * Parts that are either marked a 'attachment' or have a filename. */
        foreach ($this->_message->contentTypeMap() as $key => $val) {
            if ($key === $bodyid) {
                continue;
            }

            $mime_part = $this->getMIMEPart($key);

            if (strpos($val, 'message/') === 0) {
                if (strpos($val, 'message/rfc822') === 0) {
                    $this->_downloads[] = $key;
                }
            } elseif ((($mime_part->getDisposition() == 'attachment') ||
                       $mime_part->getContentTypeParameter('name')) &&
                      (strpos($val, 'multipart/') === false) &&
                      (strpos($val, 'application/x-pkcs7-signature') === false) &&
                      (strpos($val, 'application/pkcs7-signature') === false)) {
                $this->_downloads[] = $key;
            }
        }

        return $this->_downloads;
    }

    /**
     * Generate a download all link, if possible.
     *
     * @return string  The download link.
     */
    function getDownloadAllLink()
    {
        $url = null;

        $downloads_list = $this->getDownloadAllList();
        if (!empty($downloads_list)) {
            /* Create a dummy variable to pass to urlView() since we don't
               have a MIME_Part and we can't pass null by reference. */
            $dummy = 0;
            $url = $this->urlView($dummy, 'download_all', array('id' => 1));
            $url = Util::removeParameter($url, array('id'));
        }

        return $url;
    }

    /**
     * Processes a MIME_Part and stores the display information in the internal
     * class variables.
     *
     * @param MIME_Part &$mime_part  The MIME_Part object to process.
     *
     * @return string  The rendered text.
     */
    function buildMessagePart(&$mime_part)
    {
        $key = $this->_getMIMEKey($mime_part);
        $attachmentList = in_array($key, $this->getDownloadAllList());

        /* If we can't display the part inline, add it to the attachment
           list. If the MIME ID of the current part is '0', then force a
           render of the part (since it is the base part and, without
           attempting to render, the message will ALWAYS appear empty. */
        if (!$this->canDisplayInline($mime_part) &&
            ($mime_part->getMIMEId() != 0)) {
            /* Not displaying inline; add to the attachments list. */
            if ($attachmentList) {
                if (($this->_displayType == MIME_CONTENTS_DISPLAY_TYPE_LIST) ||
                    ($this->_displayType == MIME_CONTENTS_DISPLAY_TYPE_BOTH)) {
                    $this->setSummary($mime_part, 'attachment');
                }
                if (($this->_displayType == MIME_CONTENTS_DISPLAY_TYPE_INLINE) ||
                    ($this->_displayType == MIME_CONTENTS_DISPLAY_TYPE_BOTH)) {
                    $this->setSummary($mime_part, 'part');
                }
            }

            /* Check to see if any attachment information can be rendered by
               the MIME_Viewer. */
            $msg = $this->renderMIMEAttachmentInfo($mime_part);
            if (!empty($msg)) {
                $this->_parts[$key] = $msg;
            }
        } else {
            $msg = $this->renderMIMEPart($mime_part);
            if (!$this->_attach822) {
                $this->_parts[$key] = $msg;
            }

            /* Some MIME_Viewers set the summary by themelves, so only
             * add to attachment/inline lists if nothing has been set
             * as of yet. */
            $bodyid = $this->findBody();
            if ((($mime_part->getType() != 'multipart/mixed') ||
                 !empty($msg)) &&
                ($key !== false) &&
                !$this->getIndex($key, 'summary') &&
                (($this->_displayType == MIME_CONTENTS_DISPLAY_TYPE_LIST) ||
                 ($this->_displayType == MIME_CONTENTS_DISPLAY_TYPE_BOTH))) {

                if ($attachmentList) {
                    /* TODO: Remove this check for Horde 4.0. */
                    if ($mime_part->getType() != 'multipart/alternative') {
                        $this->setSummary($mime_part, 'attachment');
                    }
                } elseif (($bodyid !== null) && ($key != $bodyid)) {
                    $this->setSummary($mime_part, 'part');
                }
            } elseif (($mime_part->getType() == 'multipart/mixed') &&
                      empty($msg) &&
                      !is_null($bodyid)) {
                // See Bug 5157
                $this->setSummary($this->_message->getPart($bodyid), 'part');
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

            $parts = $mime_part->getParts();
            while ($part = array_shift($parts)) {
                $msg .= $this->buildMessagePart($part);
            }

            if ($increment_822) {
                $this->_attach822--;
            }
        }

        return $msg;
    }

    /**
     * Prints out the status message for a given MIME Part.
     *
     * @param mixed $msg      See MIME_Contents::formatStatusMsg().
     * @param string $img     See MIME_Contents::formatStatusMsg().
     * @param boolean $print  Output this message when in a print view?
     *
     * @return string  The formatted status message.
     */
    function formatStatusMsg($msg, $img = null, $printable = true)
    {
        if (!$printable && IMP::printMode()) {
            return '';
        } else {
            return parent::formatStatusMsg($msg, $img);
        }
    }

    /**
     * Finds the main "body" text part (if any) in a message.
     * "Body" data is the first text part in the base MIME part.
     *
     * @todo  Copied to MIME_Contents but kept here for BC.
     *
     * @param string $subtype  Specifically search for this subtype.
     *
     * @return string  The MIME ID of the main "body" part.
     */
    function findBody($subtype = null)
    {
        if (isset($this->_body_id) && ($subtype === null)) {
            return $this->_body_id;
        }

        /* Look for potential body parts. */
        $part = $this->_message->getBasePart();
        $primary_type = $part->getPrimaryType();
        if (($primary_type == MIME::type(TYPEMULTIPART)) ||
            ($primary_type == MIME::type(TYPETEXT))) {
            $body_id = $this->_findBody($part, $subtype);
            if ($subtype !== null) {
                $this->_body_id = $body_id;
            }
            return $body_id;
        }

        return null;
    }

    /**
     * Processes a MIME Part and looks for "body" data.
     *
     * @todo  Copied to MIME_Contents but kept here for BC.
     *
     * @access private
     *
     * @return string  The MIME ID of the main "body" part.
     */
    function _findBody($mime_part, $subtype)
    {
        if (intval($mime_part->getMIMEId()) < 2 ||
            $mime_part->getInformation('alternative') === 0) {
            if ($mime_part->getPrimaryType() == MIME::type(TYPEMULTIPART)) {
                $parts = $mime_part->getParts();
                while ($part = array_shift($parts)) {
                    if (($partid = $this->_findBody($part, $subtype))) {
                        return $partid;
                    }
                }
            } elseif ($mime_part->getPrimaryType() == MIME::type(TYPETEXT)) {
                if ($mime_part->getDisposition() != 'attachment' &&
                    (($subtype === null) ||
                     ($subtype == $mime_part->getSubType())) &&
                    ($mime_part->getBytes() ||
                     $this->getBodyPart($mime_part->getMIMEId()))) {
                    return $mime_part->getMIMEId();
                }
            }
        }

        return null;
    }

    /**
     * Creates a unique cache ID for this object.
     *
     * @access private
     *
     * @param mixed $in  Either an index string (see IMP_Contents::singleton()
     *                   for the format) or a MIME_Message object.
     *
     * @return string  A unique cache ID.
     */
    function _createCacheID($in = null)
    {
        if ($in === null) {
            if (isset($this)) {
                $in = $this->_index . IMP_IDX_SEP . $this->_mailbox;
            } else {
                return parent::_createCacheID();
            }
        }
        return md5(serialize($in) . Auth::getAuth());
    }

    /**
     * Make sure the contents of the current part are set from IMAP server
     * data.
     *
     * @access private
     * @since IMP 4.1
     *
     * @param MIME_Part &$mime_part  The MIME_Part object to work with.
     * @param boolean $all           Download the entire parts contents?
     */
    function _setContents(&$mime_part, $all = false)
    {
        if (!$mime_part->getInformation('imp_contents_set') &&
            !$mime_part->getContents()) {
            $id = $mime_part->getMIMEId();
            if ($all && ($mime_part->getType() == 'message/rfc822')) {
                $id = substr($mime_part->getMIMEId(), 0, -2);
            }
            $contents = $this->getBodyPart($id);
            if (($mime_part->getPrimaryType() == 'text') &&
                (String::upper($mime_part->getCharset()) == 'US-ASCII') &&
                MIME::is8bit($contents)) {
                $contents = String::convertCharset($contents, 'US-ASCII');
            }
            $mime_part->setContents($contents);
        }
        $mime_part->setInformation('imp_contents_set', true);
    }

    /**
     * Fetch part of a MIME message.
     *
     * @since IMP 4.1
     *
     * @param integer $id   The MIME ID of the part requested.
     * @param boolean $all  If this is a header part, should we return all text
     *                      in the body?
     *
     * @return MIME_Part  The MIME_Part.
     */
    function &getRawMIMEPart($id, $all = false)
    {
        $mime_part = $this->getMIMEPart($id);
        if (!is_a($mime_part, 'MIME_Part')) {
            $mime_part = null;
            return $mime_part;
        }
        $this->_setContents($mime_part, true);
        return $mime_part;
    }

    /**
     * Create a message string from a MIME message that has used
     * rebuildMessage() to build the data from the IMAP server.
     *
     * @since IMP 4.1
     *
     * @param MIME_Message $message  A MIME_Message object.
     * @param boolean $canonical     Return a canonical string?
     *
     * @return string  The contents of the MIME_Message object.
     */
    function toString($message, $canonical = false)
    {
        $text = '';

        $part = $message->getBasePart();
        foreach ($part->contentTypeMap() as $key => $val) {
            if (($key != 0) && (strpos($val, 'multipart/') === 0)) {
                $old = $part->getPart($key);
                $old->setContents('');
                $part->alterPart($key, $old);
            }
        }

        if ($message->getMIMEId() == 0) {
            $part->setContents('');
        }

        return ($canonical) ? $part->toCanonicalString() : $part->toString();
    }

    /**
     * Remove all attachment entries for the given part.
     * TODO: This is a total hack to tide us over to Horde 4.0.
     *
     * @since IMP 4.2
     *
     * @param string $index  The index to remove from the attachment list.
     */
    function removeAtcEntry($index)
    {
        $index = strval($index);
        foreach (array_keys($this->_atc) as $val) {
            if ((strpos($val, $index) === 0) && ($val != $index . '.0')) {
                unset($this->_atc[$val]);
            }
        }
    }

    /**
     * Return the attachment count.
     *
     * @since IMP 4.2
     *
     * @param return array  The attachment count.
     */
    function attachmentCount()
    {
        return count($this->_atc);
    }

}
