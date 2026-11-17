import re
from collections import Counter

SECTION_DEVICE = {1: "ont", 2: "ont", 3: "ap", 4: "switch", 5: "switch", 6: "switch", 7: "switch",
                  8: "clipboard", 9: "phone", 10: "phone", 11: "box", 12: "clipboard", 13: "clipboard"}

DEVICE_WORDS = {
    "ap": ["access", "point", "ap", "aps", "wifi", "wireless", "poe", "ssid"],
    "switch": ["switch", "switches", "idf", "mdf", "uplink", "vlan", "firmware", "switchport", "port"],
    "ont": ["ont", "gpon", "olt", "fiber", "fibre", "optical", "pon", "splitter"],
    "clipboard": ["ticket", "dispatch", "handoff", "invoice", "billing", "case", "shift"],
    "phone": ["escalate", "escalation", "isp", "call", "contact", "vendor", "circuit"],
    "box": ["replacement", "shipping", "hardware", "spare"],
}

PORT_LABELS = {
    "ap": {"poe": "PoE / LAN port on the AP and its switchport", "uplink": "Uplink port on the switch"},
    "switch": {"ports": "Switchports", "uplink": "Uplink port", "power": "Power adapter"},
    "ont": {"fiber": "Fiber (PON) connector", "lan": "Ethernet LAN ports", "power": "Power adapter", "reset": "Reset button"},
}

PORT_WORDS = {
    "ap": {"poe": ["poe", "switchport", "link", "cable", "patch"], "uplink": ["uplink"]},
    "switch": {"ports": ["port", "ports", "switchport", "link"], "uplink": ["uplink"], "power": ["power", "adapter", "unplug", "plug", "reboot"]},
    "ont": {"fiber": ["fiber", "fibre", "optical", "pon", "olt", "splitter"], "lan": ["ethernet", "lan"],
            "power": ["power", "plug", "unplug", "cycle"], "reset": ["reset", "factory"]},
}

FIGURE_TITLES = {"ap": "Access point and its switch", "switch": "Network switch", "ont": "Fiber ONT (GPON)",
                 "clipboard": "Ticket and case records", "phone": "Contacts and escalation", "box": "Hardware replacement"}


def kind_for_section(number):
    return SECTION_DEVICE.get(number, "clipboard")


def kind_for_text(text, default="clipboard"):
    words = Counter(re.findall(r"[a-z]+", text.lower()))
    scores = {kind: sum(words[w] for w in vocabulary) for kind, vocabulary in DEVICE_WORDS.items()}
    best = max(scores, key=scores.get)
    return best if scores[best] > 0 else default


def ports_mentioned(kind, text):
    words = set(re.findall(r"[a-z]+", text.lower()))
    found = []
    for port, vocabulary in PORT_WORDS.get(kind, {}).items():
        if words & set(vocabulary):
            found.append(port)
    return found


def port_labels(kind, ports):
    return [PORT_LABELS[kind][p] for p in ports if p in PORT_LABELS.get(kind, {})]


def wrap(width, height, inner, label, css="figure"):
    return (f'<svg class="{css}" viewBox="0 0 {width} {height}" role="img" aria-label="{label}" '
            f'xmlns="http://www.w3.org/2000/svg">{inner}</svg>')


def port_box(x, y, w, h, port_id, active, radius=3):
    css = "port hl" if port_id in active else "port"
    return f'<rect class="{css}" x="{x}" y="{y}" width="{w}" height="{h}" rx="{radius}"/>'


def switch_figure(active):
    parts = ['<rect class="body" x="8" y="26" width="364" height="98" rx="10"/>']
    for i in range(8):
        x = 28 + i * 32
        parts.append(f'<circle class="led on l{i % 3}" cx="{x + 12}" cy="44" r="2.6"/>')
        parts.append(port_box(x, 52, 24, 20, "ports", active))
    parts.append(port_box(304, 52, 28, 20, "uplink", active))
    parts.append(port_box(336, 52, 28, 20, "uplink", active))
    parts.append('<path class="bracket" d="M28 80 H276"/><path class="bracket" d="M304 80 H364"/>')
    parts.append('<text class="tag-light" x="152" y="100" text-anchor="middle">Switchports 1-8</text>')
    parts.append('<text class="tag-light" x="334" y="100" text-anchor="middle">Uplink</text>')
    parts.append(port_box(28, 104, 22, 12, "power", active, 6))
    parts.append('<text class="tag-light" x="58" y="114">Power</text>')
    return wrap(380, 140, "".join(parts), "Network switch with highlighted ports")


