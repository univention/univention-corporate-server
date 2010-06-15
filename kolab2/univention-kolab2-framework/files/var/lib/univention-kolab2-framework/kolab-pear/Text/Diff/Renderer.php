<?php
/**
 * A class to render Diffs in different formats.
 *
 * This class renders the diff in classic diff format. It is intended
 * that this class be customized via inheritance, to obtain fancier
 * outputs.
 *
 * $Horde: framework/Text_Diff/Diff/Renderer.php,v 1.2 2004/01/09 21:46:30 chuck Exp $
 *
 * @package Text_Diff
 */
class Text_Diff_Renderer {

    /**
     * Number of leading context "lines" to preserve.
     *
     * This should be left at zero for this class, but subclasses
     * may want to set this to other values.
     */
    var $_leading_context_lines = 0;

    /**
     * Number of trailing context "lines" to preserve.
     *
     * This should be left at zero for this class, but subclasses
     * may want to set this to other values.
     */
    var $_trailing_context_lines = 0;

    /**
     * Render a diff.
     *
     * @param $diff object Text_Diff  A Text_Diff object.
     *
     * @return string  The formatted output.
     */
    function render($diff)
    {
        $xi = $yi = 1;
        $block = false;
        $context = array();

        $nlead = $this->_leading_context_lines;
        $ntrail = $this->_trailing_context_lines;

        $this->_startDiff();

        foreach ($diff->getDiff() as $edit) {
            if (is_a($edit, 'Text_Diff_Op_copy')) {
                if (is_array($block)) {
                    if (count($edit->orig) <= $nlead + $ntrail) {
                        $block[] = $edit;
                    } else {
                        if ($ntrail) {
                            $context = array_slice($edit->orig, 0, $ntrail);
                            $block[] = &new Text_Diff_Op_copy($context);
                        }
                        $this->_block($x0, $ntrail + $xi - $x0,
                                      $y0, $ntrail + $yi - $y0,
                                      $block);
                        $block = false;
                    }
                }
                $context = $edit->orig;
            } else {
                if (!is_array($block)) {
                    $context = array_slice($context, count($context) - $nlead);
                    $x0 = $xi - count($context);
                    $y0 = $yi - count($context);
                    $block = array();
                    if ($context) {
                        $block[] = &new Text_Diff_Op_copy($context);
                    }
                }
                $block[] = $edit;
            }

            if ($edit->orig) {
                $xi += count($edit->orig);
            }
            if ($edit->final) {
                $yi += count($edit->final);
            }
        }

        if (is_array($block)) {
            $this->_block($x0, $xi - $x0,
                          $y0, $yi - $y0,
                          $block);
        }

        return $this->_endDiff();
    }

    function _block($xbeg, $xlen, $ybeg, $ylen, &$edits)
    {
        $this->_startBlock($this->_blockHeader($xbeg, $xlen, $ybeg, $ylen));
        foreach ($edits as $edit) {
            switch (get_class($edit)) {
            case 'text_diff_op_copy':
                $this->_context($edit->orig);
                break;

            case 'text_diff_op_add':
                $this->_added($edit->final);
                break;

            case 'text_diff_op_delete':
                $this->_deleted($edit->orig);
                break;

            case 'text_diff_op_change':
                $this->_changed($edit->orig, $edit->final);
                break;

            default:
                trigger_error("Unknown edit type", E_USER_ERROR);
            }
            $this->_endBlock();
        }
    }

    function _startDiff()
    {
        ob_start();
    }

    function _endDiff()
    {
        $val = ob_get_contents();
        ob_end_clean();
        return $val;
    }

    function _blockHeader($xbeg, $xlen, $ybeg, $ylen)
    {
        if ($xlen > 1) {
            $xbeg .= ',' . ($xbeg + $xlen - 1);
        }
        if ($ylen > 1) {
            $ybeg .= ',' . ($ybeg + $ylen - 1);
        }

        return $xbeg . ($xlen ? ($ylen ? 'c' : 'd') : 'a') . $ybeg;
    }

    function _startBlock($header)
    {
        echo $header . "\n";
    }

    function _endBlock()
    {
    }

    function _lines($lines, $prefix = ' ')
    {
        foreach ($lines as $line) {
            echo "$prefix$line\n";
        }
    }

    function _context($lines)
    {
        $this->_lines($lines);
    }

    function _added($lines)
    {
        $this->_lines($lines, '>');
    }

    function _deleted($lines)
    {
        $this->_lines($lines, '<');
    }

    function _changed($orig, $final)
    {
        $this->_deleted($orig);
        echo "---\n";
        $this->_added($final);
    }

}
