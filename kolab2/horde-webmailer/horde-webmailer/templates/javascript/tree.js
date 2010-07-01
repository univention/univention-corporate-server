/**
 * Horde Tree Javascript Class
 *
 * Provides the javascript class to create dynamic trees.
 *
 * $Horde: horde/templates/javascript/tree.js,v 1.62.2.16 2009-01-06 15:27:38 jan Exp $
 *
 * Copyright 2003-2009 The Horde Project (http://www.horde.org/)
 *
 * See the enclosed file COPYING for license information (GPL). If you
 * did not receive this file, see http://www.fsf.org/copyleft/gpl.html.
 *
 * @author  Marko Djukic <marko@oblo.com>
 * @package Horde_Tree
 * @since   Horde 3.0
 */
function Horde_Tree(instanceName)
{
    /* Set up this class instance for function calls from the page. */
    this._instanceName = instanceName;

    /* Image variables. */
    this.imgDir         = '<?php echo $GLOBALS['registry']->getImageDir('horde') . '/tree'; ?>';
    this.imgBlank       = 'blank.png';
    this.imgFolder      = 'folder.png';
    this.imgFolderOpen  = 'folderopen.png';

    /* Variables that change based on text direction. */
<?php if (empty($GLOBALS['nls']['rtl'][$GLOBALS['language']])): ?>
    this.floatDir       = 'float:left;';
    this.imgLine        = 'line.png';
    this.imgJoin        = 'join.png';
    this.imgJoinBottom  = 'joinbottom.png';
    this.imgPlus        = 'plus.png';
    this.imgPlusBottom  = 'plusbottom.png';
    this.imgPlusOnly    = 'plusonly.png';
    this.imgMinus       = 'minus.png';
    this.imgMinusBottom = 'minusbottom.png';
    this.imgMinusOnly   = 'minusonly.png';
    this.imgNullOnly    = 'nullonly.png';
    this.imgLeaf        = 'leaf.png';
<?php else: ?>
    this.floatDir       = 'float:right;';
    this.imgLine        = 'rev-line.png';
    this.imgJoin        = 'rev-join.png';
    this.imgJoinBottom  = 'rev-joinbottom.png';
    this.imgPlus        = 'rev-plus.png';
    this.imgPlusBottom  = 'rev-plusbottom.png';
    this.imgPlusOnly    = 'rev-plusonly.png';
    this.imgMinus       = 'rev-minus.png';
    this.imgMinusBottom = 'rev-minusbottom.png';
    this.imgMinusOnly   = 'rev-minusonly.png';
    this.imgNullOnly    = 'rev-nullonly.png';
    this.imgLeaf        = 'rev-leaf.png';
<?php endif; ?>

    /* Tree building variables. */
    this.renderStatic   = false;
    this.target         = '';
    this.header         = [];
    this.rootNodes      = [];
    this.nodes          = [];
    this.node_pos       = [];
    this.dropline       = [];
}

Horde_Tree.prototype.setImgDir = function(imgDir)
{
    this.imgDir = imgDir;
}

Horde_Tree.prototype.renderTree = function(rootNodes, renderStatic)
{
    this.rootNodes = rootNodes;
    this.renderStatic = renderStatic;
    this.nodes = eval('n_' + this._instanceName);
    this.header = eval('h_' + this._instanceName);
    this.options = eval('o_' + this._instanceName);
    this.target = 't_' + this._instanceName;
    this._renderTree();
}

Horde_Tree.prototype._renderTree = function()
{
    this.output = [];
    if (!this.options['hideHeaders']) {
        this.output.push(this._buildHeader());
    }
    for (var i = 0; i < this.rootNodes.length; ++i) {
        this.buildTree(this.rootNodes[i]);
    }
    document.getElementById(this.target).innerHTML = this.output.join('');
    this._correctWidthForScrollbar();
    // If using alternating row shading, work out correct shade.
    if (this.options['alternate']) {
        this.stripe();
    }
    if (typeof ToolTips == 'object') {
        ToolTips.attachBehavior();
    }
}

