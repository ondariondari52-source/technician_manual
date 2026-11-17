# Technician Manual: Managed WiFi / Fiber Network Operations
## Sanitized reference manual for maintenance-manual Q&A project
(Adapted from an internal NOC procedures page. All credentials, phone
numbers, emails, internal URLs, IP addresses, and named individuals
have been removed or replaced with role labels. Only operational
procedures are retained. Explanatory material below each procedure is
presented as numbered notes, in the convention used by technical
reference manuals, with citations to the public standards or published
sources that support each note.)

## Section 1: Site types and equipment overview

There are three broad categories of managed sites: ACI (fiber/GPON) sites,
ACW (copper/switch-based) sites, and a small set of dedicated GPON sites
that use a different equipment stack from the rest of the fleet.

At GPON sites, the network uses Nokia-manufactured GPON OLT (Optical Line
Terminal) and ONT (Optical Network Terminal) equipment [1], paired with
Openwifi-brand wireless access points. When troubleshooting a GPON site, do
not look for a traditional network switch or a Ruckus-brand access point;
neither is present in this equipment stack.

For any connectivity alert at a GPON site, contact the resident directly
rather than the property management office. GPON sites are otherwise
treated like standard copper-network sites for scheduling a technician
dispatch or hardware replacement.

Notes

1. GPON (Gigabit Passive Optical Network) is defined by the ITU-T G.984
   series of recommendations. G.984.1 sets out the general
   characteristics of the system; G.984.2 defines the physical media
   layer; G.984.3 defines the transmission convergence layer; and
   G.984.4 defines the management and control interface between the
   OLT and the ONT. A single OLT port divides optical signal to many
   ONTs through passive optical splitters, with no powered equipment
   between the two, which is why a GPON site has no distribution
   switch at this layer for a technician to check. The ONT performs
   the optical to electrical conversion and commonly also serves as
   the resident's gateway device. A GPON ONT can be identified in the
   field by its single optical fiber connector, typically a thin
   yellow or blue cable, entering the unit from the wall, alongside
   standard Ethernet ports serving in-unit equipment. ACW sites, by
   contrast, carry traffic over structured copper cabling through
   Ethernet switches at the IDF and MDF layer, described in Sections 4
   and 5. GPON circuits commonly carry tighter service level
   commitments than copper sites, which is part of the basis for the
   resident-direct contact rule in Section 2.
   Source: International Telecommunication Union, Telecommunication
   Standardization Sector. Recommendation G.984.1, Gigabit-capable
   Passive Optical Networks (GPON): General Characteristics. ITU-T
   Study Group 15, 2003; and Recommendations G.984.2 through G.984.4,
   2003 to 2008.

## Section 2: Resident call handling at GPON sites

Resident calls that are transferred in regarding a GPON site must be
resolved during the call itself wherever possible. Standard practice for
front-line support tiers is to transfer unresolved calls to network
operations for follow-up; for GPON sites, this transfer path should be
avoided in favor of same-call resolution because these sites have a
dedicated, tighter service-level agreement for alert response and
resolution [1].

If an alert involves equipment located inside a resident's unit (an ONT or
an access point inside the unit, rather than shared equipment), contact the
resident directly to check the equipment's power state and to confirm
their availability window for a technician dispatch, rather than routing
the inquiry through property staff.

To locate a resident's contact record for a specific unit, search the
account system for the property and enter the unit number in the
secondary address field, then open the account record to view the
resident's phone number.

Before scheduling a dispatch, two checks are worth attempting with the
resident on the call: confirming the equipment has power, and asking the
resident to power cycle it (unplug, wait roughly thirty seconds, then
plug back in). A meaningful share of transient equipment issues clear
with a power cycle alone [2].

Notes

1. A transferred, unresolved call typically results in a second contact
   attempt later, a missed service window if the resident cannot be
   reached, and a slower measured time to resolution, since the
   service level clock on most managed service agreements starts at
   first contact rather than at the eventual technician visit.
   Resolving the call during first contact, even when the resolution
   is confirmation of a later technician visit, avoids an otherwise
   preventable delay against that clock.
2. This two-step check (confirm power, then power cycle) mirrors the
   standard first-line triage step used across consumer and managed
   network equipment support generally: a substantial share of
   transient faults in network equipment, including optical
   synchronization faults and access point software hangs, are
   resolved by a power cycle without further diagnosis required.

## Section 3: Offline access point (AP): troubleshooting checklist

When an access point reports offline, work through the following checks
in order:

1. Check the switchport link status at the port the AP is physically
   connected to. Confirm whether the port shows as up or down.
2. Confirm that VLAN 100 is present on the switchport the AP is connected
   to, and that it is configured as **untagged** on that port [1].
