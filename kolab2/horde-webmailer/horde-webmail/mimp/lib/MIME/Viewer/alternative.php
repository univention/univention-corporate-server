<?php
/**
 * The MIMP_MIME_Viewer_alternative class renders out messages
 * multipart/alternative content types.
 *
 * $Horde: mimp/lib/MIME/Viewer/alternative.php,v 1.17.2.4 2009-01-06 15:24:54 jan Exp $
 *
 * Copyright 2002-2009 The Horde Project (http://www.horde.org/)
 *
 * See the enclosed file COPYING for license information (GPL). If you
 * did not receive this file, see http://www.fsf.org/copyleft/gpl.html.
 *
 * @author  Michael Slusarz <slusarz@horde.org>
 * @package Horde_MIME_Viewer
 */
class MIMP_MIME_Viewer_alternative extends MIME_Viewer {

    /**
     * The content-type of the preferred part.
     * Default: application/octet-stream
     *
     * @var string
     */
    var $_contentType = 'application/octet-stream';

    /**
     * The alternative ID for this part.
     *
     * @var string
     */
    var $_altID = '-';

    /**
     * Render out the currently set contents.
     *
     * The $mime_part class variable has the information to render
     * out, encapsulated in a MIME_Part object.
     */
    function render($params)
    {
        $contents = &$params[0];

        /* Default: Nothing displayed. */
        $display = null;
        $display_id = null;
        $partList = $this->mime_part->getParts();

        /* Default: Nothing displayed. */
        $text = _("There are no alternative parts that can be displayed inline.");

        /* We need to override the MIME key to ensure that only one
         * alternative part is displayed. */
        $this->_getAltID($contents, $partList);

        /* Now we need to remove any multipart/mixed entries that may be
         * present in the parts list, since they are simple containers
         * for parts. */
        $partList = $this->_removeMultipartMixed($partList);

        /* RFC 2046: We show the LAST choice that can be displayed inline. */
        foreach ($partList as $part) {
            if ($contents->canDisplayInline($part)) {
                $display_list[] = $part;
            }
        }

        if (!empty($display_list)) {
            while (!empty($display_list)) {
                $display = array_pop($display_list);
                $text = $contents->renderMIMEPart($display);
                if (!empty($text)) {
                    $this->_contentType = $display->getType();
                    $display_id = $display->getMIMEId();
                    break;
                }
            }
        }

        /* No longer force the alternative MIME ID for MIMP_Contents methods. */
        if (!empty($this->_altID)) {
            $contents->setMIMEKeyOverride();
        }

        return $text;
     }

    /**
     * Determine the alternative ID
     *
     * @access private
     *
     * @param MIME_Contents &$contents  A MIME_Contents object.
     * @param array &$partList          The list of parts in this alternative
     *                                  section.
     */
    function _getAltID(&$contents, &$partList)
    {
        $altID = null;
        $override = $contents->getMIMEKeyOverride();

        if ($override === null) {
            $altID = $this->mime_part->getInformation('alternative');
            if ($altID === false) {
                foreach ($partList as $part) {
                    $altID = $part->getInformation('alternative');
                    if ($altID !== false) {
                        break;
                    }
                }
            }
        }

        if ($altID !== false) {
            $contents->setMIMEKeyOverride($altID);
            $this->_altID = $altID;
        }
    }

    /**
     * Remove multipart/mixed entries from an array of MIME_Parts and
     * replace with the contents of that part.
     *
     * @access private
     *
     * @param array $list  A list of MIME_Part objects.
     *
     * @return array  The list of objects with multipart/mixed parts removed.
     */
    function _removeMultipartMixed($list)
    {
        $output = array();

        foreach ($list as $part) {
            $output = array_merge($output, ($part->getType() == 'multipart/mixed') ? $this->_removeMultipartMixed($part->getParts()) : array($part));
        }

        return $output;
    }

    /**
     * Return the content-type.
     *
     * @return string  The content-type of the message.
     *                 Returns 'application/octet-stream' until actual
     *                 content type of the message can be determined.
     */
    function getType()
    {
        return $this->_contentType;
    }

}
