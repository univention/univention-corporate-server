<?php

include_once 'Horde/RPC.php';
include_once 'Horde/SyncML.php';
include_once 'Horde/SyncML/State.php';
include_once 'Horde/SyncML/Command/Status.php';

/**
 * The Horde_RPC_syncml class provides a SyncML implementation of the
 * Horde RPC system.
 *
 * $Horde: framework/RPC/RPC/syncml.php,v 1.16 2004/04/07 17:43:42 chuck Exp $
 *
 * Copyright 2003-2004 Chuck Hagenbuch <chuck@horde.org>, Anthony Mills <amills@pyramid6.com>
 *
 * See the enclosed file COPYING for license information (LGPL). If you
 * did not receive this file, see http://www.fsf.org/copyleft/lgpl.html.
 *
 * @author  Chuck Hagenbuch <chuck@horde.org>
 * @author  Anthony Mills <amills@pyramid6.com>
 * @version $Revision: 1.1.2.1 $
 * @since   Horde 3.0
 * @package Horde_RPC
 */
class Horde_RPC_syncml extends Horde_RPC {

    /**
     * Output ContentHandler used to output XML events.
     * @var object $_output
     */
    var $_output;

    /**
     * @var integer $_xmlStack
     */
    var $_xmlStack = 0;

    /**
     * Debug directory, if set will store copies of all packets.
     */
    var $_debugDir = '/tmp/sync';

    /**
     * Default character set.  Only supports UTF-8(ASCII?).
     */
    var $_charset = 'UTF-8';

    /**
     * SyncML handles authentication internally, so bypass the
     * system-level auth check by just returning true here.
     */
    function authorize()
    {
        return true;
    }

    /**
     * Sends an RPC request to the server and returns the result.
     *
     * @param string $request  The raw request string.
     *
     * @return string   The XML encoded response from the server.
     */
    function getResponse($request)
    {
        // Very useful for debugging. Logs the xml packets to $this->_debugDir
        if (isset($this->_debugDir)) {
            $packetNum = @intval(file_get_contents($this->_debugDir . '/syncml.packetnum'));
            if (!isset($packetNum)) {
                $packetNum = 0;
            }

            $f = @fopen($this->_debugDir . '/syncml_client_' . $packetNum . '.xml', 'wb');
            if ($f) {
                fwrite($f, $request);
                fclose($f);
            }
        }

        // $this->_output can be already set by a subclass.
        // The subclass can use it's own ContentHandler and bypass
        // this classes use of the ContentHandler.  In this case
        // no output is return from this method, instead the output
        // comes from the subclasses ContentHandler
        // We may need to add this code back when we get to the content
        //if (!isset($this->_output)) {
            include_once 'XML/WBXML/ContentHandler.php';
            $this->_output = &new XML_WBXML_ContentHandler();
        //}

        $this->_parse($request);
        $xmlinput = $this->_output->getOutput();

        // Very useful for debugging.
        if (isset($this->_debugDir)) {
            $f = @fopen($this->_debugDir . '/syncml_server_' . $packetNum . '.xml', 'wb');
            if ($f) {
                fwrite($f, $xmlinput);
                fclose($f);
            }

            $packetNum++;
            $f = @fopen($this->_debugDir . '/syncml.packetnum', 'wb');
            if ($f) {
                fwrite($f, $packetNum);
                fclose($f);
            }
        }

        return $xmlinput;
    }

    function _parse($xml)
    {
        // Create the XML parser and set method references.
        $this->_parser = xml_parser_create_ns($this->_charset);
        xml_set_object($this->_parser, $this);
        xml_parser_set_option($this->_parser, XML_OPTION_CASE_FOLDING, false);
        xml_set_element_handler($this->_parser, '_startElement', '_endElement');
        xml_set_character_data_handler($this->_parser, '_characters');
        xml_set_processing_instruction_handler($this->_parser, '');
        xml_set_external_entity_ref_handler($this->_parser, '');

        if (!xml_parse($this->_parser, $xml)) {
            return $this->raiseError(sprintf('XML error: %s at line %d',
                                             xml_error_string(xml_get_error_code($this->_parser)),
                                             xml_get_current_line_number($this->_parser)));
        }

        xml_parser_free($this->_parser);
    }

    function _startElement($parser, $tag, $attributes)
    {
        list($uri, $name) = $this->_splitURI($tag);

        $this->startElement($uri, $name, $attributes);
    }

    function _characters($parser, $chars)
    {
        $this->characters($chars);
    }

    function _endElement($parser, $tag)
    {
        list($uri, $name) = $this->_splitURI($tag);

        $this->endElement($uri, $name);
    }

    function _splitURI($tag)
    {
        $parts = explode(':', $tag);
        $name = array_pop($parts);
        $uri = implode(':', $parts);
        return array($uri, $name);
    }

    /**
     * Get the Content-Type of the response.
     *
     * @return string  The MIME Content-Type of the RPC response.
     */
    function getResponseContentType()
    {
        return 'application/vnd.syncml+xml';
    }

    function startElement($uri, $element, $attrs)
    {
        $this->_xmlStack++;
        
        switch ($this->_xmlStack) {
        case 1:
            // <SyncML>
            // Defined in SyncML Representation Protocol, version 1.1 5.2.1
            $this->_output->startElement($uri, $element, $attrs);
            break;

        case 2:
            // Either <SyncML><SyncHdr> or <SyncML><SyncBody>
            if (!isset($this->_contentHandler)) {
                // If not defined then create SyncHdr.
                $this->_contentHandler = &new Horde_SyncML_SyncmlHdr();
                $this->_contentHandler->setOutput($this->_output);
            }

            $this->_contentHandler->startElement($uri, $element, $attrs);
            break;

        default:
            if (isset($this->_contentHandler)) {
                $this->_contentHandler->startElement($uri, $element, $attrs);
            }
            break;
        }
    }

    function endElement($uri, $element)
    {
        switch ($this->_xmlStack) {
        case 1:
            // </SyncML>
            // Defined in SyncML Representation Protocol, version 1.1 5.2.1
            $this->_output->endElement($uri, $element);
            break;

        case 2:
            // Either </SyncHdr></SyncML> or </SyncBody></SyncML>
            if ($element == 'SyncHdr') {
                // Then we get the state from SyncMLHdr, and create a
                // new SyncMLBody.
                $this->_contentHandler->endElement($uri, $element);

                unset($this->_contentHandler);

                $this->_contentHandler = &new Horde_SyncML_SyncmlBody();
                $this->_contentHandler->setOutput($this->_output);
            } else {
                // No longer used.
                $this->_contentHandler->endElement($uri, $element);
                unset($this->_contentHandler);
            }
            break;

        default:
            // </*></SyncHdr></SyncML> or </*></SyncBody></SyncML>
            if (isset($this->_contentHandler)) {
                $this->_contentHandler->endElement($uri, $element);
            }
            break;
        }

        if (isset($this->_chars)) {
            unset($this->_chars);
        }

        $this->_xmlStack--;
    }

    function characters($str)
    {
        if (isset($this->_contentHandler)) {
            $this->_contentHandler->characters($str);
        }
    }
    
    function raiseError($str) {
        Horde::logMEssage($str, __FILE__, __LINE__, PEAR_LOG_ERR);         
    }

}
