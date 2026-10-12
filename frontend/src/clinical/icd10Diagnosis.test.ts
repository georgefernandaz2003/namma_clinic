import test from 'node:test';
import assert from 'node:assert/strict';
import {
  ICD10_DATASET,
  ICD10_METADATA,
  searchICD10,
  getICD10ByCode,
} from '../data/icd10_who.ts';

test('WHO ICD-10 Dataset Metadata & Standards Compliance', async (t) => {
  await t.test('Dataset adheres to WHO ICD-10 2019/2016 Edition and India MoHFW standard', () => {
    assert.equal(
      ICD10_METADATA.standard,
      'WHO International Classification of Diseases, 10th Revision (ICD-10)'
    );
    assert.equal(ICD10_METADATA.edition, '2019 / 2016 Edition');
    assert.equal(
      ICD10_METADATA.adoption,
      'India Ministry of Health and Family Welfare (MoHFW) / Ayushman Bharat Digital Mission (ABDM)'
    );
    assert.ok(ICD10_METADATA.total_entries >= 400, 'Must have at least 400 clinical conditions');
    assert.equal(ICD10_DATASET.length, ICD10_METADATA.total_entries);
  });

  await t.test('All entries contain valid codes, non-empty names, categories, and keyword tags', () => {
    for (const item of ICD10_DATASET) {
      assert.ok(item.code && item.code.trim().length > 0, `Code cannot be empty: ${JSON.stringify(item)}`);
      assert.ok(item.name && item.name.trim().length > 0, `Name cannot be empty: ${item.code}`);
      assert.ok(item.category && item.category.trim().length > 0, `Category cannot be empty: ${item.code}`);
      assert.match(item.code, /^[A-Z][0-9]/, `Code ${item.code} must follow ICD-10 chapter prefix format`);
    }
  });
});

test('Searchable ICD-10 Diagnosis Search Engine', async (t) => {
  await t.test('1. Search by ICD-10 Code', () => {
    // Exact search for Hypertension
    const i10Results = searchICD10('I10');
    assert.ok(i10Results.length > 0, 'Must find results for I10');
    assert.equal(i10Results[0].code, 'I10');
    assert.equal(i10Results[0].name, 'Essential (primary) hypertension');

    // Code prefix search for Type 2 Diabetes
    const e11Results = searchICD10('E11');
    assert.ok(e11Results.length > 0, 'Must find results for E11 prefix');
    assert.ok(e11Results.some((r) => r.code === 'E11.9'));
    assert.ok(e11Results.some((r) => r.code === 'E11.2'));

    // Code search for Fever (R50.9)
    const r50Results = searchICD10('R50.9');
    assert.ok(r50Results.length > 0, 'Must find results for R50.9');
    assert.equal(r50Results[0].code, 'R50.9');
    assert.equal(r50Results[0].name, 'Fever, unspecified (Pyrexia / PUO)');
  });

  await t.test('2. Search by Diagnosis Name', () => {
    // Search "hypertension"
    const htnResults = searchICD10('hypertension');
    assert.ok(htnResults.length > 0, 'Must return results for hypertension');
    assert.ok(htnResults.some((r) => r.code === 'I10'));

    // Search "diabetes"
    const dmResults = searchICD10('diabetes');
    assert.ok(dmResults.length > 0, 'Must return results for diabetes');
    assert.ok(dmResults.some((r) => r.code === 'E11.9'));

    // Search "pneumonia"
    const pneuResults = searchICD10('pneumonia');
    assert.ok(pneuResults.length > 0, 'Must return pneumonia results');
    assert.ok(pneuResults.some((r) => r.code === 'J18.9'));

    // Search "gastroenteritis"
    const geResults = searchICD10('gastroenteritis');
    assert.ok(geResults.length > 0, 'Must return gastroenteritis');
    assert.ok(geResults.some((r) => r.code === 'A09'));
  });

  await t.test('3. Search by Common Clinical Keyword / Regional Alias', () => {
    // "bp" -> Hypertension (I10)
    const bpResults = searchICD10('bp');
    assert.ok(bpResults.some((r) => r.code === 'I10'), 'Keyword "bp" should match I10');

    // "sugar" -> Type 2 Diabetes (E11.9)
    const sugarResults = searchICD10('sugar');
    assert.ok(sugarResults.some((r) => r.code === 'E11.9'), 'Keyword "sugar" should match E11.9');

    // "dengue" -> Dengue fever (A90)
    const dengueResults = searchICD10('dengue');
    assert.ok(dengueResults.some((r) => r.code === 'A90'), 'Keyword "dengue" should match A90');

    // "loose motions" -> Acute gastroenteritis (A09)
    const lmResults = searchICD10('loose motions');
    assert.ok(lmResults.some((r) => r.code === 'A09'), 'Keyword "loose motions" should match A09');

    // "uti" -> Urinary tract infection (N39.0)
    const utiResults = searchICD10('uti');
    assert.ok(utiResults.some((r) => r.code === 'N39.0'), 'Keyword "uti" should match N39.0');
  });

  await t.test('4. Format Presentation: ICD code — Diagnosis name', () => {
    const entry = getICD10ByCode('I10');
    assert.ok(entry);
    const formatted = `${entry.code} — ${entry.name}`;
    assert.equal(formatted, 'I10 — Essential (primary) hypertension');
  });

  await t.test('5. Unmatched / Invalid search query handling', () => {
    const invalidResults = searchICD10('XYZ9999INVALID');
    assert.equal(invalidResults.length, 0, 'Unmatched queries must return empty array');

    const emptyResults = searchICD10('');
    assert.equal(emptyResults.length, 0, 'Empty queries must return empty array');

    const lookupNone = getICD10ByCode('INVALID_CODE');
    assert.equal(lookupNone, undefined, 'Invalid code lookup must be undefined');
  });

  await t.test('6. Mandatory validation: consultation requires both code and name', () => {
    const validateConsultationDiagnosis = (code: string, name: string) => {
      if (!code.trim() || !name.trim()) {
        return { valid: false, error: 'Diagnosis Code and Diagnosis Name are mandatory clinical records.' };
      }
      return { valid: true, error: null };
    };

    assert.equal(validateConsultationDiagnosis('', 'Hypertension').valid, false);
    assert.equal(validateConsultationDiagnosis('I10', '').valid, false);
    assert.equal(validateConsultationDiagnosis('  ', '   ').valid, false);
    assert.equal(validateConsultationDiagnosis('I10', 'Essential (primary) hypertension').valid, true);
  });
});
