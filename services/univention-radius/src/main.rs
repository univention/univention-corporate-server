// SPDX-FileCopyrightText: 2026 Univention GmbH
// SPDX-License-Identifier: AGPL-3.0-only

mod logger;
mod mschapv2;
mod networkaccess;
mod school_networkaccess;
mod utils;

use clap::Parser;
use log::warn;
use std::process;
use subtle::ConstantTimeEq;

use crate::networkaccess::NetworkAccess;
use crate::networkaccess::NtlmAuth;
use crate::school_networkaccess::SchoolNetworkAccess;
use univentionconfig::ConfigRegistry;

const LOGFILE: &str = "/var/log/univention/radius_ntlm_auth.log";

#[derive(Parser)]
#[clap(about = "RADIUS 802.1X NTLM-Authentication program")]
struct Args {
    #[clap(long, required = true)]
    request_nt_key: bool,

    #[clap(long, required = true)]
    username: String,

    #[clap(long, required = true)]
    challenge: String,

    #[clap(long, required = true)]
    nt_response: String,

    #[clap(long)]
    station_id: Option<String>,
}

fn main() {
    let args = Args::parse();

    let ucr = ConfigRegistry::new();

    let debug_int = ucr.get_int("freeradius/auth/helper/ntlm/debug", 2);
    let level = logger::DebugLevel::from_int(debug_int);
    let _ = logger::init(LOGFILE, level);

    let challenge = match hex::decode(&args.challenge) {
        Ok(b) => b,
        Err(_) => {
            eprintln!("--challenge must be valid hex");
            process::exit(2);
        }
    };
    if challenge.len() < 8 {
        eprintln!("--challenge must be at least 8 bytes");
        process::exit(2);
    }

    let nt_response = match hex::decode(&args.nt_response) {
        Ok(b) => b,
        Err(_) => {
            eprintln!("--nt-response must be valid hex");
            process::exit(2);
        }
    };
    if nt_response.len() < 24 {
        eprintln!("--nt-response must be at least 24 bytes");
        process::exit(2);
    }

    let mut na: Box<dyn NtlmAuth> = if ucr.is_true("radius/use-school-extension", false) {
        Box::new(SchoolNetworkAccess::new(&args.username, args.station_id.as_deref(), ucr))
    } else {
        Box::new(NetworkAccess::new(&args.username, args.station_id.as_deref(), ucr))
    };

    let password_hash_result = na.get_nt_password_hash();

    match password_hash_result {
        Ok(password_hash) => {
            let response = mschapv2::challenge_response(&challenge, &password_hash);
            if response.ct_eq(nt_response.as_slice()).into() {
                let nt_key = mschapv2::hash_nt_password_hash(&password_hash);
                println!("NT_KEY: {}", hex::encode_upper(nt_key));
                process::exit(0);
            } else {
                println!("Logon failure (0xc000006d)");
                process::exit(1);
            }
        }
        Err(e) => {
            warn!("{}", e);
            println!("Logon failure (0xc000006d)");
            process::exit(1);
        }
    }
}