def ap_figure(active):
    parts = [
        '<rect class="mount" x="38" y="14" width="64" height="8" rx="3"/>',
        '<rect class="body" x="28" y="22" width="84" height="28" rx="14"/>',
        '<circle class="led on l0" cx="58" cy="36" r="3"/><circle class="led on l1" cx="70" cy="36" r="3"/><circle class="led on l2" cx="82" cy="36" r="3"/>',
        '<path class="wave w1" d="M48 62 q22 14 44 0"/><path class="wave w2" d="M38 72 q32 20 64 0"/><path class="wave w3" d="M28 82 q42 26 84 0"/>',
        port_box(112, 31, 12, 10, "poe", active, 2),
        '<path class="cable" d="M124 36 H190 V80 H226"/>',
        '<rect class="body" x="214" y="54" width="154" height="62" rx="9"/>',
    ]
    for i in range(4):
        parts.append(port_box(226 + i * 28, 68, 22, 18, "poe" if i == 0 else "ports", active))
    parts.append(port_box(334, 68, 26, 18, "uplink", active))
    parts.append('<text class="tag-light" x="237" y="106" text-anchor="middle">Switchport</text>')
    parts.append('<text class="tag-light" x="347" y="106" text-anchor="middle">Uplink</text>')
    parts.append('<text class="tag" x="70" y="118" text-anchor="middle">Access point</text>')
    return wrap(380, 140, "".join(parts), "Access point connected to a switch with highlighted ports")


def ont_figure(active):
    parts = [
        '<path class="fibercable" d="M16 68 H130"/>',
        '<text class="tag" x="16" y="58">Fiber from OLT</text>',
        '<rect class="body" x="124" y="30" width="150" height="86" rx="10"/>',
        '<circle class="led on l0" cx="144" cy="44" r="2.6"/><circle class="led on l1" cx="156" cy="44" r="2.6"/><circle class="led on l2" cx="168" cy="44" r="2.6"/>',
        port_box(136, 58, 18, 18, "fiber", active, 2),
    ]
    for i in range(4):
        parts.append(port_box(166 + i * 24, 62, 18, 14, "lan", active))
    parts.append(f'<circle class="{"port hl" if "power" in active else "port"}" cx="270" cy="68" r="6"/>')
    parts.append(f'<circle class="{"port hl" if "reset" in active else "port"}" cx="270" cy="92" r="4"/>')
    parts.append('<text class="tag-light" x="145" y="100" text-anchor="middle">Fiber</text>')
    parts.append('<text class="tag-light" x="214" y="100" text-anchor="middle">LAN ports</text>')
    parts.append('<text class="tag-light" x="250" y="110" text-anchor="end">Power / Reset</text>')
    return wrap(380, 140, "".join(parts), "Fiber ONT with highlighted ports")


def clipboard_figure(active):
    parts = [
        '<rect class="body" x="130" y="12" width="120" height="116" rx="10"/>',
        '<rect class="mount" x="168" y="6" width="44" height="14" rx="5"/>',
        '<rect class="paper" x="144" y="30" width="92" height="88" rx="4"/>',
    ]
    for i in range(3):
        y = 44 + i * 26
        parts.append(f'<path class="check c{i}" d="M152 {y} l5 5 l9 -10"/>')
        parts.append(f'<rect class="line" x="174" y="{y - 6}" width="52" height="7" rx="3"/>')
    return wrap(380, 140, "".join(parts), "Ticket checklist")


def phone_figure(active):
    parts = [
        '<rect class="body" x="162" y="10" width="56" height="116" rx="10"/>',
        '<rect class="paper" x="168" y="22" width="44" height="82" rx="3"/>',
        '<circle class="led on l1" cx="190" cy="114" r="4"/>',
        '<path class="wave w1" d="M236 50 q14 14 0 28"/><path class="wave w2" d="M246 40 q24 24 0 48"/>',
        '<path class="wave w1" d="M144 50 q-14 14 0 28"/><path class="wave w2" d="M134 40 q-24 24 0 48"/>',
    ]
    return wrap(380, 140, "".join(parts), "Phone for contacts and escalation")


def box_figure(active):
    parts = [
        '<path class="body" d="M120 52 L190 24 L260 52 L260 104 L190 132 L120 104 Z"/>',
        '<path class="paper" d="M120 52 L190 80 L260 52 L190 24 Z"/>',
        '<path class="bracket" d="M190 80 V132"/>',
        '<rect class="label-tape" x="206" y="92" width="34" height="14" rx="2"/>',
        '<path class="cable arrow" d="M290 76 H330 M320 66 L332 76 L320 86"/>',
    ]
    return wrap(380, 140, "".join(parts), "Replacement hardware being shipped")


FIGURES = {"ap": ap_figure, "switch": switch_figure, "ont": ont_figure,
           "clipboard": clipboard_figure, "phone": phone_figure, "box": box_figure}


def guide_figure(kind, ports=()):
    return FIGURES.get(kind, clipboard_figure)(set(ports))


