# SE Security Best Practices Guide

**Created Date:** Nov 21, 2024

**Google POC(s):** stellar-engine@google.com

**Version:** 1.0.2

**Recent changes**: Updated formatting, TOC, and added
essentialcontacts.managed.allowedContactDomains information

**Purpose:** The purpose of this document is to outline recommended actions and
procedures to help organizations effectively protect their systems, data, and
infrastructure from cyber threats, while using Stellar Engine.

**Background:** Stellar Engine is designed to facilitate rapid deployment and
operation of services within a secure Google Cloud environment, specifically
targeting Department of Defense (DoD) Impact Level 5 (IL5) and FedRAMP High
Authorization to Operate (ATO) requirements. Leveraging Infrastructure as Code
(IaC), Stellar Engine utilizes bootstrap scripts to provision a baseline
environment within an Assured Workloads folder. This foundational environment
allows users to selectively deploy Google Cloud and approved third-party
services based on their specific needs, offering flexibility while maintaining a
standardized security posture.

To proactively identify and mitigate potential security vulnerabilities within
Stellar Engine, Mandiant conducted a penetration test. This assessment focused
on emulating real-world attacker tactics, techniques, and procedures (TTPs) from
the perspective of an authenticated user on a Google Compute Engine instance.
The primary objective was to attempt privilege escalation and lateral movement
within the environment.

Mandiant’s testing encompassed 18 key Google Cloud resources, aiming to identify
and close any security gaps that could impede the attainment of an ATO. The
findings and recommendations presented in this Security Best Practices guide are
derived from the penetration test report and aim to enhance Stellar Engine’s
ability to prevent, detect, and contain potential threats. These best practices
will assist in bolstering the security posture of Stellar Engine and contribute
to a successful ATO.

# Table of Contents

# Identity and Access Management

Stellar Engine's Identity and Access Management (IAM) security best practices
prioritize least privilege and Infrastructure-as-Code (IaC) using Terraform.
Human access to create or modify cloud resources is limited to tightly
controlled development environments. The Cloud Resource Manager service account
must be used for terraform apply actions within the CI/CD pipeline.

Access must be granted to _groups_, not _users_, based on curated,
least-privilege roles. Each microservice must utilize a unique service account
with minimal necessary permissions. Downloadable service account keys and
automatic role grants to default service accounts must be disabled.

Role groups, mirroring development and administrative functions must manage
access, following a gcp-X-${tenant}-${role}@X.gov naming convention. Initial
memberships are defined in Terraform with ongoing management handled by existing
IAM systems or Terraform.

While both individual Google Cloud accounts (preferred) and service accounts can
execute the bootstrap phase, an individual account (with gcp_org_admins group
membership) must be used. This account shall be tightly controlled and must be
disabled when not in use. Specific organization and folder-level roles are
required for bootstrap execution, including Organization Admin/Viewer,
Organization Policy Admin, Billing Admin/User, Folder Creator, Access Context
Manager Admin/User, and Security Admin.

ISV must follow the principle of least privilege and configure IAM roles that
align with the needs of the system.

## _Human Access_

- Access must be granted to groups, not individual users.
- Access will be granted based on a minimalized set of curated roles.

## _Machine Access_

- Individual Service Accounts will be defined for each microservice.&#9;
- Downloadable Service Account keys will not be used and their creation should
  be disabled by organization policy.
- Access will be granted based on the principle of least privilege, with only
  necessary functionality granted for the microservice.
- Disable automatic role grants to default service accounts
  (iam.automaticIamGrantsForDefaultServiceAccounts ) should be enabled as
  organization policy , this will remove the editor role from the default
  service accounts.

## _Application Specific Groups_

While Stellar Engine manages a core set of role groups, it's important to
acknowledge that other platforms and tenant-specific environments may require
additional role groups not explicitly defined within Stellar Engine. These
externally managed groups, such as those found in a secured data warehouse
(e.g., Data Analyst, Data Engineer, Network Administrator, Security
Administrator, Security Analyst), are outside the immediate scope of Stellar
Engine. However, understanding their potential overlap and interaction with
Stellar Engine's role management is crucial for a holistic view. Future
integrations or extensions may consider mapping or accommodating these external
groups.

