// Univention Maintenance Mode
//  Write progress of univention-updater in JSON file
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

use std::io::prelude::*;
use std::fs::File;
use std::io;
use std::io::BufReader;
use std::time::Duration;
use std::thread::sleep;

pub fn read_progress() -> io::Result<f32> {
    let mut ret = 0.0;
    let infile = File::open("/var/lib/univention-updater/univention-updater.status.details")?;
    for line in BufReader::new(infile).lines() {
        if let Ok(line) = line {
            let bits: Vec<&str> = line.split(":").collect();
            if bits.len() >= 3 {
                if bits[0] == "pmstatus" {
                    ret = match bits[2].parse::<f32>() {
                        Ok(val) => val,
                        Err(_) => ret
                    };
                }
            }
        }
    }
    Ok(ret)
}

pub fn write_json(percentage: f32) -> io::Result<()> {
    let mut outfile = File::create("/var/www/univention/maintenance/updater.json")?;
    write!(&mut outfile, "{{\"v1\":{{\"percentage\":{}}}}}", percentage)?;
    Ok(())
}

pub fn main() {
    loop {
        match read_progress() {
            Ok(percentage) => match write_json(percentage) {
                Ok(_) => {},
                Err(err) => println!("univention-maintenance-mode: Error while writing json: {:?}", err)
            },
            Err(err) => println!("univention-maintenance-mode: Error while reading progress: {:?}", err)
        };
        let duration = Duration::from_millis(2000);
        sleep(duration);
    }
}

