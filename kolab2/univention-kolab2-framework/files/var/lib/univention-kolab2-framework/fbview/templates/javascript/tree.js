/**
 * Horde Tree Javascript Class
 *
 * Provides the javascript class to create dynamic trees.
 *
 * Copyright 2003-2004 Marko Djukic <marko@oblo.com>
 *
 * See the enclosed file COPYING for license information (GPL). If you did not
 * receive this file, see http://www.fsf.org/copyleft/gpl.html.
 *
 * $Horde: horde/templates/javascript/tree.js,v 1.23 2004/05/03 16:04:41 jan Exp $
 *
 * @author  Marko Djukic <marko@oblo.com>
 * @version $Revision: 1.1.2.1 $
 * @package Horde_Tree
 * @since   Horde 3.0
 */
function Horde_Tree(instanceName)
{
    /* Set up this class instance for function calls from the page. */
    this._instanceName = instanceName;

    /* Image variables. */
    this.imgDir         = '<?php echo $GLOBALS['registry']->getParam('graphics', 'horde') . '/tree'; ?>';
    this.imgLine        = 'line.gif';
    this.imgBlank       = 'blank.gif';
    this.imgJoin        = 'join.gif';
    this.imgJoinBottom  = 'joinbottom.gif';
    this.imgPlus        = 'plus.gif';
    this.imgPlusBottom  = 'plusbottom.gif';
    this.imgPlusOnly    = 'plusonly.gif';
    this.imgMinus       = 'minus.gif';
    this.imgMinusBottom = 'minusbottom.gif';
    this.imgMinusOnly   = 'minusonly.gif';
    this.imgFolder      = 'folder.gif';
    this.imgFolderOpen  = 'folderopen.gif';
    this.imgLeaf        = 'leaf.gif';

    /* Tree building variables. */
    this.rootNodeId     = '';
    this.target         = '';
    this.nodes          = new Array();
    this.node_pos       = new Array();
    this.dropline       = new Array();
    this.output         = '';
    this.altCount       = 0;
}

Horde_Tree.prototype.setTableStart = function(tableParams)
{
    this.tableStart = '<table' + tableParams + '>';
}

Horde_Tree.prototype.setImgDir = function(imgDir)
{
    this.imgDir = imgDir;
}

Horde_Tree.prototype.renderTree = function(rootNodeId)
{
    this.rootNodeId = rootNodeId;
    this.nodes = eval('n_' + this._instanceName);
    this.options = eval('o_' + this._instanceName);
    this.target = 't_' + this._instanceName;
    this._renderTree();
}

Horde_Tree.prototype._renderTree = function()
{
    this.output = '';
    this.buildTree(this.rootNodeId);
    document.getElementById(this.target).innerHTML = this.tableStart + this.output + '</table>';
    this.altCount = 0;
}

/*
 * Recursive function to walk through the tree array and build
 * the output.
 */
Horde_Tree.prototype.buildTree = function(nodeId)
{
    this.output += this.buildLine(nodeId);

    if (typeof(this.nodes[nodeId]['children']) != 'undefined' &&
        this.nodes[nodeId]['expanded']) {
        var numSubnodes = this.nodes[nodeId]['children'].length;
        for (var c = 0; c < numSubnodes; c++) {
            var childNodeId = this.nodes[nodeId]['children'][c];
            this.node_pos[childNodeId] = new Array();
            this.node_pos[childNodeId]['pos'] = c + 1;
            this.node_pos[childNodeId]['count'] = numSubnodes;
            this.buildTree(childNodeId);
        }
    }

    return true;
}

