# Resources

Every link here was requested and verified on 2026-11-15. `tools/check_links.py` re-checks
them on demand and fails when a page serves an error body with a 200 status, which is how
a dead NASA link hides.

> Spanish version of the working guide, with the search keywords for each card: [`evidence/SOURCES.md`](../evidence/SOURCES.md)

## NASA — the sources this project actually uses

### The data

| URL | What it gives |
| --- | --- |
| <https://osdr.nasa.gov/osdr/data/osd/files/575> | File inventory for **OSD-575**, the Inspiration4 blood metabolic panel. All 532 real measurements come from here |
| <https://osdr.nasa.gov/osdr/data/osd/files/656> | File inventory for **OSD-656**, the urine inflammation panel. All 8,888 measurements come from here |

Both return JSON listing every file name and its download path.

### The documents behind the thresholds

| URL | What it backs |
| --- | --- |
| <https://humanresearchroadmap.nasa.gov/Evidence/reports/EvidenceBook.pdf> | The **Evidence Book** (6.7 MB). Table 4-1 gives the radiation career limit: 620 mSv at age 30 |
| <https://humanresearchroadmap.nasa.gov/Risks/risk.aspx?i=100> | Sleep risk. Holds the definition the system uses: *"sleep restriction defined as total sleep time >0 and <6 hours per 24-hour period"* |
| <https://humanresearchroadmap.nasa.gov/Risks/risk.aspx?i=96> | Radiation carcinogenesis |
| <https://humanresearchroadmap.nasa.gov/Risks/risk.aspx?i=99> | Behavioural health. Holds the sentence that keeps mood provisional: thresholds *"will need to be normed to the astronaut population"* |
| <https://humanresearchroadmap.nasa.gov/risks/> | Index of the 21 risks the `EVD-HAZ-*` cards were built from |

### To look for more

| URL | Use |
| --- | --- |
| <https://ntrs.nasa.gov/> | NASA technical reports and papers |
| <https://standards.nasa.gov/> | NASA standards. Search for **NASA-STD-3001** inside |

### Peer-reviewed literature

| URL | What it backs |
| --- | --- |
| <https://doi.org/10.1038/s41598-017-15560-w> | Stahn et al. 2017, *Scientific Reports*. The **+1.01 °C** rise in core body temperature on the ISS |

## Other agencies — context, not a source of figures

Nothing here backs a threshold in this project. These support one argument only: the
hardware already exists, and what is missing is the layer that interprets it.

| URL | What it is | Status |
| --- | --- | --- |
| <https://www.asc-csa.gc.ca/eng/sciences/bio-monitor.asp> | **Bio-Monitor / Astroskin** (CSA): the shirt measuring ECG, respiration, SpO₂, skin temperature and actigraphy | verified |
| <https://www.asc-csa.gc.ca/eng/health/> | Canadian Space Agency health section | verified |
| <https://www.esa.int/Science_Exploration/Human_and_Robotic_Exploration> | ESA human spaceflight: EveryWear, ThermoLab, the ground analogues | verified |
| <https://www.cnes.fr/en> | CNES, the French agency behind EveryWear | verified |

## Deliberately not listed

These circulate in reading lists and do not work. They are recorded here so nobody adds
them back.

| URL | Problem |
| --- | --- |
| `asc-csa.gc.ca/eng/health/health-beyond.asp` | 404. Three variants tried, none exists |
| `scispace.esa.int` | Does not connect |
| `eea.spaceflight.esa.int` | 401, institutional access required |

## A note on mixing them

The challenge requires NASA resources. Other agencies are context for the positioning
("we are not building a sensor"), not evidence for a threshold. Keep them apart: the
NASA block is what backs the numbers.