3. Confirm that VLAN 100 is present on the uplink port of that same
   switch, and that it is configured as **tagged** on the uplink [1].

If all three checks pass and the access point remains offline, power
cycle the access point itself (through PoE port disable and re-enable,
where remote power cycling is available), confirm it is not held in a
factory-reset or provisioning-pending state in the wireless controller,
and if neither resolves the issue, treat it as a hardware failure
candidate and follow the replacement procedure in Section 6.

Notes

1. An access point is classified, in IEEE 802.1Q terms, as an end
   station rather than a VLAN-aware bridge: it does not read or
   generate 802.1Q tags itself. Its access port is therefore
   configured untagged, meaning the switch adds the VLAN 100 tag to
   frames on the way in and removes it on the way out, which is
   standard practice for any end device (an access point, a desktop
   computer, a printer) connected directly to users rather than
   carrying multiple VLANs itself. A port carrying traffic between two
   VLAN-aware switches, such as the uplink in step 3, instead remains
   tagged, because it must carry VLAN 100 alongside other VLANs toward
   the rest of the network. The most frequent cause of a down link
   status at step 1 is a loose or damaged patch cable, followed by a
   Power-over-Ethernet fault on PoE-powered access points.
   Source: Institute of Electrical and Electronics Engineers. IEEE
   802.1Q, Virtual Bridged Local Area Networks (VLAN tagging and
   tagged/untagged port behavior).

## Section 4: Offline in-unit switch: troubleshooting checklist

When an in-unit switch reports offline, work through the following checks
in order:

1. Check the link status at the IDF (Intermediate Distribution Frame)
   switch port that the in-unit switch is connected to. Confirm whether
   the port shows as up or down.
2. Confirm that VLAN 100 is present on the switchport the in-unit switch
   is connected to, and that it is configured as **tagged** on that port [1].
3. Confirm that VLAN 100 is present on the uplink port of the IDF switch,
   and that it is configured as **tagged** on the uplink [1].

If all three checks pass and the in-unit switch remains offline, confirm
it is not still completing a reboot cycle (sixty to ninety seconds on
some models), then, if the switch remains unreachable after a complete
power cycle with all link and VLAN checks passing, follow the
replacement procedure in Section 6.

Notes

1. Unlike an access point, an in-unit switch is itself a VLAN-aware
   bridging device carrying traffic for multiple downstream devices,
   so under IEEE 802.1Q convention the port connecting it to the IDF
   switch is tagged rather than untagged, matching how the IDF
   switch's own uplink is tagged in Section 5. The governing pattern
   across all three checklists in this manual: a port facing an end
   device that does not read VLAN tags (an access point, as in
   Section 3) is untagged; a port facing another VLAN-aware switch (an
   in-unit switch to an IDF switch, here, or an IDF switch to an MDF
   switch, in Section 5) is tagged. Most in-unit switches are not
   PoE-powered and depend on a local power adapter, which makes
   accidental unplugging during cleaning or furniture movement a
   frequent and easily resolved cause of a down link status at step 1.
   Source: Institute of Electrical and Electronics Engineers. IEEE
   802.1Q, Virtual Bridged Local Area Networks.

## Section 5: Offline IDF switch: troubleshooting checklist

When an IDF (Intermediate Distribution Frame) switch reports offline, work
through the following checks in order:

1. Check the link status at the MDF/Core switch port that the IDF switch
   is connected to. Confirm whether the port shows as up or down.
2. Confirm that VLAN 100 is present on the MDF/Core switchport the IDF
   switch is connected to, and that it is configured as **tagged** on
   that port [1].
3. Confirm that VLAN 100 is present on the uplink port of the MDF/Core
   switch, and that it is configured as **tagged** on the uplink [1].

Given the potentially wide impact of an IDF outage, do not extend field
troubleshooting as long as would be reasonable for a single in-unit
device [2]. If a power cycle and all link and VLAN checks do not restore
service quickly, and ten or more units are already affected, escalate
immediately through the process in Section 9.

Notes

1. The MDF (Main Distribution Frame) is typically a property's central
   wiring point, where the uplink to the wider network terminates;
   IDF (Intermediate Distribution Frame) closets are secondary wiring
   points distributed around the property, commonly one per floor or
   building, that connect back to the MDF. Tagging convention at this
   layer follows the same rule given in the note to Section 4: a port
   connecting two VLAN-aware switches remains tagged along the entire
   path from the in-unit switch through the IDF to the MDF.
   Source: Institute of Electrical and Electronics Engineers. IEEE
   802.1Q, Virtual Bridged Local Area Networks.
2. An IDF switch failure affects every device served downstream of
   that closet simultaneously, in contrast to a single in-unit device
   failure. This difference in blast radius is the basis for the
   escalation threshold in Section 9 and for prioritizing faster
   escalation over extended field diagnosis specifically at the IDF
   layer.

