"""Build data/default_palette.json: a curated starter palette of Santa Clara Valley
Water rebate-qualifying plants, each tagged with the sun exposures it tolerates.

Every plant below is matched by its exact scientific name in the Valley Water list,
so coverage values come straight from Valley Water. Sun tags are general horticultural
guidance (Calscape / Sunset Western Garden style) for Bay Area valley-floor gardens.
Invasive-flagged plants are excluded. Edit SUN_TAGS to grow the palette.
"""
import json
FS, PS, SH = "Full Sun", "Partial Sun", "Full Shade"
SUN_TAGS = {
  # ── CA natives ────────────────────────────────────────────────
  "Achillea Millefolium (Ca Native Cultivars)": [FS, PS],
  "Salvia Spathacea": [PS, SH],
  "Salvia Clevelandii & Hybrids": [FS],
  "Salvia Leucophylla": [FS],
  "Salvia 'Allen Chickering'": [FS],
  "Iris Douglasiana": [PS, SH],
  "Carex Pansa": [FS, PS, SH],
  "Carex Tumulicola": [FS, PS, SH],
  "Arctostaphylos Manzanita": [FS, PS],
  "Ceanothus Griseus 'Ray Hartman'": [FS],
  "Ceanothus 'Blue Ray'": [FS],
  "Epilobium Canum 'Everett's Choice'": [FS],
  "Eriogonum Fasciculatum 'Theodore Payne'": [FS],
  "Eriogonum Grande Rubescens": [FS],
  "Eriogonum Umbellatum 'Excellent Yellow'": [FS],
  "Penstemon Heterophyllus 'Margarita Bop'": [FS, PS],
  "Mimulus Aurantiacus": [FS, PS],
  "Muhlenbergia Rigens": [FS, PS],
  "Festuca Californica": [FS, PS, SH],
  "Juncus Patens": [FS, PS],
  "Ribes Sanguineum": [PS, SH],
  "Ribes Viburnifolium": [PS, SH],
  "Ribes Malvaceum": [FS, PS],
  "Heteromeles Arbutifolia": [FS, PS],
  "Rhamnus Californica 'Eve Case'": [FS, PS, SH],
  "Rhamnus Californica 'Mound San Bruno'": [FS, PS],
  "Sisyrinchium Bellum": [FS, PS],
  "Dudleya Spp.": [FS, PS],
  "Eschscholzia Californica": [FS],
  "Erigeron Glaucus": [FS, PS],
  "Asclepias Fascicularis": [FS],
  "Romneya Coulteri": [FS],
  "Elymus Condenstatus (Leymus Condenstatus)": [FS, PS],
  "Nassella Pulchra": [FS],
  "Clinopodium Douglasii": [PS, SH],
  "Aquilegia Spp.": [PS, SH],
  "Philadelphus Microphyllus": [FS, PS],
  "Cercis Occidentalis": [FS, PS],
  "Verbena Lilacina": [FS],
  # ── Mediterranean / climate-adapted ──────────────────────────
  "Lavandula Spp.": [FS],
  "Rosmarinus 'Prostratus'": [FS],
  "Westringia Fruticosa": [FS, PS],
  "Nepeta Spp.": [FS, PS],
  "Lomandra Longifolia": [FS, PS, SH],
  "Dietes Iridioides": [FS, PS, SH],
  "Dietes Bicolor": [FS, PS],
  "Agapanthus Inapertus Major": [FS, PS, SH],
  "Sarcococca Ruscifolia": [PS, SH],
  "Sarcococca Confusa": [PS, SH],
  "Dymondia Margaretae": [FS, PS],
  "Leucadendron 'safari Sunset'": [FS],
  "Phormium Tenax": [FS, PS],
  "Kniphofia 'Elvira'": [FS],
  "Anigozanthos 'Harmony'": [FS],
  "Bulbine Frutescens": [FS],
  "Senecio Mandraliscae": [FS],
  "Grevillea 'Ruby Clusters'": [FS],
  "Polygala X Dalmaisiana": [FS, PS],
  "Teucrium Fruticans": [FS],
  "Helleborus Argutifolius": [PS, SH],
  "Aspidistra Elatior": [SH, PS],
  "Rhaphiolepis Indica": [FS, PS],
  "Loropetalum Chinense": [FS, PS],
  "Pittosporum Tobira 'Wheeler's Dwarf'": [FS, PS, SH],
  "Coprosma X Kirkii": [FS, PS],
  "Lantana Montevidensis": [FS],
  "Leonotis Leonurus": [FS],
  "Perovskia Atriplicifolia": [FS],
  "Dodonaea Viscosa 'Purpurea'": [FS, PS],
  "Acacia Cognata 'Cousin Itt'": [FS, PS],
  "Salvia Greggii & Hybrids": [FS, PS],
  "Salvia Leucantha": [FS, PS],
  "Salvia Microphylla": [FS, PS],
  "Osteospermum Spp.": [FS],
  "Thymus Spp.": [FS],
}
# Moderate-water plants (WUCOLS "M"); everything else treated as low water.
MODERATE = {"Salvia Spathacea", "Iris Douglasiana", "Ribes Sanguineum", "Clinopodium Douglasii",
            "Aquilegia Spp.", "Sarcococca Ruscifolia", "Sarcococca Confusa", "Aspidistra Elatior",
            "Helleborus Argutifolius", "Loropetalum Chinense", "Juncus Patens"}

vw = {p["scientific"]: p for p in json.load(open("data/valley_water.json"))["valley_water"]}
out, missing = [], []
for name, sun in SUN_TAGS.items():
    p = vw.get(name)
    if not p or p["invasive"]:
        missing.append(name); continue
    out.append({"botanical": name, "common": p["common"], "sun": sun, "types": p["types"],
                "coverage_sqft": p["coverage_sqft"], "native_ca": p["native_ca"],
                "rebate_status": "exact", "water": "moderate" if name in MODERATE else "low"})
json.dump({"name": "Valley Water starter palette", "palette": out}, open("data/default_palette.json", "w"), indent=1)
for s in (FS, PS, SH):
    print(s, sum(s in p["sun"] for p in out))
print(len(out), "plants; missing/invasive:", missing)