## User Specific IAM

- Navigate to <https://console.cloud.google.com>
- In the console search bar type and select **_IAM_**

- Select the **_Allow_** and **_View By Principals_**
- Click **_Grant Access_**

- Insert the email address into the **_New principals_** field
- Assign the appropriate roles needed. **Ensure to select roles based off the
  principle of least privileged. **

- Click **_SAVE_** when all necessary roles have been selected.

## Group IAM

- Navigate to <https://console.cloud.google.com>
- In the console search bar type and select **Groups**.

You will see pre-configured IAM Groups that are organically a part of Stellar
Engine

- By clicking on the three dots of a particular group, you can add users to
  the specified group

- To create additional groups, click **_Create_**

- Fill out **Group Name**, **Group email address**, _and_ **Group
  description**.
- Click **_SAVE_**
- Navigate to **_IAM_**

- Select the **_Allow_** and **_View By Principals_**
- Click **_Grant Access_**

- Insert the new group email address into the **_New principals_** field
- Assign the appropriate roles needed. **Ensure to select roles based off the
  principle of least privilege. **

- Click **_SAVE_** when all necessary roles have been selected.

**References**

**_NIST SP 800-53 revision 5, Security and Privacy Controls for Federal
Information Systems and Organizations_**

- **SA-8(14) Security and Privacy Engineering Principles | Least Privilege**
  - Implement the security design principle of least privilege

#

# Group Permission Viewing Restrictions

In most organizations a healthy amount of opacity is desired. Most organizations
will want to disable general viewership of group members. For example, an
organization may wish that their developers not be able to generally see who are
all the members of a super-admin group. For instance, an organization might want
to restrict developers' general access to the membership list of a super-admin
group. &#11;

