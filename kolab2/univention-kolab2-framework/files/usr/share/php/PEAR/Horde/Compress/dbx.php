<?php
/**
 * The Horde_Compress_dbx class allows dbx files (e.g. from Outlook Express)
 * to be read.
 *
 * This class is based on code by:
 * Anotny Raijekov <dev@strategma.bg>
 * http://uruds.gateway.bg/zeos/
 *
 * $Horde: framework/Compress/Compress/dbx.php,v 1.3 2004/01/01 15:14:12 jan Exp $
 *
 * Copyright 2003-2004 Jan Schneider <jan@horde.org>
 *
 * See the enclosed file COPYING for license information (LGPL). If you
 * did not receive this file, see http://www.fsf.org/copyleft/lgpl.html.
 *
 * @author  Jan Schneider <jan@horde.org>
 * @version $Revision: 1.1.2.1 $
 * @since   Horde 3.0
 * @package Horde_Compress
 */
class Horde_Compress_dbx extends Horde_Compress
{
    var $mails;
    var $tmp;

    /**
     * Decompresses a DBX file and gets information from it.
     *
     * @access public
     *
     * @param string $data  The dbx file data.
     *
     * @return mixed  The requested data.
     */
    function &decompress(&$data, $params = null)
    {
        $this->mails = array();
        $this->tmp = array();
        $position = 0xC4;
        $header_info = unpack('Lposition/LDataLength/nHeaderLength/nFlagCount', substr($data, $position, 12));
        $position += 12;
        // Go to the first table offest and process it.
        if ($header_info['position'] > 0) {
            $position = 0x30;
            $buf = unpack('Lposition', substr($data, $position, 4));
            $position = $buf['position'];
            $result = $this->readIndex($data, $position);
            if (is_a($result, 'PEAR_Error')) {
                return $result;
            }
        }
        return $this->mails;
    }

    /**
     * Returns a null-terminated string from the specified data.
     */
    function readString(&$buf, $pos)
    {
        if ($len = strpos(substr($buf, $pos), chr(0))) {
            return substr($buf, $pos, $len);
        }
        return '';
    }

