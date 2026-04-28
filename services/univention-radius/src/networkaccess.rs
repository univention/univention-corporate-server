// SPDX-FileCopyrightText: 2026 Univention GmbH
// SPDX-License-Identifier: AGPL-3.0-only

use log::{debug, info};
use std::collections::HashMap;

use crate::utils::{decode_station_id, parse_username};
use univentionconfig::ConfigRegistry;
use univentionpolicy::{ldap_filter_escape, LdapConnection, LdapEntry};

const SECRET_FILE: &str = "/etc/freeradius.secret";
const SAMBA_ACCOUNT_FLAG_DISABLED: u8 = b'D';
const SAMBA_ACCOUNT_FLAG_LOCKED: u8 = b'L';

#[derive(Debug)]
pub enum NetworkAccessError {
    UserNotAllowed(String),
    MacNotAllowed(String),
    NoHash(String),
    UserDeactivated(String),
    LdapError(String),
    IoError(String),
}

impl std::fmt::Display for NetworkAccessError {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        match self {
            NetworkAccessError::UserNotAllowed(m) => write!(f, "{}", m),
            NetworkAccessError::MacNotAllowed(m) => write!(f, "{}", m),
            NetworkAccessError::NoHash(m) => write!(f, "{}", m),
            NetworkAccessError::UserDeactivated(m) => write!(f, "{}", m),
            NetworkAccessError::LdapError(m) => write!(f, "{}", m),
            NetworkAccessError::IoError(m) => write!(f, "{}", m),
        }
    }
}

pub trait NtlmAuth {
    fn get_nt_password_hash(&mut self) -> Result<Vec<u8>, NetworkAccessError>;
}

pub struct NetworkAccess {
    pub username: String,
    pub mac_address: String,
    pub ucr: ConfigRegistry,
    pub use_ssp: bool,
    pub whitelisting: bool,
    ldap_connection: Option<LdapConnection>,
}

impl NetworkAccess {
    pub fn new(username: &str, station_id: Option<&str>, ucr: ConfigRegistry) -> Self {
        let username = parse_username(username);
        let mac_address = station_id.map(decode_station_id).unwrap_or_default();
        let use_ssp = ucr.is_true("radius/use-service-specific-password", false);
        let whitelisting = ucr.is_true("radius/mac/whitelisting", false);

        debug!("Given username: {:?}", username);
        debug!("Given stationId: {:?}", station_id);

        NetworkAccess {
            username,
            mac_address,
            ucr,
            use_ssp,
            whitelisting,
            ldap_connection: None,
        }
    }

    fn ldap_connection(&mut self) -> Result<&LdapConnection, NetworkAccessError> {
        if self.ldap_connection.is_none() {
            let conn = LdapConnection::new_machine_connection(&self.ucr, SECRET_FILE)
                .map_err(|e| NetworkAccessError::LdapError(e.to_string()))?;
            self.ldap_connection = Some(conn);
        }
        Ok(self.ldap_connection.as_ref().unwrap())
    }

    fn build_access_dict(entries: &[LdapEntry]) -> HashMap<String, bool> {
        entries
            .iter()
            .map(|e| {
                let has_access = e
                    .attributes
                    .get("univentionNetworkAccess")
                    .map(|vals| vals.iter().any(|v| v == b"1"))
                    .unwrap_or(false);
                (e.dn.clone(), has_access)
            })
            .collect()
    }

    fn get_user_network_access(&mut self, uid: &str) -> Result<HashMap<String, bool>, NetworkAccessError> {
        let filter = format!("(uid={})", ldap_filter_escape(uid));
        let conn = self.ldap_connection()?;
        let mut users = conn.search(&filter, &["univentionNetworkAccess"]).map_err(|e| NetworkAccessError::LdapError(e.to_string()))?;

        if users.is_empty() {
            let filter = format!("(mailPrimaryAddress={})", ldap_filter_escape(uid));
            let conn = self.ldap_connection()?;
            users = conn.search(&filter, &["univentionNetworkAccess"]).map_err(|e| NetworkAccessError::LdapError(e.to_string()))?;
        }

        if users.is_empty() {
            let filter = format!("(macAddress={})", ldap_filter_escape(uid));
            let conn = self.ldap_connection()?;
            users = conn.search(&filter, &["univentionNetworkAccess"]).map_err(|e| NetworkAccessError::LdapError(e.to_string()))?;
        }

        Ok(Self::build_access_dict(&users))
    }

    fn get_station_network_access(&mut self, mac: &str) -> Result<HashMap<String, bool>, NetworkAccessError> {
        let filter = format!("(macAddress={})", ldap_filter_escape(mac));
        let conn = self.ldap_connection()?;
        let stations = conn.search(&filter, &["univentionNetworkAccess"]).map_err(|e| NetworkAccessError::LdapError(e.to_string()))?;
        Ok(Self::build_access_dict(&stations))
    }

    fn get_groups_network_access(&mut self, dn: &str) -> Result<HashMap<String, bool>, NetworkAccessError> {
        let filter = format!("(uniqueMember={})", ldap_filter_escape(dn));
        let conn = self.ldap_connection()?;
        let groups = conn.search(&filter, &["univentionNetworkAccess"]).map_err(|e| NetworkAccessError::LdapError(e.to_string()))?;
        Ok(Self::build_access_dict(&groups))
    }

