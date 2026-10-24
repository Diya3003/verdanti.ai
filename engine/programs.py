"""Rebates and free programs for Santa Clara County lawn conversions.

Vetted October 2026: every entry is taken from the CURRENT page of the agency that runs it
(Valley Water, the city, the water utility, or the nonprofit running the program).
Rejected: Cupertino enhanced rate + Climate Garden (cupertino.gov: $2/sq ft, program "no longer
available"); Gilroy / Morgan Hill / San José Muni enhanced caps and Santa Clara residential cap
(not on the agencies' own current pages); Sunnyvale/BAWSCA rain barrels (ended June 30, 2026).
Amounts change, every program links to its official page, and the app tells users to confirm there.
who: "home", "hoa" or both.  kind: "rebate" or "free".
"""

VW_LANDSCAPE = "https://www.valleywater.org/saving-water/rebates-surveys/landscape-rebates"
VW_FLYER = "https://assets.valleywater.org/files/2025-09-05_Water%20Conservation%20Flyer_English_RO_v.6%20019816.pdf"

PROGRAMS = [
    {"id": "vw_conversion", "org": "Valley Water", "logo": "valley-water", "mark": "VW", "kind": "rebate", "who": ["home", "hoa"],
     "name": "Landscape Conversion Rebate", "amount": "$2+ / sq ft",
     "summary": "Pays you to replace lawn with low-water plants. This is the rebate the app designs for.",
     "details": ["At least $2 per sq ft of lawn converted (some areas pay more).",
                 "Caps: $3,000 for single-family homes; $100,000 for HOAs, multifamily (5+ units) and businesses.",
                 "At least 50% of the area must be covered by qualifying plants at maturity.",
                 "Apply and pass a pre-inspection before you remove any lawn. Work started early doesn't qualify.",
                 "After the Notice to Proceed you have 90 days to finish; the check comes 4–6 weeks after post-inspection.",
                 "Funded through June 30, 2027, or until funds run out."],
     "contact": "Water Conservation Hotline (408) 630-2554", "url": VW_LANDSCAPE},
    {"id": "pa_storm", "org": "City of Palo Alto Utilities", "logo": "palo-alto", "mark": "PA", "kind": "rebate", "who": ["home", "hoa"],
     "cities": ["Palo Alto"], "name": "Stormwater Rebates", "amount": "Up to $600",
     "summary": "Palo Alto pays extra for rain gardens, rain barrels, cisterns and permeable paving.",
     "details": ["Rain garden: up to $600. Rain barrels (40–199 gal): $70 each. Cisterns (200+ gal): $1 per gallon.",
                 "Permeable paving: $1.50 per sq ft.",
                 "Laundry-to-landscape graywater: $400."],
     "contact": "City of Palo Alto Utilities",
     "url": "https://www.paloalto.gov/files/assets/public/v/1/utilities/bill-inserts/cpa-2025_oct_waterrebates_ubi-residential-final.pdf"},
    {"id": "vw_irrigation", "org": "Valley Water", "logo": "valley-water", "mark": "VW", "kind": "rebate", "who": ["home", "hoa"],
     "name": "Irrigation Upgrade Rebate", "amount": "Up to $2,000",
     "summary": "Rebates for switching sprinklers to drip and adding smart controllers.",
     "details": ["Sprinkler to in-line drip conversion: $0.25 per sq ft.",
                 "Smart irrigation controllers: $300–$2,000 each. Rain sensors: up to $50.",
                 "High-efficiency nozzles: up to $5 each; pressure-regulating spray bodies: up to $20 each.",
                 "Counts toward the same site cap as the landscape conversion rebate."],
     "contact": "(408) 630-2554", "url": VW_FLYER},
    {"id": "vw_rain", "org": "Valley Water", "logo": "valley-water", "mark": "VW", "kind": "rebate", "who": ["home", "hoa"],
     "name": "Rainwater Capture Rebate", "amount": "Up to $300",
     "summary": "Catch roof runoff with rain barrels, cisterns or a rain garden.",
     "details": ["Rain barrels (under 200 gal): up to $35 each.",
                 "Cisterns (200+ gal): $0.50 per gallon.",
                 "Rain gardens: $1 per sq ft of roof area diverted, up to $300.",
                 "Must connect to existing downspouts."],
     "contact": "(408) 630-2554", "url": VW_FLYER},
    {"id": "vw_graywater", "org": "Valley Water", "logo": "valley-water", "mark": "VW", "kind": "rebate", "who": ["home"],
     "name": "Laundry-to-Landscape Graywater", "amount": "$200+",
     "summary": "Reuse washing-machine water to irrigate your new garden.",
     "details": ["At least $200 per home ($400 in Palo Alto).",
                 "No pre-inspection, but wait for approval before starting."],
     "contact": "(408) 630-2554", "url": VW_FLYER},
    {"id": "vw_mulch", "org": "Valley Water", "logo": "valley-water", "mark": "VW", "kind": "rebate", "who": ["hoa"],
     "name": "Lawn to Mulch Rebate", "amount": "$1+ / sq ft",
     "summary": "For HOAs and businesses converting low-priority lawn to mulch only.",
     "details": ["At least $1 per sq ft to replace lawn with 3+ inches of mulch.",
                 "HOAs, multifamily (5+ units), commercial and institutional sites only.",
                 "Trees in converted areas need low-flow irrigation."],
     "contact": "(408) 630-2554", "url": VW_LANDSCAPE},
    {"id": "vw_design", "org": "Valley Water", "logo": "valley-water", "mark": "VW", "kind": "free", "who": ["home"],
     "name": "Landscape Design Assistance", "amount": "Free",
     "summary": "Time with a professional landscape designer for your front-yard conversion.",
     "details": ["Up to two hours with a landscape designer for a front-yard lawn conversion.",
                 "Available to current Landscape Rebate applicants.",
                 "Bring your design from this app as a starting point."],
     "contact": "(408) 630-2554", "url": VW_LANDSCAPE},
    {"id": "vw_survey", "org": "Valley Water", "logo": "valley-water", "mark": "VW", "kind": "free", "who": ["home", "hoa"],
     "name": "Water-Wise Outdoor Survey", "amount": "Free",
     "summary": "An irrigation professional checks your system for leaks and waste.",
     "details": ["For homes and sites up to half an acre; includes a customized report and watering schedule.",
                 "HOAs with large landscapes can get free irrigation budgets through the Large Landscape Program."],
     "contact": "(408) 630-2000", "url": VW_FLYER},
    {"id": "mv_trees", "org": "City of Mountain View", "logo": "mountain-view", "mark": "MV", "kind": "free", "who": ["home", "hoa"],
     "cities": ["Mountain View"], "name": "Arbor Day Tree Giveaway", "amount": "Free tree",
     "summary": "A free 15-gallon tree, delivered to your home, to plant anywhere in your yard.",
     "details": ["Choose from pre-approved trees; a 15-gallon tree is delivered in late September or early October.",
                 "Register on the city's program page (registration window varies; confirm with Forestry).",
                 "Separate Street Tree Program: the city plants and maintains trees in your parking strip."],
     "contact": "Forestry Division (650) 903-6273",
     "url": "https://www.mountainview.gov/our-city/departments/public-works/water-and-sewer-services/water-conservation/landscape/free-trees"},
    {"id": "canopy", "org": "Canopy", "logo": "canopy", "mark": "CA", "kind": "free", "who": ["home"],
     "cities": ["Palo Alto", "Mountain View"], "name": "Free Trees", "amount": "Free tree",
     "summary": "Free trees and planting for Palo Alto, East Palo Alto and nearby neighborhoods.",
     "details": ["South Palo Alto: free arborist consultation, a free tree, volunteer installation and 3 years of check-ups.",
                 "North Palo Alto and Mountain View: free street trees.",
                 "East Palo Alto, Belle Haven and North Fair Oaks: free trees through Branching Out.",
                 "Plantings fill up, so join the waitlist if your neighborhood is full."],
     "contact": "Canopy", "url": "https://canopy.org/get-involved/tree-signup/"},
    {"id": "ocf_lawnbusters", "org": "Our City Forest", "logo": "our-city-forest", "mark": "OCF", "kind": "free", "who": ["home"],
     "name": "Lawnbusters", "amount": "Free garden",
     "summary": "Free lawn-to-garden replacement for eligible seniors, veterans, low-income residents and people with disabilities.",
     "details": ["Our City Forest replaces lawn with a water-wise garden at no cost for eligible households.",
                 "Note: Lawnbusters projects can't also claim the Valley Water landscape conversion rebate.",
                 "Availability depends on your city and current funding. Check with Our City Forest.",
                 "Our City Forest also runs free tree plantings in San José and, with VTA, in Sunnyvale and East San José."],
     "contact": "Our City Forest", "url": "https://ourcityforest.org/lawnbusters"},
    {"id": "ocf_trees", "org": "Our City Forest", "logo": "our-city-forest", "mark": "OCF", "kind": "free", "who": ["home"],
     "cities": ["San Jose", "Sunnyvale"], "name": "Free Trees", "amount": "Free tree",
     "summary": "Free 15-gallon trees, planted or delivered, for homes in funded neighborhoods.",
     "details": ["Check your address on Our City Forest's Free Tree Eligibility Map (grant zones in San José and Sunnyvale).",
                 "Sunnyvale (VTA-supported): free 15-gallon yard tree, planted or delivered by the Our City Forest team.",
                 "Pick a tree at the Community Nursery, 1000 Spring St, San José (Thu–Fri 9–12, Sat 9–2).",
                 "Outside grant zones: a 15-gallon tree for a $150–$200 donation."],
     "contact": "trees@ourcityforest.org · (408) 785-2302", "url": "https://www.ourcityforest.org/free-trees"},
    {"id": "ocf_campbell", "org": "Our City Forest", "logo": "our-city-forest", "mark": "OCF", "kind": "free",
     "who": ["home"], "cities": ["Campbell"], "name": "Free Trees for Campbell", "amount": "Up to 2 free trees",
     "summary": "Campbell residents can get up to two free trees planted in their park strip or front yard.",
     "details": ["Up to 2 free trees in your park strip, or within the first 10 feet of your yard if there's no strip.",
                 "If an old stump has to be removed first, the City of Campbell covers the cost.",
                 "Apply with Our City Forest's Tree Stewardship Application, noting you're a Campbell resident."],
     "contact": "trees@ourcityforest.org · (408) 998-7337 x124", "url": "https://ourcityforest.org/campbell"},
    {"id": "ocf_saratoga", "org": "Our City Forest", "logo": "our-city-forest", "mark": "OCF", "kind": "free",
     "who": ["home"], "cities": ["Saratoga"], "name": "Saratoga Tree Program", "amount": "Discounted trees",
     "summary": "Saratoga property owners can get discounted front-yard trees through Our City Forest.",
     "details": ["Discount on a 15-gallon tree and up to two 5-gallon trees (started October 2024).",
                 "Trees go in the front yard and must be from the approved species list.",
                 "Requires a stewardship agreement and application; confirm current availability."],
     "contact": "Our City Forest", "url": "https://ourcityforest.org/saratoga"},
    {"id": "calwater", "org": "Cal Water", "logo": "cal-water", "mark": "CW", "kind": "rebate", "who": ["home", "hoa"],
     "cities": ["Los Altos", "Mountain View", "Sunnyvale", "Cupertino"], "name": "Cal Water Lawn-to-Garden Rebate",
     "amount": "Per sq ft",
     "summary": "If Cal Water is your water company (not the city), it offers its own lawn-replacement rebate.",
     "details": ["Only for Cal Water customers. Check your water bill.",
                 "Pays a per-square-foot rebate; the current amount is shown in Cal Water's Conservation Portal.",
                 "Requires pre-approval, at least three approved low-water plants per 100 sq ft, and no artificial turf.",
                 "Ask Cal Water and Valley Water whether both rebates can be used on the same project."],
     "contact": "Cal Water Conservation Portal", "url": "https://www.calwater.com/conservation-rebates/"},
]

