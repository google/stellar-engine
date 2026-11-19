/**
 * Copyright 2026 Google LLC
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 *      http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 */

# tfdoc:file:description NGFW return routes to the spoke VPC ranges.

locals {
  # Every range that a spoke can send traffic from: the primary and secondary
  # ranges of each subnet, and the proxy-only subnets that regional load
  # balancers connect from. The firewalls have a default route on the DMZ
  # interface only, so a reply to a range that is missing here leaves through
  # the DMZ instead of returning to the spoke.
  ngfw_spoke_cidrs = {
    for k in keys(var.envs_folders) : k => compact(concat(
      values(module.env-spoke-vpc[k].subnet_ips),
      flatten([
        for ranges in values(module.env-spoke-vpc[k].subnet_secondary_ranges) :
        values(ranges)
      ]),
      [
        for s in values(module.env-spoke-vpc[k].subnets_proxy_only) :
        s.ip_cidr_range
      ]
    ))
  }
  # One static route per range, in name => CIDR format. Grouping by CIDR keeps
  # a range from being routed twice. PAN-OS limits a static route name to 31
  # characters from letters, digits, spaces, hyphens and underscores. The
  # name is therefore the CIDR with hyphens, after as much of the environment
  # name as the CIDR leaves free. The CIDR is always whole, which keeps the
  # names unique.
  ngfw_return_routes = {
    for cidr, envs in transpose(local.ngfw_spoke_cidrs) : join("-", [
      substr(envs[0], 0, 30 - length(cidr)),
      replace(replace(cidr, ".", "-"), "/", "-")
    ]) => cidr
  }
}
