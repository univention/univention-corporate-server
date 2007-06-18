<?php
/*
 *  License Information:
 *
 *    Net_DNS:  A resolver library for PHP
 *    Copyright (c) 2002-2003 Eric Kilfoil eric@ypass.net
 *
 *    This library is free software; you can redistribute it and/or
 *    modify it under the terms of the GNU Lesser General Public
 *    License as published by the Free Software Foundation; either
 *    version 2.1 of the License, or (at your option) any later version.
 *
 *    This library is distributed in the hope that it will be useful,
 *    but WITHOUT ANY WARRANTY; without even the implied warranty of
 *    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
 *    Lesser General Public License for more details.
 *
 *    You should have received a copy of the GNU Lesser General Public
 *    License along with this library; if not, write to the Free Software
 *    Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA
 */

/* Net_DNS_RR_NAPTR definition {{{ */
/**
 * A representation of a resource record of type <b>NAPTR</b>
 *
 * @package Net_DNS
 */
class Net_DNS_RR_NAPTR extends Net_DNS_RR
{
    /* class variable definitions {{{ */
    var $name;
    var $type;
    var $class;
    var $ttl;
    var $rdlength;
    var $rdata;
	var $order;
	var $preference;
	var $flags;
	var $services;
	var $regex;
	var $replacement;

    /* }}} */
    /* class constructor - RR(&$rro, $data, $offset = '') {{{ */
    function Net_DNS_RR_NAPTR(&$rro, $data, $offset = '')
    {
        $this->name = $rro->name;
        $this->type = $rro->type;
        $this->class = $rro->class;
        $this->ttl = $rro->ttl;
        $this->rdlength = $rro->rdlength;
        $this->rdata = $rro->rdata;

        if ($offset) {
            if ($this->rdlength > 0) {
                $a = unpack("@$offset/norder/npreference", $data);
                $offset += 4;
                list($flags, $offset) = Net_DNS_Packet::label_extract($data, $offset);
                list($services, $offset) = Net_DNS_Packet::label_extract($data, $offset);
                list($regex, $offset) = Net_DNS_Packet::label_extract($data, $offset);
                list($replacement, $offset) = Net_DNS_Packet::dn_expand($data, $offset);

                $this->order = $a['order'];
                $this->preference = $a['preference'];
                $this->flags = $flags;
                $this->services = $services;
                $this->regex = $regex;
                $this->replacement = $replacement;
            }
        } else {
            $data = str_replace('\\\\', chr(1) . chr(1), $data); /* disguise escaped backslash */
            $data = str_replace('\\"', chr(2) . chr(2), $data); /* disguise \" */
            ereg('([0-9]+)[ \t]+([0-9]+)[ \t]+("[^"]*"|[^ \t]*)[ \t]+("[^"]*"|[^ \t]*)[ \t]+("[^"]*"|[^ \t]*)[ \t]+(.*?)[ \t]*$', $data, $regs);
            $this->preference = $regs[1];
            $this->weight = $regs[2];
            foreach($regs as $idx => $value) {
                $value = str_replace(chr(2) . chr(2), '\\"', $value);
                $value = str_replace(chr(1) . chr(1), '\\\\', $value);
                $regs[$idx] = stripslashes($value);
            }
            $this->flags = $regs[3];
            $this->services = $regs[4];
            $this->regex = $regs[5];
            $this->replacement = $regs[6];
        }
    }

    /* }}} */
    /* Net_DNS_RR_NAPTR::rdatastr() {{{ */
    function rdatastr()
    {
        if ($this->port) {
            return(intval($this->order) . ' ' . intval($this->preference) . ' "' . addslashes($this->flags) . '" "' . 
                   addslashes($this->services) . '" "' . addslashes($this->regex) . '" "' . addslashes($this->replacement) . '"');
        } else return('; no data');
    }

    /* }}} */
    /* Net_DNS_RR_NAPTR::rr_rdata($packet, $offset) {{{ */
    function rr_rdata($packet, $offset)
    {
        if ($this->preference) {
            $rdata  = pack('nn', $this->order, $this->preference);
            $rdata .= pack('C', strlen($this->flags))    . $this->flags;
            $rdata .= pack('C', strlen($this->services)) . $this->services;
            $rdata .= pack('C', strlen($this->regex))    . $this->regex;
            $rdata .= $packet->dn_comp($this->replacement, $offset + strlen($rdata));
            return($rdata);
        }
        return(NULL);
    }

    /* }}} */
}
/* }}} */
/* VIM settings {{{
 * Local variables:
 * tab-width: 4
 * c-basic-offset: 4
 * soft-stop-width: 4
 * c indent on
 * End:
 * vim600: sw=4 ts=4 sts=4 cindent fdm=marker et
 * vim<600: sw=4 ts=4
 * }}} */
?>
