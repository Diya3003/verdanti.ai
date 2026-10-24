"""Visual descriptions of every starter-palette plant, for the image model.

An image model doesn't know what "Rhamnus californica 'Eve Case'" looks like, but it
can draw "dense rounded 1.2 m shrub, glossy dark-green oval leaves, small red berries".
Each entry: (display name, mature height cm, mature width cm, look).
Heights are mature sizes in Bay Area gardens. Run this file to write data/plant_looks.json.
"""
import json

LOOKS = {
 "Achillea Millefolium (Ca Native Cultivars)": ("Common yarrow", 60, 60, "ferny soft grey-green feathery foliage in a low mat, flat-topped clusters of tiny white or pale-yellow flowers on upright stems, spring-summer"),
 "Salvia Spathacea": ("Hummingbird sage", 50, 90, "low spreading clumps of large wrinkled bright-green arrow-shaped leaves, tall stalks of magenta-rose whorled flowers in spring"),
 "Salvia Clevelandii & Hybrids": ("Cleveland sage", 110, 150, "rounded airy grey-green aromatic shrub, small wrinkled leaves, stacked whorls of vivid violet-blue flowers on upright stems, late spring"),
 "Salvia Leucophylla": ("Purple sage", 120, 180, "large mounding shrub with silvery-white woolly leaves, soft pink-lavender flower whorls in spring"),
 "Salvia 'Allen Chickering'": ("Allen Chickering sage", 120, 150, "upright rounded grey-green shrub, long spikes of lavender-blue flower whorls, spring"),
 "Iris Douglasiana": ("Pacific Coast iris", 40, 60, "fans of narrow arching dark-green sword leaves, purple-blue iris flowers with white and yellow throats, spring"),
 "Carex Pansa": ("Dune sedge", 15, 40, "very low dense mat of fine grass-like dark-green blades, lawn-like groundcover"),
 "Carex Tumulicola": ("Foothill sedge", 40, 50, "neat fountain-shaped tuft of fine arching dark-green grassy blades"),
 "Arctostaphylos Manzanita": ("Manzanita", 250, 250, "large shrub with smooth twisting mahogany-red bark, oval grey-green leaves, tiny white urn-shaped flowers in winter"),
 "Ceanothus Griseus 'Ray Hartman'": ("Ray Hartman ceanothus", 300, 300, "large dense evergreen shrub, glossy dark-green leaves, covered in fluffy medium-blue flower clusters in spring"),
 "Ceanothus 'Blue Ray'": ("Blue Ray ceanothus", 180, 210, "dense rounded evergreen shrub, small glossy dark leaves, smothered in deep cobalt-blue flower puffs in spring"),
 "Epilobium Canum 'Everett's Choice'": ("California fuchsia", 30, 90, "low sprawling grey-green mound, masses of tubular scarlet-orange flowers, late summer-fall"),
 "Eriogonum Fasciculatum 'Theodore Payne'": ("California buckwheat", 40, 120, "low spreading mound of needle-like dark-green leaves, creamy-white flower pompoms aging to rust"),
 "Eriogonum Grande Rubescens": ("Rosy buckwheat", 30, 45, "small mound of grey-green leaves, round clusters of rosy-pink flowers on short stems, summer"),
 "Eriogonum Umbellatum 'Excellent Yellow'": ("Sulfur buckwheat", 30, 45, "low tidy mat of green leaves, umbrella-shaped balls of bright sulfur-yellow flowers, summer"),
 "Penstemon Heterophyllus 'Margarita Bop'": ("Foothill penstemon", 45, 60, "small bushy mound of narrow green leaves, spikes of tubular blue-violet and pink flowers, spring"),
 "Mimulus Aurantiacus": ("Sticky monkeyflower", 90, 90, "small upright shrub, narrow glossy dark-green leaves, trumpet-shaped apricot-orange flowers, spring-summer"),
 "Muhlenbergia Rigens": ("Deergrass", 120, 120, "large fountain-shaped clump of fine green-grey grass, tall straight silvery flower spikes"),
 "Festuca Californica": ("California fescue", 60, 60, "loose fountain tuft of blue-green grass blades, airy tan seed heads"),
 "Juncus Patens": ("California gray rush", 60, 60, "upright clump of stiff round blue-grey stems like fine pencils"),
 "Ribes Sanguineum": ("Flowering currant", 200, 180, "upright deciduous shrub, maple-like green leaves, hanging clusters of pink flowers in late winter"),
 "Ribes Viburnifolium": ("Evergreen currant", 90, 180, "low spreading shrub with arching red stems, rounded glossy green leaves, small maroon flowers"),
 "Ribes Malvaceum": ("Chaparral currant", 150, 150, "open shrub, soft fuzzy grey-green lobed leaves, drooping clusters of pink flowers in winter"),
 "Heteromeles Arbutifolia": ("Toyon", 300, 300, "large evergreen shrub, leathery serrated dark-green leaves, white flower clusters then bright red berries in winter"),
 "Rhamnus Californica 'Eve Case'": ("Coffeeberry 'Eve Case'", 150, 150, "dense rounded evergreen shrub, broad glossy dark-green oval leaves, berries ripening red to black"),
 "Rhamnus Californica 'Mound San Bruno'": ("Coffeeberry 'Mound San Bruno'", 120, 180, "compact mounding evergreen shrub, narrow glossy dark-green leaves, dark berries"),
 "Sisyrinchium Bellum": ("Blue-eyed grass", 30, 30, "small fans of flat grassy green leaves, little star-shaped violet-blue flowers with yellow centers, spring"),
 "Dudleya Spp.": ("Dudleya", 20, 30, "chalky silver-white succulent rosettes"),
 "Eschscholzia Californica": ("California poppy", 30, 30, "lacy blue-green foliage, cup-shaped bright orange poppies"),
 "Erigeron Glaucus": ("Seaside daisy", 25, 50, "low mounds of rounded grey-green leaves, lavender-pink daisies with yellow centers"),
 "Asclepias Fascicularis": ("Narrowleaf milkweed", 90, 60, "upright thin stems with whorls of narrow leaves, rounded clusters of small pale-pink-white flowers, monarch host plant"),
 "Romneya Coulteri": ("Matilija poppy", 200, 250, "tall blue-grey stems, huge white crinkled poppy flowers with yellow centers, summer"),
 "Elymus Condenstatus (Leymus Condenstatus)": ("Giant wild rye", 180, 120, "tall bold clump of wide blue-green grass blades, upright wheat-like seed spikes"),
 "Nassella Pulchra": ("Purple needlegrass", 60, 45, "fine green bunchgrass, airy purplish feathery seed heads in spring"),
 "Clinopodium Douglasii": ("Yerba buena", 10, 90, "very low trailing groundcover, small round bright-green aromatic leaves"),
 "Aquilegia Spp.": ("Western columbine", 60, 40, "delicate lacy blue-green foliage, nodding red-and-yellow spurred flowers, spring"),
 "Philadelphus Microphyllus": ("Littleleaf mock orange", 120, 120, "fine-textured rounded shrub, tiny leaves, covered in small fragrant white four-petal flowers, spring"),
 "Cercis Occidentalis": ("Western redbud", 300, 300, "multi-trunk shrub, round heart-shaped blue-green leaves, bare branches covered in magenta-pink blossoms in early spring"),
 "Verbena Lilacina": ("Lilac verbena", 90, 120, "airy rounded mound of finely cut green leaves, constant clusters of small lilac-purple flowers"),
 "Lavandula Spp.": ("Lavender", 60, 75, "compact rounded mound of silver-grey needle-like foliage, many upright spikes of deep purple flowers"),
 "Rosmarinus 'Prostratus'": ("Trailing rosemary", 30, 150, "low cascading mat of dark-green needle leaves, small pale-blue flowers, spills over edges"),
 "Westringia Fruticosa": ("Coast rosemary", 150, 150, "dense rounded shrub of soft grey-green needle-like leaves, small white flowers, neat clipped look"),
 "Nepeta Spp.": ("Catmint", 45, 75, "soft billowing mound of small grey-green leaves, haze of lavender-blue flower spikes"),
 "Lomandra Longifolia": ("Lomandra", 80, 90, "fountain clump of long glossy strappy bright-green blades"),
 "Dietes Iridioides": ("Fortnight lily", 80, 60, "upright fan clump of stiff narrow sword leaves, white iris-like flowers with yellow and violet marks"),
 "Dietes Bicolor": ("Yellow fortnight lily", 90, 60, "upright clump of stiff narrow sword leaves, pale-yellow flowers with dark brown spots"),
 "Agapanthus Inapertus Major": ("Lily of the Nile", 90, 60, "clump of arching strap-shaped green leaves, tall stems topped with globes of blue flowers, summer"),
 "Sarcococca Ruscifolia": ("Sweet box", 90, 90, "neat dense low shrub, small glossy dark-green pointed leaves, tiny fragrant white flowers in winter"),
 "Sarcococca Confusa": ("Sweet box", 120, 120, "neat dense shrub, small glossy dark-green pointed leaves, tiny fragrant white flowers in winter"),
 "Dymondia Margaretae": ("Dymondia", 5, 45, "flat, tight silvery-green groundcover mat, like a low living carpet"),
 "Leucadendron 'safari Sunset'": ("Safari Sunset conebush", 200, 150, "upright shrub, leafy stems tipped with wine-red to crimson bracts"),
 "Phormium Tenax": ("New Zealand flax", 180, 150, "bold fan of tall stiff sword-shaped bronze-green leaves"),
 "Kniphofia 'Elvira'": ("Red-hot poker", 90, 60, "grassy clump with upright torch-shaped spikes of orange-red flowers"),
 "Anigozanthos 'Harmony'": ("Kangaroo paw", 90, 60, "clump of strappy green leaves, tall stems of fuzzy yellow-and-red tubular flowers"),
 "Bulbine Frutescens": ("Bulbine", 30, 60, "clumps of fleshy bright-green tubular leaves, slender stalks of small orange-yellow star flowers"),
 "Senecio Mandraliscae": ("Blue chalksticks", 30, 60, "low groundcover of finger-like powder-blue succulent leaves"),
 "Grevillea 'Ruby Clusters'": ("Grevillea", 150, 180, "dense mounding shrub, narrow dark-green leaves, curly ruby-red spider-like flowers"),
 "Polygala X Dalmaisiana": ("Sweet pea shrub", 120, 120, "rounded shrub, small grey-green leaves, constant pea-like magenta-purple flowers"),
 "Teucrium Fruticans": ("Bush germander", 150, 150, "silvery-white airy shrub, small grey leaves, pale lavender-blue flowers"),
 "Helleborus Argutifolius": ("Corsican hellebore", 60, 75, "bold clump of spiny blue-green leaves, clusters of pale chartreuse-green cup flowers in winter"),
 "Aspidistra Elatior": ("Cast iron plant", 60, 60, "clump of large upright paddle-shaped glossy dark-green leaves, deep-shade plant"),
 "Rhaphiolepis Indica": ("Indian hawthorn", 120, 120, "tidy rounded shrub, leathery dark-green leaves, clusters of pale pink flowers in spring"),
 "Loropetalum Chinense": ("Fringe flower", 150, 150, "layered shrub, burgundy-purple foliage, fringy hot-pink ribbon flowers"),
 "Pittosporum Tobira 'Wheeler's Dwarf'": ("Dwarf mock orange", 60, 90, "neat low dome of glossy bright-green whorled leaves"),
 "Coprosma X Kirkii": ("Creeping coprosma", 45, 150, "low spreading mat of small glossy green leaves"),
 "Lantana Montevidensis": ("Trailing lantana", 30, 120, "low spreading mat covered in small round clusters of lavender-purple flowers"),
 "Leonotis Leonurus": ("Lion's tail", 180, 120, "tall upright stems with stacked whorls of fuzzy bright orange tubular flowers"),
 "Perovskia Atriplicifolia": ("Russian sage", 120, 90, "airy upright silver-white stems, long hazy spikes of tiny lavender-blue flowers"),
 "Dodonaea Viscosa 'Purpurea'": ("Purple hopseed bush", 300, 200, "tall upright dense shrub with glossy bronze-purple willow-like leaves"),
 "Acacia Cognata 'Cousin Itt'": ("Cousin Itt acacia", 60, 120, "low soft mound of fine weeping thread-like bright-green foliage"),
 "Salvia Greggii & Hybrids": ("Autumn sage", 75, 75, "small bushy shrub, tiny green leaves, many small bright red, pink or coral flowers"),
 "Salvia Leucantha": ("Mexican bush sage", 120, 150, "arching grey-green stems, long velvety purple-and-white flower spikes, fall"),
 "Salvia Microphylla": ("Cherry sage", 90, 90, "rounded twiggy shrub, small green leaves, many small cherry-red flowers"),
 "Osteospermum Spp.": ("African daisy", 30, 60, "low mound covered in white, purple or pink daisies with dark blue centers"),
 "Thymus Spp.": ("Creeping thyme", 8, 45, "flat carpet of tiny green leaves, haze of small pink-lavender flowers, between stones"),
}

if __name__ == "__main__":
    out = {k: {"name": v[0], "height_cm": v[1], "width_cm": v[2], "look": v[3]} for k, v in LOOKS.items()}
    pal = json.load(open("data/default_palette.json"))["palette"]
    missing = [p["botanical"] for p in pal if p["botanical"] not in out]
    assert not missing, missing
    json.dump(out, open("data/plant_looks.json", "w"), indent=1)
    print(len(out), "plant looks written")