/**
 * Returns the HTML code for a header row, if necessary.
 *
 * @access private
 *
 * @return string  The HTML code of the header row or an empty string.
 */
Horde_Tree.prototype._buildHeader = function()
{
    if (!this.header.length) {
        return '';
    }

    var html = [];
    html.push('<div>');
    for (var i = 0; i < this.header.length; ++i) {
        html.push('<div');
        if (this.header[i]['class']) {
            html.push(' class="');
            html.push(this.header[i]['class']);
            html.push('"');
        }

        html.push(' style="');
        html.push(this.floatDir);

        if (this.header[i]['width']) {
            html.push('width:');
            html.push(this.header[i]['width']);
            html.push(';');
        }
        if (this.header[i]['align']) {
            html.push('text-align:');
            html.push(this.header[i]['align']);
            html.push(';');
        }

        html.push('">');
        html.push(this.header[i]['html'] ? this.header[i]['html'] : '&nbsp;');
        html.push('</div>');
    }

    html.push('</div>');
    return html.join('');
}

/**
 * Recursive function to walk through the tree array and build
 * the output.
 */
Horde_Tree.prototype.buildTree = function(nodeId)
{
    this.buildLine(nodeId);

    if (typeof(this.nodes[nodeId]['children']) != 'undefined') {
        var numSubnodes = this.nodes[nodeId]['children'].length;
        if (numSubnodes > 0) {
            if (this.nodes[nodeId]['expanded']) {
                rowStyle = 'display:block;';
            } else {
                rowStyle = 'display:none;';
            }
            this.output.push('<div id="nodeChildren_' + nodeId + '" style="' + rowStyle + '">');

            for (var c = 0; c < numSubnodes; ++c) {
                var childNodeId = this.nodes[nodeId]['children'][c];
                this.node_pos[childNodeId] = [];
                this.node_pos[childNodeId]['pos'] = c + 1;
                this.node_pos[childNodeId]['count'] = numSubnodes;
                this.buildTree(childNodeId);
            }

            this.output.push('</div>');
        }
    }

    return true;
}

