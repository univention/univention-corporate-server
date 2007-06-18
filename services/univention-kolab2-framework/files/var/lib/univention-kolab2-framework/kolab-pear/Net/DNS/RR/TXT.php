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

/* Net_DNS_RR_TXT definition {{{ */
/**
 * A representation of a resource record of type <b>TXT</b>
 *
 * @package Net_DNS
 */
class Net_DNS_RR_TXT extends Net_DNS_RR
{
    /* class variable definitions {{{ */
    var $name;
    var $type;
    var $class;
    var $ttl;
    var $rdlength;
    var $rdata;
	var $text;

    /* }}} */
    /* class constructor - RR(&$rro, $data, $offset = '') {{{ */
    function Net_DNS_RR_TXT(&$rro, $data, $offset = '')
    {
        $this->name = $rro->name;
        $this->type = $rro->type;
        $this->class = $rro->class;
        $this->ttl = $rro->ttl;
        $this->rdlength = $rro->rdlength;
        $this->rdata = $rro->rdata;

        if ($offset) {
            if ($this->rdlength > 0) {
                list($text, $offset) = Net_DNS_Packet::label_extract($data, $offset);

                $this->text = $text;
            }
        } else {
            $data = str_replace('\\\\', chr(1) . chr(1), $data); /* disguise escaped backslash */
            $data = str_replace('\\"', chr(2) . chr(2), $data); /* disguise \" */

            ereg('("[^"]*"|[^ \t]*)[ \t]*$', $data, $regs);
            $regs[1] = str_replace(chr(2) . chr(2), '\\"', $regs[1]);
            $regs[1] = str_replace(chr(1) . chr(1), '\\\\', $regs[1]);
            $regs[1] = stripslashes($regs[1]);

            $this->text = $regs[1];
        }
    }

    /* }}} */
    /* Net_DNS_RR_TXT::rdatastr() {{{ */
    function rdatastr()
    {
        if ($this->text) {
            return('"' . addslashes($this->text) . '"');
        } else return('; no data');
    }

    /* }}} */
    /* Net_DNS_RR_TXT::rr_rdata($packet, $offset) {{{ */
    function rr_rdata($packet, $offset)
    {
        if ($this->text) {
            $rdata  = pack('C', strlen($this->text)) . $this->text;
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
