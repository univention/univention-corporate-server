<?php

/**
 * The IMP_MIME_Viewer_pdf class enables generation of thumbnails for PDF
 * attachments.
 *
 * $Horde: imp/lib/MIME/Viewer/pdf.php,v 1.1.2.3 2009-01-06 15:24:09 jan Exp $
 *
 * Copyright 2008-2009 The Horde Project (http://www.horde.org/)
 *
 * See the enclosed file COPYING for license information (GPL). If you
 * did not receive this file, see http://www.fsf.org/copyleft/gpl.html.
 *
 * @author  Michael Slusarz <slusarz@horde.org>
 * @package Horde_MIME_Viewer
 */
class IMP_MIME_Viewer_pdf extends MIME_Viewer {

    /**
     * The content-type of the generated data.
     *
     * @var string
     */
    var $_contentType;

    /**
     * Render out the currently set contents.
     *
     * @param array $params  An array with a reference to a MIME_Contents
     *                       object.
     *
     * @return string  The rendered information.
     */
    function render($params)
    {
        /* Create the thumbnail and display. */
        if (Util::getFormData('images_view_thumbnail')) {
            $mime = $this->mime_part;
            $img = $this->_getHordeImageOb();

            if ($img) {
                $img->resize(96, 96, true);
                $type = $img->getContentType();
                $data = $img->raw(true);
            }

            if (!$img || !$data) {
                $type = 'image/png';
                $data = file_get_contents(IMP_BASE . '/themes/graphics/mini-error.png');
            }

            $mime->setType($type);
            $this->_contentType = $type;
            $mime->setContents($data);

            return $mime->getContents();
        }

        return parent::render($params);
    }

    /**
     * Render out attachment information.
     *
     * @param array $params  An array with a reference to a MIME_Contents
     *                       object.
     *
     * @return string  The rendered text in HTML.
     */
    function renderAttachmentInfo($params)
    {
        $contents = &$params[0];

        if (is_a($contents, 'IMP_Contents')) {
            $this->mime_part = &$contents->getDecodedMIMEPart($this->mime_part->getMIMEId(), true);
        }

        /* Check to see if convert utility is available. */
        if (!$this->_getHordeImageOb(false)) {
            return '';
        }

        $status = array(
            sprintf(_("A PDF file named %s is attached to this message. A thumbnail is below."),
                    $this->mime_part->getName(true)),
        );

        if (!$GLOBALS['browser']->hasFeature('javascript')) {
            $status[] = Horde::link($contents->urlView($this->mime_part,
                            'view_attach')) .
                        Horde::img($contents->urlView($this->mime_part,
                            'view_attach', array('images_view_thumbnail' => 1), false),
                            _("View Attachment"), null, '') . '</a>';
        } else {
            $status[] = $contents->linkViewJS($this->mime_part, 'view_attach',
                        Horde::img($contents->urlView($this->mime_part,
                            'view_attach', array('images_view_thumbnail' => 1),
                            false), _("View Attachment"), null, ''), null, null,
                            null);
        }

        return $contents->formatStatusMsg($status, Horde::img('mime/image.png',
                    _("Thumbnail of attached PDF file"), null, $GLOBALS['registry']->getImageDir('horde')), false);
    }

    /**
     * Return a Horde_Image object.
     *
     * @access private
     *
     * @param boolean $load  Whether to load the image data.
     *
     * @return Horde_Image  The requested object.
     */
    function _getHordeImageOb($load = true)
    {
        include_once 'Horde/Image.php';
        require_once HORDE_BASE . '/lib/version.php';

        // Need Horde 3.2.1+ because older versions could not correctly handle
        // multipage PDF data.
        if (!empty($GLOBALS['conf']['image']['convert']) &&
            (version_compare(HORDE_VERSION, '3.2.1') >= 0)) {
            $img = &Horde_Image::singleton('im', array('temp' => Horde::getTempdir()));
            if (is_a($img, 'PEAR_Error')) {
                return false;
            }
        } else {
            return false;
        }

        if ($load) {
            $ret = $img->loadString(1, $this->mime_part->getContents());
            if (is_a($ret, 'PEAR_Error')) {
                return false;
            }
        }

        return $img;
    }

    /**
     * Return the content-type
     *
     * @return string  The content-type of the output.
     */
    function getType()
    {
        return ($this->_contentType) ? $this->_contentType : parent::getType();
    }

}