Horde_Tree.prototype.buildLine = function(nodeId)
{
    var node = this.nodes[nodeId];
    var o = this.output;
    var style = '';

    o.push('<div class="');
    o.push('treeRow');
    if (node['class']) {
        o.push(' ');
        o.push(node['class']);
    }
    o.push('">');

    // If we have headers, track which logical "column" we're in for
    // any given cell of content.
    var column = 0;

    if (typeof(node['extra']) != 'undefined' &&
        typeof(node['extra'][0]) != 'undefined') {
        var extra = node['extra'][0];
        for (var c = 0; c < extra.length; ++c) {
            o.push('<div style="');
            o.push(this.floatDir);
            if (this.header[column] && this.header[column]['width']) {
                o.push('width:');
                o.push(this.header[column]['width']);
                o.push(';');
            }
            o.push('">');
            o.push(extra[c]);
            o.push('</div>');
            ++column;
        }
        for (var d = c; d < extraColsLeft; ++d) {
            o.push('<div style="');
            o.push(this.floatDir);
            if (this.header[column] && this.header[column]['width']) {
                o.push('width:');
                o.push(this.header[column]['width']);
                o.push(';');
            }
            o.push('">&nbsp;</div>');
            ++column;
        }
    } else {
        for (var c = 0; c < extraColsLeft; ++c) {
            o.push('<div style="');
            o.push(this.floatDir);
            if (this.header[column] && this.header[column]['width']) {
                o.push('width:');
                o.push(this.header[column]['width']);
                o.push(';');
            }
            o.push('">&nbsp;</div>');
            ++column;
        }
    }

    o.push('<div style="');
    o.push(this.floatDir);
    if (this.header[column] && this.header[column]['width']) {
        o.push('width:');
        o.push(this.header[column]['width']);
        o.push(';');
    }
    o.push('">');

    if (this.options['multiline']) {
        o.push('<table cellspacing="0"><tr><td>');
    }

    for (var i = this.renderStatic ? 1 : 0; i < node['indent']; ++i) {
        o.push('<img src="');
        o.push(this.imgDir);
        o.push('/');
        if (this.dropline[i] && this.options['lines']) {
            o.push(this.imgLine);
            o.push('" alt="|&nbsp;&nbsp;&nbsp;" height="20" width="20" />');
        } else {
            o.push(this.imgBlank);
            o.push('" alt="&nbsp;&nbsp;&nbsp;" height="20" width="20" />');
        }
    }
    o.push(this._setNodeToggle(nodeId));
    if (this.options['multiline']) {
        o.push('</td><td>');
    }
    o.push(this._setLabel(nodeId));

    if (this.options['multiline']) {
        o.push('</td></tr></table>');
    }

    o.push('</div>');
    ++column;

    if (typeof(node['extra']) != 'undefined' &&
        typeof(node['extra'][1]) != 'undefined') {
        var extra = node['extra'][1];
        for (var c = 0; c < extra.length; ++c) {
            o.push('<div style="');
            o.push(this.floatDir);
            if (this.header[column] && this.header[column]['width']) {
                o.push('width:');
                o.push(this.header[column]['width']);
                o.push(';');
            }
            o.push('">');
            o.push(extra[c]);
            o.push('</div>');
            ++column;
        }
        for (var d = c; d < extraColsRight; ++d) {
            o.push('<div style="');
            o.push(this.floatDir);
            if (this.header[column] && this.header[column]['width']) {
                o.push('width:');
                o.push(this.header[column]['width']);
                o.push(';');
            }
            o.push('">&nbsp;</div>');
            ++column;
        }
    } else {
        for (var c = 0; c < extraColsRight; ++c) {
            o.push('<div style="');
            o.push(this.floatDir);
            if (this.header[column] && this.header[column]['width']) {
                o.push('width:');
                o.push(this.header[column]['width']);
                o.push(';');
            }
            o.push('">&nbsp;</div>');
            ++column;
        }
    }
    o.push('</div>');
}

