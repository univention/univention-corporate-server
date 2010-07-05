<?php

require_once dirname(__FILE__) . '/source.php';

/**
 * The MIME_Viewer_php class renders out syntax-highlighted PHP code
 * in HTML format.
 *
 * $Horde: framework/MIME/MIME/Viewer/php.php,v 1.22.10.13 2009-01-06 15:23:21 jan Exp $
 *
 * Copyright 1999-2009 The Horde Project (http://www.horde.org/)
 *
 * See the enclosed file COPYING for license information (LGPL). If you
 * did not receive this file, see http://www.fsf.org/copyleft/lgpl.html.
 *
 * @author  Chuck Hagenbuch <chuck@horde.org>
 * @package Horde_MIME_Viewer
 */
class MIME_Viewer_php extends MIME_Viewer_source {

    /**
     * Renders out the contents.
     *
     * @param array $params  Any parameters the Viewer may need.
     *
     * @return string  The rendered contents.
     */
    function render($params = array())
    {
        ini_set('highlight.comment', 'comment');
        ini_set('highlight.default', 'default');
        ini_set('highlight.keyword', 'keyword');
        ini_set('highlight.string', 'string');
        ini_set('highlight.html', 'html');

        $code = $this->mime_part->getContents();
        if (strpos($code, '<?php') === false) {
            $results = $this->lineNumber(str_replace('&lt;?php&nbsp;', '', highlight_string('<?php ' . $code, true)));
        } else {
            $results = $this->lineNumber(highlight_string($code, true));
        }

        // Educated guess at whether we are inline or not.
        if (headers_sent() || ob_get_length()) {
            return $results;
        } else {
            return Util::bufferOutput('require', $GLOBALS['registry']->get('templates', 'horde') . '/common-header.inc')
                . $results
                . Util::bufferOutput('require', $GLOBALS['registry']->get('templates', 'horde') . '/common-footer.inc');
        }
    }

    /**
     * Add line numbers to a block of code.
     *
     * @param string $code  The code to number.
     */
    function lineNumber($code, $linebreak = "\n")
    {
        // Clean up.
        $code = preg_replace(array('/<code><span style="color: #?\w+">\s*/',
                                   '/<code><font color="#?\w+">\s*/',
                                   '/\s*<\/span>\s*<\/span>\s*<\/code>/',
                                   '/\s*<\/font>\s*<\/font>\s*<\/code>/'),
                             '',
                             $code);
        $code = str_replace(array('&nbsp;',
                                  '&amp;',
                                  '<br />',
                                  '<span style="color: ',
                                  '<font color="',
                                  '</font>',
                            ),
                            array(' ',
                                  '&#38;',
                                  "\n",
                                  '<span class="',
                                  '<span class="',
                                  '</span>',
                            ),
                            $code);
        $code = trim($code);

        // Normalize newlines.
        $code = str_replace("\r", '', $code);
        $code = preg_replace('/\n\n\n+/', "\n\n", $code);

        $lines = explode("\n", $code);

        $results = array('<ol class="code-listing striped">');
        $previous = false;
        foreach ($lines as $lineno => $line) {
            if (substr($line, 0, 7) == '</span>') {
                $previous = false;
                $line = substr($line, 7);
            }

            if (empty($line)) {
                $line = '&#160;';
            }

            if ($previous) {
                $line = "<span class=\"$previous\">" . $line;
            }

            // Save the previous style.
            if (strpos($line, '<span') !== false) {
                switch (substr($line, strrpos($line, '<span') + 13, 1)) {
                case 'c':
                    $previous = 'comment';
                    break;

                case 'd':
                    $previous = 'default';
                    break;

                case 'k':
                    $previous = 'keyword';
                    break;

                case 's':
                    $previous = 'string';
                    break;
                }
            }

            // Unset previous style unless the span continues.
            if (substr($line, -7) == '</span>') {
                $previous = false;
            } elseif ($previous) {
                $line .= '</span>';
            }

            $results[] = '<li id="l' . ($lineno + 1). '">' . $line . '</li>';
        }

        $results[] = '</ol>';
        return implode("\n", $results);
    }

}