def loader(mode):
    captions = (["Matching your question", "Reading the sections", "Checking the sources"] if mode == "manual"
                else ["Understanding the question", "Drafting guidance", "Adding a safety reminder"])
    right = ('<g class="stack"><rect x="300" y="26" width="34" height="42" rx="4"/><rect x="306" y="20" width="34" height="42" rx="4"/>'
             '<path d="M313 34 h20 M313 42 h20 M313 50 h12"/></g>') if mode == "manual" else (
             '<g class="chip"><rect x="304" y="24" width="38" height="38" rx="7"/><text x="323" y="49" text-anchor="middle">AI</text>'
             '<path d="M312 24 v-7 M323 24 v-7 M334 24 v-7 M312 62 v7 M323 62 v7 M334 62 v7"/></g>')
    inner = (
        '<g class="mini-phone"><rect x="18" y="20" width="26" height="46" rx="5"/><circle cx="31" cy="60" r="2"/></g>'
        '<path class="flow" d="M52 44 H296"/>'
        '<circle class="packet p1" cx="56" cy="44" r="4"/><circle class="packet p2" cx="56" cy="44" r="4"/><circle class="packet p3" cx="56" cy="44" r="4"/>'
        + right
        + "".join(f'<text class="caption cap{i + 1}" x="180" y="86" text-anchor="middle">{c}</text>' for i, c in enumerate(captions))
    )
    return wrap(360, 96, inner, "Working on your question", "loader")


