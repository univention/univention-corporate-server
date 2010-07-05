/* This compressed file is part of Xinha. For uncompressed sources, forum, and bug reports, go to xinha.org */
/* This file is part of version 0.95 released Mon, 12 May 2008 17:33:15 +0200 */
/* The URL of the most recent version of this file is http://svn.xinha.webfactional.com/trunk/plugins/TableOperations/table-operations.js */
Xinha.Config.prototype.TableOperations={"showButtons":true};
function TableOperations(_1){
this.editor=_1;
var _2=_1.config;
var bl=TableOperations.btnList;
var _4=this;
_2.removeToolbarElement(" inserttable toggleborders ");
var _5=["linebreak","inserttable","toggleborders"];
for(var i=0;i<bl.length;++i){
var _7=bl[i];
if(!_7){
if(_2.TableOperations.showButtons){
_5.push("separator");
}
}else{
var id="TO-"+_7[0];
_2.registerButton(id,Xinha._lc(_7[2],"TableOperations"),_1.imgURL(_7[0]+".gif","TableOperations"),false,function(_9,id){
_4.buttonPress(_9,id);
},_7[1]);
if(_2.TableOperations.showButtons){
_5.push(id);
}
}
}
_2.toolbar.push(_5);
if(typeof PopupWin=="undefined"){
Xinha._loadback(_editor_url+"modules/Dialogs/popupwin.js");
}
}
TableOperations._pluginInfo={name:"TableOperations",version:"1.0",developer:"Mihai Bazon",developer_url:"http://dynarch.com/mishoo/",c_owner:"Mihai Bazon",sponsor:"Zapatec Inc.",sponsor_url:"http://www.bloki.com",license:"htmlArea"};
TableOperations.prototype._lc=function(_b){
return Xinha._lc(_b,"TableOperations");
};
TableOperations.prototype.getClosest=function(_c){
var _d=this.editor;
var _e=_d.getAllAncestors();
var _f=null;
_c=(""+_c).toLowerCase();
for(var i=0;i<_e.length;++i){
var el=_e[i];
if(el.tagName.toLowerCase()==_c){
_f=el;
break;
}
}
return _f;
};
TableOperations.prototype.dialogTableProperties=function(){
var _12=this.getClosest("table");
var _13=new PopupWin(this.editor,Xinha._lc("Table Properties","TableOperations"),function(_14,_15){
TableOperations.processStyle(_15,_12);
for(var i in _15){
if(typeof _15[i]=="function"){
continue;
}
var val=_15[i];
switch(i){
case "f_caption":
if(/\S/.test(val)){
var _18=_12.getElementsByTagName("caption")[0];
if(!_18){
_18=_14.editor._doc.createElement("caption");
_12.insertBefore(_18,_12.firstChild);
}
_18.innerHTML=val;
}else{
var _18=_12.getElementsByTagName("caption")[0];
if(_18){
_18.parentNode.removeChild(_18);
}
}
break;
case "f_summary":
_12.summary=val;
break;
case "f_width":
_12.style.width=(""+val)+_15.f_unit;
break;
case "f_align":
_12.align=val;
break;
case "f_spacing":
_12.cellSpacing=val;
break;
case "f_padding":
_12.cellPadding=val;
break;
case "f_borders":
_12.border=val;
break;
case "f_frames":
_12.frame=val;
break;
case "f_rules":
_12.rules=val;
break;
}
}
_14.editor.forceRedraw();
_14.editor.focusEditor();
_14.editor.updateToolbar();
var _19=_12.style.borderCollapse;
_12.style.borderCollapse="collapse";
_12.style.borderCollapse="separate";
_12.style.borderCollapse=_19;
},function(_1a){
var _1b="";
var _1c=_12.getElementsByTagName("caption")[0];
if(_1c){
_1b=_1c.innerHTML;
}
var _1d=_12.summary;
var _1e=parseInt(_12.style.width);
isNaN(_1e)&&(_1e="");
var _1f=/%/.test(_12.style.width)?"percent":"pixels";
var _20=_12.align;
var _21=_12.cellSpacing;
var _22=_12.cellPadding;
var _23=_12.border;
var _24=_12.frame;
var _25=_12.rules;
function selected(val){
return val?" selected":"";
}
_1a.content.style.width="400px";
_1a.content.innerHTML=" <div class='title'>"+Xinha._lc("Table Properties","TableOperations")+"</div> <table style='width:100%'>   <tr>     <td>       <fieldset><legend>"+Xinha._lc("Description","TableOperations")+"</legend>        <table style='width:100%'>         <tr>           <td class='label'>"+Xinha._lc("Caption","TableOperations")+":</td>           <td class='value'><input type='text' name='f_caption' value='"+_1b+"'/></td>         </tr><tr>           <td class='label'>"+Xinha._lc("Summary","TableOperations")+":</td>           <td class='value'><input type='text' name='f_summary' value='"+_1d+"'/></td>         </tr>        </table>       </fieldset>     </td>   </tr>   <tr><td id='--HA-layout'></td></tr>   <tr>     <td>       <fieldset><legend>"+Xinha._lc("Spacing and padding","TableOperations")+"</legend>        <table style='width:100%'> "+"        <tr>           <td class='label'>"+Xinha._lc("Spacing","TableOperations")+":</td>           <td><input type='text' name='f_spacing' size='5' value='"+_21+"' /> &nbsp;"+Xinha._lc("Padding","TableOperations")+":            <input type='text' name='f_padding' size='5' value='"+_22+"' /> &nbsp;&nbsp;"+Xinha._lc("pixels","TableOperations")+"          </td>         </tr>        </table>       </fieldset>     </td>   </tr>   <tr>     <td>       <fieldset><legend>"+Xinha._lc("Frame and borders","TableOperations")+"</legend>         <table width='100%'>           <tr>             <td class='label'>"+Xinha._lc("Borders","TableOperations")+":</td>             <td><input name='f_borders' type='text' size='5' value='"+_23+"' /> &nbsp;&nbsp;"+Xinha._lc("pixels","TableOperations")+"</td>           </tr>           <tr>             <td class='label'>"+Xinha._lc("Frames","TableOperations")+":</td>             <td>               <select name='f_frames'>                 <option value='void'"+selected(_24=="void")+">"+Xinha._lc("No sides","TableOperations")+"</option>                 <option value='above'"+selected(_24=="above")+">"+Xinha._lc("The top side only","TableOperations")+"</option>                 <option value='below'"+selected(_24=="below")+">"+Xinha._lc("The bottom side only","TableOperations")+"</option>                 <option value='hsides'"+selected(_24=="hsides")+">"+Xinha._lc("The top and bottom sides only","TableOperations")+"</option>                 <option value='vsides'"+selected(_24=="vsides")+">"+Xinha._lc("The right and left sides only","TableOperations")+"</option>                 <option value='lhs'"+selected(_24=="lhs")+">"+Xinha._lc("The left-hand side only","TableOperations")+"</option>                 <option value='rhs'"+selected(_24=="rhs")+">"+Xinha._lc("The right-hand side only","TableOperations")+"</option>                 <option value='box'"+selected(_24=="box")+">"+Xinha._lc("All four sides","TableOperations")+"</option>               </select>             </td>           </tr>           <tr>             <td class='label'>"+Xinha._lc("Rules","TableOperations")+":</td>             <td>               <select name='f_rules'>                 <option value='none'"+selected(_25=="none")+">"+Xinha._lc("No rules","TableOperations")+"</option>                 <option value='rows'"+selected(_25=="rows")+">"+Xinha._lc("Rules will appear between rows only","TableOperations")+"</option>                 <option value='cols'"+selected(_25=="cols")+">"+Xinha._lc("Rules will appear between columns only","TableOperations")+"</option>                 <option value='all'"+selected(_25=="all")+">"+Xinha._lc("Rules will appear between all rows and columns","TableOperations")+"</option>               </select>             </td>           </tr>         </table>       </fieldset>     </td>   </tr>   <tr>     <td id='--HA-style'></td>   </tr> </table> ";
var _27=TableOperations.createStyleFieldset(_1a.doc,_1a.editor,_12);
var p=_1a.doc.getElementById("--HA-style");
p.appendChild(_27);
var _29=TableOperations.createStyleLayoutFieldset(_1a.doc,_1a.editor,_12);
p=_1a.doc.getElementById("--HA-layout");
p.appendChild(_29);
_1a.modal=true;
_1a.addButtons("OK","Cancel");
_1a.showAtElement(_1a.editor._iframe,"c");
});
};
TableOperations.prototype.dialogRowCellProperties=function(_2a){
var _2b=this.getClosest(_2a?"td":"tr");
var _2c=this.getClosest("table");
var _2d=new PopupWin(this.editor,_2a?Xinha._lc("Cell Properties","TableOperations"):Xinha._lc("Row Properties","TableOperations"),function(_2e,_2f){
TableOperations.processStyle(_2f,_2b);
for(var i in _2f){
if(typeof _2f[i]=="function"){
continue;
}
var val=_2f[i];
switch(i){
case "f_align":
_2b.align=val;
break;
case "f_char":
_2b.ch=val;
break;
case "f_valign":
_2b.vAlign=val;
break;
}
}
_2e.editor.forceRedraw();
_2e.editor.focusEditor();
_2e.editor.updateToolbar();
var _32=_2c.style.borderCollapse;
_2c.style.borderCollapse="collapse";
_2c.style.borderCollapse="separate";
_2c.style.borderCollapse=_32;
},function(_33){
var _34=_2b.align;
var _35=_2b.vAlign;
var _36=_2b.ch;
function selected(val){
return val?" selected":"";
}
_33.content.style.width="400px";
_33.content.innerHTML=" <div class='title'>"+Xinha._lc(_2a?"Cell Properties":"Row Properties","TableOperations")+"</div> <table style='width:100%'>   <tr>     <td id='--HA-layout'> "+"    </td>   </tr>   <tr>     <td id='--HA-style'></td>   </tr> </table> ";
var _38=TableOperations.createStyleFieldset(_33.doc,_33.editor,_2b);
var p=_33.doc.getElementById("--HA-style");
p.appendChild(_38);
var _3a=TableOperations.createStyleLayoutFieldset(_33.doc,_33.editor,_2b);
p=_33.doc.getElementById("--HA-layout");
p.appendChild(_3a);
_33.modal=true;
_33.addButtons("OK","Cancel");
_33.showAtElement(_33.editor._iframe,"c");
});
};
TableOperations.prototype.buttonPress=function(_3b,_3c){
this.editor=_3b;
var _3d=Xinha.is_gecko?"<br />":"";
function clearRow(tr){
var tds=tr.getElementsByTagName("td");
for(var i=tds.length;--i>=0;){
var td=tds[i];
td.rowSpan=1;
td.innerHTML=_3d;
}
}
function splitRow(td){
var n=parseInt(""+td.rowSpan);
var nc=parseInt(""+td.colSpan);
td.rowSpan=1;
tr=td.parentNode;
var itr=tr.rowIndex;
var trs=tr.parentNode.rows;
var _47=td.cellIndex;
while(--n>0){
tr=trs[++itr];
var otd=_3b._doc.createElement("td");
otd.colSpan=td.colSpan;
otd.innerHTML=_3d;
tr.insertBefore(otd,tr.cells[_47]);
}
_3b.forceRedraw();
_3b.updateToolbar();
}
function splitCol(td){
var nc=parseInt(""+td.colSpan);
td.colSpan=1;
tr=td.parentNode;
var ref=td.nextSibling;
while(--nc>0){
var otd=_3b._doc.createElement("td");
otd.rowSpan=td.rowSpan;
otd.innerHTML=_3d;
tr.insertBefore(otd,ref);
}
_3b.forceRedraw();
_3b.updateToolbar();
}
function splitCell(td){
var nc=parseInt(""+td.colSpan);
splitCol(td);
var _4f=td.parentNode.cells;
var _50=td.cellIndex;
while(nc-->0){
splitRow(_4f[_50++]);
}
}
function selectNextNode(el){
var _52=el.nextSibling;
while(_52&&_52.nodeType!=1){
_52=_52.nextSibling;
}
if(!_52){
_52=el.previousSibling;
while(_52&&_52.nodeType!=1){
_52=_52.previousSibling;
}
}
if(!_52){
_52=el.parentNode;
}
_3b.selectNodeContents(_52);
}
function cellMerge(_53,_54,_55,_56,_57){
var _58=[];
var _59=[];
try{
for(i=_55;i<_55+_57;i++){
var row=_53.rows[i];
for(j=_54;j<_54+_56;j++){
if(row.cells[j].colSpan>1||row.cells[j].rowSpan>1){
splitCell(row.cells[j]);
}
_59.push(row.cells[j]);
}
if(_59.length>0){
_58.push(_59);
_59=[];
}
}
}
catch(e){
alert("Invalid selection");
return false;
}
var _5b=_58[0][0].parentNode.rowIndex;
var _5c=_58[_58.length-1][0].parentNode.rowIndex;
var _5d=_58[_58.length-1][0].rowSpan;
var _5e="";
for(i=0;i<_58.length;++i){
var _59=_58[i];
for(var j=0;j<_59.length;++j){
var _60=_59[j];
_5e+=_60.innerHTML;
(i||j)&&(_60.parentNode.removeChild(_60));
}
}
var td=_58[0][0];
td.innerHTML=_5e;
td.rowSpan=_5c-_5b+_5d;
var _62=0;
for(j=0;j<_58[0].length;j++){
_62+=_58[0][j].colSpan;
}
td.colSpan=_62;
_3b.selectNodeContents(td);
_3b.forceRedraw();
_3b.focusEditor();
}
switch(_3c){
case "TO-row-insert-above":
case "TO-row-insert-under":
var tr=this.getClosest("tr");
if(!tr){
break;
}
var otr=tr.cloneNode(true);
clearRow(otr);
tr.parentNode.insertBefore(otr,/under/.test(_3c)?tr.nextSibling:tr);
_3b.forceRedraw();
_3b.focusEditor();
break;
case "TO-row-delete":
var tr=this.getClosest("tr");
if(!tr){
break;
}
var par=tr.parentNode;
if(par.rows.length==1){
alert(Xinha._lc("Xinha cowardly refuses to delete the last row in table.","TableOperations"));
break;
}
selectNextNode(tr);
par.removeChild(tr);
_3b.forceRedraw();
_3b.focusEditor();
_3b.updateToolbar();
break;
case "TO-row-split":
var td=this.getClosest("td");
if(!td){
break;
}
splitRow(td);
break;
case "TO-col-insert-before":
case "TO-col-insert-after":
var td=this.getClosest("td");
if(!td){
break;
}
var _67=td.parentNode.parentNode.rows;
var _68=td.cellIndex;
var _69=(td.parentNode.cells.length==_68+1);
for(var i=_67.length;--i>=0;){
var tr=_67[i];
var otd=_3b._doc.createElement("td");
otd.innerHTML=_3d;
if(_69&&Xinha.is_ie){
tr.insertBefore(otd);
}else{
var ref=tr.cells[_68+(/after/.test(_3c)?1:0)];
tr.insertBefore(otd,ref);
}
}
_3b.focusEditor();
break;
case "TO-col-split":
var td=this.getClosest("td");
if(!td){
break;
}
splitCol(td);
break;
case "TO-col-delete":
var td=this.getClosest("td");
if(!td){
break;
}
var _68=td.cellIndex;
if(td.parentNode.cells.length==1){
alert(Xinha._lc("Xinha cowardly refuses to delete the last column in table.","TableOperations"));
break;
}
selectNextNode(td);
var _67=td.parentNode.parentNode.rows;
for(var i=_67.length;--i>=0;){
var tr=_67[i];
tr.removeChild(tr.cells[_68]);
}
_3b.forceRedraw();
_3b.focusEditor();
_3b.updateToolbar();
break;
case "TO-cell-split":
var td=this.getClosest("td");
if(!td){
break;
}
splitCell(td);
break;
case "TO-cell-insert-before":
case "TO-cell-insert-after":
var td=this.getClosest("td");
if(!td){
break;
}
var tr=td.parentNode;
var otd=_3b._doc.createElement("td");
otd.innerHTML=_3d;
tr.insertBefore(otd,/after/.test(_3c)?td.nextSibling:td);
_3b.forceRedraw();
_3b.focusEditor();
break;
case "TO-cell-delete":
var td=this.getClosest("td");
if(!td){
break;
}
if(td.parentNode.cells.length==1){
alert(Xinha._lc("Xinha cowardly refuses to delete the last cell in row.","TableOperations"));
break;
}
selectNextNode(td);
td.parentNode.removeChild(td);
_3b.forceRedraw();
_3b.updateToolbar();
break;
case "TO-cell-merge":
var sel=_3b._getSelection();
if(!Xinha.is_ie&&sel.rangeCount>1){
var _6e=sel.getRangeAt(0);
var td=_6e.startContainer.childNodes[_6e.startOffset];
var tr=td.parentNode;
var _6f=td.cellIndex;
var _70=tr.rowIndex;
var _71=0;
var _72=_70;
var _73=0;
var _74=0;
var td2,tr2;
for(i=0;i<sel.rangeCount;i++){
_6e=sel.getRangeAt(i);
td2=_6e.startContainer.childNodes[_6e.startOffset];
tr2=td2.parentNode;
if(tr2.rowIndex!=_72){
_72=tr2.rowIndex;
_74=0;
}
_74+=td2.colSpan;
if(_74>_73){
_73=_74;
}
if(tr2.rowIndex+td2.rowSpan-1>_71){
_71=tr2.rowIndex+td2.rowSpan-1;
}
}
var _76=_71-_70+1;
var _77=tr.parentNode;
cellMerge(_77,_6f,_70,_73,_76);
}else{
var td=this.getClosest("td");
if(!td){
alert(Xinha._lc("Please click into some cell","TableOperations"));
break;
}
_3b._popupDialog("plugin://TableOperations/merge_cells.html",function(_78){
if(!_78){
return false;
}
_73=parseInt(_78["f_cols"],10)+1;
_76=parseInt(_78["f_rows"],10)+1;
var tr=td.parentNode;
var _7a=td.cellIndex;
var _7b=tr.rowIndex;
var _7c=tr.parentNode;
cellMerge(_7c,_7a,_7b,_73,_76);
},null);
}
break;
case "TO-table-prop":
this.dialogTableProperties();
break;
case "TO-row-prop":
this.dialogRowCellProperties(false);
break;
case "TO-cell-prop":
this.dialogRowCellProperties(true);
break;
default:
alert("Button ["+_3c+"] not yet implemented");
}
};
TableOperations.btnList=[["table-prop","table","Table properties"],null,["row-prop","tr","Row properties"],["row-insert-above","tr","Insert row before"],["row-insert-under","tr","Insert row after"],["row-delete","tr","Delete row"],["row-split","td[rowSpan!=1]","Split row"],null,["col-insert-before","td","Insert column before"],["col-insert-after","td","Insert column after"],["col-delete","td","Delete column"],["col-split","td[colSpan!=1]","Split column"],null,["cell-prop","td","Cell properties"],["cell-insert-before","td","Insert cell before"],["cell-insert-after","td","Insert cell after"],["cell-delete","td","Delete cell"],["cell-merge","tr","Merge cells"],["cell-split","td[colSpan!=1,rowSpan!=1]","Split cell"]];
TableOperations.getLength=function(_7d){
var len=parseInt(_7d);
if(isNaN(len)){
len="";
}
return len;
};
TableOperations.processStyle=function(_7f,_80){
var _81=_80.style;
for(var i in _7f){
if(typeof _7f[i]=="function"){
continue;
}
var val=_7f[i];
switch(i){
case "f_st_backgroundColor":
_81.backgroundColor=val;
break;
case "f_st_color":
_81.color=val;
break;
case "f_st_backgroundImage":
if(/\S/.test(val)){
_81.backgroundImage="url("+val+")";
}else{
_81.backgroundImage="none";
}
break;
case "f_st_borderWidth":
_81.borderWidth=val;
break;
case "f_st_borderStyle":
_81.borderStyle=val;
break;
case "f_st_borderColor":
_81.borderColor=val;
break;
case "f_st_borderCollapse":
_81.borderCollapse=val?"collapse":"";
break;
case "f_st_width":
if(/\S/.test(val)){
_81.width=val+_7f["f_st_widthUnit"];
}else{
_81.width="";
}
break;
case "f_st_height":
if(/\S/.test(val)){
_81.height=val+_7f["f_st_heightUnit"];
}else{
_81.height="";
}
break;
case "f_st_textAlign":
if(val=="char"){
var ch=_7f["f_st_textAlignChar"];
if(ch=="\""){
ch="\\\"";
}
_81.textAlign="\""+ch+"\"";
}else{
if(val=="-"){
_81.textAlign="";
}else{
_81.textAlign=val;
}
}
break;
case "f_st_verticalAlign":
_80.vAlign="";
if(val=="-"){
_81.verticalAlign="";
}else{
_81.verticalAlign=val;
}
break;
case "f_st_float":
if(Xinha.is_ie){
_81.styleFloat=val;
}else{
_81.cssFloat=val;
}
break;
}
}
};
TableOperations.createColorButton=function(doc,_86,_87,_88){
if(!_87){
_87="";
}else{
if(!/#/.test(_87)){
_87=Xinha._colorToRgb(_87);
}
}
var df=doc.createElement("span");
var _8a=doc.createElement("input");
_8a.type="hidden";
df.appendChild(_8a);
_8a.name="f_st_"+_88;
_8a.value=_87;
var _8b=doc.createElement("span");
_8b.className="buttonColor";
df.appendChild(_8b);
var _8c=doc.createElement("span");
_8c.className="chooser";
_8c.style.backgroundColor=_87;
_8b.appendChild(_8c);
_8b.onmouseover=function(){
if(!this.disabled){
this.className+=" buttonColor-hilite";
}
};
_8b.onmouseout=function(){
if(!this.disabled){
this.className="buttonColor";
}
};
_8c.onclick=function(){
if(this.parentNode.disabled){
return false;
}
_86._popupDialog("select_color.html",function(_8d){
if(_8d){
_8c.style.backgroundColor="#"+_8d;
_8a.value="#"+_8d;
}
},_87);
};
var _8e=doc.createElement("span");
_8e.innerHTML="&#x00d7;";
_8e.className="nocolor";
_8e.title=Xinha._lc("Unset color","TableOperations");
_8b.appendChild(_8e);
_8e.onmouseover=function(){
if(!this.parentNode.disabled){
this.className+=" nocolor-hilite";
}
};
_8e.onmouseout=function(){
if(!this.parentNode.disabled){
this.className="nocolor";
}
};
_8e.onclick=function(){
_8c.style.backgroundColor="";
_8a.value="";
};
return df;
};
TableOperations.createStyleLayoutFieldset=function(doc,_90,el){
var _92=doc.createElement("fieldset");
var _93=doc.createElement("legend");
_92.appendChild(_93);
_93.innerHTML=Xinha._lc("Layout","TableOperations");
var _94=doc.createElement("table");
_92.appendChild(_94);
_94.style.width="100%";
var _95=doc.createElement("tbody");
_94.appendChild(_95);
var _96=el.tagName.toLowerCase();
var tr,td,input,select,option,options,i;
if(_96!="td"&&_96!="tr"&&_96!="th"){
tr=doc.createElement("tr");
_95.appendChild(tr);
td=doc.createElement("td");
td.className="label";
tr.appendChild(td);
td.innerHTML=Xinha._lc("Float","TableOperations")+":";
td=doc.createElement("td");
tr.appendChild(td);
select=doc.createElement("select");
td.appendChild(select);
select.name="f_st_float";
options=["None","Left","Right"];
for(var i=0;i<options.length;++i){
var Val=options[i];
var val=options[i].toLowerCase();
option=doc.createElement("option");
option.innerHTML=Xinha._lc(Val,"TableOperations");
option.value=val;
if(Xinha.is_ie){
option.selected=((""+el.style.styleFloat).toLowerCase()==val);
}else{
option.selected=((""+el.style.cssFloat).toLowerCase()==val);
}
select.appendChild(option);
}
}
tr=doc.createElement("tr");
_95.appendChild(tr);
td=doc.createElement("td");
td.className="label";
tr.appendChild(td);
td.innerHTML=Xinha._lc("Width","TableOperations")+":";
td=doc.createElement("td");
tr.appendChild(td);
input=doc.createElement("input");
input.type="text";
input.value=TableOperations.getLength(el.style.width);
input.size="5";
input.name="f_st_width";
input.style.marginRight="0.5em";
td.appendChild(input);
select=doc.createElement("select");
select.name="f_st_widthUnit";
option=doc.createElement("option");
option.innerHTML=Xinha._lc("percent","TableOperations");
option.value="%";
option.selected=/%/.test(el.style.width);
select.appendChild(option);
option=doc.createElement("option");
option.innerHTML=Xinha._lc("pixels","TableOperations");
option.value="px";
option.selected=/px/.test(el.style.width);
select.appendChild(option);
td.appendChild(select);
select.style.marginRight="0.5em";
td.appendChild(doc.createTextNode(Xinha._lc("Text align","TableOperations")+":"));
select=doc.createElement("select");
select.style.marginLeft=select.style.marginRight="0.5em";
td.appendChild(select);
select.name="f_st_textAlign";
options=["Left","Center","Right","Justify","-"];
if(_96=="td"){
options.push("Char");
}
input=doc.createElement("input");
input.name="f_st_textAlignChar";
input.size="1";
input.style.fontFamily="monospace";
td.appendChild(input);
for(var i=0;i<options.length;++i){
var Val=options[i];
var val=Val.toLowerCase();
option=doc.createElement("option");
option.value=val;
option.innerHTML=Xinha._lc(Val,"TableOperations");
option.selected=((el.style.textAlign.toLowerCase()==val)||(el.style.textAlign==""&&Val=="-"));
select.appendChild(option);
}
function setCharVisibility(_9b){
input.style.visibility=_9b?"visible":"hidden";
if(_9b){
input.focus();
input.select();
}
}
select.onchange=function(){
setCharVisibility(this.value=="char");
};
setCharVisibility(select.value=="char");
tr=doc.createElement("tr");
_95.appendChild(tr);
td=doc.createElement("td");
td.className="label";
tr.appendChild(td);
td.innerHTML=Xinha._lc("Height","TableOperations")+":";
td=doc.createElement("td");
tr.appendChild(td);
input=doc.createElement("input");
input.type="text";
input.value=TableOperations.getLength(el.style.height);
input.size="5";
input.name="f_st_height";
input.style.marginRight="0.5em";
td.appendChild(input);
select=doc.createElement("select");
select.name="f_st_heightUnit";
option=doc.createElement("option");
option.innerHTML=Xinha._lc("percent","TableOperations");
option.value="%";
option.selected=/%/.test(el.style.height);
select.appendChild(option);
option=doc.createElement("option");
option.innerHTML=Xinha._lc("pixels","TableOperations");
option.value="px";
option.selected=/px/.test(el.style.height);
select.appendChild(option);
td.appendChild(select);
select.style.marginRight="0.5em";
td.appendChild(doc.createTextNode(Xinha._lc("Vertical align","TableOperations")+":"));
select=doc.createElement("select");
select.name="f_st_verticalAlign";
select.style.marginLeft="0.5em";
td.appendChild(select);
options=["Top","Middle","Bottom","Baseline","-"];
for(var i=0;i<options.length;++i){
var Val=options[i];
var val=Val.toLowerCase();
option=doc.createElement("option");
option.value=val;
option.innerHTML=Xinha._lc(Val,"TableOperations");
option.selected=((el.style.verticalAlign.toLowerCase()==val)||(el.style.verticalAlign==""&&Val=="-"));
select.appendChild(option);
}
return _92;
};
TableOperations.createStyleFieldset=function(doc,_9d,el){
var _9f=doc.createElement("fieldset");
var _a0=doc.createElement("legend");
_9f.appendChild(_a0);
_a0.innerHTML=Xinha._lc("CSS Style","TableOperations");
var _a1=doc.createElement("table");
_9f.appendChild(_a1);
_a1.style.width="100%";
var _a2=doc.createElement("tbody");
_a1.appendChild(_a2);
var tr,td,input,select,option,options,i;
tr=doc.createElement("tr");
_a2.appendChild(tr);
td=doc.createElement("td");
tr.appendChild(td);
td.className="label";
td.innerHTML=Xinha._lc("Background","TableOperations")+":";
td=doc.createElement("td");
tr.appendChild(td);
var df=TableOperations.createColorButton(doc,_9d,el.style.backgroundColor,"backgroundColor");
df.firstChild.nextSibling.style.marginRight="0.5em";
td.appendChild(df);
td.appendChild(doc.createTextNode(Xinha._lc("Image URL","TableOperations")+": "));
input=doc.createElement("input");
input.type="text";
input.name="f_st_backgroundImage";
if(el.style.backgroundImage.match(/url\(\s*(.*?)\s*\)/)){
input.value=RegExp.$1;
}
td.appendChild(input);
tr=doc.createElement("tr");
_a2.appendChild(tr);
td=doc.createElement("td");
tr.appendChild(td);
td.className="label";
td.innerHTML=Xinha._lc("FG Color","TableOperations")+":";
td=doc.createElement("td");
tr.appendChild(td);
td.appendChild(TableOperations.createColorButton(doc,_9d,el.style.color,"color"));
input=doc.createElement("input");
input.style.visibility="hidden";
input.type="text";
td.appendChild(input);
tr=doc.createElement("tr");
_a2.appendChild(tr);
td=doc.createElement("td");
tr.appendChild(td);
td.className="label";
td.innerHTML=Xinha._lc("Border","TableOperations")+":";
td=doc.createElement("td");
tr.appendChild(td);
var _a5=TableOperations.createColorButton(doc,_9d,el.style.borderColor,"borderColor");
var btn=_a5.firstChild.nextSibling;
td.appendChild(_a5);
btn.style.marginRight="0.5em";
select=doc.createElement("select");
var _a7=[];
td.appendChild(select);
select.name="f_st_borderStyle";
options=["none","dotted","dashed","solid","double","groove","ridge","inset","outset"];
var _a8=el.style.borderStyle;
if(_a8.match(/([^\s]*)\s/)){
_a8=RegExp.$1;
}
for(var i=0;i<options.length;i++){
var val=options[i];
option=doc.createElement("option");
option.value=val;
option.innerHTML=val;
if(val==_a8){
option.selected=true;
}
select.appendChild(option);
}
select.style.marginRight="0.5em";
function setBorderFieldsStatus(_ab){
for(var i=0;i<_a7.length;++i){
var el=_a7[i];
el.style.visibility=_ab?"hidden":"visible";
if(!_ab&&(el.tagName.toLowerCase()=="input")){
el.focus();
el.select();
}
}
}
select.onchange=function(){
setBorderFieldsStatus(this.value=="none");
};
input=doc.createElement("input");
_a7.push(input);
input.type="text";
input.name="f_st_borderWidth";
input.value=TableOperations.getLength(el.style.borderWidth);
input.size="5";
td.appendChild(input);
input.style.marginRight="0.5em";
var _ae=doc.createElement("span");
_ae.innerHTML=Xinha._lc("pixels","TableOperations");
td.appendChild(_ae);
_a7.push(_ae);
setBorderFieldsStatus(select.value=="none");
if(el.tagName.toLowerCase()=="table"){
tr=doc.createElement("tr");
_a2.appendChild(tr);
td=doc.createElement("td");
td.className="label";
tr.appendChild(td);
input=doc.createElement("input");
input.type="checkbox";
input.name="f_st_borderCollapse";
input.id="f_st_borderCollapse";
var val=(/collapse/i.test(el.style.borderCollapse));
input.checked=val?1:0;
td.appendChild(input);
td=doc.createElement("td");
tr.appendChild(td);
var _af=doc.createElement("label");
_af.htmlFor="f_st_borderCollapse";
_af.innerHTML=Xinha._lc("Collapsed borders","TableOperations");
td.appendChild(_af);
}
return _9f;
};