# City cost-sharing that raises the Valley Water landscape conversion rebate (verified on current pages).
# Valley Water: cost-sharing areas cap single-family/≤4-unit sites at $6,000 (default $3,000).
CITY_BOOST = {
    ("Palo Alto", "home"): {"amount": "Up to $4 / sq ft", "cap": 6000,
        "note": "Palo Alto residents get up to $4 per sq ft (City of Palo Alto Utilities). Cost-sharing areas "
                "can receive up to $6,000 per site (Valley Water)."},
    ("Milpitas", "home"): {"amount": "$4 / sq ft", "cap": 6000,
        "note": "Milpitas residents get $4 per sq ft for the first 1,000 sq ft, then $2, up to $6,000. Also: rain "
                "barrels up to $70, cisterns $1/gal, rain gardens $2/sq ft up to $600, laundry-to-landscape up to $400."},
    ("Santa Clara", "hoa"): {"amount": "$3 / sq ft", "cap": 110000,
        "note": "City of Santa Clara HOAs, multifamily (5+ units) and businesses get $3 per sq ft for the first "
                "10,000 sq ft, then $2, up to $110,000 per site. Lawn to mulch: $2/sq ft for the first 10,000 sq ft."},
}
BOOST_SOURCES = {
    "Palo Alto": "https://www.paloalto.gov/files/assets/public/v/1/utilities/bill-inserts/cpa-2025_oct_waterrebates_ubi-residential-final.pdf",
    "Milpitas": "https://milpitas.gov/1089/Water-Conservation-Rebates",
    "Santa Clara": "https://www.santaclaraca.gov/our-city/departments-g-z/water-sewer-utilities/rebates-surveys",
}


def for_user(who: str, city: str | None = None) -> list:
    """Programs for 'home' or 'hoa', city-specific ones only when the city matches.
    In a cost-sharing city, the main rebate shows that city's verified rate and cap."""
    out = []
    for p in PROGRAMS:
        if who not in p["who"] or (p.get("cities") and city not in p["cities"]):
            continue
        if p["id"] == "vw_conversion" and (city, who) in CITY_BOOST:
            b = CITY_BOOST[(city, who)]
            p = {**p, "amount": b["amount"], "org": f"Valley Water + {city}", "url": BOOST_SOURCES[city],
                 "details": [b["note"]] + p["details"]}
        out.append(p)
    return out


def rebate_cap(city: str, who: str) -> int:
    """Landscape rebate cap for this city and property type."""
    default = 3000 if who == "home" else 100000
    return CITY_BOOST.get((city, who), {}).get("cap", default)


def boost(city: str, who: str):
    return CITY_BOOST.get((city, who))
