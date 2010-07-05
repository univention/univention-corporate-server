<?php

require_once 'Horde/MIME/Viewer/tnef.php';

/**
 * The IMP_MIME_Viewer_tnef class allows MS-TNEF attachments to be displayed.
 *
 * $Horde: imp/lib/MIME/Viewer/tnef.php,v 1.25.10.13 2009-01-06 15:24:09 jan Exp $
 *
 * Copyright 2002-2009 The Horde Project (http://www.horde.org/)
 *
 * See the enclosed file COPYING for license information (GPL). If you
 * did not receive this file, see http://www.fsf.org/copyleft/gpl.html.
 *
 * @author  Michael Slusarz <slusarz@horde.org>
 * @package Horde_MIME_Viewer
 */
class IMP_MIME_Viewer_tnef extends MIME_Viewer_tnef {

    /**
     * The contentType of the attachment.
     *
     * @var string
     */
    var $_contentType = 'application/octet-stream';

    /**
     * Render out the currently set contents.
     *
     * @param array $params  An array with a reference to a MIME_Contents
     *                       object.
     *
     * @return string  Either the list of tnef files or the data of an
     *                 individual tnef file.
     */
    function render($params)
    {
        $contents = &$params[0];

        $text = '';

        /* Get the data from the attachment. */
        $tnefData = $this->_getSubparts();

        /* Display the requested file. Its position in the $tnefData
           array can be found in 'tnef_attachment'. */
        if (Util::getFormData('tnef_attachment')) {
            $tnefKey = Util::getFormData('tnef_attachment') - 1;
            /* Verify that the requested file exists. */
            if (isset($tnefData[$tnefKey])) {
                $text = $tnefData[$tnefKey]['stream'];
                if (empty($text)) {
                    $text = $contents->formatStatusMsg(_("Could not extract the requested file from the MS-TNEF attachment."));
                } else {
                    $this->mime_part->setName($tnefData[$tnefKey]['name']);
                    $this->mime_part->setType($tnefData[$tnefKey]['type'] . '/' . $tnefData[$tnefKey]['subtype']);
                }
            } else {
                $text = $contents->formatStatusMsg(_("The requested file does not exist in the MS-TNEF attachment."));
            }
        } else {
            $text = $this->renderAttachmentInfo(array($params[0]));
        }

        return $text;
    }

    /**
     * Render out TNEF attachment information.
     *
     * @param array $params  An array with a reference to a MIME_Contents
     *                       object.
     *
     * @return string  The rendered text in HTML.
     */
    function renderAttachmentInfo($params)
    {
        $contents = &$params[0];

        $text = '';

        /* Make sure the contents are in the MIME_Part object. */
        if (!$this->mime_part->getContents()) {
            $this->mime_part->setContents($contents->getBodyPart($this->mime_part->getMIMEId()));
        }

        /* Get the data from the attachment. */
        $tnefData = $this->_getSubparts();

        if (!count($tnefData)) {
            $text = $contents->formatStatusMsg(_("No attachments found."));
        } else {
            $text = $contents->formatStatusMsg(_("The following files were attached to this part:")) . '<br />';
            foreach ($tnefData as $key => $data) {
                $temp_part = $this->mime_part;
                $temp_part->setName($data['name']);
                $temp_part->setDescription($data['name']);

                /* Short-circuit MIME-type guessing for winmail.dat parts;
                   we're showing enough entries for them already. */
                require_once 'Horde/MIME/Magic.php';
                $type = $data['type'] . '/' . $data['subtype'];
                if (($type == 'application/octet-stream') ||
                    ($type == 'application/base64')) {
                    $type = MIME_Magic::filenameToMIME($data['name']);
                }
                $temp_part->setType($type);

                $link = $contents->linkView($temp_part, 'view_attach', htmlspecialchars($data['name']), array('jstext' => sprintf(_("View %s"), $data['name']), 'viewparams' => array('tnef_attachment' => ($key + 1))));
                $text .= _("Attached File:") . '&nbsp;&nbsp;' . $link . '&nbsp;&nbsp;(' . $data['type'] . '/' . $data['subtype'] . ")<br />\n";
            }
        }

        return $text;
    }

    /**
     * List any embedded attachments in the TNEF part.
     *
     * @access private
     *
     * @return array  An array of any embedded attachments.
     */
    function _getSubparts()
    {
        require_once 'Horde/Compress.php';
        $tnef = &Horde_Compress::singleton('tnef');
        return $tnef->decompress($this->mime_part->transferDecode());
    }

    /**
     * Return the content-type.
     *
     * @return string  The content-type of the output.
     */
    function getType()
    {
        if (Util::getFormData('tnef_attachment')) {
            return $this->_contentType;
        } else {
            return 'text/html; charset=' . NLS::getCharset();
        }
    }

}