## Section 6: Replacing an access point or switch

When physically replacing an offline AP or switch, follow this exact
sequence:

1. Delete the old AP or switch record from both the network controller
   and the monitoring platform.
2. Clear the associated event log entry inside the network controller for
   the removed device.
3. Add the new AP or switch as a new record, using its new MAC address.

Do not simply edit the MAC address field on the existing device record
to point at the replacement hardware. Editing the MAC address in place
breaks monitoring-platform tracking for that device, because the
monitoring platform associates history and status with the original
record, not the physical port [1].

Before starting the replacement on site, confirm the replacement unit is
the correct model for the role being replaced, and record the new
unit's MAC address, usually printed on a label on the device, before it
is mounted in a hard-to-reach location. After completing the
replacement, confirm the new device record shows online in the
monitoring platform within a few minutes; if it does not, recheck link
status and VLAN configuration using the applicable checklist from
Section 3, 4, or 5.

Notes

1. Network and infrastructure monitoring platforms generally key
   uptime history, alert history, and performance records to a
   device's internal record identifier rather than to its MAC address.
   Overwriting the MAC address on an existing record therefore merges
   the replacement device's future history with the old, failed
   device's past history: the replacement inherits the prior device's
   downtime in uptime statistics, and a platform that already shows an
   open alert against that record may suppress a genuinely new alert
   on the replacement hardware. Creating a new record instead keeps
   the replacement's history independent from the start.

## Section 7: Switch firmware version requirements

Before returning a switch to service, confirm it is running an approved
firmware version for its model:

- 7000-model switches must be running firmware version 08.0.95kT211.
- 8000-model switches must be running firmware version 10.0.10bT253.

A switch running an unapproved firmware version should be flagged for
a firmware update before being marked as resolved [1]. Most switch
models expose their current firmware version through a show-version
command, or its equivalent, in the management interface; checking
before deployment takes under a minute on a standard managed switch.
A switch found on an unapproved version should not be deployed to a
live site; flag it for update through the standard equipment-staging
process first.

Notes

1. The National Institute of Standards and Technology defines patch
   management, in Special Publication 800-40 Revision 3, as the
   process of identifying, acquiring, installing, and verifying
   patches for products and systems, and notes that patches correct
   both security and functionality problems in software and firmware.
   Firmware releases for managed network switches commonly bundle
   security fixes, stability fixes for known bugs (including bugs
   capable of producing link or VLAN tagging faults of the kind
   described in Sections 3 through 5), and compatibility fixes for
   interoperating hardware. A switch returned from a prior deployment
   or pulled from inventory may be running an older firmware version
   than currently approved, which is the basis for checking firmware
   compliance specifically at the point of returning a switch to
   service.
   Source: Souppaya, M. and Scarfone, K. Special Publication 800-40
   Revision 3, Guide to Enterprise Patch Management Technologies.
   National Institute of Standards and Technology, 2013.

## Section 8: Dispatch ticket priority legend

When creating a technician dispatch ticket, use the following priority
definitions:

- **Emergency**: response required within 2 hours, same day.
- **Priority**: response required first thing the following morning
  (next business day).
- **Routine**: response may occur at any point during the standard
  business day.

Before creating any technician dispatch ticket, first reach out to
on-site property staff or maintenance personnel to ask them to check the
affected room or unit. Only proceed with a dispatch if property staff
cannot resolve the issue [1].

Reserve Emergency for outages affecting shared infrastructure or
multiple residents at once (an offline IDF switch under Section 5, or
an event meeting the multi-unit threshold in Section 9), and for any
safety-related equipment issue. Priority fits a single resident's
equipment being down with no workaround and no shared-infrastructure
impact. Routine fits non-urgent requests with no active service
disruption driving the timeline.

Notes

1. A meaningful share of equipment-offline alerts are resolved by
   property staff within minutes without a technician visit: a
   breaker switched off during unrelated maintenance, a patch panel
   disturbed during cleaning, or a power strip unplugged are common,
   quickly resolved causes. Confirming with property staff before
   dispatching avoids an unnecessary technician trip in these cases
   and restores service to the resident faster than waiting for a
   scheduled visit would.

## Section 9: Escalation for multi-unit outage events

If a single property reports outage issues affecting 10 or more units
within a 2-hour window, this qualifies as a moderate-severity event and
must be escalated to the equipment vendor's support team [1].

Escalation order:

1. Contact the primary on-call escalation contact for that vendor
   relationship first.
2. If the primary contact is unavailable, contact the secondary on-call
   escalation contact.
3. If neither escalation contact is reachable, open an escalation ticket
   directly with the vendor's support portal.

