// Univention Maintenance Mode
//  Minimal web server
//
// Copyright 2018 Univention GmbH
//
// http://www.univention.de/
//
// All rights reserved.
//
// The source code of this program is made available
// under the terms of the GNU Affero General Public License version 3
// (GNU AGPL V3) as published by the Free Software Foundation.
//
// Binary versions of this program provided by Univention to you as
// well as other copyrighted, protected or trademarked materials like
// Logos, graphics, fonts, specific documentations and configurations,
// cryptographic keys etc. are subject to a license agreement between
// you and Univention and not subject to the GNU AGPL V3.
//
// In the case you use this program under the terms of the GNU AGPL V3,
// the program is provided in the hope that it will be useful,
// but WITHOUT ANY WARRANTY; without even the implied warranty of
// MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
// GNU Affero General Public License for more details.
//
// You should have received a copy of the GNU Affero General Public
// License with the Debian GNU/Linux or Univention distribution in file
// /usr/share/common-licenses/AGPL-3; if not, see
// <http://www.gnu.org/licenses/>.
//

extern crate gotham;
extern crate hyper;
extern crate mime;

use hyper::{Response, StatusCode};

use gotham::http::response::create_response;
use gotham::state::State;

pub fn say_hello(state: State) -> (State, Response) {
    let res = create_response(
        &state,
        StatusCode::Ok,
        Some((String::from("
<html>
    <meta http-equiv=\"Content-Type\" content=\"text/html; charset=UTF-8\" />
    <title>UCS in Maintenance Mode</title>
    <body>
        <h1>UCS in Maintenance Mode</h1>
        <p>UCS is currently in Maintenance Mode. Important services like Univention Management Console (UMC) or even Apache are stopped or may not work correctly, so instead, this page is shown. New software is being installed and everything is going right. Please be patient while the system is updated.
    </body>
</html>").into_bytes(), mime::TEXT_HTML)),
    );

    (state, res)
}

pub fn main() {
    let addr = "0.0.0.0:80";
    println!("Listening for requests at http://{}", addr);
    gotham::start(addr, || Ok(say_hello))
}

