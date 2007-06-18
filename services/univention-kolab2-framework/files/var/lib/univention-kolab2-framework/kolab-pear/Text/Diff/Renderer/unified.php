<?php
/**
 * "Unified" diff renderer.
 *
 * This class renders the diff in classic "unified diff" format.
 *
 * $Horde: framework/Text_Diff/Diff/Renderer/unified.php,v 1.2 2004/01/09 21:46:30 chuck Exp $
 *
 * @package Text_Diff
 */
class Text_Diff_Renderer_unified extends Text_Diff_Renderer {

    function Text_Diff_Renderer_unified($context_lines = 4)
    {
        $this->_leading_context_lines = $context_lines;
        $this->_trailing_context_lines = $context_lines;
    }

    function _blockHeader($xbeg, $xlen, $ybeg, $ylen)
    {
        if ($xlen != 1) {
            $xbeg .= ',' . $xlen;
        }
        if ($ylen != 1) {
            $ybeg .= ',' . $ylen;
        }
        return "@@ -$xbeg +$ybeg @@";
    }

    function _added($lines)
    {
        $this->_lines($lines, '+');
    }

    function _deleted($lines)
    {
        $this->_lines($lines, '-');
    }

    function _changed($orig, $final)
    {
        $this->_deleted($orig);
        $this->_added($final);
    }

}
