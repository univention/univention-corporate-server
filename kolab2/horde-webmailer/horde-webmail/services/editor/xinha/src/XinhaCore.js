/* This compressed file is part of Xinha. For uncompressed sources, forum, and bug reports, go to xinha.org */
/* This file is part of version 0.95 released Mon, 12 May 2008 17:33:15 +0200 */
/* The URL of the most recent version of this file is http://svn.xinha.webfactional.com/trunk/XinhaCore.js */
  /*--------------------------------------------------------------------------
    --  Xinha (is not htmlArea) - http://xinha.org
    --
    --  Use of Xinha is granted by the terms of the htmlArea License (based on
    --  BSD license)  please read license.txt in this package for details.
    --
    --  Copyright 2005-2008 Xinha Developer Team and contributors
    --  
    --  Xinha was originally based on work by Mihai Bazon which is:
    --      Copyright 2003-2004 dynarch.com.
    --      Copyright 2002-2003 interactivetools.com, inc.
    --      This copyright notice MUST stay intact for use.
    -------------------------------------------------------------------------*/

Xinha.version={"Release":"0.95","Head":"$HeadURL:http://svn.xinha.webfactional.com/trunk/XinhaCore.js $".replace(/^[^:]*:\s*(.*)\s*\$$/,"$1"),"Date":"$LastChangedDate:2008-05-01 14:33:36 +0200 (Do, 01 Mai 2008) $".replace(/^[^:]*:\s*([0-9-]*) ([0-9:]*) ([+0-9]*) \((.*)\)\s*\$/,"$4 $2 $3"),"Revision":"$LastChangedRevision:999 $".replace(/^[^:]*:\s*(.*)\s*\$$/,"$1"),"RevisionBy":"$LastChangedBy:ray $".replace(/^[^:]*:\s*(.*)\s*\$$/,"$1")};
Xinha._resolveRelativeUrl=function(_1,_2){
if(_2.match(/^([^:]+\:)?\/\//)){
return _2;
}else{
var b=_1.split("/");
if(b[b.length-1]==""){
b.pop();
}
var p=_2.split("/");
if(p[0]=="."){
p.shift();
}
while(p[0]==".."){
b.pop();
p.shift();
}
return b.join("/")+"/"+p.join("/");
}
};
if(typeof _editor_url=="string"){
_editor_url=_editor_url.replace(/\x2f*$/,"/");
if(!_editor_url.match(/^([^:]+\:)?\//)){
var path=window.location.toString().split("/");
path.pop();
_editor_url=Xinha._resolveRelativeUrl(path.join("/"),_editor_url);
}
}else{
alert("WARNING: _editor_url is not set!  You should set this variable to the editor files path; it should preferably be an absolute path, like in '/htmlarea/', but it can be relative if you prefer.  Further we will try to load the editor files correctly but we'll probably fail.");
_editor_url="";
}
if(typeof _editor_lang=="string"){
_editor_lang=_editor_lang.toLowerCase();
}else{
_editor_lang="en";
}
if(typeof _editor_skin!=="string"){
_editor_skin="";
}
var __xinhas=[];
Xinha.agt=navigator.userAgent.toLowerCase();
Xinha.is_ie=((Xinha.agt.indexOf("msie")!=-1)&&(Xinha.agt.indexOf("opera")==-1));
Xinha.ie_version=parseFloat(Xinha.agt.substring(Xinha.agt.indexOf("msie")+5));
Xinha.is_opera=(Xinha.agt.indexOf("opera")!=-1);
if(Xinha.is_opera&&Xinha.agt.match(/opera[\/ ]([0-9.]+)/)){
Xinha.opera_version=parseFloat(RegExp.$1);
}else{
Xinha.opera_version=0;
}
Xinha.is_khtml=(Xinha.agt.indexOf("khtml")!=-1);
Xinha.is_webkit=(Xinha.agt.indexOf("applewebkit")!=-1);
Xinha.webkit_version=parseInt(navigator.appVersion.replace(/.*?AppleWebKit\/([\d]).*?/,"$1"));
Xinha.is_safari=(Xinha.agt.indexOf("safari")!=-1);
Xinha.is_mac=(Xinha.agt.indexOf("mac")!=-1);
Xinha.is_mac_ie=(Xinha.is_ie&&Xinha.is_mac);
Xinha.is_win_ie=(Xinha.is_ie&&!Xinha.is_mac);
Xinha.is_gecko=(navigator.product=="Gecko")||Xinha.is_opera;
Xinha.is_real_gecko=(navigator.product=="Gecko"&&!Xinha.is_webkit);
Xinha.is_ff3=Xinha.is_real_gecko&&parseInt(navigator.productSub)>=2007121016;
Xinha.is_ff2=Xinha.is_real_gecko&&parseInt(navigator.productSub)<2007121016;
Xinha.isRunLocally=document.URL.toLowerCase().search(/^file:/)!=-1;
Xinha.is_designMode=(typeof document.designMode!="undefined"&&!Xinha.is_ie);
Xinha.checkSupportedBrowser=function(){
return Xinha.is_real_gecko||(Xinha.is_opera&&Xinha.opera_version>=9.2)||Xinha.ie_version>=5.5||Xinha.webkit_version>=522;
};
Xinha.isSupportedBrowser=Xinha.checkSupportedBrowser();
if(Xinha.isRunLocally&&Xinha.isSupportedBrowser){
alert("Xinha *must* be installed on a web server. Locally opened files (those that use the \"file://\" protocol) cannot properly function. Xinha will try to initialize but may not be correctly loaded.");
}
function Xinha(_5,_6){
if(!Xinha.isSupportedBrowser){
return;
}
if(!_5){
throw new Error("Tried to create Xinha without textarea specified.");
}
if(typeof _6=="undefined"){
this.config=new Xinha.Config();
}else{
this.config=_6;
}
if(typeof _5!="object"){
_5=Xinha.getElementById("textarea",_5);
}
this._textArea=_5;
this._textArea.spellcheck=false;
Xinha.freeLater(this,"_textArea");
this._initial_ta_size={w:_5.style.width?_5.style.width:(_5.offsetWidth?(_5.offsetWidth+"px"):(_5.cols+"em")),h:_5.style.height?_5.style.height:(_5.offsetHeight?(_5.offsetHeight+"px"):(_5.rows+"em"))};
if(document.getElementById("loading_"+_5.id)||this.config.showLoading){
if(!document.getElementById("loading_"+_5.id)){
Xinha.createLoadingMessage(_5);
}
this.setLoadingMessage(Xinha._lc("Constructing object"));
}
this._editMode="wysiwyg";
this.plugins={};
this._timerToolbar=null;
this._timerUndo=null;
this._undoQueue=[this.config.undoSteps];
this._undoPos=-1;
this._customUndo=true;
this._mdoc=document;
this.doctype="";
this.__htmlarea_id_num=__xinhas.length;
__xinhas[this.__htmlarea_id_num]=this;
this._notifyListeners={};
var _7={right:{on:true,container:document.createElement("td"),panels:[]},left:{on:true,container:document.createElement("td"),panels:[]},top:{on:true,container:document.createElement("td"),panels:[]},bottom:{on:true,container:document.createElement("td"),panels:[]}};
for(var i in _7){
if(!_7[i].container){
continue;
}
_7[i].div=_7[i].container;
_7[i].container.className="panels "+i;
Xinha.freeLater(_7[i],"container");
Xinha.freeLater(_7[i],"div");
}
this._panels=_7;
this._statusBar=null;
this._statusBarTree=null;
this._statusBarTextMode=null;
this._statusBarItems=[];
this._framework={};
this._htmlArea=null;
this._iframe=null;
this._doc=null;
this._toolBar=this._toolbar=null;
this._toolbarObjects={};
}
Xinha.onload=function(){
};
Xinha.init=function(){
Xinha.onload();
};
Xinha.RE_tagName=/(<\/|<)\s*([^ \t\n>]+)/ig;
Xinha.RE_doctype=/(<!doctype((.|\n)*?)>)\n?/i;
Xinha.RE_head=/<head>((.|\n)*?)<\/head>/i;
Xinha.RE_body=/<body[^>]*>((.|\n|\r|\t)*?)<\/body>/i;
Xinha.RE_Specials=/([\/\^$*+?.()|{}[\]])/g;
Xinha.escapeStringForRegExp=function(_9){
return _9.replace(Xinha.RE_Specials,"\\$1");
};
Xinha.RE_email=/^[_a-z\d\-\.]{3,}@[_a-z\d\-]{2,}(\.[_a-z\d\-]{2,})+$/i;
Xinha.RE_url=/(https?:\/\/)?(([a-z0-9_]+:[a-z0-9_]+@)?[a-z0-9_-]{2,}(\.[a-z0-9_-]{2,}){2,}(:[0-9]+)?(\/\S+)*)/i;
Xinha.Config=function(){
this.version=Xinha.version.Revision;
this.width="auto";
this.height="auto";
this.sizeIncludesBars=true;
this.sizeIncludesPanels=true;
this.panel_dimensions={left:"200px",right:"200px",top:"100px",bottom:"100px"};
this.iframeWidth=null;
this.statusBar=true;
this.htmlareaPaste=false;
this.mozParaHandler="best";
this.getHtmlMethod="DOMwalk";
this.undoSteps=20;
this.undoTimeout=500;
this.changeJustifyWithDirection=false;
this.fullPage=false;
this.pageStyle="";
this.pageStyleSheets=[];
this.baseHref=null;
this.expandRelativeUrl=true;
this.stripBaseHref=true;
this.stripSelfNamedAnchors=true;
this.only7BitPrintablesInURLs=true;
this.sevenBitClean=false;
this.specialReplacements={};
this.inwardHtml=function(_a){
return _a;
};
this.outwardHtml=function(_b){
return _b;
};
this.killWordOnPaste=true;
this.makeLinkShowsTarget=true;
this.charSet=(typeof document.characterSet!="undefined")?document.characterSet:document.charset;
this.browserQuirksMode=null;
this.imgURL="images/";
this.popupURL="popups/";
this.htmlRemoveTags=null;
this.flowToolbars=true;
this.toolbarAlign="left";
this.showLoading=false;
this.stripScripts=true;
this.convertUrlsToLinks=true;
this.colorPickerCellSize="6px";
this.colorPickerGranularity=18;
this.colorPickerPosition="bottom,right";
this.colorPickerWebSafe=false;
this.colorPickerSaveColors=20;
this.fullScreen=false;
this.fullScreenMargins=[0,0,0,0];
this.toolbar=[["popupeditor"],["separator","formatblock","fontname","fontsize","bold","italic","underline","strikethrough"],["separator","forecolor","hilitecolor","textindicator"],["separator","subscript","superscript"],["linebreak","separator","justifyleft","justifycenter","justifyright","justifyfull"],["separator","insertorderedlist","insertunorderedlist","outdent","indent"],["separator","inserthorizontalrule","createlink","insertimage","inserttable"],["linebreak","separator","undo","redo","selectall","print"],(Xinha.is_gecko?[]:["cut","copy","paste","overwrite","saveas"]),["separator","killword","clearfonts","removeformat","toggleborders","splitblock","lefttoright","righttoleft"],["separator","htmlmode","showhelp","about"]];
this.fontname={"&mdash; font &mdash;":"","Arial":"arial,helvetica,sans-serif","Courier New":"courier new,courier,monospace","Georgia":"georgia,times new roman,times,serif","Tahoma":"tahoma,arial,helvetica,sans-serif","Times New Roman":"times new roman,times,serif","Verdana":"verdana,arial,helvetica,sans-serif","impact":"impact","WingDings":"wingdings"};
this.fontsize={"&mdash; size &mdash;":"","1 (8 pt)":"1","2 (10 pt)":"2","3 (12 pt)":"3","4 (14 pt)":"4","5 (18 pt)":"5","6 (24 pt)":"6","7 (36 pt)":"7"};
this.formatblock={"&mdash; format &mdash;":"","Heading 1":"h1","Heading 2":"h2","Heading 3":"h3","Heading 4":"h4","Heading 5":"h5","Heading 6":"h6","Normal":"p","Address":"address","Formatted":"pre"};
this.customSelects={};
this.debug=true;
this.URIs={"blank":_editor_url+"popups/blank.html","link":_editor_url+"modules/CreateLink/link.html","insert_image":_editor_url+"modules/InsertImage/insert_image.html","insert_table":_editor_url+"modules/InsertTable/insert_table.html","select_color":_editor_url+"popups/select_color.html","about":_editor_url+"popups/about.html","help":_editor_url+"popups/editor_help.html"};
this.btnList={bold:["Bold",Xinha._lc({key:"button_bold",string:["ed_buttons_main.gif",3,2]},"Xinha"),false,function(e){
e.execCommand("bold");
}],italic:["Italic",Xinha._lc({key:"button_italic",string:["ed_buttons_main.gif",2,2]},"Xinha"),false,function(e){
e.execCommand("italic");
}],underline:["Underline",Xinha._lc({key:"button_underline",string:["ed_buttons_main.gif",2,0]},"Xinha"),false,function(e){
e.execCommand("underline");
}],strikethrough:["Strikethrough",Xinha._lc({key:"button_strikethrough",string:["ed_buttons_main.gif",3,0]},"Xinha"),false,function(e){
e.execCommand("strikethrough");
}],subscript:["Subscript",Xinha._lc({key:"button_subscript",string:["ed_buttons_main.gif",3,1]},"Xinha"),false,function(e){
e.execCommand("subscript");
}],superscript:["Superscript",Xinha._lc({key:"button_superscript",string:["ed_buttons_main.gif",2,1]},"Xinha"),false,function(e){
e.execCommand("superscript");
}],justifyleft:["Justify Left",["ed_buttons_main.gif",0,0],false,function(e){
e.execCommand("justifyleft");
}],justifycenter:["Justify Center",["ed_buttons_main.gif",1,1],false,function(e){
e.execCommand("justifycenter");
}],justifyright:["Justify Right",["ed_buttons_main.gif",1,0],false,function(e){
e.execCommand("justifyright");
}],justifyfull:["Justify Full",["ed_buttons_main.gif",0,1],false,function(e){
e.execCommand("justifyfull");
}],orderedlist:["Ordered List",["ed_buttons_main.gif",0,3],false,function(e){
e.execCommand("insertorderedlist");
}],unorderedlist:["Bulleted List",["ed_buttons_main.gif",1,3],false,function(e){
e.execCommand("insertunorderedlist");
}],insertorderedlist:["Ordered List",["ed_buttons_main.gif",0,3],false,function(e){
e.execCommand("insertorderedlist");
}],insertunorderedlist:["Bulleted List",["ed_buttons_main.gif",1,3],false,function(e){
e.execCommand("insertunorderedlist");
}],outdent:["Decrease Indent",["ed_buttons_main.gif",1,2],false,function(e){
e.execCommand("outdent");
}],indent:["Increase Indent",["ed_buttons_main.gif",0,2],false,function(e){
e.execCommand("indent");
}],forecolor:["Font Color",["ed_buttons_main.gif",3,3],false,function(e){
e.execCommand("forecolor");
}],hilitecolor:["Background Color",["ed_buttons_main.gif",2,3],false,function(e){
e.execCommand("hilitecolor");
}],undo:["Undoes your last action",["ed_buttons_main.gif",4,2],false,function(e){
e.execCommand("undo");
}],redo:["Redoes your last action",["ed_buttons_main.gif",5,2],false,function(e){
e.execCommand("redo");
}],cut:["Cut selection",["ed_buttons_main.gif",5,0],false,function(e,cmd){
e.execCommand(cmd);
}],copy:["Copy selection",["ed_buttons_main.gif",4,0],false,function(e,cmd){
e.execCommand(cmd);
}],paste:["Paste from clipboard",["ed_buttons_main.gif",4,1],false,function(e,cmd){
e.execCommand(cmd);
}],selectall:["Select all","ed_selectall.gif",false,function(e){
e.execCommand("selectall");
}],inserthorizontalrule:["Horizontal Rule",["ed_buttons_main.gif",6,0],false,function(e){
e.execCommand("inserthorizontalrule");
}],createlink:["Insert Web Link",["ed_buttons_main.gif",6,1],false,function(e){
e._createLink();
}],insertimage:["Insert/Modify Image",["ed_buttons_main.gif",6,3],false,function(e){
e.execCommand("insertimage");
}],inserttable:["Insert Table",["ed_buttons_main.gif",6,2],false,function(e){
e.execCommand("inserttable");
}],htmlmode:["Toggle HTML Source",["ed_buttons_main.gif",7,0],true,function(e){
e.execCommand("htmlmode");
}],toggleborders:["Toggle Borders",["ed_buttons_main.gif",7,2],false,function(e){
e._toggleBorders();
}],print:["Print document",["ed_buttons_main.gif",8,1],false,function(e){
if(Xinha.is_gecko){
e._iframe.contentWindow.print();
}else{
e.focusEditor();
print();
}
}],saveas:["Save as","ed_saveas.gif",false,function(e){
e.execCommand("saveas",false,"noname.htm");
}],about:["About this editor",["ed_buttons_main.gif",8,2],true,function(e){
e.execCommand("about");
}],showhelp:["Help using editor",["ed_buttons_main.gif",9,2],true,function(e){
e.execCommand("showhelp");
}],splitblock:["Split Block","ed_splitblock.gif",false,function(e){
e._splitBlock();
}],lefttoright:["Direction left to right",["ed_buttons_main.gif",0,4],false,function(e){
e.execCommand("lefttoright");
}],righttoleft:["Direction right to left",["ed_buttons_main.gif",1,4],false,function(e){
e.execCommand("righttoleft");
}],overwrite:["Insert/Overwrite","ed_overwrite.gif",false,function(e){
e.execCommand("overwrite");
}],wordclean:["MS Word Cleaner",["ed_buttons_main.gif",5,3],false,function(e){
e._wordClean();
}],clearfonts:["Clear Inline Font Specifications",["ed_buttons_main.gif",5,4],true,function(e){
e._clearFonts();
}],removeformat:["Remove formatting",["ed_buttons_main.gif",4,4],false,function(e){
e.execCommand("removeformat");
}],killword:["Clear MSOffice tags",["ed_buttons_main.gif",4,3],false,function(e){
e.execCommand("killword");
}]};
for(var i in this.btnList){
var btn=this.btnList[i];
if(typeof btn!="object"){
continue;
}
if(typeof btn[1]!="string"){
btn[1][0]=_editor_url+this.imgURL+btn[1][0];
}else{
btn[1]=_editor_url+this.imgURL+btn[1];
}
btn[0]=Xinha._lc(btn[0]);
}
};
Xinha.Config.prototype.registerButton=function(id,_3c,_3d,_3e,_3f,_40){
var _41;
if(typeof id=="string"){
_41=id;
}else{
if(typeof id=="object"){
_41=id.id;
}else{
alert("ERROR [Xinha.Config::registerButton]:\ninvalid arguments");
return false;
}
}
switch(typeof id){
case "string":
this.btnList[id]=[_3c,_3d,_3e,_3f,_40];
break;
case "object":
this.btnList[id.id]=[id.tooltip,id.image,id.textMode,id.action,id.context];
break;
}
};
Xinha.prototype.registerPanel=function(_42,_43){
if(!_42){
_42="right";
}
this.setLoadingMessage("Register "+_42+" panel ");
var _44=this.addPanel(_42);
if(_43){
_43.drawPanelIn(_44);
}
};
Xinha.Config.prototype.registerDropdown=function(_45){
this.customSelects[_45.id]=_45;
};
Xinha.Config.prototype.hideSomeButtons=function(_46){
var _47=this.toolbar;
for(var i=_47.length;--i>=0;){
var _49=_47[i];
for(var j=_49.length;--j>=0;){
if(_46.indexOf(" "+_49[j]+" ")>=0){
var len=1;
if(/separator|space/.test(_49[j+1])){
len=2;
}
_49.splice(j,len);
}
}
}
};
Xinha.Config.prototype.addToolbarElement=function(id,_4d,_4e){
var _4f=this.toolbar;
var a,i,j,o,sid;
var _51=false;
var _52=false;
var _53=0;
var _54=0;
var _55=0;
var _56=false;
var _57=false;
if((id&&typeof id=="object")&&(id.constructor==Array)){
_51=true;
}
if((_4d&&typeof _4d=="object")&&(_4d.constructor==Array)){
_52=true;
_53=_4d.length;
}
if(_51){
for(i=0;i<id.length;++i){
if((id[i]!="separator")&&(id[i].indexOf("T[")!==0)){
sid=id[i];
}
}
}else{
sid=id;
}
for(i=0;i<_4f.length;++i){
a=_4f[i];
for(j=0;j<a.length;++j){
if(a[j]==sid){
return;
}
}
}
for(i=0;!_57&&i<_4f.length;++i){
a=_4f[i];
for(j=0;!_57&&j<a.length;++j){
if(_52){
for(o=0;o<_53;++o){
if(a[j]==_4d[o]){
if(o===0){
_57=true;
j--;
break;
}else{
_55=i;
_54=j;
_53=o;
}
}
}
}else{
if(a[j]==_4d){
_57=true;
break;
}
}
}
}
if(!_57&&_52){
if(_4d.length!=_53){
j=_54;
a=_4f[_55];
_57=true;
}
}
if(_57){
if(_4e===0){
if(_51){
a[j]=id[id.length-1];
for(i=id.length-1;--i>=0;){
a.splice(j,0,id[i]);
}
}else{
a[j]=id;
}
}else{
if(_4e<0){
j=j+_4e+1;
}else{
if(_4e>0){
j=j+_4e;
}
}
if(_51){
for(i=id.length;--i>=0;){
a.splice(j,0,id[i]);
}
}else{
a.splice(j,0,id);
}
}
}else{
_4f[0].splice(0,0,"separator");
if(_51){
for(i=id.length;--i>=0;){
_4f[0].splice(0,0,id[i]);
}
}else{
_4f[0].splice(0,0,id);
}
}
};
Xinha.Config.prototype.removeToolbarElement=Xinha.Config.prototype.hideSomeButtons;
Xinha.replaceAll=function(_58){
var tas=document.getElementsByTagName("textarea");
for(var i=tas.length;i>0;(new Xinha(tas[--i],_58)).generate()){
}
};
Xinha.replace=function(id,_5c){
var ta=Xinha.getElementById("textarea",id);
return ta?(new Xinha(ta,_5c)).generate():null;
};
Xinha.prototype._createToolbar=function(){
this.setLoadingMessage(Xinha._lc("Create Toolbar"));
var _5e=this;
var _5f=document.createElement("div");
this._toolBar=this._toolbar=_5f;
_5f.className="toolbar";
_5f.unselectable="1";
_5f.align=this.config.toolbarAlign;
Xinha.freeLater(this,"_toolBar");
Xinha.freeLater(this,"_toolbar");
var _60=null;
var _61={};
this._toolbarObjects=_61;
this._createToolbar1(_5e,_5f,_61);
this._htmlArea.appendChild(_5f);
return _5f;
};
Xinha.prototype._setConfig=function(_62){
this.config=_62;
};
Xinha.prototype._addToolbar=function(){
this._createToolbar1(this,this._toolbar,this._toolbarObjects);
};
Xinha._createToolbarBreakingElement=function(){
var brk=document.createElement("div");
brk.style.height="1px";
brk.style.width="1px";
brk.style.lineHeight="1px";
brk.style.fontSize="1px";
brk.style.clear="both";
return brk;
};
Xinha.prototype._createToolbar1=function(_64,_65,_66){
var _67;
if(_64.config.flowToolbars){
_65.appendChild(Xinha._createToolbarBreakingElement());
}
function newLine(){
if(typeof _67!="undefined"&&_67.childNodes.length===0){
return;
}
var _68=document.createElement("table");
_68.border="0px";
_68.cellSpacing="0px";
_68.cellPadding="0px";
if(_64.config.flowToolbars){
if(Xinha.is_ie){
_68.style.styleFloat="left";
}else{
_68.style.cssFloat="left";
}
}
_65.appendChild(_68);
var _69=document.createElement("tbody");
_68.appendChild(_69);
_67=document.createElement("tr");
_69.appendChild(_67);
_68.className="toolbarRow";
}
newLine();
function setButtonStatus(id,_6b){
var _6c=this[id];
var el=this.element;
if(_6c!=_6b){
switch(id){
case "enabled":
if(_6b){
Xinha._removeClass(el,"buttonDisabled");
el.disabled=false;
}else{
Xinha._addClass(el,"buttonDisabled");
el.disabled=true;
}
break;
case "active":
if(_6b){
Xinha._addClass(el,"buttonPressed");
}else{
Xinha._removeClass(el,"buttonPressed");
}
break;
}
this[id]=_6b;
}
}
function createSelect(txt){
var _6f=null;
var el=null;
var cmd=null;
var _72=_64.config.customSelects;
var _73=null;
var _74="";
switch(txt){
case "fontsize":
case "fontname":
case "formatblock":
_6f=_64.config[txt];
cmd=txt;
break;
default:
cmd=txt;
var _75=_72[cmd];
if(typeof _75!="undefined"){
_6f=_75.options;
_73=_75.context;
if(typeof _75.tooltip!="undefined"){
_74=_75.tooltip;
}
}else{
alert("ERROR [createSelect]:\nCan't find the requested dropdown definition");
}
break;
}
if(_6f){
el=document.createElement("select");
el.title=_74;
var obj={name:txt,element:el,enabled:true,text:false,cmd:cmd,state:setButtonStatus,context:_73};
Xinha.freeLater(obj);
_66[txt]=obj;
for(var i in _6f){
if(typeof (_6f[i])!="string"){
continue;
}
var op=document.createElement("option");
op.innerHTML=Xinha._lc(i);
op.value=_6f[i];
el.appendChild(op);
}
Xinha._addEvent(el,"change",function(){
_64._comboSelected(el,txt);
});
}
return el;
}
function createButton(txt){
var el,btn,obj=null;
switch(txt){
case "separator":
if(_64.config.flowToolbars){
newLine();
}
el=document.createElement("div");
el.className="separator";
break;
case "space":
el=document.createElement("div");
el.className="space";
break;
case "linebreak":
newLine();
return false;
case "textindicator":
el=document.createElement("div");
el.appendChild(document.createTextNode("A"));
el.className="indicator";
el.title=Xinha._lc("Current style");
obj={name:txt,element:el,enabled:true,active:false,text:false,cmd:"textindicator",state:setButtonStatus};
Xinha.freeLater(obj);
_66[txt]=obj;
break;
default:
btn=_64.config.btnList[txt];
}
if(!el&&btn){
el=document.createElement("a");
el.style.display="block";
el.href="javascript:void(0)";
el.style.textDecoration="none";
el.title=btn[0];
el.className="button";
el.style.direction="ltr";
obj={name:txt,element:el,enabled:true,active:false,text:btn[2],cmd:btn[3],state:setButtonStatus,context:btn[4]||null};
Xinha.freeLater(el);
Xinha.freeLater(obj);
_66[txt]=obj;
el.ondrag=function(){
return false;
};
Xinha._addEvent(el,"mouseout",function(ev){
if(obj.enabled){
Xinha._removeClass(el,"buttonActive");
if(obj.active){
Xinha._addClass(el,"buttonPressed");
}
}
});
Xinha._addEvent(el,"mousedown",function(ev){
if(obj.enabled){
Xinha._addClass(el,"buttonActive");
Xinha._removeClass(el,"buttonPressed");
Xinha._stopEvent(Xinha.is_ie?window.event:ev);
}
});
Xinha._addEvent(el,"click",function(ev){
ev=Xinha.is_ie?window.event:ev;
_64.btnClickEvent=ev;
if(obj.enabled){
Xinha._removeClass(el,"buttonActive");
if(Xinha.is_gecko){
_64.activateEditor();
}
obj.cmd(_64,obj.name,obj);
Xinha._stopEvent(ev);
}
});
var _7e=Xinha.makeBtnImg(btn[1]);
var img=_7e.firstChild;
Xinha.freeLater(_7e);
Xinha.freeLater(img);
el.appendChild(_7e);
obj.imgel=img;
obj.swapImage=function(_80){
if(typeof _80!="string"){
img.src=_80[0];
img.style.position="relative";
img.style.top=_80[2]?("-"+(18*(_80[2]+1))+"px"):"-18px";
img.style.left=_80[1]?("-"+(18*(_80[1]+1))+"px"):"-18px";
}else{
obj.imgel.src=_80;
img.style.top="0px";
img.style.left="0px";
}
};
}else{
if(!el){
el=createSelect(txt);
}
}
return el;
}
var _81=true;
for(var i=0;i<this.config.toolbar.length;++i){
if(!_81){
}else{
_81=false;
}
if(this.config.toolbar[i]===null){
this.config.toolbar[i]=["separator"];
}
var _83=this.config.toolbar[i];
for(var j=0;j<_83.length;++j){
var _85=_83[j];
var _86;
if(/^([IT])\[(.*?)\]/.test(_85)){
var _87=RegExp.$1=="I";
var _88=RegExp.$2;
if(_87){
_88=Xinha._lc(_88);
}
_86=document.createElement("td");
_67.appendChild(_86);
_86.className="label";
_86.innerHTML=_88;
}else{
if(typeof _85!="function"){
var _89=createButton(_85);
if(_89){
_86=document.createElement("td");
_86.className="toolbarElement";
_67.appendChild(_86);
_86.appendChild(_89);
}else{
if(_89===null){
alert("FIXME: Unknown toolbar item: "+_85);
}
}
}
}
}
}
if(_64.config.flowToolbars){
_65.appendChild(Xinha._createToolbarBreakingElement());
}
return _65;
};
var use_clone_img=false;
Xinha.makeBtnImg=function(_8a,doc){
if(!doc){
doc=document;
}
if(!doc._xinhaImgCache){
doc._xinhaImgCache={};
Xinha.freeLater(doc._xinhaImgCache);
}
var _8c=null;
if(Xinha.is_ie&&((!doc.compatMode)||(doc.compatMode&&doc.compatMode=="BackCompat"))){
_8c=doc.createElement("span");
}else{
_8c=doc.createElement("div");
_8c.style.position="relative";
}
_8c.style.overflow="hidden";
_8c.style.width="18px";
_8c.style.height="18px";
_8c.className="buttonImageContainer";
var img=null;
if(typeof _8a=="string"){
if(doc._xinhaImgCache[_8a]){
img=doc._xinhaImgCache[_8a].cloneNode();
}else{
img=doc.createElement("img");
img.src=_8a;
img.style.width="18px";
img.style.height="18px";
if(use_clone_img){
doc._xinhaImgCache[_8a]=img.cloneNode();
}
}
}else{
if(doc._xinhaImgCache[_8a[0]]){
img=doc._xinhaImgCache[_8a[0]].cloneNode();
}else{
img=doc.createElement("img");
img.src=_8a[0];
img.style.position="relative";
if(use_clone_img){
doc._xinhaImgCache[_8a[0]]=img.cloneNode();
}
}
img.style.top=_8a[2]?("-"+(18*(_8a[2]+1))+"px"):"-18px";
img.style.left=_8a[1]?("-"+(18*(_8a[1]+1))+"px"):"-18px";
}
_8c.appendChild(img);
return _8c;
};
Xinha.prototype._createStatusBar=function(){
this.setLoadingMessage(Xinha._lc("Create Statusbar"));
var _8e=document.createElement("div");
_8e.className="statusBar";
this._statusBar=_8e;
Xinha.freeLater(this,"_statusBar");
var div=document.createElement("span");
div.className="statusBarTree";
div.innerHTML=Xinha._lc("Path")+": ";
this._statusBarTree=div;
Xinha.freeLater(this,"_statusBarTree");
this._statusBar.appendChild(div);
div=document.createElement("span");
div.innerHTML=Xinha._lc("You are in TEXT MODE.  Use the [<>] button to switch back to WYSIWYG.");
div.style.display="none";
this._statusBarTextMode=div;
Xinha.freeLater(this,"_statusBarTextMode");
this._statusBar.appendChild(div);
if(!this.config.statusBar){
_8e.style.display="none";
}
return _8e;
};
Xinha.prototype.generate=function(){
if(!Xinha.isSupportedBrowser){
return;
}
var i;
var _91=this;
var url;
var _93=false;
var _94=document.getElementsByTagName("link");
if(!document.getElementById("XinhaCoreDesign")){
_editor_css=(typeof _editor_css=="string")?_editor_css:"Xinha.css";
for(i=0;i<_94.length;i++){
if((_94[i].rel=="stylesheet")&&(_94[i].href==_editor_url+_editor_css)){
_93=true;
}
}
if(!_93){
Xinha.loadStyle(_editor_css,null,"XinhaCoreDesign",true);
}
}
if(_editor_skin!==""&&!document.getElementById("XinhaSkin")){
_93=false;
for(i=0;i<_94.length;i++){
if((_94[i].rel=="stylesheet")&&(_94[i].href==_editor_url+"skins/"+_editor_skin+"/skin.css")){
_93=true;
}
}
if(!_93){
Xinha.loadStyle("skins/"+_editor_skin+"/skin.css",null,"XinhaSkin");
}
}
if(Xinha.is_ie){
url=_editor_url+"modules/InternetExplorer/InternetExplorer.js";
if(!Xinha.loadPlugins([{plugin:"InternetExplorer",url:url}],function(){
_91.generate();
})){
return false;
}
_91._browserSpecificPlugin=_91.registerPlugin("InternetExplorer");
}else{
if(Xinha.is_webkit){
url=_editor_url+"modules/WebKit/WebKit.js";
if(!Xinha.loadPlugins([{plugin:"WebKit",url:url}],function(){
_91.generate();
})){
return false;
}
_91._browserSpecificPlugin=_91.registerPlugin("WebKit");
}else{
if(Xinha.is_opera){
url=_editor_url+"modules/Opera/Opera.js";
if(!Xinha.loadPlugins([{plugin:"Opera",url:url}],function(){
_91.generate();
})){
return false;
}
_91._browserSpecificPlugin=_91.registerPlugin("Opera");
}else{
if(Xinha.is_gecko){
url=_editor_url+"modules/Gecko/Gecko.js";
if(!Xinha.loadPlugins([{plugin:"Gecko",url:url}],function(){
_91.generate();
})){
return false;
}
_91._browserSpecificPlugin=_91.registerPlugin("Gecko");
}
}
}
}
if(typeof Dialog=="undefined"&&!Xinha._loadback(_editor_url+"modules/Dialogs/dialog.js",this.generate,this)){
return false;
}
if(typeof Xinha.Dialog=="undefined"&&!Xinha._loadback(_editor_url+"modules/Dialogs/inline-dialog.js",this.generate,this)){
return false;
}
url=_editor_url+"modules/FullScreen/full-screen.js";
if(!Xinha.loadPlugins([{plugin:"FullScreen",url:url}],function(){
_91.generate();
})){
return false;
}
url=_editor_url+"modules/ColorPicker/ColorPicker.js";
if(!Xinha.loadPlugins([{plugin:"ColorPicker",url:url}],function(){
_91.generate();
})){
return false;
}else{
if(typeof ColorPicker!="undefined"){
_91.registerPlugin("ColorPicker");
}
}
var _95=_91.config.toolbar;
for(i=_95.length;--i>=0;){
for(var j=_95[i].length;--j>=0;){
switch(_95[i][j]){
case "popupeditor":
_91.registerPlugin("FullScreen");
break;
case "insertimage":
url=_editor_url+"modules/InsertImage/insert_image.js";
if(typeof Xinha.prototype._insertImage=="undefined"&&!Xinha.loadPlugins([{plugin:"InsertImage",url:url}],function(){
_91.generate();
})){
return false;
}else{
if(typeof InsertImage!="undefined"){
_91.registerPlugin("InsertImage");
}
}
break;
case "createlink":
url=_editor_url+"modules/CreateLink/link.js";
if(typeof Linker=="undefined"&&!Xinha.loadPlugins([{plugin:"CreateLink",url:url}],function(){
_91.generate();
})){
return false;
}else{
if(typeof CreateLink!="undefined"){
_91.registerPlugin("CreateLink");
}
}
break;
case "inserttable":
url=_editor_url+"modules/InsertTable/insert_table.js";
if(!Xinha.loadPlugins([{plugin:"InsertTable",url:url}],function(){
_91.generate();
})){
return false;
}else{
if(typeof InsertTable!="undefined"){
_91.registerPlugin("InsertTable");
}
}
break;
}
}
}
if(Xinha.is_gecko&&_91.config.mozParaHandler!="built-in"){
if(!Xinha.loadPlugins([{plugin:"EnterParagraphs",url:_editor_url+"modules/Gecko/paraHandlerBest.js"}],function(){
_91.generate();
})){
return false;
}
_91.registerPlugin("EnterParagraphs");
}
if(Xinha.ie_version==8){
this.config.getHtmlMethod="TransformInnerHTML";
}
switch(this.config.getHtmlMethod){
case "TransformInnerHTML":
var _97=_editor_url+"modules/GetHtml/TransformInnerHTML.js";
break;
default:
var _97=_editor_url+"modules/GetHtml/DOMwalk.js";
break;
}
if(!Xinha.loadPlugins([{plugin:"GetHtmlImplementation",url:_97}],function(){
_91.generate();
})){
return false;
}else{
_91.registerPlugin("GetHtmlImplementation");
}
this.setLoadingMessage(Xinha._lc("Generate Xinha framework"));
this._framework={"table":document.createElement("table"),"tbody":document.createElement("tbody"),"tb_row":document.createElement("tr"),"tb_cell":document.createElement("td"),"tp_row":document.createElement("tr"),"tp_cell":this._panels.top.container,"ler_row":document.createElement("tr"),"lp_cell":this._panels.left.container,"ed_cell":document.createElement("td"),"rp_cell":this._panels.right.container,"bp_row":document.createElement("tr"),"bp_cell":this._panels.bottom.container,"sb_row":document.createElement("tr"),"sb_cell":document.createElement("td")};
Xinha.freeLater(this._framework);
var fw=this._framework;
fw.table.border="0";
fw.table.cellPadding="0";
fw.table.cellSpacing="0";
fw.tb_row.style.verticalAlign="top";
fw.tp_row.style.verticalAlign="top";
fw.ler_row.style.verticalAlign="top";
fw.bp_row.style.verticalAlign="top";
fw.sb_row.style.verticalAlign="top";
fw.ed_cell.style.position="relative";
fw.tb_row.appendChild(fw.tb_cell);
fw.tb_cell.colSpan=3;
fw.tp_row.appendChild(fw.tp_cell);
fw.tp_cell.colSpan=3;
fw.ler_row.appendChild(fw.lp_cell);
fw.ler_row.appendChild(fw.ed_cell);
fw.ler_row.appendChild(fw.rp_cell);
fw.bp_row.appendChild(fw.bp_cell);
fw.bp_cell.colSpan=3;
fw.sb_row.appendChild(fw.sb_cell);
fw.sb_cell.colSpan=3;
fw.tbody.appendChild(fw.tb_row);
fw.tbody.appendChild(fw.tp_row);
fw.tbody.appendChild(fw.ler_row);
fw.tbody.appendChild(fw.bp_row);
fw.tbody.appendChild(fw.sb_row);
fw.table.appendChild(fw.tbody);
var _99=this._framework.table;
this._htmlArea=_99;
Xinha.freeLater(this,"_htmlArea");
_99.className="htmlarea";
this._framework.tb_cell.appendChild(this._createToolbar());
var _9a=document.createElement("iframe");
_9a.src=this.popupURL(_91.config.URIs.blank);
_9a.id="XinhaIFrame_"+this._textArea.id;
this._framework.ed_cell.appendChild(_9a);
this._iframe=_9a;
this._iframe.className="xinha_iframe";
Xinha.freeLater(this,"_iframe");
var _9b=this._createStatusBar();
this._framework.sb_cell.appendChild(_9b);
var _9c=this._textArea;
_9c.parentNode.insertBefore(_99,_9c);
_9c.className="xinha_textarea";
Xinha.removeFromParent(_9c);
this._framework.ed_cell.appendChild(_9c);
Xinha.addDom0Event(this._textArea,"click",function(){
if(Xinha._currentlyActiveEditor!=this){
_91.updateToolbar();
}
return true;
});
if(_9c.form){
Xinha.prependDom0Event(this._textArea.form,"submit",function(){
_91.firePluginEvent("onBeforeSubmit");
_91._textArea.value=_91.outwardHtml(_91.getHTML());
return true;
});
var _9d=_9c.value;
Xinha.prependDom0Event(this._textArea.form,"reset",function(){
_91.setHTML(_91.inwardHtml(_9d));
_91.updateToolbar();
return true;
});
if(!_9c.form.xinha_submit){
try{
_9c.form.xinha_submit=_9c.form.submit;
_9c.form.submit=function(){
this.onsubmit();
this.xinha_submit();
};
}
catch(ex){
}
}
}
Xinha.prependDom0Event(window,"unload",function(){
_91.firePluginEvent("onBeforeUnload");
_9c.value=_91.outwardHtml(_91.getHTML());
if(!Xinha.is_ie){
_99.parentNode.replaceChild(_9c,_99);
}
return true;
});
_9c.style.display="none";
_91.initSize();
this.setLoadingMessage(Xinha._lc("Finishing"));
_91._iframeLoadDone=false;
if(Xinha.is_opera){
_91.initIframe();
}else{
Xinha._addEvent(this._iframe,"load",function(e){
if(!_91._iframeLoadDone){
_91._iframeLoadDone=true;
_91.initIframe();
}
return true;
});
}
};
Xinha.prototype.initSize=function(){
this.setLoadingMessage(Xinha._lc("Init editor size"));
var _9f=this;
var _a0=null;
var _a1=null;
switch(this.config.width){
case "auto":
_a0=this._initial_ta_size.w;
break;
case "toolbar":
_a0=this._toolBar.offsetWidth+"px";
break;
default:
_a0=/[^0-9]/.test(this.config.width)?this.config.width:this.config.width+"px";
break;
}
switch(this.config.height){
case "auto":
_a1=this._initial_ta_size.h;
break;
default:
_a1=/[^0-9]/.test(this.config.height)?this.config.height:this.config.height+"px";
break;
}
this.sizeEditor(_a0,_a1,this.config.sizeIncludesBars,this.config.sizeIncludesPanels);
this.notifyOn("panel_change",function(){
_9f.sizeEditor();
});
};
Xinha.prototype.sizeEditor=function(_a2,_a3,_a4,_a5){
if(this._risizing){
return;
}
this._risizing=true;
this.notifyOf("before_resize",{width:_a2,height:_a3});
this.firePluginEvent("onBeforeResize",_a2,_a3);
this._iframe.style.height="100%";
this._textArea.style.height="100%";
this._iframe.style.width="";
this._textArea.style.width="";
if(_a4!==null){
this._htmlArea.sizeIncludesToolbars=_a4;
}
if(_a5!==null){
this._htmlArea.sizeIncludesPanels=_a5;
}
if(_a2){
this._htmlArea.style.width=_a2;
if(!this._htmlArea.sizeIncludesPanels){
var _a6=this._panels.right;
if(_a6.on&&_a6.panels.length&&Xinha.hasDisplayedChildren(_a6.div)){
this._htmlArea.style.width=(this._htmlArea.offsetWidth+parseInt(this.config.panel_dimensions.right,10))+"px";
}
var _a7=this._panels.left;
if(_a7.on&&_a7.panels.length&&Xinha.hasDisplayedChildren(_a7.div)){
this._htmlArea.style.width=(this._htmlArea.offsetWidth+parseInt(this.config.panel_dimensions.left,10))+"px";
}
}
}
if(_a3){
this._htmlArea.style.height=_a3;
if(!this._htmlArea.sizeIncludesToolbars){
this._htmlArea.style.height=(this._htmlArea.offsetHeight+this._toolbar.offsetHeight+this._statusBar.offsetHeight)+"px";
}
if(!this._htmlArea.sizeIncludesPanels){
var _a8=this._panels.top;
if(_a8.on&&_a8.panels.length&&Xinha.hasDisplayedChildren(_a8.div)){
this._htmlArea.style.height=(this._htmlArea.offsetHeight+parseInt(this.config.panel_dimensions.top,10))+"px";
}
var _a9=this._panels.bottom;
if(_a9.on&&_a9.panels.length&&Xinha.hasDisplayedChildren(_a9.div)){
this._htmlArea.style.height=(this._htmlArea.offsetHeight+parseInt(this.config.panel_dimensions.bottom,10))+"px";
}
}
}
_a2=this._htmlArea.offsetWidth;
_a3=this._htmlArea.offsetHeight;
var _aa=this._panels;
var _ab=this;
var _ac=1;
function panel_is_alive(pan){
if(_aa[pan].on&&_aa[pan].panels.length&&Xinha.hasDisplayedChildren(_aa[pan].container)){
_aa[pan].container.style.display="";
return true;
}else{
_aa[pan].container.style.display="none";
return false;
}
}
if(panel_is_alive("left")){
_ac+=1;
}
if(panel_is_alive("right")){
_ac+=1;
}
this._framework.tb_cell.colSpan=_ac;
this._framework.tp_cell.colSpan=_ac;
this._framework.bp_cell.colSpan=_ac;
this._framework.sb_cell.colSpan=_ac;
if(!this._framework.tp_row.childNodes.length){
Xinha.removeFromParent(this._framework.tp_row);
}else{
if(!Xinha.hasParentNode(this._framework.tp_row)){
this._framework.tbody.insertBefore(this._framework.tp_row,this._framework.ler_row);
}
}
if(!this._framework.bp_row.childNodes.length){
Xinha.removeFromParent(this._framework.bp_row);
}else{
if(!Xinha.hasParentNode(this._framework.bp_row)){
this._framework.tbody.insertBefore(this._framework.bp_row,this._framework.ler_row.nextSibling);
}
}
if(!this.config.statusBar){
Xinha.removeFromParent(this._framework.sb_row);
}else{
if(!Xinha.hasParentNode(this._framework.sb_row)){
this._framework.table.appendChild(this._framework.sb_row);
}
}
this._framework.lp_cell.style.width=this.config.panel_dimensions.left;
this._framework.rp_cell.style.width=this.config.panel_dimensions.right;
this._framework.tp_cell.style.height=this.config.panel_dimensions.top;
this._framework.bp_cell.style.height=this.config.panel_dimensions.bottom;
this._framework.tb_cell.style.height=this._toolBar.offsetHeight+"px";
this._framework.sb_cell.style.height=this._statusBar.offsetHeight+"px";
var _ae=_a3-this._toolBar.offsetHeight-this._statusBar.offsetHeight;
if(panel_is_alive("top")){
_ae-=parseInt(this.config.panel_dimensions.top,10);
}
if(panel_is_alive("bottom")){
_ae-=parseInt(this.config.panel_dimensions.bottom,10);
}
this._iframe.style.height=_ae+"px";
var _af=_a2;
if(panel_is_alive("left")){
_af-=parseInt(this.config.panel_dimensions.left,10);
}
if(panel_is_alive("right")){
_af-=parseInt(this.config.panel_dimensions.right,10);
}
var _b0=(this.config.iframeWidth)?parseInt(this.config.iframeWidth,10):null;
this._iframe.style.width=(_b0&&_b0<_af)?_b0+"px":_af+"px";
this._textArea.style.height=this._iframe.style.height;
this._textArea.style.width=this._iframe.style.width;
this.notifyOf("resize",{width:this._htmlArea.offsetWidth,height:this._htmlArea.offsetHeight});
this.firePluginEvent("onResize",this._htmlArea.offsetWidth,this._htmlArea.offsetWidth);
this._risizing=false;
};
Xinha.prototype.registerPanel=function(_b1,_b2){
if(!_b1){
_b1="right";
}
this.setLoadingMessage("Register "+_b1+" panel ");
var _b3=this.addPanel(_b1);
if(_b2){
_b2.drawPanelIn(_b3);
}
};
Xinha.prototype.addPanel=function(_b4){
var div=document.createElement("div");
div.side=_b4;
if(_b4=="left"||_b4=="right"){
div.style.width=this.config.panel_dimensions[_b4];
if(this._iframe){
div.style.height=this._iframe.style.height;
}
}
Xinha.addClasses(div,"panel");
this._panels[_b4].panels.push(div);
this._panels[_b4].div.appendChild(div);
this.notifyOf("panel_change",{"action":"add","panel":div});
this.firePluginEvent("onPanelChange","add",div);
return div;
};
Xinha.prototype.removePanel=function(_b6){
this._panels[_b6.side].div.removeChild(_b6);
var _b7=[];
for(var i=0;i<this._panels[_b6.side].panels.length;i++){
if(this._panels[_b6.side].panels[i]!=_b6){
_b7.push(this._panels[_b6.side].panels[i]);
}
}
this._panels[_b6.side].panels=_b7;
this.notifyOf("panel_change",{"action":"remove","panel":_b6});
this.firePluginEvent("onPanelChange","remove",_b6);
};
Xinha.prototype.hidePanel=function(_b9){
if(_b9&&_b9.style.display!="none"){
try{
var pos=this.scrollPos(this._iframe.contentWindow);
}
catch(e){
}
_b9.style.display="none";
this.notifyOf("panel_change",{"action":"hide","panel":_b9});
this.firePluginEvent("onPanelChange","hide",_b9);
try{
this._iframe.contentWindow.scrollTo(pos.x,pos.y);
}
catch(e){
}
}
};
Xinha.prototype.showPanel=function(_bb){
if(_bb&&_bb.style.display=="none"){
try{
var pos=this.scrollPos(this._iframe.contentWindow);
}
catch(e){
}
_bb.style.display="";
this.notifyOf("panel_change",{"action":"show","panel":_bb});
this.firePluginEvent("onPanelChange","show",_bb);
try{
this._iframe.contentWindow.scrollTo(pos.x,pos.y);
}
catch(e){
}
}
};
Xinha.prototype.hidePanels=function(_bd){
if(typeof _bd=="undefined"){
_bd=["left","right","top","bottom"];
}
var _be=[];
for(var i=0;i<_bd.length;i++){
if(this._panels[_bd[i]].on){
_be.push(_bd[i]);
this._panels[_bd[i]].on=false;
}
}
this.notifyOf("panel_change",{"action":"multi_hide","sides":_bd});
this.firePluginEvent("onPanelChange","multi_hide",_bd);
};
Xinha.prototype.showPanels=function(_c0){
if(typeof _c0=="undefined"){
_c0=["left","right","top","bottom"];
}
var _c1=[];
for(var i=0;i<_c0.length;i++){
if(!this._panels[_c0[i]].on){
_c1.push(_c0[i]);
this._panels[_c0[i]].on=true;
}
}
this.notifyOf("panel_change",{"action":"multi_show","sides":_c0});
this.firePluginEvent("onPanelChange","multi_show",_c0);
};
Xinha.objectProperties=function(obj){
var _c4=[];
for(var x in obj){
_c4[_c4.length]=x;
}
return _c4;
};
Xinha.prototype.editorIsActivated=function(){
try{
return Xinha.is_designMode?this._doc.designMode=="on":this._doc.body.contentEditable;
}
catch(ex){
return false;
}
};
Xinha._someEditorHasBeenActivated=false;
Xinha._currentlyActiveEditor=null;
Xinha.prototype.activateEditor=function(){
if(Xinha._currentlyActiveEditor){
if(Xinha._currentlyActiveEditor==this){
return true;
}
Xinha._currentlyActiveEditor.deactivateEditor();
}
if(Xinha.is_designMode&&this._doc.designMode!="on"){
try{
if(this._iframe.style.display=="none"){
this._iframe.style.display="";
this._doc.designMode="on";
this._iframe.style.display="none";
}else{
this._doc.designMode="on";
}
}
catch(ex){
}
}else{
if(Xinha.is_ie&&this._doc.body.contentEditable!==true){
this._doc.body.contentEditable=true;
}
}
Xinha._someEditorHasBeenActivated=true;
Xinha._currentlyActiveEditor=this;
var _c6=this;
this.enableToolbar();
};
Xinha.prototype.deactivateEditor=function(){
this.disableToolbar();
if(Xinha.is_designMode&&this._doc.designMode!="off"){
try{
this._doc.designMode="off";
}
catch(ex){
}
}else{
if(!Xinha.is_designMode&&this._doc.body.contentEditable!==false){
this._doc.body.contentEditable=false;
}
}
if(Xinha._currentlyActiveEditor!=this){
return;
}
Xinha._currentlyActiveEditor=false;
};
Xinha.prototype.initIframe=function(){
this.disableToolbar();
var doc=null;
var _c8=this;
try{
if(_c8._iframe.contentDocument){
this._doc=_c8._iframe.contentDocument;
}else{
this._doc=_c8._iframe.contentWindow.document;
}
doc=this._doc;
if(!doc){
if(Xinha.is_gecko){
setTimeout(function(){
_c8.initIframe();
},50);
return false;
}else{
alert("ERROR: IFRAME can't be initialized.");
}
}
}
catch(ex){
setTimeout(function(){
_c8.initIframe();
},50);
}
Xinha.freeLater(this,"_doc");
doc.open("text/html","replace");
var _c9="";
if(_c8.config.browserQuirksMode===false){
var _ca="<!DOCTYPE HTML PUBLIC \"-//W3C//DTD HTML 4.01 Transitional//EN\" \"http://www.w3.org/TR/html4/loose.dtd\">";
}else{
if(_c8.config.browserQuirksMode===true){
var _ca="";
}else{
var _ca=Xinha.getDoctype(document);
}
}
if(!_c8.config.fullPage){
_c9+=_ca+"\n";
_c9+="<html>\n";
_c9+="<head>\n";
_c9+="<meta http-equiv=\"Content-Type\" content=\"text/html; charset="+_c8.config.charSet+"\">\n";
if(typeof _c8.config.baseHref!="undefined"&&_c8.config.baseHref!==null){
_c9+="<base href=\""+_c8.config.baseHref+"\"/>\n";
}
_c9+=Xinha.addCoreCSS();
if(typeof _c8.config.pageStyleSheets!=="undefined"){
for(var i=0;i<_c8.config.pageStyleSheets.length;i++){
if(_c8.config.pageStyleSheets[i].length>0){
_c9+="<link rel=\"stylesheet\" type=\"text/css\" href=\""+_c8.config.pageStyleSheets[i]+"\">";
}
}
}
if(_c8.config.pageStyle){
_c9+="<style type=\"text/css\">\n"+_c8.config.pageStyle+"\n</style>";
}
_c9+="</head>\n";
_c9+="<body"+(_c8.config.bodyID?(" id=\""+_c8.config.bodyID+"\""):"")+">\n";
_c9+=_c8.inwardHtml(_c8._textArea.value);
_c9+="</body>\n";
_c9+="</html>";
}else{
_c9=_c8.inwardHtml(_c8._textArea.value);
if(_c9.match(Xinha.RE_doctype)){
_c8.setDoctype(RegExp.$1);
}
var _cc=_c9.match(/<link\s+[\s\S]*?["']\s*\/?>/gi);
_c9=_c9.replace(/<link\s+[\s\S]*?["']\s*\/?>\s*/gi,"");
_cc?_c9=_c9.replace(/<\/head>/i,_cc.join("\n")+"\n</head>"):null;
}
doc.write(_c9);
doc.close();
if(this.config.fullScreen){
this._fullScreen();
}
this.setEditorEvents();
};
Xinha.prototype.whenDocReady=function(f){
var e=this;
if(this._doc&&this._doc.body){
f();
}else{
setTimeout(function(){
e.whenDocReady(f);
},50);
}
};
Xinha.prototype.setMode=function(_cf){
var _d0;
if(typeof _cf=="undefined"){
_cf=this._editMode=="textmode"?"wysiwyg":"textmode";
}
switch(_cf){
case "textmode":
this.firePluginEvent("onBeforeMode","textmode");
this.setCC("iframe");
_d0=this.outwardHtml(this.getHTML());
this.setHTML(_d0);
this.deactivateEditor();
this._iframe.style.display="none";
this._textArea.style.display="";
if(this.config.statusBar){
this._statusBarTree.style.display="none";
this._statusBarTextMode.style.display="";
}
this.findCC("textarea");
this.notifyOf("modechange",{"mode":"text"});
this.firePluginEvent("onMode","textmode");
break;
case "wysiwyg":
this.firePluginEvent("onBeforeMode","wysiwyg");
this.setCC("textarea");
_d0=this.inwardHtml(this.getHTML());
this.deactivateEditor();
this.setHTML(_d0);
this._iframe.style.display="";
this._textArea.style.display="none";
this.activateEditor();
if(this.config.statusBar){
this._statusBarTree.style.display="";
this._statusBarTextMode.style.display="none";
}
this.findCC("iframe");
this.notifyOf("modechange",{"mode":"wysiwyg"});
this.firePluginEvent("onMode","wysiwyg");
break;
default:
alert("Mode <"+_cf+"> not defined!");
return false;
}
this._editMode=_cf;
};
Xinha.prototype.setFullHTML=function(_d1){
var _d2=RegExp.multiline;
RegExp.multiline=true;
if(_d1.match(Xinha.RE_doctype)){
this.setDoctype(RegExp.$1);
}
RegExp.multiline=_d2;
if(0){
if(_d1.match(Xinha.RE_head)){
this._doc.getElementsByTagName("head")[0].innerHTML=RegExp.$1;
}
if(_d1.match(Xinha.RE_body)){
this._doc.getElementsByTagName("body")[0].innerHTML=RegExp.$1;
}
}else{
var _d3=this.editorIsActivated();
if(_d3){
this.deactivateEditor();
}
var _d4=/<html>((.|\n)*?)<\/html>/i;
_d1=_d1.replace(_d4,"$1");
this._doc.open("text/html","replace");
this._doc.write(_d1);
this._doc.close();
if(_d3){
this.activateEditor();
}
this.setEditorEvents();
return true;
}
};
Xinha.prototype.setEditorEvents=function(){
var _d5=this;
var doc=this._doc;
_d5.whenDocReady(function(){
Xinha._addEvents(doc,["mousedown"],function(){
_d5.activateEditor();
return true;
});
if(Xinha.is_ie){
Xinha._addEvent(_d5._doc.getElementsByTagName("html")[0],"click",function(){
if(_d5._iframe.contentWindow.event.srcElement.tagName.toLowerCase()=="html"){
var r=_d5._doc.body.createTextRange();
r.collapse();
r.select();
}
return true;
});
}
Xinha._addEvents(doc,["keydown","keypress","mousedown","mouseup","drag"],function(_d8){
return _d5._editorEvent(Xinha.is_ie?_d5._iframe.contentWindow.event:_d8);
});
for(var i in _d5.plugins){
var _da=_d5.plugins[i].instance;
Xinha.refreshPlugin(_da);
}
if(typeof _d5._onGenerate=="function"){
_d5._onGenerate();
}
Xinha.addDom0Event(window,"resize",function(e){
_d5.sizeEditor();
});
_d5.removeLoadingMessage();
});
};
Xinha.prototype.registerPlugin=function(){
if(!Xinha.isSupportedBrowser){
return;
}
var _dc=arguments[0];
if(_dc===null||typeof _dc=="undefined"||(typeof _dc=="string"&&typeof window[_dc]=="undefined")){
return false;
}
var _dd=[];
for(var i=1;i<arguments.length;++i){
_dd.push(arguments[i]);
}
return this.registerPlugin2(_dc,_dd);
};
Xinha.prototype.registerPlugin2=function(_df,_e0){
if(typeof _df=="string"&&typeof window[_df]=="function"){
_df=window[_df];
}
if(typeof _df=="undefined"){
return false;
}
var obj=new _df(this,_e0);
if(obj){
var _e2={};
var _e3=_df._pluginInfo;
for(var i in _e3){
_e2[i]=_e3[i];
}
_e2.instance=obj;
_e2.args=_e0;
this.plugins[_df._pluginInfo.name]=_e2;
return obj;
}else{
alert("Can't register plugin "+_df.toString()+".");
}
};
Xinha.getPluginDir=function(_e5){
if(Xinha.externalPlugins[_e5]){
return Xinha.externalPlugins[_e5][0];
}else{
return _editor_url+"plugins/"+_e5;
}
};
Xinha.loadPlugin=function(_e6,_e7,_e8){
if(!Xinha.isSupportedBrowser){
return;
}
Xinha.setLoadingMessage(Xinha._lc("Loading plugin $plugin="+_e6+"$"));
if(typeof window["pluginName"]!="undefined"){
if(_e7){
_e7(_e6);
}
return true;
}
if(!_e8){
var dir=this.getPluginDir(_e6);
var _ea=_e6.replace(/([a-z])([A-Z])([a-z])/g,function(str,l1,l2,l3){
return l1+"-"+l2.toLowerCase()+l3;
}).toLowerCase()+".js";
_e8=dir+"/"+_ea;
}
Xinha._loadback(_e8,_e7?function(){
_e7(_e6);
}:null);
return false;
};
Xinha._pluginLoadStatus={};
Xinha.externalPlugins={};
Xinha.loadPlugins=function(_ef,_f0,url){
if(!Xinha.isSupportedBrowser){
return;
}
Xinha.setLoadingMessage(Xinha._lc("Loading plugins"));
var m;
for(var i=0;i<_ef.length;i++){
if(typeof _ef[i]=="object"){
m=_ef[i].url.match(/(.*)(\/[^\/]*)$/);
Xinha.externalPlugins[_ef[i].plugin]=[m[1],m[2]];
_ef[i]=_ef[i].plugin;
}
}
var _f4=true;
var _f5=Xinha.cloneObject(_ef);
while(_f5.length){
var p=_f5.pop();
if(p=="FullScreen"&&!Xinha.externalPlugins["FullScreen"]){
continue;
}
if(typeof Xinha._pluginLoadStatus[p]=="undefined"){
Xinha._pluginLoadStatus[p]="loading";
Xinha.loadPlugin(p,function(_f7){
if(typeof window[_f7]!="undefined"){
Xinha._pluginLoadStatus[_f7]="ready";
}else{
Xinha._pluginLoadStatus[_f7]="failed";
}
},(Xinha.externalPlugins[p]?Xinha.externalPlugins[p][0]+Xinha.externalPlugins[p][1]:url));
_f4=false;
}else{
switch(Xinha._pluginLoadStatus[p]){
case "failed":
case "ready":
break;
default:
_f4=false;
break;
}
}
}
if(_f4){
return true;
}
if(_f0){
setTimeout(function(){
if(Xinha.loadPlugins(_ef,_f0)){
_f0();
}
},150);
}
return _f4;
};
Xinha.refreshPlugin=function(_f8){
if(_f8&&typeof _f8.onGenerate=="function"){
_f8.onGenerate();
}
if(_f8&&typeof _f8.onGenerateOnce=="function"){
_f8.onGenerateOnce();
_f8.onGenerateOnce=null;
}
};
Xinha.prototype.firePluginEvent=function(_f9){
var _fa=[];
for(var i=1;i<arguments.length;i++){
_fa[i-1]=arguments[i];
}
for(var i in this.plugins){
var _fc=this.plugins[i].instance;
if(_fc==this._browserSpecificPlugin){
continue;
}
if(_fc&&typeof _fc[_f9]=="function"){
if(_fc[_f9].apply(_fc,_fa)){
return true;
}
}
}
var _fc=this._browserSpecificPlugin;
if(_fc&&typeof _fc[_f9]=="function"){
if(_fc[_f9].apply(_fc,_fa)){
return true;
}
}
return false;
};
Xinha.loadStyle=function(_fd,_fe,id,_100){
var url=_editor_url||"";
if(_fe){
url=Xinha.getPluginDir(_fe)+"/";
}
url+=_fd;
if(/^\//.test(_fd)){
url=_fd;
}
var head=document.getElementsByTagName("head")[0];
var link=document.createElement("link");
link.rel="stylesheet";
link.href=url;
link.type="text/css";
if(id){
link.id=id;
}
if(_100&&head.getElementsByTagName("link")[0]){
head.insertBefore(link,head.getElementsByTagName("link")[0]);
}else{
head.appendChild(link);
}
};
Xinha.prototype.debugTree=function(){
var ta=document.createElement("textarea");
ta.style.width="100%";
ta.style.height="20em";
ta.value="";
function debug(_105,str){
for(;--_105>=0;){
ta.value+=" ";
}
ta.value+=str+"\n";
}
function _dt(root,_108){
var tag=root.tagName.toLowerCase(),i;
var ns=Xinha.is_ie?root.scopeName:root.prefix;
debug(_108,"- "+tag+" ["+ns+"]");
for(i=root.firstChild;i;i=i.nextSibling){
if(i.nodeType==1){
_dt(i,_108+2);
}
}
}
_dt(this._doc.body,0);
document.body.appendChild(ta);
};
Xinha.getInnerText=function(el){
var txt="",i;
for(i=el.firstChild;i;i=i.nextSibling){
if(i.nodeType==3){
txt+=i.data;
}else{
if(i.nodeType==1){
txt+=Xinha.getInnerText(i);
}
}
}
return txt;
};
Xinha.prototype._wordClean=function(){
var _10d=this;
var _10e={empty_tags:0,mso_class:0,mso_style:0,mso_xmlel:0,orig_len:this._doc.body.innerHTML.length,T:(new Date()).getTime()};
var _10f={empty_tags:"Empty tags removed: ",mso_class:"MSO class names removed: ",mso_style:"MSO inline style removed: ",mso_xmlel:"MSO XML elements stripped: "};
function showStats(){
var txt="Xinha word cleaner stats: \n\n";
for(var i in _10e){
if(_10f[i]){
txt+=_10f[i]+_10e[i]+"\n";
}
}
txt+="\nInitial document length: "+_10e.orig_len+"\n";
txt+="Final document length: "+_10d._doc.body.innerHTML.length+"\n";
txt+="Clean-up took "+(((new Date()).getTime()-_10e.T)/1000)+" seconds";
alert(txt);
}
function clearClass(node){
var newc=node.className.replace(/(^|\s)mso.*?(\s|$)/ig," ");
if(newc!=node.className){
node.className=newc;
if(!(/\S/.test(node.className))){
node.removeAttribute("className");
++_10e.mso_class;
}
}
}
function clearStyle(node){
var _115=node.style.cssText.split(/\s*;\s*/);
for(var i=_115.length;--i>=0;){
if((/^mso|^tab-stops/i.test(_115[i]))||(/^margin\s*:\s*0..\s+0..\s+0../i.test(_115[i]))){
++_10e.mso_style;
_115.splice(i,1);
}
}
node.style.cssText=_115.join("; ");
}
var _117=null;
if(Xinha.is_ie){
_117=function(el){
el.outerHTML=Xinha.htmlEncode(el.innerText);
++_10e.mso_xmlel;
};
}else{
_117=function(el){
var txt=document.createTextNode(Xinha.getInnerText(el));
el.parentNode.insertBefore(txt,el);
Xinha.removeFromParent(el);
++_10e.mso_xmlel;
};
}
function checkEmpty(el){
if(/^(span|b|strong|i|em|font|div|p)$/i.test(el.tagName)&&!el.firstChild){
Xinha.removeFromParent(el);
++_10e.empty_tags;
}
}
function parseTree(root){
var tag=root.tagName.toLowerCase(),i,next;
if((Xinha.is_ie&&root.scopeName!="HTML")||(!Xinha.is_ie&&(/:/.test(tag)))){
_117(root);
return false;
}else{
clearClass(root);
clearStyle(root);
for(i=root.firstChild;i;i=next){
next=i.nextSibling;
if(i.nodeType==1&&parseTree(i)){
checkEmpty(i);
}
}
}
return true;
}
parseTree(this._doc.body);
this.updateToolbar();
};
Xinha.prototype._clearFonts=function(){
var D=this.getInnerHTML();
if(confirm(Xinha._lc("Would you like to clear font typefaces?"))){
D=D.replace(/face="[^"]*"/gi,"");
D=D.replace(/font-family:[^;}"']+;?/gi,"");
}
if(confirm(Xinha._lc("Would you like to clear font sizes?"))){
D=D.replace(/size="[^"]*"/gi,"");
D=D.replace(/font-size:[^;}"']+;?/gi,"");
}
if(confirm(Xinha._lc("Would you like to clear font colours?"))){
D=D.replace(/color="[^"]*"/gi,"");
D=D.replace(/([^-])color:[^;}"']+;?/gi,"$1");
}
D=D.replace(/(style|class)="\s*"/gi,"");
D=D.replace(/<(font|span)\s*>/gi,"");
this.setHTML(D);
this.updateToolbar();
};
Xinha.prototype._splitBlock=function(){
this._doc.execCommand("formatblock",false,"div");
};
Xinha.prototype.forceRedraw=function(){
this._doc.body.style.visibility="hidden";
this._doc.body.style.visibility="";
};
Xinha.prototype.focusEditor=function(){
switch(this._editMode){
case "wysiwyg":
try{
if(Xinha._someEditorHasBeenActivated){
this.activateEditor();
this._iframe.contentWindow.focus();
}
}
catch(ex){
}
break;
case "textmode":
try{
this._textArea.focus();
}
catch(e){
}
break;
default:
alert("ERROR: mode "+this._editMode+" is not defined");
}
return this._doc;
};
Xinha.prototype._undoTakeSnapshot=function(){
++this._undoPos;
if(this._undoPos>=this.config.undoSteps){
this._undoQueue.shift();
--this._undoPos;
}
var take=true;
var txt=this.getInnerHTML();
if(this._undoPos>0){
take=(this._undoQueue[this._undoPos-1]!=txt);
}
if(take){
this._undoQueue[this._undoPos]=txt;
}else{
this._undoPos--;
}
};
Xinha.prototype.undo=function(){
if(this._undoPos>0){
var txt=this._undoQueue[--this._undoPos];
if(txt){
this.setHTML(txt);
}else{
++this._undoPos;
}
}
};
Xinha.prototype.redo=function(){
if(this._undoPos<this._undoQueue.length-1){
var txt=this._undoQueue[++this._undoPos];
if(txt){
this.setHTML(txt);
}else{
--this._undoPos;
}
}
};
Xinha.prototype.disableToolbar=function(_123){
if(this._timerToolbar){
clearTimeout(this._timerToolbar);
}
if(typeof _123=="undefined"){
_123=[];
}else{
if(typeof _123!="object"){
_123=[_123];
}
}
for(var i in this._toolbarObjects){
var btn=this._toolbarObjects[i];
if(_123.contains(i)){
continue;
}
if(typeof (btn.state)!="function"){
continue;
}
btn.state("enabled",false);
}
};
Xinha.prototype.enableToolbar=function(){
this.updateToolbar();
};
Xinha.prototype.updateToolbar=function(_126){
var doc=this._doc;
var text=(this._editMode=="textmode");
var _129=null;
if(!text){
_129=this.getAllAncestors();
if(this.config.statusBar&&!_126){
while(this._statusBarItems.length){
var item=this._statusBarItems.pop();
item.el=null;
item.editor=null;
item.onclick=null;
item.oncontextmenu=null;
item._xinha_dom0Events["click"]=null;
item._xinha_dom0Events["contextmenu"]=null;
item=null;
}
this._statusBarTree.innerHTML=Xinha._lc("Path")+": ";
for(var i=_129.length;--i>=0;){
var el=_129[i];
if(!el){
continue;
}
var a=document.createElement("a");
a.href="javascript:void(0)";
a.el=el;
a.editor=this;
this._statusBarItems.push(a);
Xinha.addDom0Event(a,"click",function(){
this.blur();
this.editor.selectNodeContents(this.el);
this.editor.updateToolbar(true);
return false;
});
Xinha.addDom0Event(a,"contextmenu",function(){
this.blur();
var info="Inline style:\n\n";
info+=this.el.style.cssText.split(/;\s*/).join(";\n");
alert(info);
return false;
});
var txt=el.tagName.toLowerCase();
if(typeof el.style!="undefined"){
a.title=el.style.cssText;
}
if(el.id){
txt+="#"+el.id;
}
if(el.className){
txt+="."+el.className;
}
a.appendChild(document.createTextNode(txt));
this._statusBarTree.appendChild(a);
if(i!==0){
this._statusBarTree.appendChild(document.createTextNode(String.fromCharCode(187)));
}
Xinha.freeLater(a);
}
}
}
for(var cmd in this._toolbarObjects){
var btn=this._toolbarObjects[cmd];
var _132=true;
if(typeof (btn.state)!="function"){
continue;
}
if(btn.context&&!text){
_132=false;
var _133=btn.context;
var _134=[];
if(/(.*)\[(.*?)\]/.test(_133)){
_133=RegExp.$1;
_134=RegExp.$2.split(",");
}
_133=_133.toLowerCase();
var _135=(_133=="*");
for(var k=0;k<_129.length;++k){
if(!_129[k]){
continue;
}
if(_135||(_129[k].tagName.toLowerCase()==_133)){
_132=true;
var _137=null;
var att=null;
var comp=null;
var _13a=null;
for(var ka=0;ka<_134.length;++ka){
_137=_134[ka].match(/(.*)(==|!=|===|!==|>|>=|<|<=)(.*)/);
att=_137[1];
comp=_137[2];
_13a=_137[3];
if(!eval(_129[k][att]+comp+_13a)){
_132=false;
break;
}
}
if(_132){
break;
}
}
}
}
btn.state("enabled",(!text||btn.text)&&_132);
if(typeof cmd=="function"){
continue;
}
var _13c=this.config.customSelects[cmd];
if((!text||btn.text)&&(typeof _13c!="undefined")){
_13c.refresh(this);
continue;
}
switch(cmd){
case "fontname":
case "fontsize":
if(!text){
try{
var _13d=(""+doc.queryCommandValue(cmd)).toLowerCase();
if(!_13d){
btn.element.selectedIndex=0;
break;
}
var _13e=this.config[cmd];
var _13f=0;
for(var j in _13e){
if((j.toLowerCase()==_13d)||(_13e[j].substr(0,_13d.length).toLowerCase()==_13d)){
btn.element.selectedIndex=_13f;
throw "ok";
}
++_13f;
}
btn.element.selectedIndex=0;
}
catch(ex){
}
}
break;
case "formatblock":
var _141=[];
for(var _142 in this.config.formatblock){
if(typeof this.config.formatblock[_142]=="string"){
_141[_141.length]=this.config.formatblock[_142];
}
}
var _143=this._getFirstAncestor(this.getSelection(),_141);
if(_143){
for(var x=0;x<_141.length;x++){
if(_141[x].toLowerCase()==_143.tagName.toLowerCase()){
btn.element.selectedIndex=x;
}
}
}else{
btn.element.selectedIndex=0;
}
break;
case "textindicator":
if(!text){
try{
var _145=btn.element.style;
_145.backgroundColor=Xinha._makeColor(doc.queryCommandValue(Xinha.is_ie?"backcolor":"hilitecolor"));
if(/transparent/i.test(_145.backgroundColor)){
_145.backgroundColor=Xinha._makeColor(doc.queryCommandValue("backcolor"));
}
_145.color=Xinha._makeColor(doc.queryCommandValue("forecolor"));
_145.fontFamily=doc.queryCommandValue("fontname");
_145.fontWeight=doc.queryCommandState("bold")?"bold":"normal";
_145.fontStyle=doc.queryCommandState("italic")?"italic":"normal";
}
catch(ex){
}
}
break;
case "htmlmode":
btn.state("active",text);
break;
case "lefttoright":
case "righttoleft":
var _146=this.getParentElement();
while(_146&&!Xinha.isBlockElement(_146)){
_146=_146.parentNode;
}
if(_146){
btn.state("active",(_146.style.direction==((cmd=="righttoleft")?"rtl":"ltr")));
}
break;
default:
cmd=cmd.replace(/(un)?orderedlist/i,"insert$1orderedlist");
try{
btn.state("active",(!text&&doc.queryCommandState(cmd)));
}
catch(ex){
}
break;
}
}
if(this._customUndo&&!this._timerUndo){
this._undoTakeSnapshot();
var _147=this;
this._timerUndo=setTimeout(function(){
_147._timerUndo=null;
},this.config.undoTimeout);
}
this.firePluginEvent("onUpdateToolbar");
};
Xinha.getEditor=function(ref){
for(var i=__xinhas.length;i--;){
var _14a=__xinhas[i];
if(_14a&&(_14a._textArea.id==ref||_14a._textArea.name==ref||_14a._textArea==ref)){
return _14a;
}
}
return null;
};
Xinha.prototype.getPluginInstance=function(_14b){
if(this.plugins[_14b]){
return this.plugins[_14b].instance;
}else{
return null;
}
};
Xinha.prototype.getAllAncestors=function(){
var p=this.getParentElement();
var a=[];
while(p&&(p.nodeType==1)&&(p.tagName.toLowerCase()!="body")){
a.push(p);
p=p.parentNode;
}
a.push(this._doc.body);
return a;
};
Xinha.prototype._getFirstAncestor=function(sel,_14f){
var prnt=this.activeElement(sel);
if(prnt===null){
try{
prnt=(Xinha.is_ie?this.createRange(sel).parentElement():this.createRange(sel).commonAncestorContainer);
}
catch(ex){
return null;
}
}
if(typeof _14f=="string"){
_14f=[_14f];
}
while(prnt){
if(prnt.nodeType==1){
if(_14f===null){
return prnt;
}
if(_14f.contains(prnt.tagName.toLowerCase())){
return prnt;
}
if(prnt.tagName.toLowerCase()=="body"){
break;
}
if(prnt.tagName.toLowerCase()=="table"){
break;
}
}
prnt=prnt.parentNode;
}
return null;
};
Xinha.prototype._getAncestorBlock=function(sel){
var prnt=(Xinha.is_ie?this.createRange(sel).parentElement:this.createRange(sel).commonAncestorContainer);
while(prnt&&(prnt.nodeType==1)){
switch(prnt.tagName.toLowerCase()){
case "div":
case "p":
case "address":
case "blockquote":
case "center":
case "del":
case "ins":
case "pre":
case "h1":
case "h2":
case "h3":
case "h4":
case "h5":
case "h6":
case "h7":
return prnt;
case "body":
case "noframes":
case "dd":
case "li":
case "th":
case "td":
case "noscript":
return null;
default:
break;
}
}
return null;
};
Xinha.prototype._createImplicitBlock=function(type){
var sel=this.getSelection();
if(Xinha.is_ie){
sel.empty();
}else{
sel.collapseToStart();
}
var rng=this.createRange(sel);
};
Xinha.prototype.surroundHTML=function(_156,_157){
var html=this.getSelectedHTML();
this.insertHTML(_156+html+_157);
};
Xinha.prototype.hasSelectedText=function(){
return this.getSelectedHTML()!=="";
};
Xinha.prototype._comboSelected=function(el,txt){
this.focusEditor();
var _15b=el.options[el.selectedIndex].value;
switch(txt){
case "fontname":
case "fontsize":
this.execCommand(txt,false,_15b);
break;
case "formatblock":
if(!_15b){
this.updateToolbar();
break;
}
if(!Xinha.is_gecko||_15b!=="blockquote"){
_15b="<"+_15b+">";
}
this.execCommand(txt,false,_15b);
break;
default:
var _15c=this.config.customSelects[txt];
if(typeof _15c!="undefined"){
_15c.action(this);
}else{
alert("FIXME: combo box "+txt+" not implemented");
}
break;
}
};
Xinha.prototype._colorSelector=function(_15d){
var _15e=this;
if(Xinha.is_gecko){
try{
_15e._doc.execCommand("useCSS",false,false);
_15e._doc.execCommand("styleWithCSS",false,true);
}
catch(ex){
}
}
var btn=_15e._toolbarObjects[_15d].element;
var _160;
if(_15d=="hilitecolor"){
if(Xinha.is_ie){
_15d="backcolor";
_160=Xinha._colorToRgb(_15e._doc.queryCommandValue("backcolor"));
}else{
_160=Xinha._colorToRgb(_15e._doc.queryCommandValue("hilitecolor"));
}
}else{
_160=Xinha._colorToRgb(_15e._doc.queryCommandValue("forecolor"));
}
var _161=function(_162){
_15e._doc.execCommand(_15d,false,_162);
};
if(Xinha.is_ie){
var _163=_15e.createRange(_15e.getSelection());
_161=function(_164){
_163.select();
_15e._doc.execCommand(_15d,false,_164);
};
}
var _165=new Xinha.colorPicker({cellsize:_15e.config.colorPickerCellSize,callback:_161,granularity:_15e.config.colorPickerGranularity,websafe:_15e.config.colorPickerWebSafe,savecolors:_15e.config.colorPickerSaveColors});
_165.open(_15e.config.colorPickerPosition,btn,_160);
};
Xinha.prototype.execCommand=function(_166,UI,_168){
var _169=this;
this.focusEditor();
_166=_166.toLowerCase();
if(this.firePluginEvent("onExecCommand",_166,UI,_168)){
this.updateToolbar();
return false;
}
switch(_166){
case "htmlmode":
this.setMode();
break;
case "hilitecolor":
case "forecolor":
this._colorSelector(_166);
break;
case "createlink":
this._createLink();
break;
case "undo":
case "redo":
if(this._customUndo){
this[_166]();
}else{
this._doc.execCommand(_166,UI,_168);
}
break;
case "inserttable":
this._insertTable();
break;
case "insertimage":
this._insertImage();
break;
case "about":
this._popupDialog(_169.config.URIs.about,null,this);
break;
case "showhelp":
this._popupDialog(_169.config.URIs.help,null,this);
break;
case "killword":
this._wordClean();
break;
case "cut":
case "copy":
case "paste":
this._doc.execCommand(_166,UI,_168);
if(this.config.killWordOnPaste){
this._wordClean();
}
break;
case "lefttoright":
case "righttoleft":
if(this.config.changeJustifyWithDirection){
this._doc.execCommand((_166=="righttoleft")?"justifyright":"justifyleft",UI,_168);
}
var dir=(_166=="righttoleft")?"rtl":"ltr";
var el=this.getParentElement();
while(el&&!Xinha.isBlockElement(el)){
el=el.parentNode;
}
if(el){
if(el.style.direction==dir){
el.style.direction="";
}else{
el.style.direction=dir;
}
}
break;
case "justifyleft":
case "justifyright":
_166.match(/^justify(.*)$/);
var ae=this.activeElement(this.getSelection());
if(ae&&ae.tagName.toLowerCase()=="img"){
ae.align=ae.align==RegExp.$1?"":RegExp.$1;
}else{
this._doc.execCommand(_166,UI,_168);
}
break;
default:
try{
this._doc.execCommand(_166,UI,_168);
}
catch(ex){
if(this.config.debug){
alert(ex+"\n\nby execCommand("+_166+");");
}
}
break;
}
this.updateToolbar();
return false;
};
Xinha.prototype._editorEvent=function(ev){
var _16e=this;
if(typeof _16e._textArea["on"+ev.type]=="function"){
_16e._textArea["on"+ev.type]();
}
if(this.isKeyEvent(ev)){
if(_16e.firePluginEvent("onKeyPress",ev)){
return false;
}
if(this.isShortCut(ev)){
this._shortCuts(ev);
}
}
if(ev.type=="mousedown"){
if(_16e.firePluginEvent("onMouseDown",ev)){
return false;
}
}
if(_16e._timerToolbar){
clearTimeout(_16e._timerToolbar);
}
_16e._timerToolbar=setTimeout(function(){
_16e.updateToolbar();
_16e._timerToolbar=null;
},250);
};
Xinha.prototype._shortCuts=function(ev){
var key=this.getKey(ev).toLowerCase();
var cmd=null;
var _172=null;
switch(key){
case "b":
cmd="bold";
break;
case "i":
cmd="italic";
break;
case "u":
cmd="underline";
break;
case "s":
cmd="strikethrough";
break;
case "l":
cmd="justifyleft";
break;
case "e":
cmd="justifycenter";
break;
case "r":
cmd="justifyright";
break;
case "j":
cmd="justifyfull";
break;
case "z":
cmd="undo";
break;
case "y":
cmd="redo";
break;
case "v":
cmd="paste";
break;
case "n":
cmd="formatblock";
_172="p";
break;
case "0":
cmd="killword";
break;
case "1":
case "2":
case "3":
case "4":
case "5":
case "6":
cmd="formatblock";
_172="h"+key;
break;
}
if(cmd){
this.execCommand(cmd,false,_172);
Xinha._stopEvent(ev);
}
};
Xinha.prototype.convertNode=function(el,_174){
var _175=this._doc.createElement(_174);
while(el.firstChild){
_175.appendChild(el.firstChild);
}
return _175;
};
Xinha.prototype.scrollToElement=function(e){
if(!e){
e=this.getParentElement();
if(!e){
return;
}
}
var _177=Xinha.getElementTopLeft(e);
this._iframe.contentWindow.scrollTo(_177.left,_177.top);
};
Xinha.prototype.getEditorContent=function(){
return this.outwardHtml(this.getHTML());
};
Xinha.prototype.setEditorContent=function(html){
this.setHTML(this.inwardHtml(html));
};
Xinha.prototype.getHTML=function(){
var html="";
switch(this._editMode){
case "wysiwyg":
if(!this.config.fullPage){
html=Xinha.getHTML(this._doc.body,false,this).trim();
}else{
html=this.doctype+"\n"+Xinha.getHTML(this._doc.documentElement,true,this);
}
break;
case "textmode":
html=this._textArea.value;
break;
default:
alert("Mode <"+this._editMode+"> not defined!");
return false;
}
return html;
};
Xinha.prototype.outwardHtml=function(html){
for(var i in this.plugins){
var _17c=this.plugins[i].instance;
if(_17c&&typeof _17c.outwardHtml=="function"){
html=_17c.outwardHtml(html);
}
}
html=html.replace(/<(\/?)b(\s|>|\/)/ig,"<$1strong$2");
html=html.replace(/<(\/?)i(\s|>|\/)/ig,"<$1em$2");
html=html.replace(/<(\/?)strike(\s|>|\/)/ig,"<$1del$2");
html=html.replace(/(<[^>]*on(click|mouse(over|out|up|down))=['"])if\(window\.parent &amp;&amp; window\.parent\.Xinha\)\{return false\}/gi,"$1");
var _17d=location.href.replace(/(https?:\/\/[^\/]*)\/.*/,"$1")+"/";
html=html.replace(/https?:\/\/null\//g,_17d);
html=html.replace(/((href|src|background)=[\'\"])\/+/ig,"$1"+_17d);
html=this.outwardSpecialReplacements(html);
html=this.fixRelativeLinks(html);
if(this.config.sevenBitClean){
html=html.replace(/[^ -~\r\n\t]/g,function(c){
return "&#"+c.charCodeAt(0)+";";
});
}
html=html.replace(/(<script[^>]*((type=[\"\']text\/)|(language=[\"\'])))(freezescript)/gi,"$1javascript");
if(this.config.fullPage){
html=Xinha.stripCoreCSS(html);
}
if(typeof this.config.outwardHtml=="function"){
html=this.config.outwardHtml(html);
}
return html;
};
Xinha.prototype.inwardHtml=function(html){
for(var i in this.plugins){
var _181=this.plugins[i].instance;
if(_181&&typeof _181.inwardHtml=="function"){
html=_181.inwardHtml(html);
}
}
html=html.replace(/<(\/?)del(\s|>|\/)/ig,"<$1strike$2");
html=html.replace(/(<[^>]*on(click|mouse(over|out|up|down))=["'])/gi,"$1if(window.parent &amp;&amp; window.parent.Xinha){return false}");
html=this.inwardSpecialReplacements(html);
html=html.replace(/(<script[^>]*((type=[\"\']text\/)|(language=[\"\'])))(javascript)/gi,"$1freezescript");
var _182=new RegExp("((href|src|background)=['\"])/+","gi");
html=html.replace(_182,"$1"+location.href.replace(/(https?:\/\/[^\/]*)\/.*/,"$1")+"/");
html=this.fixRelativeLinks(html);
if(this.config.fullPage){
html=Xinha.addCoreCSS(html);
}
if(typeof this.config.inwardHtml=="function"){
html=this.config.inwardHtml(html);
}
return html;
};
Xinha.prototype.outwardSpecialReplacements=function(html){
for(var i in this.config.specialReplacements){
var from=this.config.specialReplacements[i];
var to=i;
if(typeof from.replace!="function"||typeof to.replace!="function"){
continue;
}
var reg=new RegExp(Xinha.escapeStringForRegExp(from),"g");
html=html.replace(reg,to.replace(/\$/g,"$$$$"));
}
return html;
};
Xinha.prototype.inwardSpecialReplacements=function(html){
for(var i in this.config.specialReplacements){
var from=i;
var to=this.config.specialReplacements[i];
if(typeof from.replace!="function"||typeof to.replace!="function"){
continue;
}
var reg=new RegExp(Xinha.escapeStringForRegExp(from),"g");
html=html.replace(reg,to.replace(/\$/g,"$$$$"));
}
return html;
};
Xinha.prototype.fixRelativeLinks=function(html){
if(typeof this.config.expandRelativeUrl!="undefined"&&this.config.expandRelativeUrl){
var src=html.match(/(src|href)="([^"]*)"/gi);
}
var b=document.location.href;
if(src){
var url,url_m,relPath,base_m,absPath;
for(var i=0;i<src.length;++i){
url=src[i].match(/(src|href)="([^"]*)"/i);
url_m=url[2].match(/\.\.\//g);
if(url_m){
relPath=new RegExp("(.*?)(([^/]*/){"+url_m.length+"})[^/]*$");
base_m=b.match(relPath);
absPath=url[2].replace(/(\.\.\/)*/,base_m[1]);
html=html.replace(new RegExp(Xinha.escapeStringForRegExp(url[2])),absPath);
}
}
}
if(typeof this.config.stripSelfNamedAnchors!="undefined"&&this.config.stripSelfNamedAnchors){
var _192=new RegExp("((href|src|background)=\")("+Xinha.escapeStringForRegExp(unescape(document.location.href.replace(/&/g,"&amp;")))+")([#?][^'\" ]*)","g");
html=html.replace(_192,"$1$4");
}
if(typeof this.config.stripBaseHref!="undefined"&&this.config.stripBaseHref){
var _193=null;
if(typeof this.config.baseHref!="undefined"&&this.config.baseHref!==null){
_193=new RegExp("((href|src|background|action)=\")("+Xinha.escapeStringForRegExp(this.config.baseHref.replace(/([^\/]\/)(?=.+\.)[^\/]*$/,"$1"))+")","g");
html=html.replace(_193,"$1");
}
_193=new RegExp("((href|src|background|action)=\")("+Xinha.escapeStringForRegExp(document.location.href.replace(/^(https?:\/\/[^\/]*)(.*)/,"$1"))+")","g");
html=html.replace(_193,"$1");
}
return html;
};
Xinha.prototype.getInnerHTML=function(){
if(!this._doc.body){
return "";
}
var html="";
switch(this._editMode){
case "wysiwyg":
if(!this.config.fullPage){
html=this._doc.body.innerHTML;
}else{
html=this.doctype+"\n"+this._doc.documentElement.innerHTML;
}
break;
case "textmode":
html=this._textArea.value;
break;
default:
alert("Mode <"+this._editMode+"> not defined!");
return false;
}
return html;
};
Xinha.prototype.setHTML=function(html){
if(!this.config.fullPage){
this._doc.body.innerHTML=html;
}else{
this.setFullHTML(html);
}
this._textArea.value=html;
};
Xinha.prototype.setDoctype=function(_196){
this.doctype=_196;
};
Xinha._object=null;
Array.prototype.isArray=true;
RegExp.prototype.isRegExp=true;
Xinha.cloneObject=function(obj){
if(!obj){
return null;
}
var _198=(obj.isArray)?[]:{};
if(obj.constructor.toString().match(/\s*function Function\(/)||typeof obj=="function"){
_198=obj;
}else{
if(obj.isRegExp){
_198=eval(obj.toString());
}else{
for(var n in obj){
var node=obj[n];
if(typeof node=="object"){
_198[n]=Xinha.cloneObject(node);
}else{
_198[n]=node;
}
}
}
}
return _198;
};
Xinha.flushEvents=function(){
var x=0;
var e=Xinha._eventFlushers.pop();
while(e){
try{
if(e.length==3){
Xinha._removeEvent(e[0],e[1],e[2]);
x++;
}else{
if(e.length==2){
e[0]["on"+e[1]]=null;
e[0]._xinha_dom0Events[e[1]]=null;
x++;
}
}
}
catch(ex){
}
e=Xinha._eventFlushers.pop();
}
};
Xinha._eventFlushers=[];
if(document.addEventListener){
Xinha._addEvent=function(el,_19e,func){
el.addEventListener(_19e,func,true);
Xinha._eventFlushers.push([el,_19e,func]);
};
Xinha._removeEvent=function(el,_1a1,func){
el.removeEventListener(_1a1,func,true);
};
Xinha._stopEvent=function(ev){
ev.preventDefault();
ev.stopPropagation();
};
}else{
if(document.attachEvent){
Xinha._addEvent=function(el,_1a5,func){
el.attachEvent("on"+_1a5,func);
Xinha._eventFlushers.push([el,_1a5,func]);
};
Xinha._removeEvent=function(el,_1a8,func){
el.detachEvent("on"+_1a8,func);
};
Xinha._stopEvent=function(ev){
try{
ev.cancelBubble=true;
ev.returnValue=false;
}
catch(ex){
}
};
}else{
Xinha._addEvent=function(el,_1ac,func){
alert("_addEvent is not supported");
};
Xinha._removeEvent=function(el,_1af,func){
alert("_removeEvent is not supported");
};
Xinha._stopEvent=function(ev){
alert("_stopEvent is not supported");
};
}
}
Xinha._addEvents=function(el,evs,func){
for(var i=evs.length;--i>=0;){
Xinha._addEvent(el,evs[i],func);
}
};
Xinha._removeEvents=function(el,evs,func){
for(var i=evs.length;--i>=0;){
Xinha._removeEvent(el,evs[i],func);
}
};
Xinha.addOnloadHandler=function(func,_1bb){
_1bb=_1bb?_1bb:window;
var init=function(){
if(arguments.callee.done){
return;
}
arguments.callee.done=true;
if(Xinha.onloadTimer){
clearInterval(Xinha.onloadTimer);
}
func();
};
if(Xinha.is_ie){
_1bb.document.write("<sc"+"ript id=__ie_onload defer src=javascript:void(0)></script>");
var _1bd=_1bb.document.getElementById("__ie_onload");
_1bd.onreadystatechange=function(){
if(this.readyState=="loaded"){
this.parentNode.removeChild(_1bd);
init();
}
};
}else{
if(/applewebkit|KHTML/i.test(navigator.userAgent)){
Xinha.onloadTimer=_1bb.setInterval(function(){
if(/loaded|complete/.test(_1bb.document.readyState)){
init();
}
},10);
}else{
_1bb.document.addEventListener("DOMContentLoaded",init,false);
}
}
Xinha._addEvent(_1bb,"load",init);
};
Xinha.addDom0Event=function(el,ev,fn){
Xinha._prepareForDom0Events(el,ev);
el._xinha_dom0Events[ev].unshift(fn);
};
Xinha.prependDom0Event=function(el,ev,fn){
Xinha._prepareForDom0Events(el,ev);
el._xinha_dom0Events[ev].push(fn);
};
Xinha._prepareForDom0Events=function(el,ev){
if(typeof el._xinha_dom0Events=="undefined"){
el._xinha_dom0Events={};
Xinha.freeLater(el,"_xinha_dom0Events");
}
if(typeof el._xinha_dom0Events[ev]=="undefined"){
el._xinha_dom0Events[ev]=[];
if(typeof el["on"+ev]=="function"){
el._xinha_dom0Events[ev].push(el["on"+ev]);
}
el["on"+ev]=function(_1c6){
var a=el._xinha_dom0Events[ev];
var _1c8=true;
for(var i=a.length;--i>=0;){
el._xinha_tempEventHandler=a[i];
if(el._xinha_tempEventHandler(_1c6)===false){
el._xinha_tempEventHandler=null;
_1c8=false;
break;
}
el._xinha_tempEventHandler=null;
}
return _1c8;
};
Xinha._eventFlushers.push([el,ev]);
}
};
Xinha.prototype.notifyOn=function(ev,fn){
if(typeof this._notifyListeners[ev]=="undefined"){
this._notifyListeners[ev]=[];
Xinha.freeLater(this,"_notifyListeners");
}
this._notifyListeners[ev].push(fn);
};
Xinha.prototype.notifyOf=function(ev,args){
if(this._notifyListeners[ev]){
for(var i=0;i<this._notifyListeners[ev].length;i++){
this._notifyListeners[ev][i](ev,args);
}
}
};
Xinha._blockTags=" body form textarea fieldset ul ol dl li div "+"p h1 h2 h3 h4 h5 h6 quote pre table thead "+"tbody tfoot tr td th iframe address blockquote ";
Xinha.isBlockElement=function(el){
return el&&el.nodeType==1&&(Xinha._blockTags.indexOf(" "+el.tagName.toLowerCase()+" ")!=-1);
};
Xinha._paraContainerTags=" body td th caption fieldset div";
Xinha.isParaContainer=function(el){
return el&&el.nodeType==1&&(Xinha._paraContainerTags.indexOf(" "+el.tagName.toLowerCase()+" ")!=-1);
};
Xinha._closingTags=" a abbr acronym address applet b bdo big blockquote button caption center cite code del dfn dir div dl em fieldset font form frameset h1 h2 h3 h4 h5 h6 i iframe ins kbd label legend map menu noframes noscript object ol optgroup pre q s samp script select small span strike strong style sub sup table textarea title tt u ul var ";
Xinha.needsClosingTag=function(el){
return el&&el.nodeType==1&&(Xinha._closingTags.indexOf(" "+el.tagName.toLowerCase()+" ")!=-1);
};
Xinha.htmlEncode=function(str){
if(typeof str.replace=="undefined"){
str=str.toString();
}
str=str.replace(/&/ig,"&amp;");
str=str.replace(/</ig,"&lt;");
str=str.replace(/>/ig,"&gt;");
str=str.replace(/\xA0/g,"&nbsp;");
str=str.replace(/\x22/g,"&quot;");
return str;
};
Xinha.prototype.stripBaseURL=function(_1d3){
if(this.config.baseHref===null||!this.config.stripBaseHref){
return _1d3;
}
var _1d4=this.config.baseHref.replace(/^(https?:\/\/[^\/]+)(.*)$/,"$1");
var _1d5=new RegExp(_1d4);
return _1d3.replace(_1d5,"");
};
String.prototype.trim=function(){
return this.replace(/^\s+/,"").replace(/\s+$/,"");
};
Xinha._makeColor=function(v){
if(typeof v!="number"){
return v;
}
var r=v&255;
var g=(v>>8)&255;
var b=(v>>16)&255;
return "rgb("+r+","+g+","+b+")";
};
Xinha._colorToRgb=function(v){
if(!v){
return "";
}
var r,g,b;
function hex(d){
return (d<16)?("0"+d.toString(16)):d.toString(16);
}
if(typeof v=="number"){
r=v&255;
g=(v>>8)&255;
b=(v>>16)&255;
return "#"+hex(r)+hex(g)+hex(b);
}
if(v.substr(0,3)=="rgb"){
var re=/rgb\s*\(\s*([0-9]+)\s*,\s*([0-9]+)\s*,\s*([0-9]+)\s*\)/;
if(v.match(re)){
r=parseInt(RegExp.$1,10);
g=parseInt(RegExp.$2,10);
b=parseInt(RegExp.$3,10);
return "#"+hex(r)+hex(g)+hex(b);
}
return null;
}
if(v.substr(0,1)=="#"){
return v;
}
return null;
};
Xinha.prototype._popupDialog=function(url,_1df,init){
Dialog(this.popupURL(url),_1df,init);
};
Xinha.prototype.imgURL=function(file,_1e2){
if(typeof _1e2=="undefined"){
return _editor_url+file;
}else{
return _editor_url+"plugins/"+_1e2+"/img/"+file;
}
};
Xinha.prototype.popupURL=function(file){
var url="";
if(file.match(/^plugin:\/\/(.*?)\/(.*)/)){
var _1e5=RegExp.$1;
var _1e6=RegExp.$2;
if(!(/\.(html?|php)$/.test(_1e6))){
_1e6+=".html";
}
url=Xinha.getPluginDir(_1e5)+"/popups/"+_1e6;
}else{
if(file.match(/^\/.*?/)||file.match(/^https?:\/\//)){
url=file;
}else{
url=_editor_url+this.config.popupURL+file;
}
}
return url;
};
Xinha.getElementById=function(tag,id){
var el,i,objs=document.getElementsByTagName(tag);
for(i=objs.length;--i>=0&&(el=objs[i]);){
if(el.id==id){
return el;
}
}
return null;
};
Xinha.prototype._toggleBorders=function(){
var _1ea=this._doc.getElementsByTagName("TABLE");
if(_1ea.length!==0){
if(!this.borders){
this.borders=true;
}else{
this.borders=false;
}
for(var i=0;i<_1ea.length;i++){
if(this.borders){
Xinha._addClass(_1ea[i],"htmtableborders");
}else{
Xinha._removeClass(_1ea[i],"htmtableborders");
}
}
}
return true;
};
Xinha.addCoreCSS=function(html){
var _1ed="<style title=\"XinhaInternalCSS\" type=\"text/css\">"+".htmtableborders, .htmtableborders td, .htmtableborders th {border : 1px dashed lightgrey ! important;}\n"+"html, body { border: 0px; } \n"+"body { background-color: #ffffff; } \n"+"img, hr { cursor: default } \n"+"</style>\n";
if(html&&/<head>/i.test(html)){
return html.replace(/<head>/i,"<head>"+_1ed);
}else{
if(html){
return _1ed+html;
}else{
return _1ed;
}
}
};
Xinha.prototype.addEditorStylesheet=function(_1ee){
var _1ef=this._doc.createElement("link");
_1ef.rel="stylesheet";
_1ef.type="text/css";
_1ef.title="XinhaInternalCSS";
_1ef.href=_1ee;
this._doc.getElementsByTagName("HEAD")[0].appendChild(_1ef);
};
Xinha.stripCoreCSS=function(html){
return html.replace(/<style[^>]+title="XinhaInternalCSS"(.|\n)*?<\/style>/ig,"").replace(/<link[^>]+title="XinhaInternalCSS"(.|\n)*?>/ig,"");
};
Xinha._removeClass=function(el,_1f2){
if(!(el&&el.className)){
return;
}
var cls=el.className.split(" ");
var ar=[];
for(var i=cls.length;i>0;){
if(cls[--i]!=_1f2){
ar[ar.length]=cls[i];
}
}
el.className=ar.join(" ");
};
Xinha._addClass=function(el,_1f7){
Xinha._removeClass(el,_1f7);
el.className+=" "+_1f7;
};
Xinha.addClasses=function(el,_1f9){
if(el!==null){
var _1fa=el.className.trim().split(" ");
var ours=_1f9.split(" ");
for(var x=0;x<ours.length;x++){
var _1fd=false;
for(var i=0;_1fd===false&&i<_1fa.length;i++){
if(_1fa[i]==ours[x]){
_1fd=true;
}
}
if(_1fd===false){
_1fa[_1fa.length]=ours[x];
}
}
el.className=_1fa.join(" ").trim();
}
};
Xinha.removeClasses=function(el,_200){
var _201=el.className.trim().split();
var _202=[];
var _203=_200.trim().split();
for(var i=0;i<_201.length;i++){
var _205=false;
for(var x=0;x<_203.length&&!_205;x++){
if(_201[i]==_203[x]){
_205=true;
}
}
if(!_205){
_202[_202.length]=_201[i];
}
}
return _202.join(" ");
};
Xinha.addClass=Xinha._addClass;
Xinha.removeClass=Xinha._removeClass;
Xinha._addClasses=Xinha.addClasses;
Xinha._removeClasses=Xinha.removeClasses;
Xinha._hasClass=function(el,_208){
if(!(el&&el.className)){
return false;
}
var cls=el.className.split(" ");
for(var i=cls.length;i>0;){
if(cls[--i]==_208){
return true;
}
}
return false;
};
Xinha._postback_send_charset=true;
Xinha._postback=function(url,data,_20d){
var req=null;
req=Xinha.getXMLHTTPRequestObject();
var _20f="";
if(typeof data=="string"){
_20f=data;
}else{
if(typeof data=="object"){
for(var i in data){
_20f+=(_20f.length?"&":"")+i+"="+encodeURIComponent(data[i]);
}
}
}
function callBack(){
if(req.readyState==4){
if(req.status==200||Xinha.isRunLocally&&req.status==0){
if(typeof _20d=="function"){
_20d(req.responseText,req);
}
}else{
if(Xinha._postback_send_charset){
Xinha._postback_send_charset=false;
Xinha._postback(url,data,_20d);
}else{
alert("An error has occurred: "+req.statusText+"\nURL: "+url);
}
}
}
}
req.onreadystatechange=callBack;
req.open("POST",url,true);
req.setRequestHeader("Content-Type","application/x-www-form-urlencoded"+(Xinha._postback_send_charset?"; charset=UTF-8":""));
req.send(_20f);
};
Xinha._getback=function(url,_212){
var req=null;
req=Xinha.getXMLHTTPRequestObject();
function callBack(){
if(req.readyState==4){
if(req.status==200||Xinha.isRunLocally&&req.status==0){
_212(req.responseText,req);
}else{
alert("An error has occurred: "+req.statusText+"\nURL: "+url);
}
}
}
req.onreadystatechange=callBack;
req.open("GET",url,true);
req.send(null);
};
Xinha._geturlcontent=function(url){
var req=null;
req=Xinha.getXMLHTTPRequestObject();
req.open("GET",url,false);
req.send(null);
if(req.status==200||Xinha.isRunLocally&&req.status==0){
return req.responseText;
}else{
return "";
}
};
if(typeof dumpValues=="undefined"){
function dumpValues(o){
var s="";
for(var prop in o){
if(window.console&&typeof window.console.log=="function"){
if(typeof console.firebug!="undefined"){
console.log(o);
}else{
console.log(prop+" = "+o[prop]+"\n");
}
}else{
s+=prop+" = "+o[prop]+"\n";
}
}
if(s){
if(document.getElementById("errors")){
document.getElementById("errors").value+=s;
}else{
var x=window.open("","debugger");
x.document.write("<pre>"+s+"</pre>");
}
}
}
}
if(!Array.prototype.contains){
Array.prototype.contains=function(_21a){
var _21b=this;
for(var i=0;i<_21b.length;i++){
if(_21a==_21b[i]){
return true;
}
}
return false;
};
}
if(!Array.prototype.indexOf){
Array.prototype.indexOf=function(_21d){
var _21e=this;
for(var i=0;i<_21e.length;i++){
if(_21d==_21e[i]){
return i;
}
}
return null;
};
}
if(!Array.prototype.append){
Array.prototype.append=function(a){
for(var i=0;i<a.length;i++){
this.push(a[i]);
}
return this;
};
}
Xinha.arrayContainsArray=function(a1,a2){
var _224=true;
for(var x=0;x<a2.length;x++){
var _226=false;
for(var i=0;i<a1.length;i++){
if(a1[i]==a2[x]){
_226=true;
break;
}
}
if(!_226){
_224=false;
break;
}
}
return _224;
};
Xinha.arrayFilter=function(a1,_229){
var _22a=[];
for(var x=0;x<a1.length;x++){
if(_229(a1[x])){
_22a[_22a.length]=a1[x];
}
}
return _22a;
};
Xinha.collectionToArray=function(_22c){
var _22d=[];
for(var i=0;i<_22c.length;i++){
_22d.push(_22c.item(i));
}
return _22d;
};
Xinha.uniq_count=0;
Xinha.uniq=function(_22f){
return _22f+Xinha.uniq_count++;
};
Xinha._loadlang=function(_230,url){
var lang;
if(typeof _editor_lcbackend=="string"){
url=_editor_lcbackend;
url=url.replace(/%lang%/,_editor_lang);
url=url.replace(/%context%/,_230);
}else{
if(!url){
if(_230!="Xinha"){
url=Xinha.getPluginDir(_230)+"/lang/"+_editor_lang+".js";
}else{
Xinha.setLoadingMessage("Loading language");
url=_editor_url+"lang/"+_editor_lang+".js";
}
}
}
var _233=Xinha._geturlcontent(url);
if(_233!==""){
try{
eval("lang = "+_233);
}
catch(ex){
alert("Error reading Language-File ("+url+"):\n"+Error.toString());
lang={};
}
}else{
lang={};
}
return lang;
};
Xinha._lc=function(_234,_235,_236){
var url,ret;
if(typeof _235=="object"&&_235.url&&_235.context){
url=_235.url+_editor_lang+".js";
_235=_235.context;
}
var m=null;
if(typeof _234=="string"){
m=_234.match(/\$(.*?)=(.*?)\$/g);
}
if(m){
if(!_236){
_236={};
}
for(var i=0;i<m.length;i++){
var n=m[i].match(/\$(.*?)=(.*?)\$/);
_236[n[1]]=n[2];
_234=_234.replace(n[0],"$"+n[1]);
}
}
if(_editor_lang=="en"){
if(typeof _234=="object"&&_234.string){
ret=_234.string;
}else{
ret=_234;
}
}else{
if(typeof Xinha._lc_catalog=="undefined"){
Xinha._lc_catalog=[];
}
if(typeof _235=="undefined"){
_235="Xinha";
}
if(typeof Xinha._lc_catalog[_235]=="undefined"){
Xinha._lc_catalog[_235]=Xinha._loadlang(_235,url);
}
var key;
if(typeof _234=="object"&&_234.key){
key=_234.key;
}else{
if(typeof _234=="object"&&_234.string){
key=_234.string;
}else{
key=_234;
}
}
if(typeof Xinha._lc_catalog[_235][key]=="undefined"){
if(_235=="Xinha"){
if(typeof _234=="object"&&_234.string){
ret=_234.string;
}else{
ret=_234;
}
}else{
return Xinha._lc(_234,"Xinha",_236);
}
}else{
ret=Xinha._lc_catalog[_235][key];
}
}
if(typeof _234=="object"&&_234.replace){
_236=_234.replace;
}
if(typeof _236!="undefined"){
for(var i in _236){
ret=ret.replace("$"+i,_236[i]);
}
}
return ret;
};
Xinha.hasDisplayedChildren=function(el){
var _23d=el.childNodes;
for(var i=0;i<_23d.length;i++){
if(_23d[i].tagName){
if(_23d[i].style.display!="none"){
return true;
}
}
}
return false;
};
Xinha._loadback=function(url,_240,_241,_242){
if(document.getElementById(url)){
return true;
}
var t=!Xinha.is_ie?"onload":"onreadystatechange";
var s=document.createElement("script");
s.type="text/javascript";
s.src=url;
s.id=url;
if(_240){
s[t]=function(){
if(Xinha.is_ie&&(!(/loaded|complete/.test(window.event.srcElement.readyState)))){
return;
}
_240.call(_241?_241:this,_242);
s[t]=null;
};
}
document.getElementsByTagName("head")[0].appendChild(s);
return false;
};
Xinha.makeEditors=function(_245,_246,_247){
if(!Xinha.isSupportedBrowser){
return;
}
if(typeof _246=="function"){
_246=_246();
}
var _248={};
var _249;
for(var x=0;x<_245.length;x++){
if(typeof _245[x]=="string"){
_249=Xinha.getElementById("textarea",_245[x]);
if(!_249){
_245[x]=null;
continue;
}
}else{
if(typeof _245[x]=="object"&&_245[x].tagName&&_245[x].tagName.toLowerCase()=="textarea"){
_249=_245[x];
if(!_249.id){
_249.id="xinha_id_"+x;
}
}
}
var _24b=new Xinha(_249,Xinha.cloneObject(_246));
_24b.registerPlugins(_247);
_248[_249.id]=_24b;
}
return _248;
};
Xinha.startEditors=function(_24c){
if(!Xinha.isSupportedBrowser){
return;
}
for(var i in _24c){
if(_24c[i].generate){
_24c[i].generate();
}
}
};
Xinha.prototype.registerPlugins=function(_24e){
if(!Xinha.isSupportedBrowser){
return;
}
if(_24e){
for(var i=0;i<_24e.length;i++){
this.setLoadingMessage(Xinha._lc("Register plugin $plugin","Xinha",{"plugin":_24e[i]}));
this.registerPlugin(_24e[i]);
}
}
};
Xinha.base64_encode=function(_250){
var _251="ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/=";
var _252="";
var chr1,chr2,chr3;
var enc1,enc2,enc3,enc4;
var i=0;
do{
chr1=_250.charCodeAt(i++);
chr2=_250.charCodeAt(i++);
chr3=_250.charCodeAt(i++);
enc1=chr1>>2;
enc2=((chr1&3)<<4)|(chr2>>4);
enc3=((chr2&15)<<2)|(chr3>>6);
enc4=chr3&63;
if(isNaN(chr2)){
enc3=enc4=64;
}else{
if(isNaN(chr3)){
enc4=64;
}
}
_252=_252+_251.charAt(enc1)+_251.charAt(enc2)+_251.charAt(enc3)+_251.charAt(enc4);
}while(i<_250.length);
return _252;
};
Xinha.base64_decode=function(_256){
var _257="ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/=";
var _258="";
var chr1,chr2,chr3;
var enc1,enc2,enc3,enc4;
var i=0;
_256=_256.replace(/[^A-Za-z0-9\+\/\=]/g,"");
do{
enc1=_257.indexOf(_256.charAt(i++));
enc2=_257.indexOf(_256.charAt(i++));
enc3=_257.indexOf(_256.charAt(i++));
enc4=_257.indexOf(_256.charAt(i++));
chr1=(enc1<<2)|(enc2>>4);
chr2=((enc2&15)<<4)|(enc3>>2);
chr3=((enc3&3)<<6)|enc4;
_258=_258+String.fromCharCode(chr1);
if(enc3!=64){
_258=_258+String.fromCharCode(chr2);
}
if(enc4!=64){
_258=_258+String.fromCharCode(chr3);
}
}while(i<_256.length);
return _258;
};
Xinha.removeFromParent=function(el){
if(!el.parentNode){
return;
}
var pN=el.parentNode;
pN.removeChild(el);
return el;
};
Xinha.hasParentNode=function(el){
if(el.parentNode){
if(el.parentNode.nodeType==11){
return false;
}
return true;
}
return false;
};
Xinha.viewportSize=function(_25f){
_25f=(_25f)?_25f:window;
var x,y;
if(_25f.innerHeight){
x=_25f.innerWidth;
y=_25f.innerHeight;
}else{
if(_25f.document.documentElement&&_25f.document.documentElement.clientHeight){
x=_25f.document.documentElement.clientWidth;
y=_25f.document.documentElement.clientHeight;
}else{
if(_25f.document.body){
x=_25f.document.body.clientWidth;
y=_25f.document.body.clientHeight;
}
}
}
return {"x":x,"y":y};
};
Xinha.pageSize=function(_261){
_261=(_261)?_261:window;
var x,y;
var _263=_261.document.body.scrollHeight;
var _264=_261.document.documentElement.scrollHeight;
if(_263>_264){
x=_261.document.body.scrollWidth;
y=_261.document.body.scrollHeight;
}else{
x=_261.document.documentElement.scrollWidth;
y=_261.document.documentElement.scrollHeight;
}
return {"x":x,"y":y};
};
Xinha.prototype.scrollPos=function(_265){
_265=(_265)?_265:window;
var x,y;
if(_265.pageYOffset){
x=_265.pageXOffset;
y=_265.pageYOffset;
}else{
if(_265.document.documentElement&&document.documentElement.scrollTop){
x=_265.document.documentElement.scrollLeft;
y=_265.document.documentElement.scrollTop;
}else{
if(_265.document.body){
x=_265.document.body.scrollLeft;
y=_265.document.body.scrollTop;
}
}
}
return {"x":x,"y":y};
};
Xinha.getElementTopLeft=function(_267){
var _268=curtop=0;
if(_267.offsetParent){
_268=_267.offsetLeft;
curtop=_267.offsetTop;
while(_267=_267.offsetParent){
_268+=_267.offsetLeft;
curtop+=_267.offsetTop;
}
}
return {top:curtop,left:_268};
};
Xinha.findPosX=function(obj){
var _26a=0;
if(obj.offsetParent){
return Xinha.getElementTopLeft(obj).left;
}else{
if(obj.x){
_26a+=obj.x;
}
}
return _26a;
};
Xinha.findPosY=function(obj){
var _26c=0;
if(obj.offsetParent){
return Xinha.getElementTopLeft(obj).top;
}else{
if(obj.y){
_26c+=obj.y;
}
}
return _26c;
};
Xinha.createLoadingMessages=function(_26d){
if(Xinha.loadingMessages||!Xinha.isSupportedBrowser){
return;
}
Xinha.loadingMessages=[];
for(var i=0;i<_26d.length;i++){
if(!document.getElementById(_26d[i])){
continue;
}
Xinha.loadingMessages.push(Xinha.createLoadingMessage(Xinha.getElementById("textarea",_26d[i])));
}
};
Xinha.createLoadingMessage=function(_26f,text){
if(document.getElementById("loading_"+_26f.id)||!Xinha.isSupportedBrowser){
return;
}
var _271=document.createElement("div");
_271.id="loading_"+_26f.id;
_271.className="loading";
_271.style.left=(Xinha.findPosX(_26f)+_26f.offsetWidth/2)-106+"px";
_271.style.top=(Xinha.findPosY(_26f)+_26f.offsetHeight/2)-50+"px";
var _272=document.createElement("div");
_272.className="loading_main";
_272.id="loading_main_"+_26f.id;
_272.appendChild(document.createTextNode(Xinha._lc("Loading in progress. Please wait!")));
var _273=document.createElement("div");
_273.className="loading_sub";
_273.id="loading_sub_"+_26f.id;
text=text?text:Xinha._lc("Loading Core");
_273.appendChild(document.createTextNode(text));
_271.appendChild(_272);
_271.appendChild(_273);
document.body.appendChild(_271);
Xinha.freeLater(_271);
Xinha.freeLater(_272);
Xinha.freeLater(_273);
return _273;
};
Xinha.prototype.setLoadingMessage=function(_274,_275){
if(!document.getElementById("loading_sub_"+this._textArea.id)){
return;
}
document.getElementById("loading_main_"+this._textArea.id).innerHTML=_275?_275:Xinha._lc("Loading in progress. Please wait!");
document.getElementById("loading_sub_"+this._textArea.id).innerHTML=_274;
};
Xinha.setLoadingMessage=function(_276){
if(!Xinha.loadingMessages){
return;
}
for(var i=0;i<Xinha.loadingMessages.length;i++){
Xinha.loadingMessages[i].innerHTML=_276;
}
};
Xinha.prototype.removeLoadingMessage=function(){
if(document.getElementById("loading_"+this._textArea.id)){
document.body.removeChild(document.getElementById("loading_"+this._textArea.id));
}
};
Xinha.removeLoadingMessages=function(_278){
for(var i=0;i<_278.length;i++){
if(!document.getElementById(_278[i])){
continue;
}
var main=document.getElementById("loading_"+document.getElementById(_278[i]).id);
main.parentNode.removeChild(main);
}
Xinha.loadingMessages=null;
};
Xinha.toFree=[];
Xinha.freeLater=function(obj,prop){
Xinha.toFree.push({o:obj,p:prop});
};
Xinha.free=function(obj,prop){
if(obj&&!prop){
for(var p in obj){
Xinha.free(obj,p);
}
}else{
if(obj){
if(prop.indexOf("src")==-1){
try{
obj[prop]=null;
}
catch(x){
}
}
}
}
};
Xinha.collectGarbageForIE=function(){
Xinha.flushEvents();
for(var x=0;x<Xinha.toFree.length;x++){
Xinha.free(Xinha.toFree[x].o,Xinha.toFree[x].p);
Xinha.toFree[x].o=null;
}
};
Xinha.prototype.insertNodeAtSelection=function(_281){
Xinha.notImplemented("insertNodeAtSelection");
};
Xinha.prototype.getParentElement=function(sel){
Xinha.notImplemented("getParentElement");
};
Xinha.prototype.activeElement=function(sel){
Xinha.notImplemented("activeElement");
};
Xinha.prototype.selectionEmpty=function(sel){
Xinha.notImplemented("selectionEmpty");
};
Xinha.prototype.saveSelection=function(){
Xinha.notImplemented("saveSelection");
};
Xinha.prototype.restoreSelection=function(_285){
Xinha.notImplemented("restoreSelection");
};
Xinha.prototype.selectNodeContents=function(node,pos){
Xinha.notImplemented("selectNodeContents");
};
Xinha.prototype.insertHTML=function(html){
Xinha.notImplemented("insertHTML");
};
Xinha.prototype.getSelectedHTML=function(){
Xinha.notImplemented("getSelectedHTML");
};
Xinha.prototype.getSelection=function(){
Xinha.notImplemented("getSelection");
};
Xinha.prototype.createRange=function(sel){
Xinha.notImplemented("createRange");
};
Xinha.prototype.isKeyEvent=function(_28a){
Xinha.notImplemented("isKeyEvent");
};
Xinha.prototype.isShortCut=function(_28b){
if(_28b.ctrlKey&&!_28b.altKey){
return true;
}
return false;
};
Xinha.prototype.getKey=function(_28c){
Xinha.notImplemented("getKey");
};
Xinha.getOuterHTML=function(_28d){
Xinha.notImplemented("getOuterHTML");
};
Xinha.getXMLHTTPRequestObject=function(){
try{
if(typeof XMLHttpRequest!="undefined"&&typeof XMLHttpRequest.constructor=="function"){
return new XMLHttpRequest();
}else{
if(typeof ActiveXObject=="function"){
return new ActiveXObject("Microsoft.XMLHTTP");
}
}
}
catch(e){
Xinha.notImplemented("getXMLHTTPRequestObject");
}
};
Xinha.prototype._activeElement=function(sel){
return this.activeElement(sel);
};
Xinha.prototype._selectionEmpty=function(sel){
return this.selectionEmpty(sel);
};
Xinha.prototype._getSelection=function(){
return this.getSelection();
};
Xinha.prototype._createRange=function(sel){
return this.createRange(sel);
};
HTMLArea=Xinha;
Xinha.init();
if(Xinha.ie_version<8){
Xinha.addDom0Event(window,"unload",Xinha.collectGarbageForIE);
}
Xinha.notImplemented=function(_291){
throw new Error("Method Not Implemented","Part of Xinha has tried to call the "+_291+" method which has not been implemented.");
};

