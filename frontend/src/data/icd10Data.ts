export interface ICD10Diagnosis {
  code: string;
  name: string;
  category: string;
  common?: boolean;
}

export const COMMON_ICD10_DIAGNOSES: ICD10Diagnosis[] = [
  // Endocrine, Nutritional & Metabolic
  { code: 'E11.9', name: 'Type 2 Diabetes Mellitus without Complications', category: 'Endocrine & Metabolic', common: true },
  { code: 'E11.65', name: 'Type 2 Diabetes Mellitus with Hyperglycemia', category: 'Endocrine & Metabolic', common: true },
  { code: 'E11.9 / I10', name: 'Type 2 Diabetes Mellitus with Essential Hypertension', category: 'Endocrine & Metabolic', common: true },
  { code: 'E10.9', name: 'Type 1 Diabetes Mellitus without Complications', category: 'Endocrine & Metabolic' },
  { code: 'E03.9', name: 'Hypothyroidism, Unspecified', category: 'Endocrine & Metabolic', common: true },
  { code: 'E05.90', name: 'Thyrotoxicosis / Hyperthyroidism, Unspecified', category: 'Endocrine & Metabolic' },
  { code: 'E66.9', name: 'Obesity, Unspecified', category: 'Endocrine & Metabolic', common: true },
  { code: 'E78.5', name: 'Hyperlipidemia / Dyslipidemia, Unspecified', category: 'Endocrine & Metabolic', common: true },
  { code: 'E79.0', name: 'Hyperuricemia without Signs of Inflammatory Arthritis / Gout', category: 'Endocrine & Metabolic' },
  { code: 'E55.9', name: 'Vitamin D Deficiency, Unspecified', category: 'Endocrine & Metabolic', common: true },
  { code: 'E53.8', name: 'Vitamin B12 / B-Complex Deficiency', category: 'Endocrine & Metabolic', common: true },
  { code: 'D50.9', name: 'Iron Deficiency Anemia, Unspecified', category: 'Hematology & Blood', common: true },
  { code: 'D53.9', name: 'Nutritional Anemia, Unspecified', category: 'Hematology & Blood' },

  // Circulatory / Cardiovascular
  { code: 'I10', name: 'Essential (Primary) Hypertension', category: 'Cardiovascular', common: true },
  { code: 'I11.9', name: 'Hypertensive Heart Disease without Heart Failure', category: 'Cardiovascular', common: true },
  { code: 'I20.9', name: 'Angina Pectoris, Unspecified', category: 'Cardiovascular' },
  { code: 'I25.10', name: 'Atherosclerotic Heart Disease of Native Coronary Artery (CAD)', category: 'Cardiovascular' },
  { code: 'I50.9', name: 'Heart Failure, Unspecified', category: 'Cardiovascular' },
  { code: 'I95.9', name: 'Hypotension, Unspecified', category: 'Cardiovascular', common: true },
  { code: 'I83.90', name: 'Varicose Veins of Lower Extremities', category: 'Cardiovascular' },

  // Respiratory System
  { code: 'J06.9', name: 'Acute Upper Respiratory Tract Infection (URTI), Unspecified', category: 'Respiratory', common: true },
  { code: 'J00', name: 'Acute Nasopharyngitis (Common Cold)', category: 'Respiratory', common: true },
  { code: 'J02.9', name: 'Acute Pharyngitis, Unspecified (Sore Throat)', category: 'Respiratory', common: true },
  { code: 'J03.90', name: 'Acute Tonsillitis, Unspecified', category: 'Respiratory', common: true },
  { code: 'J01.90', name: 'Acute Sinusitis, Unspecified', category: 'Respiratory' },
  { code: 'J20.9', name: 'Acute Bronchitis, Unspecified', category: 'Respiratory', common: true },
  { code: 'J45.909', name: 'Bronchial Asthma, Unspecified', category: 'Respiratory', common: true },
  { code: 'J44.9', name: 'Chronic Obstructive Pulmonary Disease (COPD), Unspecified', category: 'Respiratory', common: true },
  { code: 'J18.9', name: 'Pneumonia, Unspecified Organism', category: 'Respiratory' },
  { code: 'J30.9', name: 'Allergic Rhinitis, Unspecified', category: 'Respiratory', common: true },

  // Digestive / Gastrointestinal
  { code: 'K29.70', name: 'Gastritis, Unspecified, without Bleeding', category: 'Gastrointestinal', common: true },
  { code: 'K21.9', name: 'Gastro-Esophageal Reflux Disease (GERD) without Esophagitis', category: 'Gastrointestinal', common: true },
  { code: 'K25.9', name: 'Gastric / Peptic Ulcer Disease, Unspecified', category: 'Gastrointestinal' },
  { code: 'K30', name: 'Functional Dyspepsia / Indigestion', category: 'Gastrointestinal', common: true },
  { code: 'A09', name: 'Infectious Gastroenteritis and Colitis, Unspecified (Acute Diarrhea)', category: 'Gastrointestinal', common: true },
  { code: 'K59.00', name: 'Constipation, Unspecified', category: 'Gastrointestinal', common: true },
  { code: 'K58.9', name: 'Irritable Bowel Syndrome (IBS) without Diarrhea', category: 'Gastrointestinal' },
  { code: 'K64.9', name: 'Hemorrhoids / Piles, Unspecified', category: 'Gastrointestinal', common: true },
  { code: 'K76.0', name: 'Fatty (Change of) Liver, Not Elsewhere Classified (NAFLD)', category: 'Gastrointestinal' },

  // Infectious & Parasitic Diseases
  { code: 'A90', name: 'Dengue Fever (Classic Dengue)', category: 'Infectious', common: true },
  { code: 'A91', name: 'Dengue Hemorrhagic Fever', category: 'Infectious' },
  { code: 'A01.00', name: 'Typhoid Fever, Unspecified (Enteric Fever)', category: 'Infectious', common: true },
  { code: 'B54', name: 'Malaria, Unspecified', category: 'Infectious', common: true },
  { code: 'B34.9', name: 'Viral Infection, Unspecified', category: 'Infectious', common: true },
  { code: 'A15.0', name: 'Tuberculosis of Lung (Pulmonary TB)', category: 'Infectious' },
  { code: 'B01.9', name: 'Varicella (Chickenpox) without Complication', category: 'Infectious' },
  { code: 'B35.9', name: 'Dermatophytosis / Fungal Skin Infection (Tinea / Ringworm)', category: 'Infectious', common: true },
  { code: 'B86', name: 'Scabies', category: 'Infectious', common: true },

  // Musculoskeletal & Connective Tissue
  { code: 'M54.50', name: 'Low Back Pain / Lumbago, Unspecified', category: 'Musculoskeletal', common: true },
  { code: 'M54.2', name: 'Cervicalgia (Neck Pain)', category: 'Musculoskeletal', common: true },
  { code: 'M25.50', name: 'Arthralgia / Joint Pain, Unspecified Site', category: 'Musculoskeletal', common: true },
  { code: 'M19.90', name: 'Primary Osteoarthritis, Unspecified Site', category: 'Musculoskeletal', common: true },
  { code: 'M06.9', name: 'Rheumatoid Arthritis, Unspecified', category: 'Musculoskeletal' },
  { code: 'M79.1', name: 'Myalgia / Muscle Ache & Pain', category: 'Musculoskeletal', common: true },
  { code: 'M77.9', name: 'Enthesopathy / Tendinitis, Unspecified', category: 'Musculoskeletal' },

  // Genitourinary System
  { code: 'N39.0', name: 'Urinary Tract Infection (UTI), Site Not Specified', category: 'Genitourinary', common: true },
  { code: 'N20.0', name: 'Calculus of Kidney (Renal Calculi / Kidney Stones)', category: 'Genitourinary', common: true },
  { code: 'N40.0', name: 'Benign Prostatic Hyperplasia (BPH) without LUTS', category: 'Genitourinary' },
  { code: 'N94.6', name: 'Dysmenorrhea, Unspecified', category: 'Genitourinary', common: true },
  { code: 'N76.0', name: 'Acute Vaginitis, Unspecified', category: 'Genitourinary' },
  { code: 'N92.0', name: 'Excessive and Frequent Menstruation (Menorrhagia)', category: 'Genitourinary' },

  // Skin & Subcutaneous Tissue
  { code: 'L23.9', name: 'Allergic Contact Dermatitis, Unspecified Cause', category: 'Dermatological', common: true },
  { code: 'L20.9', name: 'Atopic Dermatitis / Eczema, Unspecified', category: 'Dermatological', common: true },
  { code: 'L50.9', name: 'Urticaria (Hives), Unspecified', category: 'Dermatological', common: true },
  { code: 'L70.0', name: 'Acne Vulgaris', category: 'Dermatological', common: true },
  { code: 'L03.90', name: 'Cellulitis, Unspecified', category: 'Dermatological' },
  { code: 'L02.91', name: 'Cutaneous Abscess / Boil / Furuncle, Unspecified', category: 'Dermatological', common: true },
  { code: 'L40.9', name: 'Psoriasis, Unspecified', category: 'Dermatological' },

  // Nervous System & Mental Health
  { code: 'G43.909', name: 'Migraine, Unspecified, Not Intractable', category: 'Neurological', common: true },
  { code: 'G44.209', name: 'Tension-Type Headache, Unspecified', category: 'Neurological', common: true },
  { code: 'R51.9', name: 'Headache, Unspecified', category: 'Neurological', common: true },
  { code: 'R42', name: 'Dizziness and Giddiness / Peripheral Vertigo', category: 'Neurological', common: true },
  { code: 'G40.909', name: 'Epilepsy / Seizure Disorder, Unspecified', category: 'Neurological' },
  { code: 'F41.9', name: 'Anxiety Disorder, Unspecified', category: 'Psychiatric' },
  { code: 'F32.9', name: 'Depressive Episode, Unspecified', category: 'Psychiatric' },
  { code: 'G47.00', name: 'Insomnia, Unspecified', category: 'Neurological' },

  // Eye, Ear & Sensory
  { code: 'H10.9', name: 'Unspecified Conjunctivitis (Pink Eye)', category: 'Eye & Ear', common: true },
  { code: 'H66.90', name: 'Otitis Media, Unspecified', category: 'Eye & Ear', common: true },
  { code: 'H60.90', name: 'Otitis Externa, Unspecified', category: 'Eye & Ear' },
  { code: 'H52.4', name: 'Presbyopia (Refractive Eye Disorder)', category: 'Eye & Ear' },

  // Pregnancy, Childbirth & Puerperium
  { code: 'Z34.90', name: 'Encounter for Supervision of Normal Pregnancy (ANC Review)', category: 'Obstetrics / ANC', common: true },
  { code: 'O99.019', name: 'Anemia Complicating Pregnancy, Unspecified Trimester', category: 'Obstetrics / ANC', common: true },
  { code: 'O13.9', name: 'Gestational [Pregnancy-Induced] Hypertension without Significant Proteinuria', category: 'Obstetrics / ANC' },
  { code: 'O21.0', name: 'Mild Hyperemesis Gravidarum (Pregnancy Morning Sickness)', category: 'Obstetrics / ANC' },

  // General Symptoms, Signs & Injuries
  { code: 'R50.9', name: 'Fever, Unspecified (Pyrexia)', category: 'General Symptoms', common: true },
  { code: 'R05.9', name: 'Cough, Unspecified', category: 'General Symptoms', common: true },
  { code: 'R10.9', name: 'Abdominal Pain, Unspecified', category: 'General Symptoms', common: true },
  { code: 'R53.83', name: 'Other Fatigue and Malaise / Generalized Weakness', category: 'General Symptoms', common: true },
  { code: 'R07.9', name: 'Chest Pain, Unspecified', category: 'General Symptoms' },
  { code: 'T14.90', name: 'Injury / Superficial Trauma, Unspecified', category: 'Injury & Trauma', common: true },
  { code: 'Z00.00', name: 'Encounter for General Adult Medical Examination without Abnormal Findings', category: 'General & Preventive', common: true }
];