    function readMessage(&$data, $position)
    {
        $msg = '';
        if ($position > 0) {
            $IndexItemsCount = array_pop(unpack('S', substr($data, 0xC4, 4)));
            if ($IndexItemsCount > 0) {
                $msg = '';
                $part = 0;
                while ($position < strlen($data)) {
                    $part++;
                    $s = substr($data, $position, 528);
                    if (strlen($s) == 0) {
                        break;
                    }
                    $msg_item = unpack('LFilePos/LUnknown/LItemSize/LNextItem/a512Content', $s);
                    //var_dump($msg_item);
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

    function readMessageInfo(&$data, $position)
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
        //process flags
        for ($i = 0; $i < $flags; $i++) {
            $pos = 0;
            $f = array_pop(unpack('L', substr($FlagsBuffer, $i * 4, 4)));

            switch ($f & 0xFF) {
            case 0x1:
                $pos = $pos + ($f >> 8);
                $message_info['MsgFlags'] = array_pop(unpack('C', substr($DataBuffer, $pos, 1)));
                $pos++;
                $message_info['MsgFlags'] += array_pop(unpack('C', substr($DataBuffer, $pos, 1))) * 256;
                $pos++;
                $message_info['MsgFlags'] += array_pop(unpack('C', substr($DataBuffer, $pos, 1))) * 65536;
                break;

            case 0x2:
                $pos += array_pop(unpack('L', substr($FlagsBuffer, $i * 4, 4))) >> 8;
                $message_info['Sent'] = array_pop(unpack('L', substr($DataBuffer, $pos, 4)));
                break;

            case 0x4:
                $pos += array_pop(unpack('L', substr($FlagsBuffer, $i * 4, 4))) >> 8;
                $message_info['position'] = array_pop(unpack('L', substr($DataBuffer, $pos, 4)));
                break;

            case 0x7:
                $pos += array_pop(unpack('L', substr($FlagsBuffer, $i * 4, 4))) >> 8;
                $message_info['MessageID'] = $this->readstring($DataBuffer, $pos);
                break;

            case 0x8:
                $pos += array_pop(unpack('L', substr($FlagsBuffer, $i * 4, 4))) >> 8;
                $message_info['Subject'] = $this->readstring($DataBuffer, $pos);
                break;

            case 0x9:
                $pos += array_pop(unpack('L', substr($FlagsBuffer, $i * 4, 4))) >> 8;
                $message_info['From_reply'] = $this->readstring($DataBuffer, $pos);
                break;

            case 0xA:
                $pos += array_pop(unpack('L', substr($FlagsBuffer, $i * 4, 4))) >> 8;
                $message_info['References'] = $this->readstring($DataBuffer, $pos);
                break;

            case 0xB:
                $pos += array_pop(unpack('L', substr($FlagsBuffer, $i * 4, 4))) >> 8;
                $message_info['Newsgroup'] = $this->readstring($DataBuffer, $pos);
                break;

            case 0xD:
                $pos += array_pop(unpack('L', substr($FlagsBuffer, $i * 4, 4))) >> 8;
                $message_info['From'] = $this->readstring($DataBuffer, $pos);
                break;

            case 0xE:
                $pos += array_pop(unpack('L', substr($FlagsBuffer, $i * 4, 4))) >> 8;
                $message_info['Reply_To'] = $this->readstring($DataBuffer, $pos);
                break;

            case 0x12:
                $pos += array_pop(unpack('L', substr($FlagsBuffer, $i * 4, 4))) >> 8;
                $message_info['Received'] = array_pop(unpack('L', substr($DataBuffer, $pos, 4)));
                break;

            case 0x13:
                $pos += array_pop(unpack('L', substr($FlagsBuffer, $i * 4, 4))) >> 8;
                $message_info['Receipt'] = $this->readstring($DataBuffer, $pos);
                break;

            case 0x1A:
                $pos += array_pop(unpack('L', substr($FlagsBuffer, $i * 4, 4))) >> 8;
                $message_info['Account'] = $this->readstring($DataBuffer, $pos);
                break;

            case 0x1B:
                $pos += array_pop(unpack('L', substr($FlagsBuffer, $i * 4, 4))) >> 8;
                $message_info['AccountID'] = intval($this->readstring($DataBuffer, $pos));
                break;

            case 0x80:
                $message_info['Msg'] = array_pop(unpack('L', substr($FlagsBuffer, $i * 4, 4))) >> 8;
                break;

            case 0x81:
                $message_info['MsgFlags'] = array_pop(unpack('L', substr($FlagsBuffer, $i * 4, 4))) >> 8;
                break;

            case 0x84:
                $message_info['position'] = array_pop(unpack('L', substr($FlagsBuffer, $i * 4, 4))) >> 8;
                break;

            case 0x91:
                $message_info['size'] = array_pop(unpack('L', substr($FlagsBuffer, $i * 4, 4))) >> 8;
                break;
            }
        }

        return $message_info;
    }

    function readIndex(&$data, $position)
    {
        //var_dump($position);
        $index_header = unpack('LFilePos/LUnknown1/LPrevIndex/LNextIndex/LCount/LUnknown', substr($data, $position, 24));
        //var_dump($index_header);
        if ($index_header['FilePos'] != $position) {
            return PEAR::raiseError(_("Invalid file format"));
        }

        // Push it into list of processed items.
        $this->tmp[$position] = true;
        if (($index_header['NextIndex'] > 0) &&
            empty($this->tmp[$index_header['NextIndex']])) {
            $this->readIndex($data, $index_header['NextIndex']);
        }
        if (($index_header['PrevIndex'] > 0) &&
            empty($this->tmp[$index_header['PrevIndex']])) {
            $this->readIndex($data, $index_header['PrevIndex']);
        }
        $position += 24;
        $icount = $index_header['Count'] >> 8;
        //var_dump($icount);
        if ($icount > 0) {
            $buf = substr($data, $position, 12 * $icount);
            for ($i = 0; $i < $icount; $i++) {
                $hdr_buf = substr($buf, $i * 12, 12);
                $IndexItem = unpack('LHeaderPos/LChildIndex/LUnknown', $hdr_buf);
                //var_dump($IndexItem);
                if ($IndexItem['HeaderPos'] > 0) {
                    if (false && strtolower($this->fname) == 'folders.dbx')
                        //read_folder($fp,$IndexItem['HeaderPos']);
                        print 'Read folder not implemented in v1.0a<br>';
                    else {
                        $mail['info'] = $this->readMessageInfo($data, $IndexItem['HeaderPos']);
                        $mail['content'] = $this->readMessage($data, $mail['info']['position']);
                        $this->mails[] = $mail;
                    }
               }
                if (($IndexItem['ChildIndex'] > 0) &&
                    empty($this->tmp[$IndexItem['ChildIndex']])) {
                    $this->readIndex($fp, $IndexItem['ChildIndex']);
                }
            }
        }
    }

    //debug function to display human readble message flags (Just for debugging purpose)
    function decode_flags($x)
    {
        $decode_flag['DOWNLOADED']              = 0x1;
        $decode_flag['MARKED']                  = 0x20;
        $decode_flag['READED']                  = 0x80;
        $decode_flag['DOWNLOAD_LATER']          = 0x100;
        $decode_flag['NEWS_MSG']                = 0x800;  // to verify
        $decode_flag['ATTACHMENTS']             = 0x4000;
        $decode_flag['REPLY']                   = 0x80000;
        $decode_flag['INSPECT_CONVERSATION']    = 0x400000;
        $decode_flag['IGNORE_CONVERSATION']     = 0x800000;

        $decoded_flags = '';

        if(($x & $decode_flag['NEWS_MSG']) != 0) $decoded_flags .= "NEWS MESSAGE\n<br>";
        if(($x & $decode_flag['DOWNLOAD_LATER']) != 0) $decoded_flags .= "DOWNLOAD LATER\n<br>";
        if(($x & $decode_flag['DOWNLOADED']) != 0) $decoded_flags .= "DOWNLOADED\n<br>";
        if(($x & $decode_flag['READED']) != 0) $decoded_flags .= "READED\n<br>";
        if(($x & $decode_flag['MARKED']) != 0) $decoded_flags .= "MARKED\n<br>";
        if(($x & $decode_flag['ATTACHMENTS']) != 0) $decoded_flags .= "ATTACHMENTS\n<br>";
        if(($x & $decode_flag['REPLY']) != 0) $decoded_flags .= "REPLY\n<br>";
        if(($x & $decode_flag['INSPECT_CONVERSATION']) != 0) $decoded_flags .= "INSPECT CONVERSATION\n<br>";
        if(($x & $decode_flag['IGNORE_CONVERSATION']) != 0) $decoded_flags .= "IGNORE CONVERSATION\n<br>";

        return $decoded_flags;
    }

}
