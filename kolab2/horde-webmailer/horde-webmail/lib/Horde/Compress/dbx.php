<?php
/**
 * The Horde_Compress_dbx class allows dbx files (e.g. from Outlook Express)
 * to be read.
 *
 * This class is based on code by:
 * Antony Raijekov <dev@strategma.bg>
 * http://uruds.gateway.bg/zeos/
 *
 * $Horde: framework/Compress/Compress/dbx.php,v 1.3.12.13 2009-01-06 15:22:59 jan Exp $
 *
 * Copyright 2003-2009 The Horde Project (http://www.horde.org/)
 *
 * See the enclosed file COPYING for license information (LGPL). If you
 * did not receive this file, see http://www.fsf.org/copyleft/lgpl.html.
 *
 * @author  Jan Schneider <jan@horde.org>
 * @since   Horde 3.0
 * @package Horde_Compress
 */
class Horde_Compress_dbx extends Horde_Compress {

    /**
     * TODO
     *
     * @var array
     */
    var $_mails = array();

    /**
     * TODO
     *
     * @var array
     */
    var $_tmp = array();

    /**
     * Decompresses a DBX file and gets information from it.
     *
     * @param string $data  The dbx file data.
     * @param array $params  Any
     *
     * @return mixed  The requested data.
     */
    function decompress(&$data, $params = null)
    {
        $this->_mails = array();
        $this->_tmp = array();
        $position = 0xC4;
        $header_info = unpack('Lposition/LDataLength/nHeaderLength/nFlagCount', substr($data, $position, 12));
        $position += 12;
        // Go to the first table offest and process it.
        if ($header_info['position'] > 0) {
            $position = 0x30;
            $buf = unpack('Lposition', substr($data, $position, 4));
            $position = $buf['position'];
            $result = $this->_readIndex($data, $position);
            if (is_a($result, 'PEAR_Error')) {
                return $result;
            }
        }
        return $this->_mails;
    }

    /**
     * Returns a null-terminated string from the specified data.
     *
     * @access private
     *
     * @param string &$buf  TODO
     * @param integer $pos  TODO
     *
     * @return string  TODO
     */
    function _readString(&$buf, $pos)
    {
        if ($len = strpos(substr($buf, $pos), chr(0))) {
            return substr($buf, $pos, $len);
        }
        return '';
    }

    /**
     * TODO
     *
     * @access private
     *
     * @param string &$data      TODO
     * @param integer $position  TODO
     *
     * @return string  TODO
     */
    function _readMessage(&$data, $position)
    {
        $msg = '';
        $part = 0;

        if ($position > 0) {
            $IndexItemsCount = array_pop(unpack('S', substr($data, 0xC4, 4)));
            if ($IndexItemsCount > 0) {
                while ($position < strlen($data)) {
                    $part++;
                    $s = substr($data, $position, 528);
                    if (strlen($s) == 0) {
                        break;
                    }
                    $msg_item = unpack('LFilePos/LUnknown/LItemSize/LNextItem/a512Content', $s);
                    if ($msg_item['FilePos'] != $position) {
                        return PEAR::raiseError(_("Invalid file format"));
                    }
                    $position += 528;
                    $msg .= substr($msg_item['Content'], 0, $msg_item['ItemSize']);
                    $position = $msg_item['NextItem'];
                    if ($position == 0) {
                        break;
                    }
                }
            }
        }

        return $msg;
    }