    fn evaluate_ldap_network_access(
        &mut self,
        access: &HashMap<String, bool>,
        visited: &mut std::collections::HashSet<String>,
    ) -> Result<bool, NetworkAccessError> {
        let short_circuit = !log::log_enabled!(log::Level::Debug);

        // short-circuit: if not in debug mode and any entry allows access,
        // skip LDAP group traversal entirely
        // /usr/bin/univention-radius-check-access sets the loglevel hardcoded to DEBUG
        if short_circuit {
            if access.values().any(|v| *v) {
                return Ok(true);
            }
        }

        let mut policy = false;
        for (dn, pol) in access {
            if !visited.insert(dn.clone()) {
                log::debug!("Skipping already-visited DN: {}", dn);
                continue;
            }
            log::debug!("{} {:?}", if *pol { "ALLOW" } else { "DENY" }, dn);
            if *pol {
                policy = true;
                if short_circuit {
                    break;
                }
            }
            let parents = self.get_groups_network_access(dn)?;
            if self.evaluate_ldap_network_access(&parents, visited)? {
                policy = true;
            }
        }
        Ok(policy)
    }


    pub fn check_proxy_filter_policy(&self) -> bool {
        debug!("UCS@school RADIUS support is not installed");
        false
    }

    pub fn check_network_access(&mut self) -> Result<bool, NetworkAccessError> {
        let username = self.username.clone();
        let result = self.get_user_network_access(&username)?;
        if result.is_empty() {
            log::info!("Login attempt with unknown username");
            return Ok(false);
        }
        log::debug!("Checking LDAP settings for user");
        let mut visited = std::collections::HashSet::new();
        let policy = self.evaluate_ldap_network_access(&result, &mut visited)?;
        if policy {
            log::info!("Login attempt permitted by LDAP settings");
        } else {
            log::info!("Login attempt denied by LDAP settings");
        }
        Ok(policy)
    }

    pub fn check_station_whitelist(&mut self) -> Result<bool, NetworkAccessError> {
        if !self.whitelisting {
            log::debug!("MAC filtering is disabled by radius/mac/whitelisting.");
            return Ok(true);
        }
        log::debug!("Checking LDAP settings for stationId");
        if self.mac_address.is_empty() {
            log::info!("Login attempt without MAC address, but MAC filtering is enabled.");
            return Ok(false);
        }
        let mac = self.mac_address.clone();
        let result = self.get_station_network_access(&mac)?;
        if result.is_empty() {
            log::info!("Login attempt with unknown MAC address");
            return Ok(false);
        }
        let mut visited = std::collections::HashSet::new();
        let policy = self.evaluate_ldap_network_access(&result, &mut visited)?;
        if policy {
            log::info!("Login attempt permitted by LDAP settings");
        } else {
            log::info!("Login attempt denied by LDAP settings");
        }
        Ok(policy)
    }

    pub fn fetch_password_hash(&mut self) -> Result<Vec<u8>, NetworkAccessError> {
        let pwd_attr = if self.use_ssp {
            "univentionRadiusPassword"
        } else {
            "sambaNTPassword"
        };

        let username = self.username.clone();
        let filter = if username.contains('@') {
            format!("(mailPrimaryAddress={})", ldap_filter_escape(&username))
        } else {
            format!("(|(uid={})(macAddress={}))", ldap_filter_escape(&username), ldap_filter_escape(&username))
        };

        let conn = self.ldap_connection()?;
        let result = conn
            .search(&filter, &[pwd_attr, "sambaAcctFlags"])
            .map_err(|e| NetworkAccessError::LdapError(e.to_string()))?;

        let no_hash_error = || {
            NetworkAccessError::NoHash(format!(
                "No valid NT-password-hash found. Check the \"{}\" attribute of the user.",
                pwd_attr
            ))
        };

        let entry = result.first().ok_or_else(no_hash_error)?;

        let hex_hash = entry
            .attributes
            .get(pwd_attr)
            .and_then(|vals| vals.first())
            .ok_or_else(no_hash_error)?;

        let nt_password_hash = hex::decode(hex_hash).map_err(|_| no_hash_error())?;

        // NT hashes are MD4 hashes, i.e. exactly 128 bits / 16 bytes
        if nt_password_hash.len() != 16 {
            return Err(no_hash_error());
        }

        if let Some(flags_vals) = entry.attributes.get("sambaAcctFlags") {
            let flags = flags_vals
                .first()
                .filter(|value| !value.is_empty())
                .ok_or_else(|| {
                    NetworkAccessError::UserDeactivated(
                        "Missing or invalid sambaAcctFlags".to_string(),
                    )
                })?;

            if flags.contains(&SAMBA_ACCOUNT_FLAG_DISABLED) || flags.contains(&SAMBA_ACCOUNT_FLAG_LOCKED) {
                return Err(NetworkAccessError::UserDeactivated(
                    "Account is deactivated".to_string(),
                ));
            }
        }

        Ok(nt_password_hash)
    }
}

impl NtlmAuth for NetworkAccess {
    fn get_nt_password_hash(&mut self) -> Result<Vec<u8>, NetworkAccessError> {
        let proxy = self.check_proxy_filter_policy();
        if !proxy {
            let access = self.check_network_access()?;
            if !access {
                return Err(NetworkAccessError::UserNotAllowed(
                    "User is not allowed to authenticate via RADIUS".to_string(),
                ));
            }
        }

        self.check_station_whitelist().and_then(|allowed| {
            if !allowed {
                Err(NetworkAccessError::MacNotAllowed(
                    "stationId is denied, because it is not whitelisted".to_string(),
                ))
            } else {
                Ok(())
            }
        })?;

        log::info!("User is allowed to use RADIUS");
        self.fetch_password_hash()
    }
}
