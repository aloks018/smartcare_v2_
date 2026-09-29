# Data strategy

## Medical navigation catalog

The JSON files below form the modular, local specialty-search catalog used by
`backend/app/services/medical_catalog.py`:

- `specialties.json`
- `subspecialties.json`
- `symptoms.json`
- `conditions.json`
- `treatments.json`
- `medical_keywords.json`

They use stable IDs and cross-references so data can grow without changes to
the frontend. To update the bundled seed catalog, edit
`scripts/build_medical_catalog.py` and run:

```powershell
python scripts\build_medical_catalog.py
```

The catalog supports healthcare navigation only. It does not diagnose disease,
set urgency beyond the application’s existing safety guardrails, or replace a
qualified clinician’s assessment.

## 1) Current bundled data
- `symptom_training_data.csv`: 69 authored bilingual examples, **not patient records**. They are not used by the voice recommendation route.
- `providers.csv`: demo fixture records retained for development only. They are not imported into the production provider search.
- The bundled specialty and symptom JSON files are a navigation catalog, not a clinician-validated clinical decision-support dataset. It must not be described as diagnostic or clinically validated.

## 2) Facility search source
Location-based facility search queries OpenStreetMap through Nominatim and Overpass. Results include source-object links and OSM attribution, are limited to named mapped facilities, and are not verified by SmartCare. Coverage and tags may be incomplete; confirm contact details and services with the facility before travelling. Source and terms: https://www.openstreetmap.org/copyright

## 3) Production ML data
For clinical-grade model development, use a properly licensed and de-identified clinical dataset with labels created/verified by qualified clinicians. Do not train on scraped patient content or identifiable health information.
