<?php

/* Disable block if not configured. */
if (isset($GLOBALS['conf']['fortune']['exec_path']) &&
    is_executable($GLOBALS['conf']['fortune']['exec_path'])) {
    $block_name = _("Random Fortune");
}

/**
 * $Horde: horde/lib/Block/fortune.php,v 1.14.10.4 2007-12-20 15:01:35 jan Exp $
 *
 * @package Horde_Block
 */
class Horde_Block_Horde_fortune extends Horde_Block {

    /**
     * Whether this block has changing content.
     */
    var $updateable = true;

    var $_app = 'horde';

    /**
     * The title to go in this block.
     *
     * @return string   The title text.
     */
    function _title()
    {
        return _("Fortune");
    }

    function _params()
    {
        global $conf;

        $descriptions = array('art' => _("Art"),
                              'ascii-art' => _("Ascii Art"),
                              'bofh-excuses' => _("BOFH Excuses"),
                              'computers' => _("Computers"),
                              'cookie' => _("Cookie"),
                              'definitions' => _("Definitions"),
                              'drugs' => _("Drugs"),
                              'education' => _("Education"),
                              'ethnic' => _("Ethnic"),
                              'food' => _("Food"),
                              'fortunes' => _("Fortunes"),
                              'fortunes2' => _("Fortunes 2"),
                              'goedel' => _("Goedel"),
                              'humorists' => _("Humorists"),
                              'kernelnewbies' => _("Kernel Newbies"),
                              'kids' => _("Kids"),
                              'law' => _("Law"),
                              'limerick' => _("Limerick"),
                              'linuxcookie' => _("Linux Cookie"),
                              'literature' => _("Literature"),
                              'love' => _("Love"),
                              'magic' => _("Magic"),
                              'medicine' => _("Medicine"),
                              'miscellaneous' => _("Miscellaneous"),
                              'news' => _("News"),
                              'osfortune' => _("Operating System"),
                              'people' => _("People"),
                              'pets' => _("Pets"),
                              'platitudes' => _("Platitudes"),
                              'politics' => _("Politics"),
                              'riddles' => _("Riddles"),
                              'science' => _("Science"),
                              'songs-poems' => _("Songs & Poems"),
                              'sports' => _("Sports"),
                              'startrek' => _("Star Trek"),
                              'translate-me' => _("Translations"),
                              'wisdom' => _("Wisdom"),
                              'work' => _("Work"),
                              'zippy' => _("Zippy"));

        $values = null;
        if (isset($conf['fortune']['exec_path']) &&
            is_executable($conf['fortune']['exec_path'])) {
            exec($conf['fortune']['exec_path'] . ' -f 2>&1', $output, $status);
            if (!$status) {
                for ($i = 1; $i < count($output); $i++) {
                    $fortune = substr($output[$i], strrpos($output[$i], ' ') + 1);
                    if (isset($descriptions[$fortune])) {
                        $values[$fortune] = $descriptions[$fortune];
                    } else {
                        $values[$fortune] = $fortune;
                    }
                }
            }
        }
        if (is_null($values)) {
            $values = $descriptions;
        }
        asort($values);
        $values = array_merge(array('' => _("All")), $values);

        return array(
            'offend' => array(
                'type' => 'enum',
                'name' => _("Offense filter"),
                'default' => '',
                'values' => array('' => _("No offensive fortunes"),
                                 ' -o' => _("Only offensive fortunes"),
                                 ' -a' => _("Both"))),
            'fortune' => array(
                'type' => 'multienum',
                'name' => _("Fortune type"),
                'default' => array(''),
                'values' => $values));
    }

    /**
     * The content to go in this block.
     *
     * @return string   The content
     */
    function _content()
    {
        global $conf;

        require_once 'Horde/Text/Filter.php';

        if (isset($conf['fortune']['exec_path']) &&
            is_executable($conf['fortune']['exec_path'])) {
            $cmdLine = $conf['fortune']['exec_path']
                . $this->_params['offend']
                . ' ' . implode(' ', $this->_params['fortune']);
            return '<span class="fixed"><small>'
                . nl2br(Text_Filter::filter(shell_exec($cmdLine),
                                            array('space2html'),
                                            array(array('encode' => true))))
                . '</small></span>';
        } else {
            return '';
        }
    }

}