- With a Super User account, visit
  [https://admin.google.com](https://admin.google.com/ac/security/2sv)
- Via the Dropdown Menu Directory \> Groups
- Select the group which you wish to restrict membership viewers
- Access Settings \> Edit (hover over access type and click the pencil)
- Change the Radio Icon to Restricted.

# Multi Factor Authentication

Multi-Factor Authentication (MFA) must be enforced for all users (both
privileged and non-privileged) to significantly enhance account security. While
not enforced by default in Stellar Engine due to logistical reasons, enabling
MFA is crucial for IL5 compliance and aligns with best practices recommended by
Google and NIST. Without MFA, compromised user credentials (obtained via methods
like password spraying or social engineering) grant an attacker unrestricted
access to internal resources, potentially facilitating lateral movement.

ISV must implement MFA when creating user accounts.

- With a Super User account, visit <https://admin.google.com/ac/security/2sv>
- Check the box **_Allow users to turn on 2-Step Verification_**
- Select **_Enforcement On_**
- Configure **_New user enrollment period_**, **_Frequency_**, and
  **_Methods_**, as needed

- Click **_SAVE_**

**References**

**_NIST SP 800-53 revision 5, Security and Privacy Controls for Federal
Information Systems and Organizations_**

- **IA-2(1) Identification and Authentication (organizational users) |
  Multi-Factor Authentication for Privileged Accounts**
  - Implement multi-factor authentication for access to privileged accounts
- **IA-2(2) Identification and Authentication (organizational users) |
  Multi-Factor Authentication for Non-Privileged Accounts**
  - Implement multi-factor authentication for access to non-privileged
    accounts

**_NIST SP 800-63-3, Digital Identity Guidelines_**

#

# GCP Cloud Shell Enabled

Cloud Shell is not currently supported at IL2, IL4, and IL5 and should be
disabled. To see a list of compliant products, refer to this page
[https://cloud.google.com/assured-workloads/docs/supported-products
](https://cloud.google.com/assured-workloads/docs/supported-products)

Cloud Shell provides an opportunity for execution within the GCP Environment. An
attacker can leverage this resource to execute a payload and gain persistence in
the environment. The Cloud Shell instance is not a Compute Instance hosted by
the GCP customer, rather GCP. Although the compromised instance isn't directly
involved in critical projects, it lets attackers proxy traffic through Google
and bypass system-level logging on the host.

ISV is responsible for disabling GCP Cloud Shell access.

- With a Super User account, visit
  <https://admin.google.com/ac/appslist/additional>

<!-- end list -->

- Scroll down and click **_Google Cloud Platform_**
- Click **Cloud Shell Access Settings**

- Uncheck **_Allow access to Cloud Shell_**
- Click **_SAVE_**

#

**References**

**_Google Cloud Shell Documentation_**

- **_Disable or reset Cloud Shell;
  _**<https://cloud.google.com/shell/docs/resetting-cloud-shell>

# Detection, Alerting, and Logging; Security Information and Event Management is Not Segmented

Google Cloud collects several types of logs for auditing and monitoring:

- **Audit Logs**: Record actions within the cloud environment. There are three
  types:
  - **Admin Activity**: Logs changes to resource configurations (e.g.,
    creating VMs, changing permissions).
  - **Data Access**: Logs reads of resource configuration and metadata, as
    well as user actions that create, modify, or read user data.
  - **System Event**: Logs changes made by Google's systems, not directly by
    users.
- **Other Logs**: Provide network and access information:
- **VPC Flow Logs**: Sample network traffic to and from your VMs. Useful for
  network monitoring and security analysis.
- **Firewall Rule Logs**: Show how firewall rules are working and how many
  connections they affect.
- **Access Transparency Logs**: Detail actions taken by Google staff when they
  access your environment.

ISV must bring a SIEM/SOAR solution that lives outside the project, in order to
meet organizational and compliance requirements.

The ISV shall implement their own SIEM to proactively monitor their software’s
infrastructure and the usage patterns within the software. This SIEM system may
integrate with existing SIEM tools, but the ISV shall maintain its own dedicated
instance for comprehensive internal security oversight. The SIEM system must
provide real-time alerts and notifications based on configured rules and
thresholds, enabling the ISV to promptly respond to potential threats or
anomalies.

The ISV must segment the SIEM in another project and on a separate VPC from
where it is collecting data.

**References**

**_NIST SP 800-53 revision 5, Security and Privacy Controls for Federal
Information Systems and Organizations_**

- **Audit and Accountability (AU)**
- **Assessment, Authorization, and Monitoring (CA)**
- **System and information Integrity (SI)**

# Data Exfiltration Possible from Cloud Storage

Multi-Factor Authentication (MFA) must be enforced for all users (both
privileged and non-privileged) to significantly enhance account security. While
not enforced by default in Stellar Engine due to logistical reasons, enabling
MFA is crucial for IL5 compliance and aligns with best practices recommended by
Google and NIST. Without MFA, compromised user credentials (obtained via methods
like password spraying or social engineering) grant an attacker unrestricted
access to internal resources, potentially facilitating lateral movement.

ISV must implement MFA when creating user accounts.

Referring to **_Multi Factor Authentication_**

While implementing robust security measures, Stellar Engine shall utilize
Context Aware Access to restrict resource access based on user context.
Additionally, the implementation of VPC Service Controls on data storage buckets
is strongly recommended for enhanced data security. However, it is important to
note that Identity-Aware Proxy (IAP) is not compliant with IL5 and VPC Service
Controls are currently unavailable within an IL5.

**References**

**_NIST SP 800-53 revision 5, Security and Privacy Controls for Federal
Information Systems and Organizations_**

- **IA-2(1) Identification and Authentication (organizational users) |
  Multi-Factor Authentication for Privileged Accounts**
  - Implement multi-factor authentication for access to privileged accounts
- **IA-2(2) Identification and Authentication (organizational users) |
  Multi-Factor Authentication for Non-Privileged Accounts**
  - Implement multi-factor authentication for access to non-privileged
    accounts

**_NIST SP 800-63-3, Digital Identity Guidelines_**

**_Context Aware Access_**

- <https://cloud.google.com/iap/docs/cloud-iap-context-aware-access-howto>

**_VPC Service Controls_**

- [https://cloud.google.com/vpc-service-controls/docs/overview\#how-vpc-service-controls-work](https://cloud.google.com/vpc-service-controls/docs/overview#how-vpc-service-controls-works)

# Essential Contacts

Essential Contacts, a core service within Google Cloud, is designed to provide
timely and relevant notifications to designated personnel regarding critical
aspects of resources and projects. This service allows organizations to assign
specific individuals or groups to receive alerts on a wide range of topics,
including billing, security, technical matters, and legal obligations. Properly
leveraging Essential Contacts is essential for mitigating risks, ensuring
compliance, and fostering a proactive approach to maintaining a secure and
well-managed Google Cloud environment.

ISV must configure essential contacts.

## Managing Essential Contacts Domain Restrictions

To enhance security, Google Cloud may enforce the
essentialcontacts.managed.allowedContactDomains organization policy constraint.
This policy restricts the email domains that can be used when adding [Essential
Contacts](https://cloud.google.com/resource-manager/docs/managing-notification-contacts)
for important notifications.

By default, for organizations created on or after June 26, 2025, the
organization's own domain is automatically included in the allowed list.
However, you might find that the list of allowed domains is empty or does not
include all necessary domains. This can occur if the organization was created
before this date or if an Infrastructure as Code (IaC) tool like Terraform is
managing and applying a stricter version of the policy.

If a domain is not on the allowed list, you will be blocked from adding contacts
with email addresses from that domain.

**Action**:

1.  Verify the current state of the
    essentialcontacts.managed.allowedContactDomains policy for your
    organization.
2.  If necessary, update the policy to add any required contact domains. Each
    domain entry must be prefixed with an "@" symbol (e.g., @myorgdomain.com,
    @[partnerdomain.com](http://partnerdomain.com)).
3.  **Important**: If you use Terraform, Latchkey, or another IaC tool to manage
    organization policies, ensure you make these changes within your IaC
    configuration files. Manual changes made via the Cloud Console or gcloud may
    be overwritten by your IaC automation.

This ensures that only email addresses from approved domains can be designated
as essential contacts, while allowing you to configure the domains your
organization trusts.

## Add Essential Contacts

- Navigate to <https://console.cloud.google.com>
- Select the appropriate organization or project where Essential Contacts will
  be configured. Essential Contacts configured at the organizational level
  will be inherited by sub-folders and projects but are able to be overridden
  at lower levels

- In the console search bar type and select **_Essential Contacts_**

- Click **_Add Contact_**

- Enter the email address of the individual or group to configure
  notifications.
- Select the Notification Categories to send corresponding notifications for.
  - Suspension; messages related to imminent suspension
  - Security; Security/Privacy issues, notifications, and vulnerabilities
  - Technical; Technical events and issues, such as outages, errors, and
    bugs
  - Billing; Billing and payments notifications, price updates, errors,
    credits
  - Legal; Enforcement actions, regulatory compliance, government notices
  - Product Updates; New versions, product terms updates, deprecations
  - All; All notifications from every other category
- Click **_SAVE_**

## Manage Existing Contacts

- Click to **_edit_** the Essential Contact for the applicable **_Notification
  Category_**

- Click to **_EDIT_** the Essential Contact or Click to ***DELETE ***the
  Essential Contact

**References**

**_Managing Contacts for Notifications_**

- <https://cloud.google.com/resource-manager/docs/managing-notification-contacts>

# Data Security

Google provides many protections to GCP customers, however, security of
workloads running in GCP is a shared responsibility.

Customers are responsible for the following aspects of their application
security:

## Data

Google encrypts all data communication channels that it uses to transmit data
between services; customers are responsible for ensuring that the transmission
of data is facilitated over an encrypted channel.

Google encrypts all data on storage devices to prevent anyone with physical
access to physical devices from being able to inspect the data contained on
those devices. Customers can provide their own encryption keys for the
encryption of Google Compute Engine Persistent Disks and Google Cloud Storage
buckets.

Data stored within databases are all encrypted at the storage level, however
additional encryption is advisable at the application level to prevent customer
users from accessing content and limiting spillage in the event of intrusion.

A customer may load data which may include PII and PCI into BigQuery for
analysis. Customers are responsible for being aware of and abiding by any
regulations regarding the use and storage of this data and are responsible for
developing their own aggregation capabilities.

## Cloud Key Management Service (KMS)

Cloud KMS is a global cloud-hosted key management service that lets customers
manage encryption for cloud services the same way a customer would on-premise.

Cloud KMS is a good solution if a customer needs to encrypt data at the
application level or manage their own encryption keys for compliance or
regulatory reasons.

- **Key Rotation: **Regular rotation of the encryption key is encouraged.
  Regular rotation will limit the amount of data protected by a single key.
  Automatic rotation can be configured on a user defined schedule by using
  _gcloud_ or the _GCP Console_.
- **Separation of duties: **Cloud KMS should be run in its own project without
  an owner at the project-level and instead being managed by an Org Admin. The
  Org Admin is not able to manage or use keys, but they are able to set IAM
  policies to restrict who has permissions for key management and usage.
  Additionally, the ability to manage Cloud KMS should have role separation
  from the ability to perform encryption and decryption operations. Any user
  with management access should not be able to decrypt data.
- **Additional Authenticated Data (AAD): **It is recommended to use AAD as an
  additional integrity check to help protect your data from a confused deputy
  attack. Additional authenticated data is a string that is passed to Cloud
  KMS as part of an encrypt or decrypt API call. Cloud KMS cannot decrypt
  ciphertext unless the same AAD value is used for both encryption and
  decryption. By default, an empty string is used for the AAD value.

## Google Cloud Storage

Google Cloud Storage identifies buckets and objects by their names. While Access
Control Lists (ACLs) prevent unauthorized actions, anyone can attempt requests
using bucket or object names. Even a failed request reveals whether a bucket or
object exists. This is a potential security concern, as observing error
responses can expose the existence of buckets and objects to unauthorized
parties. Furthermore, bucket names themselves might hint at the data they
contain, potentially leading to information leaks. If you're concerned about
protecting the privacy of your bucket and object names, consider taking
appropriate precautions, such as:

- Choosing bucket and object names that are difficult to guess
  - For example, a bucket named _stellar-engine-mybucket-gxl3_ is random
    enough that unauthorized third parties cannot feasibly guess it or
    enumerate other bucket names from it.
- Ensure your default object ACLs meet your requirements before uploading
  objects to a bucket. Setting them correctly beforehand can save significant
  time compared to updating individual object ACLs later.
- A straightforward and effective security practice is to segregate private
  and public data into separate buckets, clearly labeling those intended for
  public access.
  - For example, _stellar-engine-mybucket-public-3vxa_.
- **_Best Practice_**: Carefully evaluate the access control settings for each
  Cloud Storage object before writing data. Public read access grants
  universal read permissions and should only be used when deliberately
  exposing data to the public internet. Once an object is made publicly
  readable, it can be copied and disseminated, making it virtually impossible
  to regain exclusive control over the content.
- **_Best Practice_**: Avoid granting public write access to Cloud Storage
  buckets. While publicly writable buckets may appear convenient, the security
  risks are substantial. They can be easily exploited for malicious purposes,
  including the distribution of illegal content, viruses, and malware. Bucket
  owners bear full legal and financial responsibility for all content stored
  within their buckets, regardless of its origin.
- **_Best Practice_**: Utilize Signed URLs to securely share Cloud Storage
  content with users who do not have Google accounts. Signed URLs offer a
  controlled method for granting temporary, authenticated access to specific
  objects without requiring users to directly authenticate with Cloud Storage.
  Users retain control over the access type (read, write, delete) and its
  duration.

## Data residency

**_Best Practice_**: Implement a comprehensive data residency strategy
leveraging the Organization Policy Service and Cloud IAM.

- **Define Required Regions**: Clearly define the regions where your data is
  permitted to reside, based on regulatory requirements and business needs.
- **Implement Organization Policy**: Use the Organization Policy Service's
  "resource locations" constraint to restrict the creation of new resources to
  the approved regions. Apply this policy at the organization, folder, or
  project level as appropriate.
- **Integrate with Cloud IAM**: Configure Cloud IAM to control service usage,
  preventing users from inadvertently deploying resources in non-compliant
  regions.
- **Audit and Monitor**: Regularly audit your Google Cloud environment to
  ensure ongoing compliance with data residency policies.
- **Understand Limitations**: Be aware that the "resource locations"
  constraint only applies to newly created resources. Existing resources
  created before the policy was implemented will continue to function in their
  existing locations.

This multi-faceted approach helps ensure your data at rest remains within the
intended geographic boundaries.