    /**
     * TODO
     *
     * @access private
     *
     * @param string &$data      TODO
     * @param integer $position  TODO
     *
     * @return array  TODO
     */
    function _readMessageInfo(&$data, $position)
    {
        $message_info = array();
        $msg_header = unpack('Lposition/LDataLength/SHeaderLength/SFlagCount', substr($data, $position, 12));
        if ($msg_header['position'] != $position) {
            return PEAR::raiseError(_("Invalid file format"));
        }
        $position += 12;
        $message_info['HeaderPosition'] = $msg_header['position'];
        $flags = $msg_header['FlagCount'] & 0xFF;
        $DataSize = $msg_header['DataLength'] - $flags * 4;
        $size = 4 * $flags;
        $FlagsBuffer = substr($data, $position, $size);
        $position += $size;
        $size = $DataSize;
        $DataBuffer = substr($data, $position, $size);
        $position += $size;
        $message_info = array();

        $flag_array = array(
            0x1 => 'MsgFlags',
            0x2 => 'Sent',
            0x4 => 'position',
            0x7 => 'MessageID',
            0x8 => 'Subject',
            0x9 => 'From_reply',
            0xA => 'References',
            0xB => 'Newsgroup',
            0xD => 'From',
            0xE => 'Reply_To',
            0x12 => 'Received',
            0x13 => 'Receipt',
            0x1A => 'Account',
            0x1B => 'AccountID',
            0x80 => 'Msg',
            0x81 => 'MsgFlags',
            0x84 => 'position',
            0x91 => 'size',
        );

        /* Process flags */
        for ($i = 0; $i < $flags; $i++) {
            $pos = 0;
            $f = array_pop(unpack('L', substr($FlagsBuffer, $i * 4, 4)));

            $mask = $f & 0xFF;
            switch ($mask) {
            case 0x1:
                $pos = $pos + ($f >> 8);
                $message_info['MsgFlags'] = array_pop(unpack('C', substr($DataBuffer, $pos++, 1)));
                $message_info['MsgFlags'] += array_pop(unpack('C', substr($DataBuffer, $pos++, 1))) * 256;
                $message_info['MsgFlags'] += array_pop(unpack('C', substr($DataBuffer, $pos, 1))) * 65536;
                break;

            case 0x2:
            case 0x4:
                $pos += array_pop(unpack('L', substr($FlagsBuffer, $i * 4, 4))) >> 8;
                $message_info[$flag_array[$mask]] = array_pop(unpack('L', substr($DataBuffer, $pos, 4)));
                break;

            case 0x7:
            case 0x8:
            case 0x9:
            case 0xA:
            case 0xB:
            case 0xD:
            case 0xE:
            case 0x13:
            case 0x1A:
                $pos += array_pop(unpack('L', substr($FlagsBuffer, $i * 4, 4))) >> 8;
                $message_info[$flag_array[$mask]] = $this->_readString($DataBuffer, $pos);
                break;

            case 0x12:
                $pos += array_pop(unpack('L', substr($FlagsBuffer, $i * 4, 4))) >> 8;
                $message_info['Received'] = array_pop(unpack('L', substr($DataBuffer, $pos, 4)));
                break;

            case 0x1B:
                $pos += array_pop(unpack('L', substr($FlagsBuffer, $i * 4, 4))) >> 8;
                $message_info['AccountID'] = intval($this->_readString($DataBuffer, $pos));
                break;

            case 0x80:
            case 0x81:
            case 0x84:
            case 0x91:
                $message_info[$flag_array[$mask]] = array_pop(unpack('L', substr($FlagsBuffer, $i * 4, 4))) >> 8;
                break;
            }
        }

        return $message_info;
    }

    /**
     * TODO
     *
     * @access private
     *
     * @param string &$data      TODO
     * @param integer $position  TODO
     */
    function _readIndex(&$data, $position)
    {
        $index_header = unpack('LFilePos/LUnknown1/LPrevIndex/LNextIndex/LCount/LUnknown', substr($data, $position, 24));
        if ($index_header['FilePos'] != $position) {
            return PEAR::raiseError(_("Invalid file format"));
        }

        // Push it into list of processed items.
        $this->_tmp[$position] = true;
        if (($index_header['NextIndex'] > 0) &&
            empty($this->_tmp[$index_header['NextIndex']])) {
            $this->_readIndex($data, $index_header['NextIndex']);
        }
        if (($index_header['PrevIndex'] > 0) &&
            empty($this->_tmp[$index_header['PrevIndex']])) {
            $this->_readIndex($data, $index_header['PrevIndex']);
        }
        $position += 24;
        $icount = $index_header['Count'] >> 8;
        if ($icount > 0) {
            $buf = substr($data, $position, 12 * $icount);
            for ($i = 0; $i < $icount; $i++) {
                $hdr_buf = substr($buf, $i * 12, 12);
                $IndexItem = unpack('LHeaderPos/LChildIndex/LUnknown', $hdr_buf);
                if ($IndexItem['HeaderPos'] > 0) {
                    $mail['info'] = $this->_readMessageInfo($data, $IndexItem['HeaderPos']);
                    $mail['content'] = $this->_readMessage($data, $mail['info']['position']);
                    $this->_mails[] = $mail;
                }
                if (($IndexItem['ChildIndex'] > 0) &&
                    empty($this->_tmp[$IndexItem['ChildIndex']])) {
                    $this->_readIndex($fp, $IndexItem['ChildIndex']);
                }
            }
        }
    }

}
