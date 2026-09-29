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
- `symptom_training_data.csv`: 69 bilingual baseline examples for the ML routing prototype. These are authored examples, **not real patient records**.
- `providers.csv`: 10 demo provider records for local UI testing. They are **not a verified live directory**.

## 2) Recommended real provider source
India's Open Government Data portal publishes a National Health Portal Hospital Directory with fields including location, category, contact details, website and specializations. Use the official dataset/API as the provider source after checking its current licensing and freshness. Source: https://data.gov.in/catalog/hospital-directory-national-health-portal

## 3) Production ML data
For clinical-grade model development, use a properly licensed and de-identified clinical dataset with labels created/verified by qualified clinicians. Do not train on scraped patient content or identifiable health information.
