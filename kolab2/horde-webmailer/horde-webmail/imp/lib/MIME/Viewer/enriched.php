<?php

require_once 'Horde/MIME/Viewer/enriched.php';

/**
 * The IMP_MIME_Viewer_enriched class renders out plain text from
 * enriched content tags, ala RFC 1896
 *
 * $Horde: imp/lib/MIME/Viewer/enriched.php,v 1.33.10.10 2009-01-06 15:24:09 jan Exp $
 *
 * Copyright 2001-2009 The Horde Project (http://www.horde.org/)
 *
 * See the enclosed file COPYING for license information (GPL). If you
 * did not receive this file, see http://www.fsf.org/copyleft/gpl.html.
 *
 * @author  Eric Rostetter <eric.rostetter@physics.utexas.edu>
 * @package Horde_MIME_Viewer
 */
class IMP_MIME_Viewer_enriched extends MIME_Viewer_enriched {

    /**
     * Render out the currently set contents.
     *
     * @param array $params  An array with a reference to a MIME_Contents
     *                       object.
     *
     * @return string  The rendered text in HTML.
     */
    function render($params)
    {
        $contents = &$params[0];

        global $prefs;

        if (($text = $this->mime_part->getContents()) === false) {
            return $contents->formatPartError(_("There was an error displaying this message part"));
        }

        if (trim($text) == '') {
            return $text;
        }

        $text = parent::render();

        // Highlight quoted parts of an email.
        if ($prefs->getValue('highlight_text')) {
            $text = implode("\n", preg_replace('|^(\s*&gt;.+)$|', '<span class="quoted1">\1</span>', explode("\n", $text)));
            $indent = 1;
            while (preg_match('|&gt;(\s?&gt;){' . $indent . '}|', $text)) {
                $text = implode("\n", preg_replace('|^<span class="quoted' . ((($indent - 1) % 5) + 1) . '">(\s*&gt;(\s?&gt;){' . $indent . '}.+)$|', '<span class="quoted' . (($indent % 5) + 1) . '">\1', explode("\n", $text)));
                $indent++;
            }
        }

        // Dim signatures.
        if ($prefs->getValue('dim_signature')) {
            $parts = preg_split('|(\n--\s*\n)|', $text, 2, PREG_SPLIT_DELIM_CAPTURE);
            $text = array_shift($parts);
            if (count($parts)) {
                $text .= '<span class="signature">' . $parts[0] .
                    preg_replace('|class="[^"]+"|', 'class="signature-fixed"', $parts[1]) .
                    '</span>';
            }
        }

        // Filter bad language.
        $text = IMP::filterText($text);

        return $text;
    }

}
