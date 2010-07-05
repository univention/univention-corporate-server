<?php
/**
 * The MIME_Viewer_ooo class renders out OpenOffice.org
 * documents in HTML format.
 *
 * $Horde: framework/MIME/MIME/Viewer/ooo.php,v 1.14.10.12 2009-01-06 15:23:21 jan Exp $
 *
 * Copyright 2003-2009 The Horde Project (http://www.horde.org/)
 *
 * See the enclosed file COPYING for license information (LGPL). If you
 * did not receive this file, see http://www.fsf.org/copyleft/lgpl.html.
 *
 * @author  Marko Djukic <marko@oblo.com>
 * @author  Jan Schneider <jan@horde.org>
 * @package Horde_MIME_Viewer
 */
class MIME_Viewer_ooo extends MIME_Viewer {

    /**
     * Render out the current data.
     *
     * @param array $params  Any parameters the Viewer may need.
     *
     * @return string  The rendered contents.
     */
    function render($params = array())
    {
        $use_xslt = Util::extensionExists('xslt') || function_exists('domxml_xslt_stylesheet_file');
        if ($use_xslt) {
            $tmpdir = Util::createTempDir(true);
        }

        require_once 'Horde/Compress.php';
        $xml_tags  = array('text:p', 'table:table ', 'table:table-row', 'table:table-cell', 'table:number-columns-spanned=');
        $html_tags = array('p', 'table border="0" cellspacing="1" cellpadding="0" ', 'tr bgcolor="#cccccc"', 'td', 'colspan=');
        $zip = &Horde_Compress::singleton('zip');
        $list = $zip->decompress($this->mime_part->getContents(),
            array('action' => HORDE_COMPRESS_ZIP_LIST));
        foreach ($list as $key => $file) {
            if ($file['name'] == 'content.xml' ||
                $file['name'] == 'styles.xml' ||
                $file['name'] == 'meta.xml') {
                $content = $zip->decompress($this->mime_part->getContents(),
                    array('action' => HORDE_COMPRESS_ZIP_DATA,
                          'info'   => $list,
                          'key'    => $key));
                if ($use_xslt) {
                    $fp = fopen($tmpdir . $file['name'], 'w');
                    fwrite($fp, $content);
                    fclose($fp);
                } elseif ($file['name'] == 'content.xml') {
                    $content = str_replace($xml_tags, $html_tags, $content);
                    return $content;
                }
            }
        }
        if (!Util::extensionExists('xslt')) {
            return;
        }

        if (function_exists('domxml_xslt_stylesheet_file')) {
            // Use DOMXML
            $xslt = domxml_xslt_stylesheet_file(dirname(__FILE__) . '/ooo/main_html.xsl');
            $dom  = domxml_open_file($tmpdir . 'content.xml');
            $result = @$xslt->process($dom, array('metaFileURL' => $tmpdir . 'meta.xml', 'stylesFileURL' => $tmpdir . 'styles.xml', 'disableJava' => true));
            return String::convertCharset($xslt->result_dump_mem($result), 'UTF-8', NLS::getCharset());
        } else {
            // Use XSLT
            $xslt = xslt_create();
            $result = @xslt_process($xslt, $tmpdir . 'content.xml',
                                    dirname(__FILE__) . '/ooo/main_html.xsl', null, null,
                                    array('metaFileURL' => $tmpdir . 'meta.xml', 'stylesFileURL' => $tmpdir . 'styles.xml', 'disableJava' => true));
            if (!$result) {
                $result = xslt_error($xslt);
            }
            xslt_free($xslt);
            return String::convertCharset($result, 'UTF-8', NLS::getCharset());
        }
    }

    /**
     * Return the MIME content type of the rendered content.
     *
     * @return string  The content type of the output.
     */
    function getType()
    {
        return 'text/html; charset=' . NLS::getCharset();
    }

}
