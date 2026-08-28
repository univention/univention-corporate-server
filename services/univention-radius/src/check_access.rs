// SPDX-FileCopyrightText: 2026 Univention GmbH
// SPDX-License-Identifier: AGPL-3.0-only

mod logger;
mod mschapv2;
mod networkaccess;
mod school_networkaccess;
mod utils;

use clap::Parser;

use crate::networkaccess::NetworkAccess;
use crate::networkaccess::NtlmAuth;
use crate::school_networkaccess::SchoolNetworkAccess;
use univentionconfig::ConfigRegistry;

#[derive(Parser)]
#[clap(about = "Check network access for a user and/or MAC address")]
struct Args {
    #[clap(long, required = true)]
    username: String,

    #[clap(long)]
    station_id: Option<String>,
}

fn main() {
    let args = Args::parse();
    let ucr = ConfigRegistry::new();

    // We are setting the loglevel to DEBUG hardcoded here so that
    // networkaccess.rs:evaluate_ldap_network_access() evaluates all groups and shows the
    // information verbosely
    let _ = logger::init_with_writer(std::io::stdout(), logger::DebugLevel::Debug);

    let mut na: Box<dyn NtlmAuth> = if ucr.is_true("freeradius/auth/helper/ntlm/enable-proxy-filter-rules", false) {
        Box::new(SchoolNetworkAccess::new(&args.username, args.station_id.as_deref(), ucr))
    } else {
        Box::new(NetworkAccess::new(&args.username, args.station_id.as_deref(), ucr))
    };

    match na.get_nt_password_hash() {
        Ok(_) => {
            log::debug!("--- Thus access is ALLOWED.");
            // println!("--- Thus access is ALLOWED.");
            std::process::exit(0);
        }
        Err(e) => {
            log::debug!("{}", e);
            log::debug!("--- Thus access is DENIED.");
            // println!("--- Thus access is DENIED.");
            std::process::exit(1);
        }
    }
}
