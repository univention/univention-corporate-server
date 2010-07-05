/* This compressed file is part of Xinha. For uncompressed sources, forum, and bug reports, go to xinha.org */
/* This file is part of version 0.95 released Mon, 12 May 2008 17:33:15 +0200 */
/* The URL of the most recent version of this file is http://svn.xinha.webfactional.com/trunk/modules/Opera/Opera.js */
Opera._pluginInfo={name:"Opera",origin:"Xinha Core",version:"$LastChangedRevision:970 $".replace(/^[^:]*:\s*(.*)\s*\$$/,"$1"),developer:"The Xinha Core Developer Team",developer_url:"$HeadURL:http://svn.xinha.webfactional.com/trunk/modules/Opera/Opera.js $".replace(/^[^:]*:\s*(.*)\s*\$$/,"$1"),sponsor:"Gogo Internet Services Limited",sponsor_url:"http://www.gogo.co.nz/",license:"htmlArea"};
function Opera(_1){
this.editor=_1;
_1.Opera=this;
}
Opera.prototype.onKeyPress=function(ev){
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
Opera.prototype.handleBackspace=function(){
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
Opera.prototype.inwardHtml=function(_25){
_25=_25.replace(/<(\/?)del(\s|>|\/)/ig,"<$1strike$2");
return _25;
};
Opera.prototype.outwardHtml=function(_26){
return _26;
};
Opera.prototype.onExecCommand=function(_27,UI,_29){
switch(_27){
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
Opera.prototype.onMouseDown=function(ev){
};
Xinha.prototype.insertNodeAtSelection=function(_32){
if(_32.ownerDocument!=this._doc){
try{
_32=this._doc.adoptNode(_32);
}
catch(e){
}
}
this.focusEditor();
var sel=this.getSelection();
var _34=this.createRange(sel);
_34.deleteContents();
var _35=_34.startContainer;
var pos=_34.startOffset;
var _37=_32;
sel.removeAllRanges();
switch(_35.nodeType){
case 3:
if(_32.nodeType==3){
_35.insertData(pos,_32.data);
_34=this.createRange();
_34.setEnd(_35,pos+_32.length);
_34.setStart(_35,pos+_32.length);
sel.addRange(_34);
}else{
_35=_35.splitText(pos);
if(_32.nodeType==11){
_37=_37.firstChild;
}
_35.parentNode.insertBefore(_32,_35);
this.selectNodeContents(_37);
this.updateToolbar();
}
break;
case 1:
if(_32.nodeType==11){
_37=_37.firstChild;
}
_35.insertBefore(_32,_35.childNodes[pos]);
this.selectNodeContents(_37);
this.updateToolbar();
break;
}
};
Xinha.prototype.getParentElement=function(sel){
if(typeof sel=="undefined"){
sel=this.getSelection();
}
var _39=this.createRange(sel);
try{
var p=_39.commonAncestorContainer;
if(!_39.collapsed&&_39.startContainer==_39.endContainer&&_39.startOffset-_39.endOffset<=1&&_39.startContainer.hasChildNodes()){
p=_39.startContainer.childNodes[_39.startOffset];
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
Xinha.prototype.restoreSelection=function(_3d){
var sel=this.getSelection();
sel.removeAllRanges();
sel.addRange(_3d);
};
Xinha.prototype.selectNodeContents=function(_3f,pos){
this.focusEditor();
this.forceRedraw();
var _41;
var _42=typeof pos=="undefined"?true:false;
var sel=this.getSelection();
_41=this._doc.createRange();
if(_42&&_3f.tagName&&_3f.tagName.toLowerCase().match(/table|img|input|textarea|select/)){
_41.selectNode(_3f);
}else{
_41.selectNodeContents(_3f);
}
sel.removeAllRanges();
sel.addRange(_41);
};
Xinha.prototype.insertHTML=function(_44){
var sel=this.getSelection();
var _46=this.createRange(sel);
this.focusEditor();
var _47=this._doc.createDocumentFragment();
var div=this._doc.createElement("div");
div.innerHTML=_44;
while(div.firstChild){
_47.appendChild(div.firstChild);
}
var _49=this.insertNodeAtSelection(_47);
};
Xinha.prototype.getSelectedHTML=function(){
var sel=this.getSelection();
if(sel.isCollapsed){
return "";
}
var _4b=this.createRange(sel);
return Xinha.getHTML(_4b.cloneContents(),false,this);
};
Xinha.prototype.getSelection=function(){
var sel=this._iframe.contentWindow.getSelection();
if(sel&&sel.focusNode&&sel.focusNode.tagName&&sel.focusNode.tagName=="HTML"){
var bod=this._doc.getElementsByTagName("body")[0];
var rng=this.createRange();
rng.selectNodeContents(bod);
sel.removeAllRanges();
sel.addRange(rng);
sel.collapseToEnd();
}
return sel;
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
Xinha.prototype.isKeyEvent=function(_50){
return _50.type=="keypress";
};
Xinha.prototype.getKey=function(_51){
return String.fromCharCode(_51.charCode);
};
Xinha.getOuterHTML=function(_52){
return (new XMLSerializer()).serializeToString(_52);
};
Xinha.prototype.setCC=function(_53){
var cc=String.fromCharCode(8286);
try{
if(_53=="textarea"){
var ta=this._textArea;
var _56=ta.selectionStart;
var _57=ta.value.substring(0,_56);
var _58=ta.value.substring(_56,ta.value.length);
if(_58.match(/^[^<]*>/)){
var _59=_58.indexOf(">")+1;
ta.value=_57+_58.substring(0,_59)+cc+_58.substring(_59,_58.length);
}else{
ta.value=_57+cc+_58;
}
ta.value=ta.value.replace(new RegExp("(&[^"+cc+"]*?)("+cc+")([^"+cc+"]*?;)"),"$1$3$2");
ta.value=ta.value.replace(new RegExp("(<script[^>]*>[^"+cc+"]*?)("+cc+")([^"+cc+"]*?</script>)"),"$1$3$2");
ta.value=ta.value.replace(new RegExp("^([^"+cc+"]*)("+cc+")([^"+cc+"]*<body[^>]*>)(.*?)"),"$1$3$2$4");
ta.value=ta.value.replace(cc,"<span id=\"XinhaOperaCaretMarker\">MARK</span>");
}else{
var sel=this.getSelection();
var _5b=this._doc.createElement("span");
_5b.id="XinhaOperaCaretMarker";
sel.getRangeAt(0).insertNode(_5b);
}
}
catch(e){
}
};
Xinha.prototype.findCC=function(_5c){
if(_5c=="textarea"){
var ta=this._textArea;
var pos=ta.value.search(/(<span\s+id="XinhaOperaCaretMarker"\s*\/?>((\s|(MARK))*<\/span>)?)/);
if(pos==-1){
return;
}
var cc=RegExp.$1;
var end=pos+cc.length;
var _61=ta.value.substring(0,pos);
var _62=ta.value.substring(end,ta.value.length);
ta.value=_61;
ta.scrollTop=ta.scrollHeight;
var _63=ta.scrollTop;
ta.value+=_62;
ta.setSelectionRange(pos,pos);
ta.focus();
ta.scrollTop=_63;
}else{
var _64=this._doc.getElementById("XinhaOperaCaretMarker");
if(_64){
this.focusEditor();
var rng=this.createRange();
rng.selectNode(_64);
var sel=this.getSelection();
sel.addRange(rng);
sel.collapseToStart();
this.scrollToElement(_64);
_64.parentNode.removeChild(_64);
return;
}
}
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
Xinha.prototype._standardInitIframe=Xinha.prototype.initIframe;
Xinha.prototype.initIframe=function(){
if(!this._iframeLoadDone){
if(this._iframe.contentWindow&&this._iframe.contentWindow.xinhaReadyToRoll){
this._iframeLoadDone=true;
this._standardInitIframe();
}else{
var _69=this;
setTimeout(function(){
_69.initIframe();
},5);
}
}
};
Xinha._addEventOperaOrig=Xinha._addEvent;
Xinha._addEvent=function(el,_6b,_6c){
if(el.tagName&&el.tagName.toLowerCase()=="select"&&_6b=="change"){
return Xinha.addDom0Event(el,_6b,_6c);
}
return Xinha._addEventOperaOrig(el,_6b,_6c);
};