Before escalating, gather the property name or site identifier, the
approximate number of units affected and how that count was determined,
when the outage was first observed, whether it correlates with a known
shared point of failure, and whether the checklists in Sections 3
through 5 have already been attempted. Having this ready at the start
of the first escalation call avoids a slower information-gathering
exchange.

Notes

1. A small number of simultaneous, independent equipment failures is
   statistically expected at any given time across a large property
   portfolio. Ten or more outages within a two-hour window is a
   substantially stronger signal of a shared infrastructure cause,
   such as a single failed IDF switch (Section 5) or MDF uplink, than
   of coincidental independent failures, which is the basis for
   treating this as its own severity category with a dedicated
   escalation path rather than working it as ten separate individual
   tickets.

## Section 10: Circuit issue handling

When an issue is identified as a circuit-level fault (rather than an
on-site equipment fault), open a ticket through the ISP's express
ticketing portal first, then follow up by phone using the appropriate
ISP support line to request a status update. Do not skip directly to a
phone call without first opening the express ticket, as the ticket
number is generally required before the ISP will discuss the case [1].

A circuit-level fault sits upstream of the property's own equipment:
on the ISP's network, or on the link connecting the property to it,
rather than in anything covered by Sections 3 through 6. Signs pointing
to a circuit-level fault include a healthy link status and correct VLAN
configuration on every internal MDF/Core port while the uplink toward
the ISP shows down or is flapping, or multiple properties served by the
same ISP circuit being affected at once.

Notes

1. Internet service providers generally require an open ticket
   reference number before discussing or prioritizing a case by phone,
   since the ticket is what creates the tracked case in their system
   and gives the phone support agent a record to work from. Calling
   before opening a ticket typically results in being asked to open
   one and call back, which costs more time than opening the ticket
   first and calling only to expedite or clarify an already-open case.

## Section 11: Hardware replacement processing

Routine hardware replacements involving five units or fewer at a single
property should be processed directly through the case management
system. Do not email the property manager to arrange these smaller
replacements; the case management system handles scheduling and
shipping automatically once the replacement is logged there [1].

The case management system generates a shipping request for the
replacement hardware and creates the technician dispatch ticket for
installation automatically once a replacement is logged, without a
separate manual step. Track a replacement's status through the case
management system itself rather than by contacting the property
manager, since the property manager does not coordinate shipping or
scheduling in this workflow.

Notes

1. Small, routine replacements follow a standard, automatable shipping
   and scheduling workflow. Batches larger than five units at once
   more often indicate a bulk equipment refresh or a larger underlying
   issue, such as an aging equipment generation being phased out
   across a property, which benefits from direct coordination with
   the property manager on timing, resident notification, and access
   scheduling rather than automated case processing.

## Section 12: Billing and invoice inquiries

Residents asking about billing charges or requesting copies of their
invoices should be referred to their property manager. Property
managers, not network operations staff, are the party able to issue or
resend resident invoices [1].

For account-level billing disputes at the ISP level (not resident
invoices), route the inquiry to the ISP's dedicated special billing
team rather than the resident invoice channel.

Notes

1. Resident billing for managed WiFi service is typically bundled into
   a property's own billing relationship with its residents, often as
   part of rent or a separate amenity fee, rather than billed directly
   by the network operations team. Network operations staff generally
   do not have visibility into or authority over that billing
   relationship, which is the basis for routing resident billing
   questions to the property manager rather than handling them
   directly. An ISP-level billing dispute is a separate relationship
   entirely, between the property and the ISP for the underlying
   circuit, and is routed to the ISP's dedicated billing team instead.

## Section 13: Shift handoff procedure

Any case marked Urgent or Critical that will not be resolved before the
end of a shift must be explicitly handed off to the next shift. When
logging a handoff:

- Add a comment to the case noting the current date.
- Summarize the current status and the next required action.

A handoff should occur at every shift boundary where an unresolved
urgent or critical case exists, so that no urgent case sits untouched
between shifts [1].

A useful handoff note answers three questions: what is currently known
about the issue, including which checklist steps from Sections 3
through 5 have already been completed; what has already been tried,
including any escalation opened under Section 9 or replacement logged
under Section 6; and exactly what the next action is and what it is
waiting on.

Notes

1. Published research on shift handovers in incident response and
   network operations settings identifies a consistent failure
   pattern in the absence of an explicit handoff: an incoming team
   either duplicates work already completed, or incorrectly assumes
   another team is already handling an open issue, so it goes
   untouched. Established handover practice in both cybersecurity
   incident response and network operations centers recommends
   linking the live case or incident record directly rather than
   retyping a summary, and confirming that the incoming shift
   understands the current state before the outgoing shift signs off.
   Source: Kent, L., Tuptuk, N., and Becker, I. Passing the Baton:
   Shift Handovers Within Cybersecurity Incident Response Teams, 2026.
