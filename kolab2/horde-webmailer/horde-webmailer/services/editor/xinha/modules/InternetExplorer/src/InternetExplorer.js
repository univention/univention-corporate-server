/* This compressed file is part of Xinha. For uncompressed sources, forum, and bug reports, go to xinha.org */
/* This file is part of version 0.95 released Mon, 12 May 2008 17:33:15 +0200 */
/* The URL of the most recent version of this file is http://svn.xinha.webfactional.com/trunk/modules/InternetExplorer/InternetExplorer.js */
InternetExplorer._pluginInfo={name:"Internet Explorer",origin:"Xinha Core",version:"$LastChangedRevision:980 $".replace(/^[^:]*:\s*(.*)\s*\$$/,"$1"),developer:"The Xinha Core Developer Team",developer_url:"$HeadURL:http://svn.xinha.webfactional.com/trunk/modules/InternetExplorer/InternetExplorer.js $".replace(/^[^:]*:\s*(.*)\s*\$$/,"$1"),sponsor:"",sponsor_url:"",license:"htmlArea"};
function InternetExplorer(_1){
this.editor=_1;
_1.InternetExplorer=this;
}
InternetExplorer.prototype.onKeyPress=function(ev){
if(this.editor.isShortCut(ev)){
switch(this.editor.getKey(ev).toLowerCase()){
case "n":
this.editor.execCommand("formatblock",false,"<p>");
Xinha._stopEvent(ev);
return true;
break;
case "1":
case "2":
case "3":
case "4":
case "5":
case "6":
this.editor.execCommand("formatblock",false,"<h"+this.editor.getKey(ev).toLowerCase()+">");
Xinha._stopEvent(ev);
return true;
break;
}
}
switch(ev.keyCode){
case 8:
case 46:
if(this.handleBackspace()){
Xinha._stopEvent(ev);
return true;
}
break;
}
return false;
};
InternetExplorer.prototype.handleBackspace=function(){
var _3=this.editor;
var _4=_3.getSelection();
if(_4.type=="Control"){
var _5=_3.activeElement(_4);
Xinha.removeFromParent(_5);
return true;
}
var _6=_3.createRange(_4);
var r2=_6.duplicate();
r2.moveStart("character",-1);
var a=r2.parentElement();
if(a!=_6.parentElement()&&(/^a$/i.test(a.tagName))){
r2.collapse(true);
r2.moveEnd("character",1);
r2.pasteHTML("");
r2.select();
return true;
}
};
InternetExplorer.prototype.inwardHtml=function(_9){
_9=_9.replace(/<(\/?)del(\s|>|\/)/ig,"<$1strike$2");
_9=_9.replace(/(<script|<!--)/i,"&nbsp;$1");
return _9;
};
InternetExplorer.prototype.outwardHtml=function(_a){
_a=_a.replace(/&nbsp;(\s*)(<script|<!--)/i,"$1$2");
return _a;
};
InternetExplorer.prototype.onExecCommand=function(_b,UI,_d){
switch(_b){
case "saveas":
var _e=null;
var _f=this.editor;
var _10=document.createElement("iframe");
_10.src="about:blank";
_10.style.display="none";
document.body.appendChild(_10);
try{
if(_10.contentDocument){
_e=_10.contentDocument;
}else{
_e=_10.contentWindow.document;
}
}
catch(ex){
}
_e.open("text/html","replace");
var _11="";
if(_f.config.browserQuirksMode===false){
var _12="<!DOCTYPE HTML PUBLIC \"-//W3C//DTD HTML 4.01 Transitional//EN\" \"http://www.w3.org/TR/html4/loose.dtd\">";
}else{
if(_f.config.browserQuirksMode===true){
var _12="";
}else{
var _12=Xinha.getDoctype(document);
}
}
if(!_f.config.fullPage){
_11+=_12+"\n";
_11+="<html>\n";
_11+="<head>\n";
_11+="<meta http-equiv=\"Content-Type\" content=\"text/html; charset="+_f.config.charSet+"\">\n";
if(typeof _f.config.baseHref!="undefined"&&_f.config.baseHref!==null){
_11+="<base href=\""+_f.config.baseHref+"\"/>\n";
}
if(typeof _f.config.pageStyleSheets!=="undefined"){
for(var i=0;i<_f.config.pageStyleSheets.length;i++){
if(_f.config.pageStyleSheets[i].length>0){
_11+="<link rel=\"stylesheet\" type=\"text/css\" href=\""+_f.config.pageStyleSheets[i]+"\">";
}
}
}
if(_f.config.pageStyle){
_11+="<style type=\"text/css\">\n"+_f.config.pageStyle+"\n</style>";
}
_11+="</head>\n";
_11+="<body>\n";
_11+=_f.getEditorContent();
_11+="</body>\n";
_11+="</html>";
}else{
_11=_f.getEditorContent();
if(_11.match(Xinha.RE_doctype)){
_f.setDoctype(RegExp.$1);
}
}
_e.write(_11);
_e.close();
_e.execCommand(_b,UI,_d);
document.body.removeChild(_10);
return true;
break;
case "removeformat":
var _f=this.editor;
var sel=_f.getSelection();
var _15=_f.saveSelection(sel);
var i,el,els;
function clean(el){
if(el.nodeType!=1){
return;
}
el.removeAttribute("style");
for(var j=0;j<el.childNodes.length;j++){
clean(el.childNodes[j]);
}
if((el.tagName.toLowerCase()=="span"&&!el.attributes.length)||el.tagName.toLowerCase()=="font"){
el.outerHTML=el.innerHTML;
}
}
if(_f.selectionEmpty(sel)){
els=_f._doc.body.childNodes;
for(i=0;i<els.length;i++){
el=els[i];
if(el.nodeType!=1){
continue;
}
if(el.tagName.toLowerCase()=="span"){
newNode=_f.convertNode(el,"div");
el.parentNode.replaceChild(newNode,el);
el=newNode;
}
clean(el);
}
}
_f._doc.execCommand(_b,UI,_d);
_f.restoreSelection(_15);
return true;
break;
}
return false;
};
Xinha.prototype.insertNodeAtSelection=function(_18){
this.insertHTML(_18.outerHTML);
};
Xinha.prototype.getParentElement=function(sel){
if(typeof sel=="undefined"){
sel=this.getSelection();
}
var _1a=this.createRange(sel);
switch(sel.type){
case "Text":
var _1b=_1a.parentElement();
while(true){
var _1c=_1a.duplicate();
_1c.moveToElementText(_1b);
if(_1c.inRange(_1a)){
break;
}
if((_1b.nodeType!=1)||(_1b.tagName.toLowerCase()=="body")){
break;
}
_1b=_1b.parentElement;
}
return _1b;
case "None":
return _1a.parentElement();
case "Control":
return _1a.item(0);
default:
return this._doc.body;
}
};
Xinha.prototype.activeElement=function(sel){
if((sel===null)||this.selectionEmpty(sel)){
return null;
}
if(sel.type.toLowerCase()=="control"){
return sel.createRange().item(0);
}else{
var _1e=sel.createRange();
var _1f=this.getParentElement(sel);
if(_1f.innerHTML==_1e.htmlText){
return _1f;
}
return null;
}
};
Xinha.prototype.selectionEmpty=function(sel){
if(!sel){
return true;
}
return this.createRange(sel).htmlText==="";
};
Xinha.prototype.saveSelection=function(){
return this.createRange(this.getSelection());
};
Xinha.prototype.restoreSelection=function(_21){
try{
_21.select();
}
catch(e){
}
};
Xinha.prototype.selectNodeContents=function(_22,pos){
this.focusEditor();
this.forceRedraw();
var _24;
var _25=typeof pos=="undefined"?true:false;
if(_25&&_22.tagName&&_22.tagName.toLowerCase().match(/table|img|input|select|textarea/)){
_24=this._doc.body.createControlRange();
_24.add(_22);
}else{
_24=this._doc.body.createTextRange();
_24.moveToElementText(_22);
}
_24.select();
};
Xinha.prototype.insertHTML=function(_26){
this.focusEditor();
var sel=this.getSelection();
var _28=this.createRange(sel);
_28.pasteHTML(_26);
};
Xinha.prototype.getSelectedHTML=function(){
var sel=this.getSelection();
if(this.selectionEmpty(sel)){
return "";
}
var _2a=this.createRange(sel);
if(_2a.htmlText){
return _2a.htmlText;
}else{
if(_2a.length>=1){
return _2a.item(0).outerHTML;
}
}
return "";
};
Xinha.prototype.getSelection=function(){
return this._doc.selection;
};
Xinha.prototype.createRange=function(sel){
if(!sel){
sel=this.getSelection();
}
return sel.createRange();
};
Xinha.prototype.isKeyEvent=function(_2c){
return _2c.type=="keydown";
};
Xinha.prototype.getKey=function(_2d){
return String.fromCharCode(_2d.keyCode);
};
Xinha.getOuterHTML=function(_2e){
return _2e.outerHTML;
};
Xinha.prototype.cc=String.fromCharCode(8201);
Xinha.prototype.setCC=function(_2f){
var cc=this.cc;
if(_2f=="textarea"){
var ta=this._textArea;
var pos=document.selection.createRange();
pos.collapse();
pos.text=cc;
var _33=ta.value.indexOf(cc);
var _34=ta.value.substring(0,_33);
var _35=ta.value.substring(_33+cc.length,ta.value.length);
if(_35.match(/^[^<]*>/)){
var _36=_35.indexOf(">")+1;
ta.value=_34+_35.substring(0,_36)+cc+_35.substring(_36,_35.length);
}else{
ta.value=_34+cc+_35;
}
ta.value=ta.value.replace(new RegExp("(&[^"+cc+"]*?)("+cc+")([^"+cc+"]*?;)"),"$1$3$2");
ta.value=ta.value.replace(new RegExp("(<script[^>]*>[^"+cc+"]*?)("+cc+")([^"+cc+"]*?</script>)"),"$1$3$2");
ta.value=ta.value.replace(new RegExp("^([^"+cc+"]*)("+cc+")([^"+cc+"]*<body[^>]*>)(.*?)"),"$1$3$2$4");
}else{
var sel=this.getSelection();
var r=sel.createRange();
if(sel.type=="Control"){
var _39=r.item(0);
_39.outerHTML+=cc;
}else{
r.collapse();
r.text=cc;
}
}
};
Xinha.prototype.findCC=function(_3a){
var _3b=(_3a=="textarea")?this._textArea:this._doc.body;
range=_3b.createTextRange();
if(range.findText(escape(this.cc))){
range.select();
range.text="";
}
if(range.findText(this.cc)){
range.select();
range.text="";
}
if(_3a=="textarea"){
this._textArea.focus();
}
};
Xinha.getDoctype=function(doc){
return (doc.compatMode=="CSS1Compat"&&Xinha.ie_version<8)?"<!DOCTYPE HTML PUBLIC \"-//W3C//DTD HTML 4.01 Transitional//EN\" \"http://www.w3.org/TR/html4/loose.dtd\">":"";
};

