# Thailand country evidence for the fish roster

The accepted-name table contains **2,159 distinct GBIF species keys**. Of these, 1,497 have Thai GBIF occurrence evidence in the previous import. The national checklist contributes 1,448 accepted keys, including 786 shared with the occurrence import and 662 additional keys. Twenty of those 662 correspond to an existing hand-authored fish, leaving **642 additional playable entries**. The generator retains the previously assigned extended IDs and appends the new species. This import brought the game roster to 2,168 entries, including eight fictional creatures and a real freshwater prawn. A subsequent check of Thai museum specimens and research-grade observations adds 377 species and brings the playable total to **2,545**. [Field evidence and attribution](field-evidence.md)

## National source

Supap Monkolprasit, Suebsin Sontirat, Suri Vimollohakarn and Taweesak Songsirikul compiled *Checklist of Fishes in Thailand*, OEPP Biodiversity Series volume four. Thailand’s Office of Environmental Policy and Planning published it in May 1997, ISBN 974-89954-6-1. It compiles observations and earlier literature, with reporting localities and citations in the printed tables. The later web hosting date does not change the publication year. [1997 national checklist](https://chm-thai.onep.go.th/wp-content/uploads/2021/09/ONEP_V04.pdf)

The national import reads the primary scientific-name column on printed checklist pages and uses the species index to check spellings and page references. It expanded abbreviated genera within each group. It extracted 1,734 distinct primary names. GBIF matched 1,589 primary names exactly at species rank. After combining accepted synonyms, these represent 1,448 accepted keys. The other 145 primary names lack an exact match under the lookup rules. Spelling differences, historic names, incomplete entries and the limitations of PDF text extraction can affect these counts. The source gives differing totals of 1,741 and 1,742 historical species in its introduction. Neither source total is a present-day national census. [Scientific-name reconciliation](national-checklist-audit.csv) · [GBIF matching API](https://techdocs.gbif.org/en/openapi/v1/species)

The audit holds 1,907 candidate names from the index and table. It distinguishes accepted main rows from 110 matched index or alternate names that have no separately confirmed primary row. There are also 181 names without an exact GBIF species match, of which 145 are primary, and 27 names whose cited table entry could not be confirmed. GBIF supplies the modern key and accepted name. The country source supplies national evidence. Of the 662 newly included country keys, 582 also match either the historical or accepted binomial in the regional ASEAN checklist. A regional checklist match alone does not establish a Thai occurrence. [ASEAN fish checklist archive v7.13](https://ipt.aseanbiodiversity.org/archive.do?r=aseanfishspecieslist&v=7.13)

In the CSV, `evidence_sources` identifies the supporting datasets. `oepp_name` and `oepp_page` are a representative printed name and printed page for that accepted key. For example, *Acanthocepola abbreviata* is recorded on printed page 196. Historic national evidence does not establish current abundance or presence at the fishing destination selected by the game. The encounter destinations and times are game design assignments. The tables distribute scientific identifiers and original provenance annotations. [Accepted names and sources](thai-accepted.csv) · [Thai occurrence evidence](thai-occurrence.csv)

## Reproduce

From the repository root, supply the national PDF, ASEAN Darwin Core Archive and a local GBIF cache. The script checks the PDF SHA-256. It preserves GBIF Thai occurrence rows in the supplied base and rebuilds the union. The network refresh uses up to six workers, reuses cached exact-match results and honors rate-limit responses. The GBIF backbone can change. This snapshot was reconciled on 19 November 2026, Bangkok time.

~~~sh
python -m pip install pypdf requests
python game/content/import_national_checklist.py --pdf ONEP_V04.pdf --archive asean.zip --cache gbif-accepted --base game/content/thai-accepted.csv --output thai-accepted.rebuilt.csv --audit national-checklist-audit.rebuilt.csv
~~~

The full PDF and cache path reproduced both published CSVs byte for byte. The accepted-name CSV has SHA-256 `7aae1c5a868a939dd4906008a4aa78bb9cc7651c3a3f9a582dc8c600b91cf25c`. The audit CSV has SHA-256 `a033b8e84b04e23ceedc457d486783bd20a78be34a79bdd4c0339ace75a79123`. [Importer](import_national_checklist.py)
