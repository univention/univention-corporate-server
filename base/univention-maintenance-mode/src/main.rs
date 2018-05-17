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

fn read_progress() -> io::Result<f32> {
    let updater_status = UpdaterStatus::new()?;
    if updater_status.status == Some("DONE".to_string()) {
        return Ok(0.0);
    }
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

#[derive(Debug)]
struct UpdaterStatus {
    current_version: Option<String>,
    next_version: Option<String>,
    target_version: Option<String>,
    updatetype: Option<String>,
    status: Option<String>,
    errorsource: Option<String>,
    overall_updates: Vec<String>,
}

impl UpdaterStatus {
    pub fn finished_updates(&self) -> usize {
        let finished_updates_index = self.overall_updates.iter().position(|x| Some(x.to_string()) == self.current_version);
        match finished_updates_index {
            Some(index) => index + 1,
            None => 0
        }
    }

    pub fn new() -> io::Result<Self> {
        let status_file = File::open("/var/lib/univention-updater/univention-updater.status")?;
        let mut current_version: Option<String> = None;
        let mut next_version = None;
        let mut target_version = None;
        let mut updatetype = None;
        let mut status = None;
        let mut errorsource = None;
        for line in BufReader::new(status_file).lines() {
            if let Ok(line) = line {
                let bits: Vec<&str> = line.split("=").collect();
                if line.starts_with("current_version=") {
                    current_version = Some(String::from(bits[1]));
                }
                if line.starts_with("next_version=") {
                    next_version = Some(String::from(bits[1]));
                }
                if line.starts_with("target_version=") {
                    target_version = Some(String::from(bits[1]));
                }
                if line.starts_with("type=") {
                    updatetype = Some(String::from(bits[1]));
                }
                if line.starts_with("status=") {
                    status = Some(String::from(bits[1]));
                }
                if line.starts_with("errorsource=") {
                    errorsource = Some(String::from(bits[1]));
                }
            }
        }
		let mut release_file = File::open("/var/lib/univention-updater/univention-updater.releases")?;
		let mut contents = String::new();
		release_file.read_to_string(&mut contents)?;
        let mut overall_updates = Vec::new();
        for ver in contents.split(",") {
            if Some(ver.to_string()) == target_version {
                break;
            }
            overall_updates.push(ver.to_string());
        }

        let status = UpdaterStatus {
            current_version: current_version,
            next_version: next_version,
            target_version: target_version,
            updatetype: updatetype,
            status: status,
            errorsource: errorsource,
            overall_updates: overall_updates,
        };
        println!("Status: {:?}", status);
        Ok(status)
    }
}
fn add_updater_context(percentage: f32) -> io::Result<f32> {
    let updater_status = UpdaterStatus::new()?;
    if updater_status.target_version == updater_status.current_version {
        return Ok(100.0);
    }
    let finished_updates = updater_status.finished_updates() as f32;
    let ret = (finished_updates * 100.0 + percentage) / (updater_status.overall_updates.len() as f32);
    Ok(ret)
}

fn write_json(percentage: f32) -> io::Result<()> {
    let mut outfile = File::create("/var/www/univention/maintenance/updater.json")?;
    write!(&mut outfile, "{{\"v1\":{{\"percentage\":{}}}}}", percentage)?;
    Ok(())
}

pub fn main() {
    loop {
        match read_progress() {
            Ok(percentage) => match add_updater_context(percentage) {
                Ok(percentage) => match write_json(percentage) {
                    Ok(_) => {},
                    Err(err) => println!("univention-maintenance-mode: Error while writing json: {:?}", err)
                },
                Err(err) => println!("univention-maintenance-mode: Error while adding context: {:?}", err)
            },
            Err(err) => println!("univention-maintenance-mode: Error while reading progress: {:?}", err)
        };
        let duration = Duration::from_millis(2000);
        sleep(duration);
    }
}

