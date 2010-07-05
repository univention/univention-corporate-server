/* This compressed file is part of Xinha. For uncompressed sources, forum, and bug reports, go to xinha.org */
/* This file is part of version 0.95 released Mon, 12 May 2008 17:33:15 +0200 */
/* The URL of the most recent version of this file is http://svn.xinha.webfactional.com/trunk/modules/Gecko/Gecko.js */
Gecko._pluginInfo={name:"Gecko",origin:"Xinha Core",version:"$LastChangedRevision:998 $".replace(/^[^:]*:\s*(.*)\s*\$$/,"$1"),developer:"The Xinha Core Developer Team",developer_url:"$HeadURL:http://svn.xinha.webfactional.com/trunk/modules/Gecko/Gecko.js $".replace(/^[^:]*:\s*(.*)\s*\$$/,"$1"),sponsor:"",sponsor_url:"",license:"htmlArea"};
function Gecko(_1){
this.editor=_1;
_1.Gecko=this;
}
Gecko.prototype.onKeyPress=function(ev){
var _3=this.editor;
var s=_3.getSelection();
if(_3.isShortCut(ev)){
switch(_3.getKey(ev).toLowerCase()){
case "z":
if(_3._unLink&&_3._unlinkOnUndo){
Xinha._stopEvent(ev);
_3._unLink();
_3.updateToolbar();
return true;
}
break;
case "a":
sel=_3.getSelection();
sel.removeAllRanges();
range=_3.createRange();
range.selectNodeContents(_3._doc.body);
sel.addRange(range);
Xinha._stopEvent(ev);
return true;
break;
case "v":
if(!_3.config.htmlareaPaste){
return true;
}
break;
}
}
switch(_3.getKey(ev)){
case " ":
var _5=function(_6,_7){
var _8=_6.nextSibling;
if(typeof _7=="string"){
_7=_3._doc.createElement(_7);
}
var a=_6.parentNode.insertBefore(_7,_8);
Xinha.removeFromParent(_6);
a.appendChild(_6);
_8.data=" "+_8.data;
s.collapse(_8,1);
_3._unLink=function(){
var t=a.firstChild;
a.removeChild(t);
a.parentNode.insertBefore(t,a);
Xinha.removeFromParent(a);
_3._unLink=null;
_3._unlinkOnUndo=false;
};
_3._unlinkOnUndo=true;
return a;
};
if(_3.config.convertUrlsToLinks&&s&&s.isCollapsed&&s.anchorNode.nodeType==3&&s.anchorNode.data.length>3&&s.anchorNode.data.indexOf(".")>=0){
var _b=s.anchorNode.data.substring(0,s.anchorOffset).search(/\S{4,}$/);
if(_b==-1){
break;
}
if(_3._getFirstAncestor(s,"a")){
break;
}
var _c=s.anchorNode.data.substring(0,s.anchorOffset).replace(/^.*?(\S*)$/,"$1");
var _d=_c.match(Xinha.RE_email);
if(_d){
var _e=s.anchorNode;
var _f=_e.splitText(s.anchorOffset);
var _10=_e.splitText(_b);
_5(_10,"a").href="mailto:"+_d[0];
break;
}
RE_date=/([0-9]+\.)+/;
RE_ip=/(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)/;
var _11=_c.match(Xinha.RE_url);
if(_11){
if(RE_date.test(_c)){
break;
}
var _12=s.anchorNode;
var _13=_12.splitText(s.anchorOffset);
var _14=_12.splitText(_b);
_5(_14,"a").href=(_11[1]?_11[1]:"http://")+_11[2];
break;
}
}
break;
}
switch(ev.keyCode){
case 27:
if(_3._unLink){
_3._unLink();
Xinha._stopEvent(ev);
}
break;
break;
case 8:
case 46:
if(!ev.shiftKey&&this.handleBackspace()){
Xinha._stopEvent(ev);
}
default:
_3._unlinkOnUndo=false;
if(s.anchorNode&&s.anchorNode.nodeType==3){
var a=_3._getFirstAncestor(s,"a");
if(!a){
break;
}
if(!a._updateAnchTimeout){
if(s.anchorNode.data.match(Xinha.RE_email)&&a.href.match("mailto:"+s.anchorNode.data.trim())){
var _16=s.anchorNode;
var _17=function(){
a.href="mailto:"+_16.data.trim();
a._updateAnchTimeout=setTimeout(_17,250);
};
a._updateAnchTimeout=setTimeout(_17,1000);
break;
}
var m=s.anchorNode.data.match(Xinha.RE_url);
if(m&&a.href.match(new RegExp("http(s)?://"+Xinha.escapeStringForRegExp(s.anchorNode.data.trim())))){
var _19=s.anchorNode;
var _1a=function(){
m=_19.data.match(Xinha.RE_url);
if(m){
a.href=(m[1]?m[1]:"http://")+m[2];
}
a._updateAnchTimeout=setTimeout(_1a,250);
};
a._updateAnchTimeout=setTimeout(_1a,1000);
}
}
}
break;
}
return false;
};
Gecko.prototype.handleBackspace=function(){
var _1b=this.editor;
setTimeout(function(){
var sel=_1b.getSelection();
var _1d=_1b.createRange(sel);
var SC=_1d.startContainer;
var SO=_1d.startOffset;
var EC=_1d.endContainer;
var EO=_1d.endOffset;
var _22=SC.nextSibling;
if(SC.nodeType==3){
SC=SC.parentNode;
}
if(!(/\S/.test(SC.tagName))){
var p=document.createElement("p");
while(SC.firstChild){
p.appendChild(SC.firstChild);
}
SC.parentNode.insertBefore(p,SC);
Xinha.removeFromParent(SC);
var r=_1d.cloneRange();
r.setStartBefore(_22);
r.setEndAfter(_22);
r.extractContents();
sel.removeAllRanges();
sel.addRange(r);
}
},10);
};
Gecko.prototype.inwardHtml=function(_25){
_25=_25.replace(/<(\/?)strong(\s|>|\/)/ig,"<$1b$2");
_25=_25.replace(/<(\/?)em(\s|>|\/)/ig,"<$1i$2");
_25=_25.replace(/<(\/?)del(\s|>|\/)/ig,"<$1strike$2");
return _25;
};
Gecko.prototype.outwardHtml=function(_26){
_26=_26.replace(/<script[\s]*src[\s]*=[\s]*['"]chrome:\/\/.*?["']>[\s]*<\/script>/ig,"");
return _26;
};
Gecko.prototype.onExecCommand=function(_27,UI,_29){
try{
this.editor._doc.execCommand("useCSS",false,true);
this.editor._doc.execCommand("styleWithCSS",false,false);
}
catch(ex){
}
switch(_27){
case "paste":
alert(Xinha._lc("The Paste button does not work in Mozilla based web browsers (technical security reasons). Press CTRL-V on your keyboard to paste directly."));
return true;
break;
case "removeformat":
var _2a=this.editor;
var sel=_2a.getSelection();
var _2c=_2a.saveSelection(sel);
var _2d=_2a.createRange(sel);
var els=_2a._doc.body.getElementsByTagName("*");
var _2f=(_2d.startContainer.nodeType==1)?_2d.startContainer:_2d.startContainer.parentNode;
var i,el;
if(sel.isCollapsed){
_2d.selectNodeContents(_2a._doc.body);
}
for(i=0;i<els.length;i++){
el=els[i];
if(_2d.isPointInRange(el,0)||(els[i]==_2f&&_2d.startOffset==0)){
el.removeAttribute("style");
}
}
this.editor._doc.execCommand(_27,UI,_29);
_2a.restoreSelection(_2c);
return true;
break;
}
return false;
};
Gecko.prototype.onMouseDown=function(ev){
if(ev.target.tagName.toLowerCase()=="hr"){
var sel=this.editor.getSelection();
var _33=this.editor.createRange(sel);
_33.selectNode(ev.target);
}
};
Xinha.prototype.insertNodeAtSelection=function(_34){
if(_34.ownerDocument!=this._doc){
try{
_34=this._doc.adoptNode(_34);
}
catch(e){
}
}
var sel=this.getSelection();
var _36=this.createRange(sel);
sel.removeAllRanges();
_36.deleteContents();
var _37=_36.startContainer;
var pos=_36.startOffset;
var _39=_34;
switch(_37.nodeType){
case 3:
if(_34.nodeType==3){
_37.insertData(pos,_34.data);
_36=this.createRange();
_36.setEnd(_37,pos+_34.length);
_36.setStart(_37,pos+_34.length);
sel.addRange(_36);
}else{
_37=_37.splitText(pos);
if(_34.nodeType==11){
_39=_39.firstChild;
}
_37.parentNode.insertBefore(_34,_37);
this.selectNodeContents(_39);
this.updateToolbar();
}
break;
case 1:
if(_34.nodeType==11){
_39=_39.firstChild;
}
_37.insertBefore(_34,_37.childNodes[pos]);
this.selectNodeContents(_39);
this.updateToolbar();
break;
}
};
Xinha.prototype.getParentElement=function(sel){
if(typeof sel=="undefined"){
sel=this.getSelection();
}
var _3b=this.createRange(sel);
try{
var p=_3b.commonAncestorContainer;
if(!_3b.collapsed&&_3b.startContainer==_3b.endContainer&&_3b.startOffset-_3b.endOffset<=1&&_3b.startContainer.hasChildNodes()){
p=_3b.startContainer.childNodes[_3b.startOffset];
}
while(p.nodeType==3){
p=p.parentNode;
}
return p;
}
catch(ex){
return null;
}
};
Xinha.prototype.activeElement=function(sel){
if((sel===null)||this.selectionEmpty(sel)){
return null;
}
if(!sel.isCollapsed){
if(sel.anchorNode.childNodes.length>sel.anchorOffset&&sel.anchorNode.childNodes[sel.anchorOffset].nodeType==1){
return sel.anchorNode.childNodes[sel.anchorOffset];
}else{
if(sel.anchorNode.nodeType==1){
return sel.anchorNode;
}else{
return null;
}
}
}
return null;
};
Xinha.prototype.selectionEmpty=function(sel){
if(!sel){
return true;
}
if(typeof sel.isCollapsed!="undefined"){
return sel.isCollapsed;
}
return true;
};
Xinha.prototype.saveSelection=function(){
return this.createRange(this.getSelection()).cloneRange();
};
Xinha.prototype.restoreSelection=function(_3f){
var sel=this.getSelection();
sel.removeAllRanges();
sel.addRange(_3f);
};
Xinha.prototype.selectNodeContents=function(_41,pos){
this.focusEditor();
this.forceRedraw();
var _43;
var _44=typeof pos=="undefined"?true:false;
var sel=this.getSelection();
_43=this._doc.createRange();
if(!_41){
sel.removeAllRanges();
return;
}
if(_44&&_41.tagName&&_41.tagName.toLowerCase().match(/table|img|input|textarea|select/)){
_43.selectNode(_41);
}else{
_43.selectNodeContents(_41);
}
sel.removeAllRanges();
sel.addRange(_43);
};
Xinha.prototype.insertHTML=function(_46){
var sel=this.getSelection();
var _48=this.createRange(sel);
this.focusEditor();
var _49=this._doc.createDocumentFragment();
var div=this._doc.createElement("div");
div.innerHTML=_46;
while(div.firstChild){
_49.appendChild(div.firstChild);
}
var _4b=this.insertNodeAtSelection(_49);
};
Xinha.prototype.getSelectedHTML=function(){
var sel=this.getSelection();
if(sel.isCollapsed){
return "";
}
var _4d=this.createRange(sel);
return Xinha.getHTML(_4d.cloneContents(),false,this);
};
Xinha.prototype.getSelection=function(){
return this._iframe.contentWindow.getSelection();
};
Xinha.prototype.createRange=function(sel){
this.activateEditor();
if(typeof sel!="undefined"){
try{
return sel.getRangeAt(0);
}
catch(ex){
return this._doc.createRange();
}
}else{
return this._doc.createRange();
}
};
Xinha.prototype.isKeyEvent=function(_4f){
return _4f.type=="keypress";
};
Xinha.prototype.getKey=function(_50){
return String.fromCharCode(_50.charCode);
};
Xinha.getOuterHTML=function(_51){
return (new XMLSerializer()).serializeToString(_51);
};
Xinha.prototype.cc=String.fromCharCode(8286);
Xinha.prototype.setCC=function(_52){
var cc=this.cc;
try{
if(_52=="textarea"){
var ta=this._textArea;
var _55=ta.selectionStart;
var _56=ta.value.substring(0,_55);
var _57=ta.value.substring(_55,ta.value.length);
if(_57.match(/^[^<]*>/)){
var _58=_57.indexOf(">")+1;
ta.value=_56+_57.substring(0,_58)+cc+_57.substring(_58,_57.length);
}else{
ta.value=_56+cc+_57;
}
ta.value=ta.value.replace(new RegExp("(&[^"+cc+"]*?)("+cc+")([^"+cc+"]*?;)"),"$1$3$2");
ta.value=ta.value.replace(new RegExp("(<script[^>]*>[^"+cc+"]*?)("+cc+")([^"+cc+"]*?</script>)"),"$1$3$2");
ta.value=ta.value.replace(new RegExp("^([^"+cc+"]*)("+cc+")([^"+cc+"]*<body[^>]*>)(.*?)"),"$1$3$2$4");
}else{
var sel=this.getSelection();
sel.getRangeAt(0).insertNode(this._doc.createTextNode(cc));
}
}
catch(e){
}
};
Xinha.prototype.findCC=function(_5a){
if(_5a=="textarea"){
var ta=this._textArea;
var pos=ta.value.indexOf(this.cc);
if(pos==-1){
return;
}
var end=pos+this.cc.length;
var _5e=ta.value.substring(0,pos);
var _5f=ta.value.substring(end,ta.value.length);
ta.value=_5e;
ta.scrollTop=ta.scrollHeight;
var _60=ta.scrollTop;
ta.value+=_5f;
ta.setSelectionRange(pos,pos);
ta.focus();
ta.scrollTop=_60;
}else{
try{
var doc=this._doc;
doc.body.innerHTML=doc.body.innerHTML.replace(new RegExp(this.cc),"<span id=\"XinhaEditingPostion\"></span>");
var _62=doc.getElementById("XinhaEditingPostion");
this.selectNodeContents(_62);
_62.scrollIntoView(true);
_62.parentNode.removeChild(_62);
this._iframe.contentWindow.focus();
}
catch(e){
}
}
};
Xinha.prototype._standardToggleBorders=Xinha.prototype._toggleBorders;
Xinha.prototype._toggleBorders=function(){
var _63=this._standardToggleBorders();
var _64=this._doc.getElementsByTagName("TABLE");
for(var i=0;i<_64.length;i++){
_64[i].style.display="none";
_64[i].style.display="table";
}
return _63;
};
Xinha.getDoctype=function(doc){
var d="";
if(doc.doctype){
d+="<!DOCTYPE "+doc.doctype.name+" PUBLIC ";
d+=doc.doctype.publicId?"\""+doc.doctype.publicId+"\"":"";
d+=doc.doctype.systemId?" \""+doc.doctype.systemId+"\"":"";
d+=">";
}
return d;
};