def tile_position(number, columns=5):
    return 410 + ((number - 1) % columns) * 30, 150 + ((number - 1) // columns) * 38


def hero_scene():
    tiles = []
    for number in range(1, 14):
        x, y = tile_position(number)
        tiles.append(f'<g class="tile"><rect x="{x}" y="{y}" width="24" height="30" rx="3"/>'
                     f'<text x="{x + 12}" y="{y + 19}" text-anchor="middle">{number}</text></g>')
    highlights = "".join(
        f'<rect class="tile-hl" x="{tile_position(n)[0] - 3}" y="{tile_position(n)[1] - 3}" width="30" height="36" rx="5"/>'
        for n in (3, 6))
    inner = f"""
<rect class="ground" x="0" y="296" width="760" height="4"/>
<g class="person technician">
  <rect class="leg" x="95" y="236" width="12" height="60"/><rect class="leg" x="113" y="236" width="12" height="60"/>
  <rect class="vest" x="88" y="160" width="44" height="80" rx="8"/>
  <rect class="stripe" x="88" y="192" width="44" height="8"/>
  <circle class="skin" cx="110" cy="140" r="17"/>
  <path class="hat" d="M92 137 a18 18 0 0 1 36 0 z"/><rect class="brim" x="88" y="135" width="44" height="5" rx="2"/>
  <path class="arm" d="M130 172 L156 152"/>
  <g class="phone-bob"><rect class="phone" x="154" y="118" width="26" height="46" rx="5"/><rect class="screen" x="158" y="124" width="18" height="30" rx="2"/></g>
</g>
<g class="bubble">
  <rect x="96" y="46" width="160" height="46" rx="12"/><path d="M130 92 l8 14 l8 -14 z"/>
  <g class="dots"><circle cx="152" cy="69" r="4"/><circle cx="168" cy="69" r="4"/><circle cx="184" cy="69" r="4"/></g>
  <text class="ask" x="176" y="73" text-anchor="middle">AP offline. What first?</text>
</g>
<path class="route route-out" d="M184 138 C230 138 250 190 300 190"/>
<g class="server">
  <rect class="srv-body" x="300" y="150" width="56" height="90" rx="6"/>
  <rect class="srv-slot" x="310" y="162" width="36" height="10" rx="2"/><rect class="srv-slot" x="310" y="180" width="36" height="10" rx="2"/><rect class="srv-slot" x="310" y="198" width="36" height="10" rx="2"/>
  <circle class="led on l0" cx="338" cy="167" r="2.6"/><circle class="led on l1" cx="338" cy="185" r="2.6"/><circle class="led on l2" cx="338" cy="203" r="2.6"/>
  <g class="magnifier"><circle cx="332" cy="132" r="11"/><path d="M340 140 L350 150"/></g>
</g>
{''.join(tiles)}{highlights}
<path class="route route-back" d="M482 146 C450 108 240 108 170 132"/>
<g class="answer-card">
  <rect class="card" x="290" y="14" width="232" height="68" rx="10"/>
  <rect class="amber" x="302" y="24" width="64" height="18" rx="2"/><text class="tagtext" x="334" y="37" text-anchor="middle">Section 3</text>
  <text class="cardtext" x="302" y="60">1. Check the switchport link</text><text class="cardtext" x="302" y="75">2. VLAN 100 untagged on the port</text>
</g>
<g class="ceiling"><rect x="590" y="30" width="150" height="6" rx="3"/>
  <rect class="ap-body" x="640" y="36" width="60" height="16" rx="8"/>
  <circle class="led-red" cx="670" cy="44" r="3.5"/><circle class="led-green" cx="670" cy="44" r="3.5"/>
  <g class="wifi"><path d="M650 66 q20 14 40 0"/><path d="M640 78 q30 20 60 0"/><path d="M630 90 q40 26 80 0"/></g></g>
<g class="person resident">
  <circle class="skin" cx="650" cy="196" r="13"/><path class="hair" d="M637 194 a13 13 0 0 1 26 0 z"/>
  <rect class="shirt" x="630" y="212" width="40" height="52" rx="10"/><rect class="leg" x="634" y="262" width="12" height="34"/><rect class="leg" x="654" y="262" width="12" height="34"/>
  <rect class="laptop" x="682" y="236" width="48" height="32" rx="3"/><rect class="laptop-base" x="676" y="268" width="60" height="5" rx="2"/>
  <g class="laptop-wifi"><path d="M698 250 q8 -7 16 0"/><path d="M702 255 q4 -4 8 0"/><circle cx="706" cy="259" r="1.5"/></g>
</g>
<text class="name" x="110" y="322" text-anchor="middle">Technician</text>
<text class="name" x="328" y="322" text-anchor="middle">Search</text>
<text class="name" x="482" y="322" text-anchor="middle">Manual, 13 sections</text>
<text class="name" x="670" y="322" text-anchor="middle">Access point and resident</text>"""
    return wrap(760, 336, inner, "A technician asks a question on a phone. The search finds sections of the manual and sends back a cited answer, and the access point comes back online.", "scene")


def step_icons():
    admin = """
<svg class="icon" viewBox="0 0 160 110" role="img" aria-label="Administrator hands a technician number badge to the technician" xmlns="http://www.w3.org/2000/svg">
<circle class="skin" cx="34" cy="30" r="12"/><rect class="shirt-dark" x="18" y="44" width="32" height="44" rx="9"/>
<circle class="skin" cx="126" cy="30" r="12"/><path class="hat" d="M114 28 a12 12 0 0 1 24 0 z"/><rect class="vest" x="110" y="44" width="32" height="44" rx="9"/>
<g class="badge"><rect x="48" y="56" width="42" height="26" rx="4"/><rect class="amber" x="48" y="56" width="42" height="7"/><text x="69" y="76" text-anchor="middle">TECH-…</text></g>
</svg>"""
    signup = """
<svg class="icon" viewBox="0 0 160 110" role="img" aria-label="Technician fills in the sign-up form on a laptop" xmlns="http://www.w3.org/2000/svg">
<circle class="skin" cx="30" cy="40" r="12"/><path class="hat" d="M18 38 a12 12 0 0 1 24 0 z"/><rect class="vest" x="14" y="54" width="32" height="40" rx="9"/>
<rect class="laptop" x="58" y="22" width="86" height="58" rx="5"/><rect class="laptop-base" x="50" y="80" width="102" height="6" rx="3"/>
<rect class="fill f1" x="70" y="34" width="60" height="8" rx="3"/><rect class="fill f2" x="70" y="48" width="60" height="8" rx="3"/><rect class="fill f3" x="70" y="62" width="60" height="8" rx="3"/>
</svg>"""
    email = """
<svg class="icon" viewBox="0 0 160 110" role="img" aria-label="An email with a six digit code arrives on the technician's phone" xmlns="http://www.w3.org/2000/svg">
<rect class="phone" x="92" y="12" width="46" height="86" rx="9"/><rect class="screen" x="98" y="24" width="34" height="58" rx="3"/>
<text class="code" x="115" y="58" text-anchor="middle">482 913</text>
<g class="envelope"><rect x="12" y="42" width="48" height="32" rx="4"/><path d="M12 46 L36 62 L60 46"/></g>
</svg>"""
    unlock = """
<svg class="icon" viewBox="0 0 160 110" role="img" aria-label="A padlock opens and the manual becomes available" xmlns="http://www.w3.org/2000/svg">
<g class="pages"><rect x="96" y="18" width="40" height="56" rx="4"/><rect x="106" y="12" width="40" height="56" rx="4"/><path d="M114 26 h24 M114 36 h24 M114 46 h14"/></g>
<g class="lock"><path class="shackle" d="M36 52 v-14 a16 16 0 0 1 32 0 v14"/><rect class="lock-body" x="28" y="52" width="48" height="38" rx="7"/><circle cx="52" cy="68" r="5"/></g>
</svg>"""
    return [admin, signup, email, unlock]