Horde_Tree.prototype.buildLine = function(nodeId)
{
    var nodeClass = '';
    if (this.options['alternate']) {
        this.altCount = (this.altCount ? 0 : 1);
    }

    if (this.nodes[nodeId]['class']) {
        nodeClass = ' class="' + this.nodes[nodeId]['class'] + '"';
    } else if (this.options['class']) {
        nodeClass = ' class="' + this.options['class'] + this.altCount + '"';
    } else {
        nodeClass = ' class="item' + this.altCount + '"';
    }

    var line = '<tr>';

    if (typeof(this.nodes[nodeId]['extra']) != 'undefined' &&
        typeof(this.nodes[nodeId]['extra'][0]) != 'undefined') {
        var extra = this.nodes[nodeId]['extra'][0];
        for (var c = 0; c < extra.length; c++) {
            line += '<td' + nodeClass + ' align="center">' + extra[c] + '</td>';
        }
        for (var d = c; d < extraColsLeft; d++) {
            line += '<td' + nodeClass + '>&nbsp;</td>';
        }
    } else {
        for (var c = 0; c < extraColsLeft; c++) {
            line += '<td' + nodeClass + '>&nbsp;</td>';
        }
    }

    line += '<td' + nodeClass + '>';

    for (var i = 0; i < this.nodes[nodeId]['indent']; i++) {
        if (this.dropline[i]) {
            line += '<img src="' + this.imgDir + '/' + this.imgLine + '" height="20" width="20" align="middle" border="0" />';
        } else {
            line += '<img src="' + this.imgDir + '/' + this.imgBlank + '" height="20" width="20" align="middle" border="0" />';
        }
    }

    line += this._setNodeToggle(nodeId) + this._setNodeIcon(nodeId) + this._setLabel(nodeId) + '</td>';

    if (typeof(this.nodes[nodeId]['extra']) != 'undefined' &&
        typeof(this.nodes[nodeId]['extra'][1]) != 'undefined') {
        var extra = this.nodes[nodeId]['extra'][1];
        for (var c = 0; c < extra.length; c++) {
            line += '<td' + nodeClass + ' align="center">' + extra[c] + '</td>';
        }
        for (var d = c; d < extraColsRight; d++) {
            line += '<td' + nodeClass + '>&nbsp;</td>';
        }
    } else {
        for (var c = 0; c < extraColsRight; c++) {
            line += '<td' + nodeClass + '>&nbsp;</td>';
        }
    }
    line += '</tr>';

    return line;
}

Horde_Tree.prototype._setLabel = function(nodeId)
{
    var label = this.nodes[nodeId]['label'];
    var onClick = '';
    if (this.nodes[nodeId]['onclick']) {
        onClick = ' onclick="' + this.nodes[nodeId]['onclick'] + '" style="cursor:pointer"';
    }
    if (this.nodes[nodeId]['url']) {
        label = '<a href="' + this.nodes[nodeId]['url'] + '">' + label + '</a>';
    }
    return '<span' + onClick + '>' + label + '</span></td>';
}

Horde_Tree.prototype._setNodeToggle = function(nodeId)
{
    var attrib = '';
    if (nodeId == this.rootNodeId &&
        typeof(this.nodes[nodeId]['children']) != 'undefined') {
        /* Root, and children. */
        img = (this.nodes[nodeId]['expanded']) ? this.imgMinusOnly : this.imgPlusOnly;
        this.dropline[0] = false;
        attrib = ' style="cursor:pointer;cursor:hand;" onclick="' + this._instanceName + '.toggle(\'' + nodeId + '\')"';
    } else if (nodeId != this.rootNodeId &&
        typeof(this.nodes[nodeId]['children']) == 'undefined') {
        /* Node no children. */
        if (this.node_pos[nodeId]['pos'] < this.node_pos[nodeId]['count']) {
            /* Not last node. */
            img = this.imgJoin;
            this.dropline[this.nodes[nodeId]['indent']] = true;
        } else {
            /* Last node. */
            img = this.imgJoinBottom;
            this.dropline[this.nodes[nodeId]['indent']] = false;
        }
    } else if (typeof(this.nodes[nodeId]['children']) != 'undefined') {
        /* Node with children. */
        if (this.node_pos[nodeId]['pos'] < this.node_pos[nodeId]['count']) {
            /* Not last node. */
            img = (this.nodes[nodeId]['expanded']) ? this.imgMinus : this.imgPlus;
            this.dropline[this.nodes[nodeId]['indent']] = true;
        } else {
            /* Last node. */
            img = (this.nodes[nodeId]['expanded']) ? this.imgMinusBottom : this.imgPlusBottom;
            this.dropline[this.nodes[nodeId]['indent']] = false;
        }
        attrib = ' style="cursor:pointer;cursor:hand;" onclick="' + this._instanceName + '.toggle(\'' + nodeId + '\')"';
    } else {
        /* Root only, no children. */
        img = this.imgMinusOnly;
        this.dropline[0] = false;
    }

    return '<img src="' + this.imgDir + '/' + img + '" ' + attrib + ' height="20" width="20" align="middle" border="0" />';
}