Horde_Tree.prototype._setLabel = function(nodeId)
{
    var node = this.nodes[nodeId];
    var label = [];

    if (node['url']) {
        label.push('<a');

        if (node['urlclass']) {
            label.push(' class="');
            label.push(node['urlclass']);
            label.push('"');
        } else if (this.options['urlclass']) {
            label.push(' class="');
            label.push(this.options['urlclass']);
            label.push('"');
        }

        label.push(' href="');
        label.push(node['url']);
        label.push('"');

        if (node['title']) {
            label.push(' title="');
            label.push(node['title']);
            label.push('"');
        }

        if (node['target']) {
            label.push(' target="');
            label.push(node['target']);
            label.push('"');
        } else if (this.options['target']) {
            label.push(' target="');
            label.push(this.options['target']);
            label.push('"');
        }

        if (node['onclick']) {
            label.push(' onclick="');
            label.push(node['onclick']);
            label.push('"');
        }

        label.push('>');
        label.push(this._setNodeIcon(nodeId));
        label.push(node['label']);
        label.push('</a>');
    } else {
        label.push('<span class="toggle" onclick="');
        label.push(this._instanceName);
        label.push('.toggle(\'');
        label.push(nodeId.toString().replace(/'/, "\\'"));
        label.push('\')">');
        label.push(this._setNodeIcon(nodeId));
        label.push(node['label']);
        label.push('</span>');
    }

    return label.join('');
}

Horde_Tree.prototype._setNodeToggle = function(nodeId)
{
    var node = this.nodes[nodeId];
    var attrib = '';
    if (node['indent'] == '0' &&
        typeof(node['children']) != 'undefined') {
        // Top level with children.
        this.dropline[0] = false;
        if (this.renderStatic) {
            return '';
        } else {
            attrib = ' style="cursor:pointer" onclick="' + this._instanceName + '.toggle(\'' + nodeId.toString().replace(/'/, "\\'") + '\')"';
        }
    } else if (node['indent'] != '0' &&
               typeof(node['children']) == 'undefined') {
        // Node no children.
        if (this.node_pos[nodeId]['pos'] < this.node_pos[nodeId]['count']) {
            // Not last node.
            this.dropline[node['indent']] = true;
        } else {
            this.dropline[node['indent']] = false;
        }
    } else if (typeof(node['children']) != 'undefined') {
        // Node with children.
        if (this.node_pos[nodeId]['pos'] < this.node_pos[nodeId]['count']) {
            // Not last node.
            this.dropline[node['indent']] = true;
        } else {
            // Last node.
            this.dropline[node['indent']] = false;
        }
        if (!this.renderStatic) {
            attrib = ' style="cursor:pointer" onclick="' + this._instanceName + '.toggle(\'' + nodeId.toString().replace(/'/, "\\'") + '\')"';
        }
    } else {
        // Top level node with no children.
        if (this.renderStatic) {
            return '';
        }
        this.dropline[0] = false;
    }

    var nodeToggle = this._getNodeToggle(nodeId);
    var img = [];
    img.push('<img id="nodeToggle_');
    img.push(nodeId);
    img.push('" src="');
    img.push(this.imgDir);
    img.push('/');
    img.push(nodeToggle[0]);
    img.push('" ');
    if (nodeToggle[1]) {
        img.push('alt="');
        img.push(nodeToggle[1]);
        img.push('" ');
    }
    img.push(attrib);
    img.push(' height="20" width="20" />');
    return img.join('');
}

Horde_Tree.prototype._getNodeToggle = function(nodeId)
{
    var node = this.nodes[nodeId];
    var nodeToggle = ['', ''];
    if (node['indent'] == '0' &&
        typeof(node['children']) != 'undefined') {
        // Top level with children.
        if (this.renderStatic) {
            return nodeToggle;
        } else if (!this.options['lines']) {
            nodeToggle[0] = this.imgBlank;
            nodeToggle[1] = '&nbsp;&nbsp;&nbsp;'
        } else if (node['expanded']) {
            nodeToggle[0] = this.imgMinusOnly;
            nodeToggle[1] = '-';
        } else {
            nodeToggle[0] = this.imgPlusOnly;
            nodeToggle[1] = '+';
        }
    } else if (node['indent'] != '0' &&
        typeof(node['children']) == 'undefined') {
        // Node no children.
        if (this.node_pos[nodeId]['pos'] < this.node_pos[nodeId]['count']) {
            // Not last node.
            if (this.options['lines']) {
                nodeToggle[0] = this.imgJoin;
                nodeToggle[1] = '|-';
            } else {
                nodeToggle[0] = this.imgBlank;
                nodeToggle[1] = '&nbsp;&nbsp;&nbsp;';
            }
        } else {
            // Last node.
            if (this.options['lines']) {
                nodeToggle[0] = this.imgJoinBottom;
                nodeToggle[1] = '`-';
            } else {
                nodeToggle[0] = this.imgBlank;
                nodeToggle[1] = '&nbsp;&nbsp;&nbsp;';
            }
        }
    } else if (typeof(node['children']) != 'undefined') {
        // Node with children.
        if (this.node_pos[nodeId]['pos'] < this.node_pos[nodeId]['count']) {
            // Not last node.
            if (!this.options['lines']) {
                nodeToggle[0] = this.imgBlank;
                nodeToggle[1] = '&nbsp;&nbsp;&nbsp;';
            } else if (this.renderStatic) {
                nodeToggle[0] = this.imgJoin;
                nodeToggle[1] = '|-';
            } else if (node['expanded']) {
                nodeToggle[0] = this.imgMinus;
                nodeToggle[1] = '-';
            } else {
                nodeToggle[0] = this.imgPlus;
                nodeToggle[1] = '+';
            }
        } else {
            // Last node.
            if (!this.options['lines']) {
                nodeToggle[0] = this.imgBlank;
                nodeToggle[1] = '&nbsp;';
            } else if (this.renderStatic) {
                nodeToggle[0] = this.imgJoinBottom;
                nodeToggle[1] = '`-';
            } else if (node['expanded']) {
                nodeToggle[0] = this.imgMinusBottom;
                nodeToggle[1] = '-';
            } else {
                nodeToggle[0] = this.imgPlusBottom;
                nodeToggle[1] = '+';
            }
        }
    } else {
        // Top level node with no children.
        if (this.renderStatic) {
            return nodeToggle;
        }
        if (this.options['lines']) {
            nodeToggle[0] = this.imgNullOnly;
            nodeToggle[1] = '&nbsp;&nbsp;';
        } else {
            nodeToggle[0] = this.imgBlank;
            nodeToggle[1] = '&nbsp;&nbsp;&nbsp;';
        }
    }

    return nodeToggle;
}

Horde_Tree.prototype._setNodeIcon = function(nodeId)
{
    var node = this.nodes[nodeId];
    var img = []

    img.push('<img id="nodeIcon_');
    img.push(nodeId);
    img.push('" src="');

    // Image directory.
    if (typeof(node['icondir']) != 'undefined') {
        if (node['icondir']) {
            img.push(node['icondir']);
            img.push('/');
        }
    } else if (this.imgDir) {
        img.push(this.imgDir);
        img.push('/');
    }

    // Image.
    if (typeof(node['icon']) != 'undefined') {
        // Node has a user defined icon.
        if (!node['icon']) {
            return '';
        }
        if (typeof(node['iconopen']) != 'undefined' && node['expanded']) {
            img.push(node['iconopen']);
        } else {
            img.push(node['icon']);
        }
    } else {
        // Use standard icon set.
        if (typeof(node['children']) != 'undefined') {
            // Node with children.
            img.push((node['expanded']) ? this.imgFolderOpen : this.imgFolder);
        } else {
            // Node, no children.
            img.push(this.imgLeaf);
        }
    }

    img.push('"');

    if (typeof(node['iconalt']) != 'undefined') {
        img.push(' alt="');
        img.push(node['iconalt']);
        img.push('"');
    }

    img.push(' /> ');
    return img.join('');
}

Horde_Tree.prototype.toggle = function(nodeId)
{
    var node = this.nodes[nodeId];
    node['expanded'] = !node['expanded'];
    if (node['expanded']) {
        if (children = document.getElementById('nodeChildren_' + nodeId)) {
            children.style.display = 'block';
        }
    } else {
        if (children = document.getElementById('nodeChildren_' + nodeId)) {
            children.style.display = 'none';
        }
    }

    // Toggle the node's icon if it has seperate open and closed
    // icons.
    if (typeof node['iconopen'] != 'undefined') {
        var icon = document.getElementById('nodeIcon_' + nodeId);
        if (icon) {
            var src = [];

            // Image directory.
            if (typeof(node['icondir']) != 'undefined') {
                if (node['icondir']) {
                    src.push(node['icondir']);
                    src.push('/');
                }
            } else if (this.imgDir) {
                src.push(this.imgDir);
                src.push('/');
            }

            // Image.
            if (typeof(node['icon']) != 'undefined') {
                if (node['expanded']) {
                    src.push(node['iconopen']);
                } else {
                    src.push(node['icon']);
                }
            } else {
                // Use standard icon set.
                src.push((node['expanded']) ? this.imgFolderOpen : this.imgFolder);
            }

            icon.src = src.join('');
        }
    }

    // If using alternating row shading, work out correct shade.
    if (this.options['alternate']) {
        this.stripe();
    }

    nodeToggle = this._getNodeToggle(nodeId);
    if (toggle = document.getElementById('nodeToggle_' + nodeId)) {
        toggle.src = this.imgDir + '/' + nodeToggle[0];
        toggle.alt = nodeToggle[1];
    }

    this.saveState(nodeId, node['expanded'])
}

Horde_Tree.prototype.stripe = function()
{
    // The element to start striping.
    var id = arguments[0] ? arguments[0] : this.target;

    // The flag we'll use to keep track of whether the current row is
    // odd or even.
    var even = arguments[1] ? arguments[1] : false;

    // Obtain a reference to the tree parent element.
    var tree = document.getElementById(id);
    if (!tree) {
        return even;
    }

    // Iterate over each child div.
    for (var i = 0; i < tree.childNodes.length; ++i) {
        var _node = tree.childNodes[i];
        if (_node.id.indexOf('nodeChildren') != -1) {
            if (this.nodes[_node.id.toString().replace('nodeChildren_', '')]['expanded']) {
                even = this.stripe(_node.id, even);
            }
        } else {
            _node.className = _node.className.replace(new RegExp(' ?rowEven ?'), '');
            _node.className = _node.className.replace(new RegExp(' ?rowOdd ?'), '');
            if (_node.className) {
                _node.className += even ? ' rowEven' : ' rowOdd';
            } else {
                _node.className = even ? 'rowEven' : 'rowOdd';
            }

            // Flip from odd to even, or vice-versa.
            even = !even;
        }
    }

    return even;
}

Horde_Tree.prototype.saveState = function(nodeId, expanded)
{
    var newCookie = '';
    var oldCookie = this._getCookie(this._instanceName + '_expanded');
    if (expanded) {
        // Expand requested so add to cookie.
        newCookie = (oldCookie) ? oldCookie + ',' : '';
        newCookie = newCookie + nodeId;
    } else {
        // Collapse requested so remove from cookie.
        var nodes = oldCookie.split(',');
        var newNodes = [];
        for (var i = 0; i < nodes.length; ++i) {
            if (nodes[i] != nodeId) {
                newNodes[newNodes.length] = nodes[i];
            }
        }
        newCookie = newNodes.join(',');
    }
    this._setCookie(this._instanceName + '_expanded', newCookie);
}

Horde_Tree.prototype._getCookie = function(name)
{
    var dc = document.cookie;
    var prefix = name + '=exp';
    var begin = dc.indexOf('; ' + prefix);
    if (begin == -1) {
        begin = dc.indexOf(prefix);
        if (begin != 0) {
            return '';
        }
    } else {
        begin += 2;
    }
    var end = document.cookie.indexOf(';', begin);
    if (end == -1) {
        end = dc.length;
    }
    return unescape(dc.substring(begin + prefix.length, end));
}

Horde_Tree.prototype._setCookie = function(name, value)
{
    var curCookie = name + '=exp' + escape(value);
    curCookie += ';DOMAIN=<?php echo $GLOBALS['conf']['cookie']['domain']; ?>;PATH=<?php echo $GLOBALS['conf']['cookie']['path']; ?>;';
    document.cookie = curCookie;
}

Horde_Tree.prototype._correctWidthForScrollbar = function()
{
<?php if ($GLOBALS['browser']->hasQuirk('scrollbar_in_way')): ?>
    // Correct for frame scrollbar in IE by determining if a scrollbar is present,
    // and if not readjusting the marginRight property to 0
    // See http://www.xs4all.nl/~ppk/js/doctypes.html for why this works
    if (document.documentElement.clientHeight == document.documentElement.offsetHeight) {
        // no scrollbar present, take away extra margin
        document.body.style.marginRight = '0';
    } else {
        document.body.style.marginRight = '15px';
    }
<?php endif; ?>
}
