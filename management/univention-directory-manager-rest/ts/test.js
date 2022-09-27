lib = require("./udm.js");
udm = new lib.UDM("http://10.200.4.70/univention/udm/", "Administrator", "univention");

async function main() {
  //console.log(await udm.getLdapBase());
  //console.log(await udm.objByUuid("98ba39f4-d5b3-103b-9458-591d3ad7dd70"));
  //anna = await udm.objByDn("uid=anna,cn=users,dc=intranet,dc=wiesenthal,dc=de");
  //title = anna.properties.title
  //console.log(title);
  //console.log(anna.uri);
  //if (title === "Prof.") {
  //  anna.properties.title = "Dr."
  //} else {
  //  anna.properties.title = "Prof."
  //}
  //anna.properties.username = "anna"
  //await anna.save();
  //console.log(anna.properties.title);
  //console.log(anna.dn);
  const users = await udm.get("users/user");

  // console.log(await users.createReport("PDF Document", ["uid=anna,cn=users,dc=intranet,dc=wiesenthal,dc=de"])); FIXME: 500!

  //let user = await users.new();
  //user.properties.username = "t5";
  //user.properties.lastname = "T5";
  //user.properties.password = "univention";
  //await user.save();
  //console.log(user.dn);
  //user.properties.username = "t6";
  //await user.save();
  //await user.move("dc=intranet,dc=wiesenthal,dc=de");
  //console.log(user.dn);
  //await user.delete();

  user = await users.get("uid=t4,cn=users,dc=intranet,dc=wiesenthal,dc=de");
  p = await user.generateServiceSpecificPassword("radius");
  console.log(p);
  //user.properties.username = "t7";
  //await user.save();
  //console.log(user.dn);
  //user.properties.username = "t4";
  //await user.save();
  //console.log(user.dn);
}

main();