Horde_Tree.prototype._setNodeIcon = function(nodeId)
{
    var imgDir = (this.nodes[nodeId]['icondir']) ? this.nodes[nodeId]['icondir']
                                                 : this.imgDir;
    if (typeof(this.nodes[nodeId]['icon']) != 'undefined') {
        /* Node has a user defined icon. */
        if (typeof(this.nodes[nodeId]['iconopen']) != 'undefined' && this.nodes[nodeId]['expanded']) {
            img = this.nodes[nodeId]['iconopen'];
        } else {
            img = this.nodes[nodeId]['icon'];
        }
    } else {
        /* Use standard icon set. */
        if (typeof(this.nodes[nodeId]['children']) != 'undefined') {
            /* Node with children. */
            img = (this.nodes[nodeId]['expanded']) ? this.imgFolderOpen
                                                   : this.imgFolder;
        } else {
            /* Node no children. */
            img = this.imgLeaf;
        }
    }

    var imgtxt = '<img src="' + imgDir + '/' + img + '" align="middle" border="0" ';

    if (typeof(this.nodes[nodeId]['iconalt']) != 'undefined') {
        imgtxt += 'alt="' + this.nodes[nodeId]['iconalt'] + '" ';
    }

    return imgtxt + '/>';
}

Horde_Tree.prototype.toggle = function(nodeId)
{
    this.nodes[nodeId]['expanded'] = !this.nodes[nodeId]['expanded'];
    this.saveState(nodeId, this.nodes[nodeId]['expanded'])
    this._renderTree();
}

Horde_Tree.prototype.saveState = function(nodeId, expanded)
{
    var newCookie = '';
    var oldCookie = this._getCookie(this._instanceName + '_expanded');
    if (expanded) {
        /* Expand requested so add to cookie. */
        newCookie = (oldCookie) ? oldCookie + ',' : '';
        newCookie = newCookie + nodeId;
    } else {
        /* Collapse requested so remove from cookie. */
        var nodes = oldCookie.split(',');
        var newNodes = new Array();
        for (var i = 0; i < nodes.length; i++) {
            if (nodes[i] != nodeId) {
                newNodes.push(nodes[i]);
            }
        }
        newCookie = newNodes.join(',');
    }
    this._setCookie(this._instanceName + '_expanded', newCookie);
}

Horde_Tree.prototype._getCookie = function(name)
{
    var dc = document.cookie;
    var prefix = name + '=';
    var begin = dc.indexOf('; ' + prefix);
    if (begin == -1) {
        begin = dc.indexOf(prefix);
        if (begin != 0) {
            return '';
        }
    } else {
        begin += 2;
    }
    var end = document.cookie.indexOf(";", begin);
    if (end == -1) {
        end = dc.length;
    }
    return unescape(dc.substring(begin + prefix.length, end));
}

Horde_Tree.prototype._setCookie = function(name, value)
{
    var curCookie = name + '=' + escape(value);
    curCookie = curCookie + ';DOMAIN=<?php echo $GLOBALS['conf']['cookie']['domain']; ?>;PATH=<?php echo $GLOBALS['conf']['cookie']['path']; ?>;';
    document.cookie = curCookie;
}
