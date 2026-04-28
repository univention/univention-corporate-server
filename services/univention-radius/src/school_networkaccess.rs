// SPDX-FileCopyrightText: 2026 Univention GmbH
// SPDX-License-Identifier: AGPL-3.0-only

use log::debug;
use std::collections::HashMap;
use univentionconfig::ConfigRegistry;

use crate::networkaccess::NtlmAuth;
use crate::networkaccess::{NetworkAccess, NetworkAccessError};

pub struct SchoolNetworkAccess {
    pub base: NetworkAccess,
    user_to_group: HashMap<String, Vec<String>>,
    group_info: HashMap<String, (i32, bool)>,
}

impl SchoolNetworkAccess {
    pub fn new(username: &str, station_id: Option<&str>, ucr: ConfigRegistry) -> Self {
        let base = NetworkAccess::new(username, station_id, ucr);
        let mut s = SchoolNetworkAccess {
            base,
            user_to_group: HashMap::new(),
            group_info: HashMap::new(),
        };
        s.load_info();
        s
    }

    fn load_info(&mut self) {
        debug!("Loading proxy rules from UCR");

        let user_group_entries = self.base.ucr.iter_prefix("proxy/filter/usergroup/");
        for (key, value) in user_group_entries {
            let group = key["proxy/filter/usergroup/".len()..].to_string();
            for user in value.split(',') {
                self.user_to_group
                    .entry(user.trim().to_lowercase())
                    .or_default()
                    .push(group.clone());
            }
        }

        let group_default_entries = self.base.ucr.iter_prefix("proxy/filter/groupdefault/");
        for (key, value) in group_default_entries {
            let group = key["proxy/filter/groupdefault/".len()..].to_string();
            let rule = value;
            let priority_key = format!("proxy/filter/setting/{}/priority", rule);
            let priority = self.base.ucr.get_int(&priority_key, 0).max(0);
            let wlan_key = format!("proxy/filter/setting/{}/wlan", rule);
            let wlan_enabled = self.base.ucr.is_true(&wlan_key, false);
            self.group_info.insert(group, (priority, wlan_enabled));
        }

        debug!("Loaded user_to_group {:?}", self.user_to_group);
        debug!("Loaded group_info {:?}", self.group_info);
    }

    pub fn check_proxy_filter_policy(&self) -> bool {
        debug!("Checking UCR proxy rules for user");
        let access = self.evaluate_proxy_network_access(&self.base.username.clone());
        if access {
            log::info!("Login attempt permitted by UCR proxy rules");
        } else {
            log::info!("Login attempt denied by UCR proxy rules");
        }
        access
    }

    fn evaluate_proxy_network_access(&self, username: &str) -> bool {
        let groups = match self.user_to_group.get(&username.to_lowercase()) {
            Some(g) => g,
            None => {
                debug!("DENY: No proxy rules for user {} found", username);
                return false;
            }
        };

        let matching_groups: HashMap<&String, &(i32, bool)> = self
            .group_info
            .iter()
            .filter(|(g, _)| groups.contains(g))
            .collect();

        if matching_groups.is_empty() {
            debug!("DENY: user {} not found in any WLAN enabled group", username);
            return false;
        }

        let max_priority = matching_groups.values().map(|(p, _)| *p).max().unwrap_or(0);
        let max_priority_groups: HashMap<_, _> = matching_groups
            .iter()
            .filter(|(_, (p, _))| *p == max_priority)
            .collect();

        if max_priority_groups.values().any(|(_, wlan)| *wlan) {
            debug!("ALLOW: WLAN is enabled in a group with highest priority");
            true
        } else {
            debug!("DENY: WLAN is not enabled in any group with highest priority");
            false
        }
    }
}
impl NtlmAuth for SchoolNetworkAccess {
    fn get_nt_password_hash(&mut self) -> Result<Vec<u8>, NetworkAccessError> {
        let proxy = self.check_proxy_filter_policy();
        if !proxy {
            let access = self.base.check_network_access()?;
            if !access {
                return Err(NetworkAccessError::UserNotAllowed(
                    "User is not allowed to authenticate via RADIUS".to_string(),
                ));
            }
        }

        self.base.check_station_whitelist().and_then(|allowed| {
            if !allowed {
                Err(NetworkAccessError::MacNotAllowed(
                    "stationId is denied, because it is not whitelisted".to_string(),
                ))
            } else {
                Ok(())
            }
        })?;

        log::info!("User is allowed to use RADIUS");
        self.base.fetch_password_hash()
    }
}
