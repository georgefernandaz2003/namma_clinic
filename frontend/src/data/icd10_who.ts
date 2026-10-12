/**
 * WHO International Classification of Diseases, 10th Revision (ICD-10)
 * 
 * Standard: WHO International Classification of Diseases, 10th Revision (ICD-10)
 * Edition: 2019 / 2016 Edition
 * Adoption: India Ministry of Health and Family Welfare (MoHFW) / Ayushman Bharat Digital Mission (ABDM)
 * Version: 2019.1-in-phc
 * Scope: Primary Health Centre (PHC), Community Health Centre (CHC) & Outpatient General Practice
 * 
 * Locally stored, versioned dataset for offline clinic operation.
 * Do not fetch from external websites during consultation workflows.
 */

export interface ICD10Entry {
  code: string;
  name: string;
  category: string;
  keywords?: string[];
}

export interface ICD10Metadata {
  standard: string;
  edition: string;
  classification_system: string;
  adoption: string;
  version: string;
  scope: string;
  description: string;
  total_entries: number;
}

export const ICD10_METADATA: ICD10Metadata = {
  "standard": "WHO International Classification of Diseases, 10th Revision (ICD-10)",
  "edition": "2019 / 2016 Edition",
  "classification_system": "WHO ICD-10 (Tabular List & Clinical Coding Standard)",
  "adoption": "India Ministry of Health and Family Welfare (MoHFW) / Ayushman Bharat Digital Mission (ABDM)",
  "version": "2019.1-in-phc",
  "scope": "Primary Health Centre (PHC), Community Health Centre (CHC) & Outpatient General Practice",
  "description": "Curated, high-fidelity offline WHO ICD-10 diagnosis dataset for Namma Clinic consultation.",
  "total_entries": 447
};

export const ICD10_DATASET: ICD10Entry[] = [
  {
    "code": "A00.9",
    "name": "Cholera, unspecified",
    "category": "Infectious & Parasitic Diseases",
    "keywords": [
      "cholera",
      "vibrio",
      "watery diarrhoea",
      "rice water stools"
    ]
  },
  {
    "code": "A01.0",
    "name": "Typhoid fever (Salmonella typhi)",
    "category": "Infectious & Parasitic Diseases",
    "keywords": [
      "typhoid",
      "enteric fever",
      "salmonella",
      "step-ladder fever"
    ]
  },
  {
    "code": "A01.1",
    "name": "Paratyphoid fever A",
    "category": "Infectious & Parasitic Diseases",
    "keywords": [
      "paratyphoid",
      "enteric fever"
    ]
  },
  {
    "code": "A01.4",
    "name": "Paratyphoid fever, unspecified",
    "category": "Infectious & Parasitic Diseases",
    "keywords": [
      "paratyphoid",
      "enteric fever"
    ]
  },
  {
    "code": "A02.0",
    "name": "Salmonella enteritis",
    "category": "Infectious & Parasitic Diseases",
    "keywords": [
      "salmonellosis",
      "food poisoning",
      "salmonella"
    ]
  },
  {
    "code": "A03.9",
    "name": "Shigellosis, unspecified (Bacillary dysentery)",
    "category": "Infectious & Parasitic Diseases",
    "keywords": [
      "dysentery",
      "bacillary dysentery",
      "shigella",
      "blood in stool"
    ]
  },
  {
    "code": "A04.9",
    "name": "Bacterial intestinal infection, unspecified",
    "category": "Infectious & Parasitic Diseases",
    "keywords": [
      "bacterial diarrhoea",
      "enteritis",
      "loose motions"
    ]
  },
  {
    "code": "A05.9",
    "name": "Bacterial foodborne intoxication, unspecified",
    "category": "Infectious & Parasitic Diseases",
    "keywords": [
      "food poisoning",
      "foodborne infection"
    ]
  },
  {
    "code": "A06.0",
    "name": "Acute amoebic dysentery",
    "category": "Infectious & Parasitic Diseases",
    "keywords": [
      "amoebiasis",
      "amoebic dysentery",
      "entamoeba",
      "blood stools"
    ]
  },
  {
    "code": "A06.4",
    "name": "Amoebic liver abscess",
    "category": "Infectious & Parasitic Diseases",
    "keywords": [
      "liver abscess",
      "amoebic abscess"
    ]
  },
  {
    "code": "A07.1",
    "name": "Giardiasis [lambliasis]",
    "category": "Infectious & Parasitic Diseases",
    "keywords": [
      "giardia",
      "giardiasis",
      "malabsorption"
    ]
  },
  {
    "code": "A08.4",
    "name": "Viral intestinal infection, unspecified (Viral gastroenteritis)",
    "category": "Infectious & Parasitic Diseases",
    "keywords": [
      "viral diarrhea",
      "rotavirus",
      "stomach flu"
    ]
  },
  {
    "code": "A09",
    "name": "Infectious gastroenteritis and colitis, unspecified",
    "category": "Infectious & Parasitic Diseases",
    "keywords": [
      "gastroenteritis",
      "acute gastroenteritis",
      "age",
      "loose motions",
      "diarrhea",
      "vomiting"
    ]
  },
  {
    "code": "A15.0",
    "name": "Tuberculosis of lung, confirmed by sputum microscopy",
    "category": "Infectious & Parasitic Diseases",
    "keywords": [
      "tb",
      "pulmonary tuberculosis",
      "pulmonary tb",
      "phthisis",
      "koch",
      "sputum positive"
    ]
  },
  {
    "code": "A15.1",
    "name": "Tuberculosis of lung, confirmed by culture only",
    "category": "Infectious & Parasitic Diseases",
    "keywords": [
      "pulmonary tb",
      "tuberculosis",
      "culture positive"
    ]
  },
  {
    "code": "A16.2",
    "name": "Tuberculosis of lung, without mention of bacteriological or histological confirmation",
    "category": "Infectious & Parasitic Diseases",
    "keywords": [
      "pulmonary tuberculosis",
      "clinical tb",
      "suspected tb"
    ]
  },
  {
    "code": "A18.0",
    "name": "Tuberculosis of bones and joints (Pott's disease)",
    "category": "Infectious & Parasitic Diseases",
    "keywords": [
      "bone tb",
      "spine tb",
      "potts spine"
    ]
  },
  {
    "code": "A18.2",
    "name": "Tuberculous peripheral lymphadenopathy",
    "category": "Infectious & Parasitic Diseases",
    "keywords": [
      "lymph node tb",
      "scrofula",
      "cervical lymphadenopathy"
    ]
  },
  {
    "code": "A18.4",
    "name": "Tuberculosis of skin and subcutaneous tissue (Lupus vulgaris)",
    "category": "Infectious & Parasitic Diseases",
    "keywords": [
      "skin tb",
      "lupus vulgaris"
    ]
  },
  {
    "code": "A27.9",
    "name": "Leptospirosis, unspecified",
    "category": "Infectious & Parasitic Diseases",
    "keywords": [
      "leptospirosis",
      "weils disease",
      "monsoon fever"
    ]
  },
  {
    "code": "A30.9",
    "name": "Leprosy [Hansen's disease], unspecified",
    "category": "Infectious & Parasitic Diseases",
    "keywords": [
      "leprosy",
      "hansens disease",
      "hypopigmented patch",
      "numbness"
    ]
  },
  {
    "code": "A35",
    "name": "Other tetanus (Tetanus)",
    "category": "Infectious & Parasitic Diseases",
    "keywords": [
      "tetanus",
      "lockjaw",
      "clostridium tetani"
    ]
  },
  {
    "code": "A36.9",
    "name": "Diphtheria, unspecified",
    "category": "Infectious & Parasitic Diseases",
    "keywords": [
      "diphtheria",
      "pseudomembrane"
    ]
  },
  {
    "code": "A37.9",
    "name": "Whooping cough, unspecified (Pertussis)",
    "category": "Infectious & Parasitic Diseases",
    "keywords": [
      "whooping cough",
      "pertussis",
      "paroxysmal cough"
    ]
  },
  {
    "code": "A39.0",
    "name": "Meningococcal meningitis",
    "category": "Infectious & Parasitic Diseases",
    "keywords": [
      "meningitis",
      "meningococcal infection"
    ]
  },
  {
    "code": "A82.9",
    "name": "Rabies, unspecified",
    "category": "Infectious & Parasitic Diseases",
    "keywords": [
      "rabies",
      "hydrophobia",
      "dog bite infection"
    ]
  },
  {
    "code": "A90",
    "name": "Dengue fever [classical dengue]",
    "category": "Infectious & Parasitic Diseases",
    "keywords": [
      "dengue",
      "breakbone fever",
      "dengue virus",
      "ns1 positive"
    ]
  },
  {
    "code": "A91",
    "name": "Dengue haemorrhagic fever",
    "category": "Infectious & Parasitic Diseases",
    "keywords": [
      "dhf",
      "dengue hemorrhagic",
      "severe dengue",
      "thrombocytopenia",
      "bleeding"
    ]
  },
  {
    "code": "A92.0",
    "name": "Chikungunya virus disease",
    "category": "Infectious & Parasitic Diseases",
    "keywords": [
      "chikungunya",
      "chikingunya",
      "arbovirus",
      "joint pain fever"
    ]
  },
  {
    "code": "B00.9",
    "name": "Herpesviral infection, unspecified (Herpes simplex)",
    "category": "Infectious & Parasitic Diseases",
    "keywords": [
      "herpes",
      "hsv",
      "cold sore",
      "fever blister"
    ]
  },
  {
    "code": "B01.9",
    "name": "Varicella without complication (Chickenpox)",
    "category": "Infectious & Parasitic Diseases",
    "keywords": [
      "chickenpox",
      "varicella",
      "vesicular rash"
    ]
  },
  {
    "code": "B02.9",
    "name": "Zoster without complication (Herpes zoster / Shingles)",
    "category": "Infectious & Parasitic Diseases",
    "keywords": [
      "shingles",
      "herpes zoster",
      "radicular pain",
      "dermatomal rash"
    ]
  },
  {
    "code": "B05.9",
    "name": "Measles without complication",
    "category": "Infectious & Parasitic Diseases",
    "keywords": [
      "measles",
      "rubeola",
      "koplik spots"
    ]
  },
  {
    "code": "B06.9",
    "name": "Rubella without complication (German measles)",
    "category": "Infectious & Parasitic Diseases",
    "keywords": [
      "rubella",
      "german measles"
    ]
  },
  {
    "code": "B07",
    "name": "Viral warts (Verruca vulgaris)",
    "category": "Infectious & Parasitic Diseases",
    "keywords": [
      "warts",
      "verruca",
      "hpv"
    ]
  },
  {
    "code": "B15.9",
    "name": "Hepatitis A without hepatic coma",
    "category": "Infectious & Parasitic Diseases",
    "keywords": [
      "viral hepatitis",
      "hepatitis a",
      "jaundice",
      "acute jaundice"
    ]
  },
  {
    "code": "B16.9",
    "name": "Acute hepatitis B without delta-agent and without hepatic coma",
    "category": "Infectious & Parasitic Diseases",
    "keywords": [
      "hepatitis b",
      "hbv",
      "hbsag positive"
    ]
  },
  {
    "code": "B17.1",
    "name": "Acute hepatitis C",
    "category": "Infectious & Parasitic Diseases",
    "keywords": [
      "hepatitis c",
      "hcv"
    ]
  },
  {
    "code": "B17.2",
    "name": "Acute hepatitis E",
    "category": "Infectious & Parasitic Diseases",
    "keywords": [
      "hepatitis e",
      "hev",
      "enterically transmitted hepatitis"
    ]
  },
  {
    "code": "B18.1",
    "name": "Chronic viral hepatitis B without delta-agent",
    "category": "Infectious & Parasitic Diseases",
    "keywords": [
      "chronic hepatitis b",
      "chronic hbv"
    ]
  },
  {
    "code": "B20",
    "name": "Human immunodeficiency virus [HIV] disease",
    "category": "Infectious & Parasitic Diseases",
    "keywords": [
      "hiv",
      "aids",
      "retroviral disease"
    ]
  },
  {
    "code": "B26.9",
    "name": "Mumps without complication",
    "category": "Infectious & Parasitic Diseases",
    "keywords": [
      "mumps",
      "parotitis",
      "swollen cheek"
    ]
  },
  {
    "code": "B35.0",
    "name": "Tinea barbae and tinea capitis (Ringworm of beard and scalp)",
    "category": "Infectious & Parasitic Diseases",
    "keywords": [
      "tinea capitis",
      "ringworm",
      "scalp fungal infection"
    ]
  },
  {
    "code": "B35.3",
    "name": "Tinea pedis (Athlete's foot)",
    "category": "Infectious & Parasitic Diseases",
    "keywords": [
      "athletes foot",
      "tinea pedis",
      "foot fungal"
    ]
  },
  {
    "code": "B35.4",
    "name": "Tinea corporis (Ringworm of the body)",
    "category": "Infectious & Parasitic Diseases",
    "keywords": [
      "tinea corporis",
      "ringworm",
      "dermatophytosis",
      "itchy ring rash"
    ]
  },
  {
    "code": "B35.6",
    "name": "Tinea cruris (Jock itch)",
    "category": "Infectious & Parasitic Diseases",
    "keywords": [
      "tinea cruris",
      "groin fungal",
      "jock itch"
    ]
  },
  {
    "code": "B36.0",
    "name": "Pityriasis versicolor (Tinea versicolor)",
    "category": "Infectious & Parasitic Diseases",
    "keywords": [
      "tinea versicolor",
      "fungal spots",
      "pityriasis versicolor"
    ]
  },
  {
    "code": "B37.0",
    "name": "Candidal stomatitis (Oral thrush)",
    "category": "Infectious & Parasitic Diseases",
    "keywords": [
      "oral thrush",
      "candida",
      "moniliasis",
      "white patches tongue"
    ]
  },
  {
    "code": "B37.3",
    "name": "Candidiasis of vulva and vagina (Vaginal thrush)",
    "category": "Infectious & Parasitic Diseases",
    "keywords": [
      "vaginal candidiasis",
      "curdy discharge",
      "yeast infection"
    ]
  },
  {
    "code": "B50.9",
    "name": "Plasmodium falciparum malaria, unspecified",
    "category": "Infectious & Parasitic Diseases",
    "keywords": [
      "malaria",
      "falciparum",
      "pf malaria",
      "fever with chills"
    ]
  },
  {
    "code": "B51.9",
    "name": "Plasmodium vivax malaria without complication",
    "category": "Infectious & Parasitic Diseases",
    "keywords": [
      "malaria",
      "vivax",
      "pv malaria",
      "rigors"
    ]
  },
  {
    "code": "B54",
    "name": "Unspecified malaria",
    "category": "Infectious & Parasitic Diseases",
    "keywords": [
      "malaria",
      "fever rigors",
      "plasmodium"
    ]
  },
  {
    "code": "B74.9",
    "name": "Filariasis, unspecified (Lymphatic filariasis / Elephantiasis)",
    "category": "Infectious & Parasitic Diseases",
    "keywords": [
      "filariasis",
      "elephantiasis",
      "wuchereria",
      "swollen leg"
    ]
  },
  {
    "code": "B76.0",
    "name": "Ancylostomiasis (Hookworm infection)",
    "category": "Infectious & Parasitic Diseases",
    "keywords": [
      "hookworm",
      "ancylostoma",
      "anaemia worms"
    ]
  },
  {
    "code": "B77.9",
    "name": "Ascariasis, unspecified (Roundworm infection)",
    "category": "Infectious & Parasitic Diseases",
    "keywords": [
      "roundworm",
      "ascariasis",
      "intestinal worms"
    ]
  },
  {
    "code": "B80",
    "name": "Enterobiasis (Pinworm / Threadworm infection)",
    "category": "Infectious & Parasitic Diseases",
    "keywords": [
      "pinworm",
      "threadworm",
      "pruritus ani",
      "nocturnal anal itching"
    ]
  },
  {
    "code": "B82.9",
    "name": "Intestinal parasitism, unspecified (Worm infestation)",
    "category": "Infectious & Parasitic Diseases",
    "keywords": [
      "worms",
      "worm infestation",
      "deworming"
    ]
  },
  {
    "code": "B86",
    "name": "Scabies",
    "category": "Infectious & Parasitic Diseases",
    "keywords": [
      "scabies",
      "sarcoptes",
      "night itching",
      "burrows",
      "finger webs"
    ]
  },
  {
    "code": "C00.9",
    "name": "Malignant neoplasm of lip, unspecified",
    "category": "Neoplasms",
    "keywords": [
      "lip cancer",
      "oral cancer",
      "tobacco chew"
    ]
  },
  {
    "code": "C02.9",
    "name": "Malignant neoplasm of tongue, unspecified",
    "category": "Neoplasms",
    "keywords": [
      "tongue cancer",
      "oral ulcer cancer"
    ]
  },
  {
    "code": "C06.9",
    "name": "Malignant neoplasm of mouth, unspecified",
    "category": "Neoplasms",
    "keywords": [
      "oral cancer",
      "mouth cancer",
      "buccal mucosa"
    ]
  },
  {
    "code": "C15.9",
    "name": "Malignant neoplasm of oesophagus, unspecified",
    "category": "Neoplasms",
    "keywords": [
      "esophageal cancer",
      "oesophagus cancer",
      "dysphagia"
    ]
  },
  {
    "code": "C16.9",
    "name": "Malignant neoplasm of stomach, unspecified (Gastric cancer)",
    "category": "Neoplasms",
    "keywords": [
      "stomach cancer",
      "gastric cancer"
    ]
  },
  {
    "code": "C18.9",
    "name": "Malignant neoplasm of colon, unspecified",
    "category": "Neoplasms",
    "keywords": [
      "colon cancer",
      "bowel cancer"
    ]
  },
  {
    "code": "C20",
    "name": "Malignant neoplasm of rectum",
    "category": "Neoplasms",
    "keywords": [
      "rectal cancer",
      "bleeding per rectum"
    ]
  },
  {
    "code": "C22.0",
    "name": "Liver cell carcinoma (Hepatocellular carcinoma)",
    "category": "Neoplasms",
    "keywords": [
      "liver cancer",
      "hepatoma",
      "hcc"
    ]
  },
  {
    "code": "C34.9",
    "name": "Malignant neoplasm of bronchus or lung, unspecified",
    "category": "Neoplasms",
    "keywords": [
      "lung cancer",
      "smoking cancer",
      "haemoptysis"
    ]
  },
  {
    "code": "C50.9",
    "name": "Malignant neoplasm of breast, unspecified",
    "category": "Neoplasms",
    "keywords": [
      "breast cancer",
      "breast lump",
      "ca breast"
    ]
  },
  {
    "code": "C53.9",
    "name": "Malignant neoplasm of cervix uteri, unspecified",
    "category": "Neoplasms",
    "keywords": [
      "cervical cancer",
      "ca cervix",
      "postcoital bleeding"
    ]
  },
  {
    "code": "C54.9",
    "name": "Malignant neoplasm of corpus uteri, unspecified (Uterine cancer)",
    "category": "Neoplasms",
    "keywords": [
      "uterine cancer",
      "endometrial cancer"
    ]
  },
  {
    "code": "C56",
    "name": "Malignant neoplasm of ovary",
    "category": "Neoplasms",
    "keywords": [
      "ovarian cancer",
      "ovarian mass"
    ]
  },
  {
    "code": "C61",
    "name": "Malignant neoplasm of prostate",
    "category": "Neoplasms",
    "keywords": [
      "prostate cancer",
      "psa",
      "ca prostate"
    ]
  },
  {
    "code": "C95.9",
    "name": "Leukaemia, unspecified",
    "category": "Neoplasms",
    "keywords": [
      "leukemia",
      "blood cancer"
    ]
  },
  {
    "code": "D17.9",
    "name": "Benign lipomatous neoplasm, unspecified (Lipoma)",
    "category": "Neoplasms",
    "keywords": [
      "lipoma",
      "fatty lump",
      "subcutaneous swelling"
    ]
  },
  {
    "code": "D24",
    "name": "Benign neoplasm of breast (Fibroadenoma of breast)",
    "category": "Neoplasms",
    "keywords": [
      "fibroadenoma",
      "breast mouse",
      "benign breast lump"
    ]
  },
  {
    "code": "D25.9",
    "name": "Leiomyoma of uterus, unspecified (Uterine fibroid)",
    "category": "Neoplasms",
    "keywords": [
      "uterine fibroid",
      "fibroid",
      "leiomyoma",
      "menorrhagia"
    ]
  },
  {
    "code": "D50.0",
    "name": "Iron deficiency anaemia secondary to blood loss (chronic)",
    "category": "Blood & Haematological",
    "keywords": [
      "iron deficiency anemia",
      "blood loss",
      "pallor",
      "fatigue"
    ]
  },
  {
    "code": "D50.8",
    "name": "Other iron deficiency anaemias",
    "category": "Blood & Haematological",
    "keywords": [
      "iron deficiency anemia",
      "nutritional anemia"
    ]
  },
  {
    "code": "D50.9",
    "name": "Iron deficiency anaemia, unspecified",
    "category": "Blood & Haematological",
    "keywords": [
      "anaemia",
      "anemia",
      "iron deficiency",
      "low hemoglobin",
      "ida",
      "pallor"
    ]
  },
  {
    "code": "D51.0",
    "name": "Vitamin B12 deficiency anaemia due to intrinsic factor deficiency (Pernicious anaemia)",
    "category": "Blood & Haematological",
    "keywords": [
      "b12 deficiency",
      "pernicious anemia",
      "macrocytic anemia"
    ]
  },
  {
    "code": "D51.9",
    "name": "Vitamin B12 deficiency anaemia, unspecified",
    "category": "Blood & Haematological",
    "keywords": [
      "b12 anemia",
      "vitamin b12 deficiency",
      "megaloblastic anemia"
    ]
  },
  {
    "code": "D52.9",
    "name": "Folate deficiency anaemia, unspecified",
    "category": "Blood & Haematological",
    "keywords": [
      "folate deficiency",
      "folic acid deficiency"
    ]
  },
  {
    "code": "D53.9",
    "name": "Nutritional anaemia, unspecified",
    "category": "Blood & Haematological",
    "keywords": [
      "nutritional anemia",
      "dietary deficiency"
    ]
  },
  {
    "code": "D56.0",
    "name": "Alpha thalassaemia",
    "category": "Blood & Haematological",
    "keywords": [
      "alpha thalassemia",
      "thalassaemia"
    ]
  },
  {
    "code": "D56.1",
    "name": "Beta thalassaemia",
    "category": "Blood & Haematological",
    "keywords": [
      "beta thalassemia",
      "thalassemia major",
      "thalassemia minor"
    ]
  },
  {
    "code": "D57.0",
    "name": "Sickle-cell anaemia with crisis",
    "category": "Blood & Haematological",
    "keywords": [
      "sickle cell crisis",
      "sickle cell anemia",
      "pain crisis"
    ]
  },
  {
    "code": "D57.1",
    "name": "Sickle-cell anaemia without crisis",
    "category": "Blood & Haematological",
    "keywords": [
      "sickle cell anemia",
      "sickling"
    ]
  },
  {
    "code": "D64.9",
    "name": "Anaemia, unspecified",
    "category": "Blood & Haematological",
    "keywords": [
      "anemia",
      "low hb",
      "pallor",
      "weakness"
    ]
  },
  {
    "code": "D69.3",
    "name": "Idiopathic thrombocytopenic purpura (ITP)",
    "category": "Blood & Haematological",
    "keywords": [
      "itp",
      "thrombocytopenia",
      "petechiae",
      "purpura"
    ]
  },
  {
    "code": "D69.6",
    "name": "Thrombocytopenia, unspecified",
    "category": "Blood & Haematological",
    "keywords": [
      "low platelets",
      "thrombocytopenia",
      "bleeding tendency"
    ]
  },
  {
    "code": "E01.2",
    "name": "Iodine-deficiency-related (endemic) goitre, unspecified",
    "category": "Endocrine & Metabolic",
    "keywords": [
      "goitre",
      "goiter",
      "iodine deficiency",
      "neck swelling"
    ]
  },
  {
    "code": "E03.9",
    "name": "Hypothyroidism, unspecified",
    "category": "Endocrine & Metabolic",
    "keywords": [
      "hypothyroidism",
      "thyroid",
      "low thyroid",
      "tsh high",
      "weight gain",
      "lethargy"
    ]
  },
  {
    "code": "E04.1",
    "name": "Non-toxic single thyroid nodule",
    "category": "Endocrine & Metabolic",
    "keywords": [
      "thyroid nodule",
      "solitary nodule"
    ]
  },
  {
    "code": "E04.2",
    "name": "Non-toxic multinodular goitre",
    "category": "Endocrine & Metabolic",
    "keywords": [
      "multinodular goiter",
      "mng"
    ]
  },
  {
    "code": "E05.0",
    "name": "Thyrotoxicosis with diffuse goitre (Graves' disease)",
    "category": "Endocrine & Metabolic",
    "keywords": [
      "graves disease",
      "hyperthyroidism",
      "thyrotoxicosis",
      "exophthalmos"
    ]
  },
  {
    "code": "E05.9",
    "name": "Thyrotoxicosis, unspecified (Hyperthyroidism)",
    "category": "Endocrine & Metabolic",
    "keywords": [
      "hyperthyroidism",
      "thyrotoxicosis",
      "weight loss",
      "palpitations",
      "tsh low"
    ]
  },
  {
    "code": "E06.3",
    "name": "Autoimmune thyroiditis (Hashimoto's thyroiditis)",
    "category": "Endocrine & Metabolic",
    "keywords": [
      "hashimotos thyroiditis",
      "autoimmune thyroid"
    ]
  },
  {
    "code": "E10.9",
    "name": "Type 1 diabetes mellitus without complications",
    "category": "Endocrine & Metabolic",
    "keywords": [
      "type 1 diabetes",
      "t1dm",
      "insulin dependent diabetes",
      "iddm"
    ]
  },
  {
    "code": "E11.0",
    "name": "Type 2 diabetes mellitus with coma (Hyperosmolar state)",
    "category": "Endocrine & Metabolic",
    "keywords": [
      "type 2 diabetes",
      "diabetic coma",
      "honk",
      "hhs"
    ]
  },
  {
    "code": "E11.1",
    "name": "Type 2 diabetes mellitus with ketoacidosis",
    "category": "Endocrine & Metabolic",
    "keywords": [
      "diabetic ketoacidosis",
      "dka",
      "ketosis"
    ]
  },
  {
    "code": "E11.2",
    "name": "Type 2 diabetes mellitus with renal complications (Diabetic nephropathy)",
    "category": "Endocrine & Metabolic",
    "keywords": [
      "diabetic nephropathy",
      "t2dm kidney",
      "microalbuminuria",
      "proteinuria"
    ]
  },
  {
    "code": "E11.3",
    "name": "Type 2 diabetes mellitus with ophthalmic complications (Diabetic retinopathy)",
    "category": "Endocrine & Metabolic",
    "keywords": [
      "diabetic retinopathy",
      "t2dm eye",
      "vision blur"
    ]
  },
  {
    "code": "E11.4",
    "name": "Type 2 diabetes mellitus with neurological complications (Diabetic neuropathy)",
    "category": "Endocrine & Metabolic",
    "keywords": [
      "diabetic neuropathy",
      "t2dm numbness",
      "burning feet",
      "paresthesia"
    ]
  },
  {
    "code": "E11.5",
    "name": "Type 2 diabetes mellitus with peripheral circulatory complications (Diabetic foot)",
    "category": "Endocrine & Metabolic",
    "keywords": [
      "diabetic foot",
      "diabetic ulcer",
      "peripheral vascular disease"
    ]
  },
  {
    "code": "E11.8",
    "name": "Type 2 diabetes mellitus with unspecified complications",
    "category": "Endocrine & Metabolic",
    "keywords": [
      "type 2 diabetes with complications",
      "sugar complicated"
    ]
  },
  {
    "code": "E11.9",
    "name": "Type 2 diabetes mellitus without complications",
    "category": "Endocrine & Metabolic",
    "keywords": [
      "diabetes",
      "type 2 diabetes",
      "t2dm",
      "sugar",
      "high sugar",
      "hyperglycemia",
      "niddm"
    ]
  },
  {
    "code": "E14.9",
    "name": "Unspecified diabetes mellitus without complications",
    "category": "Endocrine & Metabolic",
    "keywords": [
      "diabetes mellitus",
      "sugar",
      "diabetic"
    ]
  },
  {
    "code": "E16.2",
    "name": "Hypoglycaemia, unspecified",
    "category": "Endocrine & Metabolic",
    "keywords": [
      "hypoglycemia",
      "low blood sugar",
      "sweating shakiness",
      "insulin shock"
    ]
  },
  {
    "code": "E40",
    "name": "Kwashiorkor",
    "category": "Endocrine & Metabolic",
    "keywords": [
      "kwashiorkor",
      "protein malnutrition",
      "edema malnutrition"
    ]
  },
  {
    "code": "E41",
    "name": "Nutritional marasmus",
    "category": "Endocrine & Metabolic",
    "keywords": [
      "marasmus",
      "severe wasting",
      "malnutrition"
    ]
  },
  {
    "code": "E44.0",
    "name": "Moderate protein-energy malnutrition",
    "category": "Endocrine & Metabolic",
    "keywords": [
      "protein energy malnutrition",
      "pem",
      "underweight"
    ]
  },
  {
    "code": "E46",
    "name": "Unspecified protein-energy malnutrition",
    "category": "Endocrine & Metabolic",
    "keywords": [
      "malnutrition",
      "undernutrition",
      "wasting"
    ]
  },
  {
    "code": "E50.9",
    "name": "Vitamin A deficiency, unspecified",
    "category": "Endocrine & Metabolic",
    "keywords": [
      "vitamin a deficiency",
      "night blindness",
      "xerophthalmia",
      "bitot spots"
    ]
  },
  {
    "code": "E51.9",
    "name": "Thiamine deficiency, unspecified (Beriberi)",
    "category": "Endocrine & Metabolic",
    "keywords": [
      "beriberi",
      "thiamine deficiency",
      "vitamin b1"
    ]
  },
  {
    "code": "E52",
    "name": "Niacin deficiency [pellagra]",
    "category": "Endocrine & Metabolic",
    "keywords": [
      "pellagra",
      "niacin deficiency",
      "vitamin b3"
    ]
  },
  {
    "code": "E53.8",
    "name": "Deficiency of other specified B group vitamins",
    "category": "Endocrine & Metabolic",
    "keywords": [
      "vitamin b complex deficiency",
      "glossitis",
      "angular stomatitis",
      "cheilosis"
    ]
  },
  {
    "code": "E54",
    "name": "Ascorbic acid deficiency (Scurvy / Vitamin C deficiency)",
    "category": "Endocrine & Metabolic",
    "keywords": [
      "scurvy",
      "vitamin c deficiency",
      "bleeding gums"
    ]
  },
  {
    "code": "E55.0",
    "name": "Rickets, active",
    "category": "Endocrine & Metabolic",
    "keywords": [
      "rickets",
      "vitamin d deficiency",
      "bow legs",
      "rosary beads"
    ]
  },
  {
    "code": "E55.9",
    "name": "Vitamin D deficiency, unspecified",
    "category": "Endocrine & Metabolic",
    "keywords": [
      "vitamin d deficiency",
      "hypovitaminosis d",
      "bone pain"
    ]
  },
  {
    "code": "E58",
    "name": "Dietary calcium deficiency",
    "category": "Endocrine & Metabolic",
    "keywords": [
      "calcium deficiency",
      "hypocalcemia"
    ]
  },
  {
    "code": "E66.0",
    "name": "Obesity due to excess calories",
    "category": "Endocrine & Metabolic",
    "keywords": [
      "obesity",
      "overweight",
      "high bmi"
    ]
  },
  {
    "code": "E78.0",
    "name": "Pure hypercholesterolaemia",
    "category": "Endocrine & Metabolic",
    "keywords": [
      "hypercholesterolemia",
      "high cholesterol",
      "lipid disorder"
    ]
  },
  {
    "code": "E78.1",
    "name": "Pure hyperglyceridaemia (Hypertriglyceridaemia)",
    "category": "Endocrine & Metabolic",
    "keywords": [
      "hypertriglyceridemia",
      "high triglycerides"
    ]
  },
  {
    "code": "E78.2",
    "name": "Mixed hyperlipidaemia",
    "category": "Endocrine & Metabolic",
    "keywords": [
      "dyslipidemia",
      "hyperlipidemia",
      "high lipid"
    ]
  },
  {
    "code": "E78.5",
    "name": "Hyperlipidaemia, unspecified",
    "category": "Endocrine & Metabolic",
    "keywords": [
      "dyslipidaemia",
      "cholesterol",
      "lipid abnormalities"
    ]
  },
  {
    "code": "E79.0",
    "name": "Hyperuricaemia without signs of inflammatory arthritis and tophaceous disease",
    "category": "Endocrine & Metabolic",
    "keywords": [
      "hyperuricemia",
      "high uric acid",
      "asymptomatic uric acid"
    ]
  },
  {
    "code": "F03",
    "name": "Unspecified dementia",
    "category": "Mental & Behavioural",
    "keywords": [
      "dementia",
      "memory loss",
      "cognitive decline"
    ]
  },
  {
    "code": "F10.1",
    "name": "Mental and behavioural disorders due to use of alcohol: harmful use",
    "category": "Mental & Behavioural",
    "keywords": [
      "alcohol abuse",
      "harmful drinking"
    ]
  },
  {
    "code": "F10.2",
    "name": "Mental and behavioural disorders due to use of alcohol: dependence syndrome",
    "category": "Mental & Behavioural",
    "keywords": [
      "alcohol dependence",
      "alcoholism",
      "alcohol addiction",
      "withdrawal"
    ]
  },
  {
    "code": "F17.1",
    "name": "Mental and behavioural disorders due to use of tobacco: harmful use",
    "category": "Mental & Behavioural",
    "keywords": [
      "tobacco use",
      "smoking",
      "beedi chewing",
      "khaini"
    ]
  },
  {
    "code": "F17.2",
    "name": "Mental and behavioural disorders due to use of tobacco: dependence syndrome",
    "category": "Mental & Behavioural",
    "keywords": [
      "nicotine dependence",
      "tobacco addiction",
      "smoker"
    ]
  },
  {
    "code": "F20.9",
    "name": "Schizophrenia, unspecified",
    "category": "Mental & Behavioural",
    "keywords": [
      "schizophrenia",
      "psychosis",
      "hallucinations",
      "delusions"
    ]
  },
  {
    "code": "F31.9",
    "name": "Bipolar affective disorder, unspecified",
    "category": "Mental & Behavioural",
    "keywords": [
      "bipolar disorder",
      "mania",
      "mood swings"
    ]
  },
  {
    "code": "F32.0",
    "name": "Mild depressive episode",
    "category": "Mental & Behavioural",
    "keywords": [
      "mild depression",
      "sadness",
      "low mood"
    ]
  },
  {
    "code": "F32.1",
    "name": "Moderate depressive episode",
    "category": "Mental & Behavioural",
    "keywords": [
      "depression",
      "depressive episode",
      "loss of interest"
    ]
  },
  {
    "code": "F32.9",
    "name": "Depressive episode, unspecified",
    "category": "Mental & Behavioural",
    "keywords": [
      "depression",
      "depressed mood",
      "anhedonia"
    ]
  },
  {
    "code": "F41.0",
    "name": "Panic disorder [episodic paroxysmal anxiety]",
    "category": "Mental & Behavioural",
    "keywords": [
      "panic attack",
      "panic disorder",
      "sudden fear",
      "palpitations fear"
    ]
  },
  {
    "code": "F41.1",
    "name": "Generalized anxiety disorder",
    "category": "Mental & Behavioural",
    "keywords": [
      "anxiety",
      "generalized anxiety",
      "gad",
      "nervousness",
      "restlessness"
    ]
  },
  {
    "code": "F41.2",
    "name": "Mixed anxiety and depressive disorder",
    "category": "Mental & Behavioural",
    "keywords": [
      "anxiety depression",
      "mixed neurosis"
    ]
  },
  {
    "code": "F43.0",
    "name": "Acute stress reaction",
    "category": "Mental & Behavioural",
    "keywords": [
      "acute stress",
      "shock",
      "emotional crisis"
    ]
  },
  {
    "code": "F45.0",
    "name": "Somatization disorder",
    "category": "Mental & Behavioural",
    "keywords": [
      "somatoform",
      "psychosomatic",
      "medically unexplained symptoms"
    ]
  },
  {
    "code": "F51.0",
    "name": "Nonorganic insomnia",
    "category": "Mental & Behavioural",
    "keywords": [
      "insomnia",
      "sleeplessness",
      "sleep trouble",
      "disturbed sleep"
    ]
  },
  {
    "code": "G00.9",
    "name": "Bacterial meningitis, unspecified",
    "category": "Nervous System",
    "keywords": [
      "meningitis",
      "pyogenic meningitis",
      "neck stiffness",
      "photophobia"
    ]
  },
  {
    "code": "G03.9",
    "name": "Meningitis, unspecified (Aseptic / Viral meningitis)",
    "category": "Nervous System",
    "keywords": [
      "viral meningitis",
      "aseptic meningitis"
    ]
  },
  {
    "code": "G20",
    "name": "Parkinson's disease",
    "category": "Nervous System",
    "keywords": [
      "parkinsons",
      "tremor",
      "rigidity",
      "bradykinesia",
      "pill rolling"
    ]
  },
  {
    "code": "G30.9",
    "name": "Alzheimer's disease, unspecified",
    "category": "Nervous System",
    "keywords": [
      "alzheimers",
      "dementia",
      "memory loss"
    ]
  },
  {
    "code": "G40.3",
    "name": "Generalized idiopathic epilepsy and epileptic syndromes",
    "category": "Nervous System",
    "keywords": [
      "epilepsy",
      "grand mal",
      "tonic clonic",
      "fits",
      "convulsions",
      "seizures"
    ]
  },
  {
    "code": "G40.9",
    "name": "Epilepsy, unspecified",
    "category": "Nervous System",
    "keywords": [
      "epilepsy",
      "seizure disorder",
      "fits",
      "convulsions"
    ]
  },
  {
    "code": "G43.0",
    "name": "Migraine without aura",
    "category": "Nervous System",
    "keywords": [
      "migraine",
      "hemicrania",
      "unilateral headache",
      "throbbing headache",
      "nausea"
    ]
  },
  {
    "code": "G43.9",
    "name": "Migraine, unspecified",
    "category": "Nervous System",
    "keywords": [
      "migraine headache",
      "vascular headache"
    ]
  },
  {
    "code": "G44.0",
    "name": "Cluster headache syndrome",
    "category": "Nervous System",
    "keywords": [
      "cluster headache",
      "periorbital headache"
    ]
  },
  {
    "code": "G44.2",
    "name": "Tension-type headache",
    "category": "Nervous System",
    "keywords": [
      "tension headache",
      "band-like headache",
      "stress headache"
    ]
  },
  {
    "code": "G45.9",
    "name": "Transient cerebral ischaemic attack, unspecified (TIA)",
    "category": "Nervous System",
    "keywords": [
      "tia",
      "mini stroke",
      "transient ischemic attack"
    ]
  },
  {
    "code": "G51.0",
    "name": "Bell's palsy (Facial nerve palsy)",
    "category": "Nervous System",
    "keywords": [
      "bells palsy",
      "facial palsy",
      "facial drooping",
      "lower motor neuron 7th nerve"
    ]
  },
  {
    "code": "G56.0",
    "name": "Carpal tunnel syndrome",
    "category": "Nervous System",
    "keywords": [
      "carpal tunnel",
      "median nerve compression",
      "tingling hand"
    ]
  },
  {
    "code": "G62.9",
    "name": "Peripheral neuropathy, unspecified",
    "category": "Nervous System",
    "keywords": [
      "neuropathy",
      "peripheral neuropathy",
      "numbness",
      "tingling feet",
      "burning sensation"
    ]
  },
  {
    "code": "G81.9",
    "name": "Hemiplegia, unspecified",
    "category": "Nervous System",
    "keywords": [
      "hemiplegia",
      "paralysis one side",
      "stroke weakness"
    ]
  },
  {
    "code": "H00.0",
    "name": "Hordeolum and other deep inflammation of eyelid (Stye)",
    "category": "Eye & Adnexa",
    "keywords": [
      "stye",
      "hordeolum",
      "eyelid boil",
      "painful eyelid"
    ]
  },
  {
    "code": "H00.1",
    "name": "Chalazion",
    "category": "Eye & Adnexa",
    "keywords": [
      "chalazion",
      "meibomian cyst",
      "eyelid swelling"
    ]
  },
  {
    "code": "H01.0",
    "name": "Blepharitis",
    "category": "Eye & Adnexa",
    "keywords": [
      "blepharitis",
      "eyelid crusting",
      "itchy eyelids"
    ]
  },
  {
    "code": "H10.0",
    "name": "Mucopurulent conjunctivitis",
    "category": "Eye & Adnexa",
    "keywords": [
      "bacterial conjunctivitis",
      "eye discharge",
      "sticky eyes"
    ]
  },
  {
    "code": "H10.1",
    "name": "Acute atopic conjunctivitis",
    "category": "Eye & Adnexa",
    "keywords": [
      "allergic conjunctivitis",
      "itchy red eyes",
      "watery eyes"
    ]
  },
  {
    "code": "H10.9",
    "name": "Conjunctivitis, unspecified (Pink eye / Madras eye)",
    "category": "Eye & Adnexa",
    "keywords": [
      "conjunctivitis",
      "madras eye",
      "pink eye",
      "red eye",
      "eye infection"
    ]
  },
  {
    "code": "H16.0",
    "name": "Corneal ulcer",
    "category": "Eye & Adnexa",
    "keywords": [
      "corneal ulcer",
      "keratitis",
      "eye pain redness"
    ]
  },
  {
    "code": "H25.9",
    "name": "Senile cataract, unspecified",
    "category": "Eye & Adnexa",
    "keywords": [
      "cataract",
      "senile cataract",
      "motiabindu",
      "cloudy lens",
      "diminished vision"
    ]
  },
  {
    "code": "H26.9",
    "name": "Cataract, unspecified",
    "category": "Eye & Adnexa",
    "keywords": [
      "cataract",
      "blurred vision",
      "white reflex"
    ]
  },
  {
    "code": "H40.1",
    "name": "Primary open-angle glaucoma",
    "category": "Eye & Adnexa",
    "keywords": [
      "open angle glaucoma",
      "high intraocular pressure",
      "glaucoma"
    ]
  },
  {
    "code": "H40.2",
    "name": "Primary angle-closure glaucoma",
    "category": "Eye & Adnexa",
    "keywords": [
      "angle closure glaucoma",
      "acute glaucoma",
      "halos",
      "severe eye pain"
    ]
  },
  {
    "code": "H40.9",
    "name": "Glaucoma, unspecified",
    "category": "Eye & Adnexa",
    "keywords": [
      "glaucoma",
      "iop high",
      "tunnel vision"
    ]
  },
  {
    "code": "H52.0",
    "name": "Hypermetropia (Farsightedness)",
    "category": "Eye & Adnexa",
    "keywords": [
      "hypermetropia",
      "long sightedness"
    ]
  },
  {
    "code": "H52.1",
    "name": "Myopia (Nearsightedness)",
    "category": "Eye & Adnexa",
    "keywords": [
      "myopia",
      "short sightedness",
      "distance blur"
    ]
  },
  {
    "code": "H52.2",
    "name": "Astigmatism",
    "category": "Eye & Adnexa",
    "keywords": [
      "astigmatism",
      "cylindrical error"
    ]
  },
  {
    "code": "H52.4",
    "name": "Presbyopia",
    "category": "Eye & Adnexa",
    "keywords": [
      "presbyopia",
      "reading glass power",
      "near vision blur"
    ]
  },
  {
    "code": "H57.1",
    "name": "Ocular pain (Eye strain / Asthenopia)",
    "category": "Eye & Adnexa",
    "keywords": [
      "eye pain",
      "eye strain",
      "tired eyes"
    ]
  },
  {
    "code": "H60.9",
    "name": "Otitis externa, unspecified (Swimmer's ear)",
    "category": "Ear & Mastoid",
    "keywords": [
      "otitis externa",
      "ear canal infection",
      "ear discharge",
      "ear pain"
    ]
  },
  {
    "code": "H61.2",
    "name": "Impacted cerumen (Ear wax impaction)",
    "category": "Ear & Mastoid",
    "keywords": [
      "ear wax",
      "impacted wax",
      "blocked ear",
      "ear syringing"
    ]
  },
  {
    "code": "H65.0",
    "name": "Acute serous otitis media",
    "category": "Ear & Mastoid",
    "keywords": [
      "otitis media with effusion",
      "fluid in ear",
      "blocked ear"
    ]
  },
  {
    "code": "H66.0",
    "name": "Acute suppurative otitis media (ASOM)",
    "category": "Ear & Mastoid",
    "keywords": [
      "asom",
      "acute otitis media",
      "ear ache",
      "pus in ear",
      "ear discharge"
    ]
  },
  {
    "code": "H66.9",
    "name": "Otitis media, unspecified (Chronic suppurative otitis media / CSOM)",
    "category": "Ear & Mastoid",
    "keywords": [
      "csom",
      "chronic ear discharge",
      "eardrum perforation",
      "runny ear"
    ]
  },
  {
    "code": "H72.9",
    "name": "Perforation of tympanic membrane, unspecified",
    "category": "Ear & Mastoid",
    "keywords": [
      "perforated eardrum",
      "tympanic perforation"
    ]
  },
  {
    "code": "H81.0",
    "name": "Meniere's disease",
    "category": "Ear & Mastoid",
    "keywords": [
      "menieres disease",
      "endolymphatic hydrops",
      "tinnitus vertigo"
    ]
  },
  {
    "code": "H81.1",
    "name": "Benign paroxysmal positional vertigo (BPPV)",
    "category": "Ear & Mastoid",
    "keywords": [
      "bppv",
      "positional vertigo",
      "spinning sensation"
    ]
  },
  {
    "code": "H81.4",
    "name": "Vertigo of central origin",
    "category": "Ear & Mastoid",
    "keywords": [
      "vertigo",
      "giddiness",
      "chakkar",
      "dizziness"
    ]
  },
  {
    "code": "H90.3",
    "name": "Sensorineural hearing loss, bilateral",
    "category": "Ear & Mastoid",
    "keywords": [
      "hearing loss",
      "deafness",
      "presbycusis",
      "snhl"
    ]
  },
  {
    "code": "H91.9",
    "name": "Hearing loss, unspecified",
    "category": "Ear & Mastoid",
    "keywords": [
      "hard of hearing",
      "hearing impairment"
    ]
  },
  {
    "code": "H92.0",
    "name": "Otalgia (Earache)",
    "category": "Ear & Mastoid",
    "keywords": [
      "ear pain",
      "earache",
      "otalgia"
    ]
  },
  {
    "code": "H93.1",
    "name": "Tinnitus",
    "category": "Ear & Mastoid",
    "keywords": [
      "tinnitus",
      "ringing in ear",
      "buzzing ear"
    ]
  },
  {
    "code": "I00",
    "name": "Rheumatic fever without mention of heart involvement",
    "category": "Circulatory System",
    "keywords": [
      "rheumatic fever",
      "migratory polyarthritis",
      "strep throat"
    ]
  },
  {
    "code": "I05.0",
    "name": "Mitral stenosis (Rheumatic mitral stenosis)",
    "category": "Circulatory System",
    "keywords": [
      "mitral stenosis",
      "rhd",
      "rheumatic heart disease",
      "murmur"
    ]
  },
  {
    "code": "I05.9",
    "name": "Mitral valve disease, unspecified (Rheumatic heart disease)",
    "category": "Circulatory System",
    "keywords": [
      "rheumatic heart disease",
      "rhd",
      "valvular heart disease"
    ]
  },
  {
    "code": "I10",
    "name": "Essential (primary) hypertension",
    "category": "Circulatory System",
    "keywords": [
      "hypertension",
      "high blood pressure",
      "htn",
      "bp",
      "essential hypertension",
      "high bp"
    ]
  },
  {
    "code": "I11.9",
    "name": "Hypertensive heart disease without heart failure",
    "category": "Circulatory System",
    "keywords": [
      "hypertensive heart disease",
      "lvh",
      "left ventricular hypertrophy"
    ]
  },
  {
    "code": "I15.9",
    "name": "Secondary hypertension, unspecified",
    "category": "Circulatory System",
    "keywords": [
      "secondary hypertension",
      "renal hypertension"
    ]
  },
  {
    "code": "I20.0",
    "name": "Unstable angina",
    "category": "Circulatory System",
    "keywords": [
      "unstable angina",
      "acs",
      "acute coronary syndrome",
      "chest pain"
    ]
  },
  {
    "code": "I20.9",
    "name": "Angina pectoris, unspecified (Stable angina)",
    "category": "Circulatory System",
    "keywords": [
      "angina",
      "angina pectoris",
      "chest tightness",
      "exertional chest pain"
    ]
  },
  {
    "code": "I21.9",
    "name": "Acute myocardial infarction, unspecified (Heart attack)",
    "category": "Circulatory System",
    "keywords": [
      "myocardial infarction",
      "heart attack",
      "mi",
      "stemi",
      "nstemi",
      "coronary thrombosis"
    ]
  },
  {
    "code": "I25.1",
    "name": "Atherosclerotic heart disease (Coronary artery disease / CAD)",
    "category": "Circulatory System",
    "keywords": [
      "coronary artery disease",
      "cad",
      "ihd",
      "ischemic heart disease"
    ]
  },
  {
    "code": "I25.9",
    "name": "Chronic ischaemic heart disease, unspecified",
    "category": "Circulatory System",
    "keywords": [
      "ischemic heart disease",
      "ihd",
      "cad"
    ]
  },
  {
    "code": "I27.9",
    "name": "Pulmonary heart disease, unspecified (Cor pulmonale)",
    "category": "Circulatory System",
    "keywords": [
      "cor pulmonale",
      "pulmonary hypertension"
    ]
  },
  {
    "code": "I48.9",
    "name": "Atrial fibrillation and atrial flutter, unspecified",
    "category": "Circulatory System",
    "keywords": [
      "atrial fibrillation",
      "afib",
      "irregular pulse",
      "flutter"
    ]
  },
  {
    "code": "I49.9",
    "name": "Cardiac arrhythmia, unspecified",
    "category": "Circulatory System",
    "keywords": [
      "arrhythmia",
      "palpitations",
      "irregular heartbeat",
      "tachycardia"
    ]
  },
  {
    "code": "I50.0",
    "name": "Congestive heart failure (CHF)",
    "category": "Circulatory System",
    "keywords": [
      "congestive heart failure",
      "chf",
      "bipedal edema",
      "orthopnea",
      "pnd"
    ]
  },
  {
    "code": "I50.9",
    "name": "Heart failure, unspecified",
    "category": "Circulatory System",
    "keywords": [
      "heart failure",
      "cardiac failure",
      "fluid overload"
    ]
  },
  {
    "code": "I64",
    "name": "Stroke, not specified as haemorrhage or infarction (CVA)",
    "category": "Circulatory System",
    "keywords": [
      "stroke",
      "cva",
      "cerebrovascular accident",
      "paralysis",
      "slurred speech"
    ]
  },
  {
    "code": "I63.9",
    "name": "Cerebral infarction, unspecified (Ischaemic stroke)",
    "category": "Circulatory System",
    "keywords": [
      "ischemic stroke",
      "brain stroke",
      "infarct"
    ]
  },
  {
    "code": "I70.9",
    "name": "Generalized and unspecified atherosclerosis",
    "category": "Circulatory System",
    "keywords": [
      "atherosclerosis",
      "arteriosclerosis",
      "hardening of arteries"
    ]
  },
  {
    "code": "I73.9",
    "name": "Peripheral vascular disease, unspecified (PVD)",
    "category": "Circulatory System",
    "keywords": [
      "peripheral vascular disease",
      "pvd",
      "pad",
      "intermittent claudication",
      "leg pain"
    ]
  },
  {
    "code": "I80.2",
    "name": "Phlebitis and thrombophlebitis of other deep vessels of lower extremities (DVT)",
    "category": "Circulatory System",
    "keywords": [
      "dvt",
      "deep vein thrombosis",
      "swollen calf",
      "leg thrombosis"
    ]
  },
  {
    "code": "I83.9",
    "name": "Varicose veins of lower extremities without ulcer or inflammation",
    "category": "Circulatory System",
    "keywords": [
      "varicose veins",
      "tortuous veins",
      "leg heaviness"
    ]
  },
  {
    "code": "I84.9",
    "name": "Haemorrhoids without complication, unspecified (Piles)",
    "category": "Circulatory System",
    "keywords": [
      "haemorrhoids",
      "hemorrhoids",
      "piles",
      "bleeding per rectum",
      "anal mass"
    ]
  },
  {
    "code": "I95.9",
    "name": "Hypotension, unspecified",
    "category": "Circulatory System",
    "keywords": [
      "hypotension",
      "low blood pressure",
      "low bp",
      "postural drop"
    ]
  },
  {
    "code": "J00",
    "name": "Acute nasopharyngitis [common cold]",
    "category": "Respiratory System",
    "keywords": [
      "common cold",
      "coryza",
      "runny nose",
      "rhinorrhea",
      "cold",
      "sneezing",
      "nasopharyngitis"
    ]
  },
  {
    "code": "J01.9",
    "name": "Acute sinusitis, unspecified",
    "category": "Respiratory System",
    "keywords": [
      "sinusitis",
      "acute sinusitis",
      "facial pain",
      "sinus headache",
      "postnasal drip"
    ]
  },
  {
    "code": "J02.0",
    "name": "Streptococcal pharyngitis (Strep throat)",
    "category": "Respiratory System",
    "keywords": [
      "strep throat",
      "streptococcal pharyngitis",
      "sore throat",
      "fever"
    ]
  },
  {
    "code": "J02.9",
    "name": "Acute pharyngitis, unspecified (Sore throat)",
    "category": "Respiratory System",
    "keywords": [
      "pharyngitis",
      "sore throat",
      "throat pain",
      "throat infection",
      "pain swallowing"
    ]
  },
  {
    "code": "J03.0",
    "name": "Streptococcal tonsillitis",
    "category": "Respiratory System",
    "keywords": [
      "tonsillitis",
      "strep tonsillitis",
      "exudative tonsils"
    ]
  },
  {
    "code": "J03.9",
    "name": "Acute tonsillitis, unspecified",
    "category": "Respiratory System",
    "keywords": [
      "tonsillitis",
      "acute tonsillitis",
      "swollen tonsils",
      "pus on tonsils"
    ]
  },
  {
    "code": "J04.0",
    "name": "Acute laryngitis (Croup / Hoarseness)",
    "category": "Respiratory System",
    "keywords": [
      "laryngitis",
      "hoarse voice",
      "loss of voice",
      "croup"
    ]
  },
  {
    "code": "J06.9",
    "name": "Acute upper respiratory infection, unspecified (URTI)",
    "category": "Respiratory System",
    "keywords": [
      "urti",
      "upper respiratory tract infection",
      "acute respiratory infection",
      "uri",
      "cough cold"
    ]
  },
  {
    "code": "J10.1",
    "name": "Influenza with other respiratory manifestations, other influenza virus identified",
    "category": "Respiratory System",
    "keywords": [
      "influenza",
      "flu",
      "h1n1",
      "swine flu"
    ]
  },
  {
    "code": "J11.1",
    "name": "Influenza with other respiratory manifestations, virus not identified",
    "category": "Respiratory System",
    "keywords": [
      "influenza",
      "flu",
      "seasonal flu",
      "viral fever"
    ]
  },
  {
    "code": "J12.9",
    "name": "Viral pneumonia, unspecified",
    "category": "Respiratory System",
    "keywords": [
      "viral pneumonia",
      "chest infection",
      "infiltrates"
    ]
  },
  {
    "code": "J15.9",
    "name": "Bacterial pneumonia, unspecified",
    "category": "Respiratory System",
    "keywords": [
      "bacterial pneumonia",
      "consolidation",
      "productive cough"
    ]
  },
  {
    "code": "J18.0",
    "name": "Bronchopneumonia, unspecified",
    "category": "Respiratory System",
    "keywords": [
      "bronchopneumonia",
      "crepitations",
      "chest congestion"
    ]
  },
  {
    "code": "J18.9",
    "name": "Pneumonia, unspecified",
    "category": "Respiratory System",
    "keywords": [
      "pneumonia",
      "lower respiratory tract infection",
      "lrti",
      "chest infection",
      "fever cough"
    ]
  },
  {
    "code": "J20.9",
    "name": "Acute bronchitis, unspecified",
    "category": "Respiratory System",
    "keywords": [
      "acute bronchitis",
      "bronchitis",
      "chest cold",
      "cough sputum"
    ]
  },
  {
    "code": "J21.9",
    "name": "Acute bronchiolitis, unspecified",
    "category": "Respiratory System",
    "keywords": [
      "bronchiolitis",
      "infant wheeze",
      "rsv"
    ]
  },
  {
    "code": "J22",
    "name": "Unspecified acute lower respiratory infection (LRTI)",
    "category": "Respiratory System",
    "keywords": [
      "lrti",
      "lower respiratory infection",
      "chest infection"
    ]
  },
  {
    "code": "J30.1",
    "name": "Allergic rhinitis due to pollen",
    "category": "Respiratory System",
    "keywords": [
      "hay fever",
      "allergic rhinitis",
      "pollen allergy"
    ]
  },
  {
    "code": "J30.4",
    "name": "Allergic rhinitis, unspecified",
    "category": "Respiratory System",
    "keywords": [
      "allergic rhinitis",
      "sneezing",
      "nasal allergy",
      "morning sneezing",
      "dust allergy"
    ]
  },
  {
    "code": "J32.9",
    "name": "Chronic sinusitis, unspecified",
    "category": "Respiratory System",
    "keywords": [
      "chronic sinusitis",
      "chronic sinus",
      "nasal congestion"
    ]
  },
  {
    "code": "J33.9",
    "name": "Nasal polyp, unspecified",
    "category": "Respiratory System",
    "keywords": [
      "nasal polyp",
      "nasal obstruction",
      "fleshy mass nose"
    ]
  },
  {
    "code": "J35.0",
    "name": "Chronic tonsillitis",
    "category": "Respiratory System",
    "keywords": [
      "chronic tonsillitis",
      "recurrent tonsillitis"
    ]
  },
  {
    "code": "J35.2",
    "name": "Hypertrophy of adenoids",
    "category": "Respiratory System",
    "keywords": [
      "adenoid hypertrophy",
      "adenoids",
      "mouth breathing",
      "snoring"
    ]
  },
  {
    "code": "J40",
    "name": "Bronchitis, not specified as acute or chronic",
    "category": "Respiratory System",
    "keywords": [
      "bronchitis",
      "cough"
    ]
  },
  {
    "code": "J42",
    "name": "Unspecified chronic bronchitis",
    "category": "Respiratory System",
    "keywords": [
      "chronic bronchitis",
      "smokers cough",
      "mucus"
    ]
  },
  {
    "code": "J44.0",
    "name": "Chronic obstructive pulmonary disease with acute lower respiratory infection",
    "category": "Respiratory System",
    "keywords": [
      "copd with infection",
      "copd exacerbation"
    ]
  },
  {
    "code": "J44.1",
    "name": "Chronic obstructive pulmonary disease with acute exacerbation, unspecified",
    "category": "Respiratory System",
    "keywords": [
      "aecoopd",
      "copd exacerbation",
      "acute exacerbation"
    ]
  },
  {
    "code": "J44.9",
    "name": "Chronic obstructive pulmonary disease, unspecified (COPD)",
    "category": "Respiratory System",
    "keywords": [
      "copd",
      "chronic obstructive pulmonary disease",
      "chronic bronchitis",
      "emphysema",
      "smokers lung"
    ]
  },
  {
    "code": "J45.0",
    "name": "Predominantly allergic asthma",
    "category": "Respiratory System",
    "keywords": [
      "allergic asthma",
      "extrinsic asthma",
      "dust wheeze"
    ]
  },
  {
    "code": "J45.9",
    "name": "Asthma, unspecified (Bronchial asthma)",
    "category": "Respiratory System",
    "keywords": [
      "asthma",
      "bronchial asthma",
      "wheezing",
      "breathlessness",
      "inhaler",
      "rhonchi"
    ]
  },
  {
    "code": "J46",
    "name": "Status asthmaticus (Severe acute asthma)",
    "category": "Respiratory System",
    "keywords": [
      "status asthmaticus",
      "acute severe asthma",
      "severe wheezing"
    ]
  },
  {
    "code": "J47",
    "name": "Bronchiectasis",
    "category": "Respiratory System",
    "keywords": [
      "bronchiectasis",
      "copious sputum",
      "foul smelling sputum"
    ]
  },
  {
    "code": "J90",
    "name": "Pleural effusion, not elsewhere classified",
    "category": "Respiratory System",
    "keywords": [
      "pleural effusion",
      "fluid in lung",
      "tuberculous effusion"
    ]
  },
  {
    "code": "K02.9",
    "name": "Dental caries, unspecified (Tooth decay)",
    "category": "Digestive System",
    "keywords": [
      "dental caries",
      "tooth decay",
      "cavity",
      "toothache"
    ]
  },
  {
    "code": "K04.7",
    "name": "Periapical abscess without sinus (Dental abscess)",
    "category": "Digestive System",
    "keywords": [
      "tooth abscess",
      "dental abscess",
      "swollen gum"
    ]
  },
  {
    "code": "K05.0",
    "name": "Acute gingivitis",
    "category": "Digestive System",
    "keywords": [
      "gingivitis",
      "bleeding gums",
      "gum infection"
    ]
  },
  {
    "code": "K05.3",
    "name": "Chronic periodontitis",
    "category": "Digestive System",
    "keywords": [
      "periodontitis",
      "pyorrhea",
      "loose teeth",
      "bad breath"
    ]
  },
  {
    "code": "K12.0",
    "name": "Recurrent aphthous stomatitis (Mouth ulcers)",
    "category": "Digestive System",
    "keywords": [
      "mouth ulcers",
      "aphthous ulcer",
      "stomatitis",
      "canker sore"
    ]
  },
  {
    "code": "K21.0",
    "name": "Gastro-oesophageal reflux disease with oesophagitis",
    "category": "Digestive System",
    "keywords": [
      "gerd",
      "reflux esophagitis",
      "heartburn",
      "acid reflux"
    ]
  },
  {
    "code": "K21.9",
    "name": "Gastro-oesophageal reflux disease without oesophagitis (GERD)",
    "category": "Digestive System",
    "keywords": [
      "gerd",
      "acid reflux",
      "heartburn",
      "sour belching",
      "acidity"
    ]
  },
  {
    "code": "K25.9",
    "name": "Gastric ulcer, unspecified",
    "category": "Digestive System",
    "keywords": [
      "gastric ulcer",
      "stomach ulcer",
      "postprandial pain"
    ]
  },
  {
    "code": "K26.9",
    "name": "Duodenal ulcer, unspecified",
    "category": "Digestive System",
    "keywords": [
      "duodenal ulcer",
      "hunger pain",
      "night pain epigastric"
    ]
  },
  {
    "code": "K27.9",
    "name": "Peptic ulcer, site unspecified (PUD)",
    "category": "Digestive System",
    "keywords": [
      "peptic ulcer",
      "pud",
      "ulcer pain",
      "epigastric burning"
    ]
  },
  {
    "code": "K29.1",
    "name": "Other acute gastritis",
    "category": "Digestive System",
    "keywords": [
      "acute gastritis",
      "stomach irritation",
      "nsaid gastritis"
    ]
  },
  {
    "code": "K29.7",
    "name": "Gastritis, unspecified",
    "category": "Digestive System",
    "keywords": [
      "gastritis",
      "acidity",
      "burning epigastrium",
      "gas trouble"
    ]
  },
  {
    "code": "K30",
    "name": "Dyspepsia (Indigestion)",
    "category": "Digestive System",
    "keywords": [
      "dyspepsia",
      "indigestion",
      "bloating",
      "gas",
      "belching",
      "fullness"
    ]
  },
  {
    "code": "K35.8",
    "name": "Acute appendicitis, other and unspecified",
    "category": "Digestive System",
    "keywords": [
      "appendicitis",
      "right lower quadrant pain",
      "rif pain",
      "acute abdomen"
    ]
  },
  {
    "code": "K40.9",
    "name": "Unilateral inguinal hernia, without obstruction or gangrene",
    "category": "Digestive System",
    "keywords": [
      "inguinal hernia",
      "hernia",
      "groin swelling"
    ]
  },
  {
    "code": "K42.9",
    "name": "Umbilical hernia without obstruction or gangrene",
    "category": "Digestive System",
    "keywords": [
      "umbilical hernia",
      "navel swelling"
    ]
  },
  {
    "code": "K43.9",
    "name": "Ventral hernia without obstruction or gangrene (Incisional hernia)",
    "category": "Digestive System",
    "keywords": [
      "incisional hernia",
      "ventral hernia"
    ]
  },
  {
    "code": "K50.9",
    "name": "Crohn's disease, unspecified",
    "category": "Digestive System",
    "keywords": [
      "crohns disease",
      "inflammatory bowel disease",
      "ibd"
    ]
  },
  {
    "code": "K51.9",
    "name": "Ulcerative colitis, unspecified",
    "category": "Digestive System",
    "keywords": [
      "ulcerative colitis",
      "ibd",
      "bloody diarrhea"
    ]
  },
  {
    "code": "K58.0",
    "name": "Irritable bowel syndrome with diarrhoea (IBS-D)",
    "category": "Digestive System",
    "keywords": [
      "ibs",
      "irritable bowel syndrome",
      "diarrhea-predominant ibs"
    ]
  },
  {
    "code": "K58.9",
    "name": "Irritable bowel syndrome without diarrhoea (IBS)",
    "category": "Digestive System",
    "keywords": [
      "ibs",
      "irritable bowel syndrome",
      "crampy abdominal pain",
      "mucus stool"
    ]
  },
  {
    "code": "K59.0",
    "name": "Constipation",
    "category": "Digestive System",
    "keywords": [
      "constipation",
      "hard stools",
      "straining",
      "bowel irregularity"
    ]
  },
  {
    "code": "K60.0",
    "name": "Acute anal fissure",
    "category": "Digestive System",
    "keywords": [
      "anal fissure",
      "fissure in ano",
      "pain defecation",
      "streak blood stool"
    ]
  },
  {
    "code": "K60.2",
    "name": "Anal fissure, unspecified",
    "category": "Digestive System",
    "keywords": [
      "fissure",
      "painful bowel movement"
    ]
  },
  {
    "code": "K60.3",
    "name": "Anal fistula (Fistula-in-ano)",
    "category": "Digestive System",
    "keywords": [
      "anal fistula",
      "fistula in ano",
      "perianal discharge"
    ]
  },
  {
    "code": "K61.0",
    "name": "Anal abscess (Perianal abscess)",
    "category": "Digestive System",
    "keywords": [
      "perianal abscess",
      "anal boil",
      "perianal swelling"
    ]
  },
  {
    "code": "K70.3",
    "name": "Alcoholic cirrhosis of liver",
    "category": "Digestive System",
    "keywords": [
      "alcoholic cirrhosis",
      "liver cirrhosis",
      "portal hypertension",
      "alcohol liver"
    ]
  },
  {
    "code": "K71.9",
    "name": "Toxic liver disease, unspecified (Drug-induced liver injury)",
    "category": "Digestive System",
    "keywords": [
      "drug induced hepatitis",
      "dili",
      "toxic hepatitis"
    ]
  },
  {
    "code": "K74.6",
    "name": "Other and unspecified cirrhosis of liver",
    "category": "Digestive System",
    "keywords": [
      "liver cirrhosis",
      "cirrhosis",
      "chronic liver disease",
      "cld",
      "ascites"
    ]
  },
  {
    "code": "K76.0",
    "name": "Fatty (change of) liver, not elsewhere classified (NAFLD / Hepatic steatosis)",
    "category": "Digestive System",
    "keywords": [
      "fatty liver",
      "nafld",
      "nash",
      "hepatic steatosis"
    ]
  },
  {
    "code": "K80.2",
    "name": "Calculus of gallbladder without cholecystitis (Cholelithiasis / Gallstones)",
    "category": "Digestive System",
    "keywords": [
      "gallstones",
      "cholelithiasis",
      "gallbladder stones",
      "biliary colic"
    ]
  },
  {
    "code": "K81.0",
    "name": "Acute cholecystitis",
    "category": "Digestive System",
    "keywords": [
      "acute cholecystitis",
      "murphys sign",
      "ruq pain",
      "gallbladder inflammation"
    ]
  },
  {
    "code": "K81.9",
    "name": "Cholecystitis, unspecified",
    "category": "Digestive System",
    "keywords": [
      "cholecystitis",
      "gallbladder infection"
    ]
  },
  {
    "code": "K85.9",
    "name": "Acute pancreatitis, unspecified",
    "category": "Digestive System",
    "keywords": [
      "acute pancreatitis",
      "epigastric radiating to back",
      "elevated amylase"
    ]
  },
  {
    "code": "K92.0",
    "name": "Haematemesis (Vomiting blood)",
    "category": "Digestive System",
    "keywords": [
      "hematemesis",
      "vomiting blood",
      "coffee ground vomiting",
      "gi bleed"
    ]
  },
  {
    "code": "K92.1",
    "name": "Melaena (Black tarry stools)",
    "category": "Digestive System",
    "keywords": [
      "melena",
      "black stools",
      "upper gi bleed"
    ]
  },
  {
    "code": "L01.0",
    "name": "Impetigo [any organism] [any type]",
    "category": "Skin & Subcutaneous",
    "keywords": [
      "impetigo",
      "honey coloured crusts",
      "bacterial skin infection",
      "school sores"
    ]
  },
  {
    "code": "L02.9",
    "name": "Cutaneous abscess, furuncle and carbuncle, unspecified (Boils)",
    "category": "Skin & Subcutaneous",
    "keywords": [
      "boil",
      "furuncle",
      "carbuncle",
      "skin abscess",
      "pus boil"
    ]
  },
  {
    "code": "L03.1",
    "name": "Cellulitis of other parts of limb",
    "category": "Skin & Subcutaneous",
    "keywords": [
      "leg cellulitis",
      "cellulitis",
      "spreading erythema",
      "warm red swelling"
    ]
  },
  {
    "code": "L03.9",
    "name": "Cellulitis, unspecified",
    "category": "Skin & Subcutaneous",
    "keywords": [
      "cellulitis",
      "skin infection",
      "strep staph cellulitis"
    ]
  },
  {
    "code": "L04.9",
    "name": "Acute lymphadenitis, unspecified",
    "category": "Skin & Subcutaneous",
    "keywords": [
      "lymphadenitis",
      "painful swollen gland",
      "tender lymph node"
    ]
  },
  {
    "code": "L08.0",
    "name": "Pyoderma",
    "category": "Skin & Subcutaneous",
    "keywords": [
      "pyoderma",
      "pus lesions",
      "staphylococcal skin"
    ]
  },
  {
    "code": "L20.9",
    "name": "Atopic dermatitis, unspecified (Atopic eczema)",
    "category": "Skin & Subcutaneous",
    "keywords": [
      "atopic dermatitis",
      "eczema",
      "dry itchy skin",
      "flexural eczema"
    ]
  },
  {
    "code": "L21.9",
    "name": "Seborrhoeic dermatitis, unspecified (Dandruff / Cradle cap)",
    "category": "Skin & Subcutaneous",
    "keywords": [
      "dandruff",
      "seborrheic dermatitis",
      "greasy scales",
      "scalp flaking"
    ]
  },
  {
    "code": "L23.9",
    "name": "Allergic contact dermatitis, unspecified cause",
    "category": "Skin & Subcutaneous",
    "keywords": [
      "contact dermatitis",
      "skin allergy",
      "patch test",
      "nickel allergy"
    ]
  },
  {
    "code": "L24.9",
    "name": "Irritant contact dermatitis, unspecified cause",
    "category": "Skin & Subcutaneous",
    "keywords": [
      "irritant dermatitis",
      "detergent dermatitis",
      "housewives eczema"
    ]
  },
  {
    "code": "L29.9",
    "name": "Pruritus, unspecified (Itching)",
    "category": "Skin & Subcutaneous",
    "keywords": [
      "pruritus",
      "itching",
      "itchy skin",
      "generalized pruritus"
    ]
  },
  {
    "code": "L30.9",
    "name": "Dermatitis, unspecified (Eczema)",
    "category": "Skin & Subcutaneous",
    "keywords": [
      "dermatitis",
      "eczema",
      "skin rash"
    ]
  },
  {
    "code": "L40.0",
    "name": "Psoriasis vulgaris (Plaque psoriasis)",
    "category": "Skin & Subcutaneous",
    "keywords": [
      "psoriasis",
      "silvery scales",
      "plaque psoriasis",
      "auspitz sign"
    ]
  },
  {
    "code": "L40.9",
    "name": "Psoriasis, unspecified",
    "category": "Skin & Subcutaneous",
    "keywords": [
      "psoriasis",
      "extensor plaques"
    ]
  },
  {
    "code": "L43.9",
    "name": "Lichen planus, unspecified",
    "category": "Skin & Subcutaneous",
    "keywords": [
      "lichen planus",
      "pruritic purple papules",
      "wickhams striae"
    ]
  },
  {
    "code": "L50.0",
    "name": "Allergic urticaria (Hives / Nettle rash)",
    "category": "Skin & Subcutaneous",
    "keywords": [
      "urticaria",
      "hives",
      "wheals",
      "allergic wheals",
      "itching"
    ]
  },
  {
    "code": "L50.9",
    "name": "Urticaria, unspecified",
    "category": "Skin & Subcutaneous",
    "keywords": [
      "urticaria",
      "welts",
      "angioedema hives"
    ]
  },
  {
    "code": "L55.9",
    "name": "Sunburn, unspecified",
    "category": "Skin & Subcutaneous",
    "keywords": [
      "sunburn",
      "solar erythema"
    ]
  },
  {
    "code": "L60.0",
    "name": "Ingrowing nail (Ingrown toenail / Onychocryptosis)",
    "category": "Skin & Subcutaneous",
    "keywords": [
      "ingrown toenail",
      "nail bed infection",
      "paronychia"
    ]
  },
  {
    "code": "L63.9",
    "name": "Alopecia areata, unspecified (Patchy hair loss)",
    "category": "Skin & Subcutaneous",
    "keywords": [
      "alopecia areata",
      "hair loss",
      "bald patches"
    ]
  },
  {
    "code": "L65.9",
    "name": "Nonscarring hair loss, unspecified (Telogen effluvium)",
    "category": "Skin & Subcutaneous",
    "keywords": [
      "hair fall",
      "diffuse hair loss",
      "telogen effluvium"
    ]
  },
  {
    "code": "L70.0",
    "name": "Acne vulgaris (Pimples)",
    "category": "Skin & Subcutaneous",
    "keywords": [
      "acne",
      "acne vulgaris",
      "pimples",
      "comedones",
      "blackheads",
      "facial pustules"
    ]
  },
  {
    "code": "L73.2",
    "name": "Hidradenitis suppurativa",
    "category": "Skin & Subcutaneous",
    "keywords": [
      "hidradenitis",
      "axillary boils",
      "groin boils"
    ]
  },
  {
    "code": "L74.3",
    "name": "Miliaria, unspecified (Prickly heat / Heat rash)",
    "category": "Skin & Subcutaneous",
    "keywords": [
      "prickly heat",
      "heat rash",
      "miliaria rubra",
      "sweat rash"
    ]
  },
  {
    "code": "L80",
    "name": "Vitiligo (Leucoderma)",
    "category": "Skin & Subcutaneous",
    "keywords": [
      "vitiligo",
      "leucoderma",
      "white patches",
      "depigmentation"
    ]
  },
  {
    "code": "L82",
    "name": "Seborrhoeic keratosis",
    "category": "Skin & Subcutaneous",
    "keywords": [
      "seborrheic keratosis",
      "warty lesion",
      "senile wart"
    ]
  },
  {
    "code": "L97",
    "name": "Ulcer of lower limb, not elsewhere classified (Chronic leg ulcer)",
    "category": "Skin & Subcutaneous",
    "keywords": [
      "leg ulcer",
      "venous ulcer",
      "trophic ulcer",
      "non-healing wound"
    ]
  },
  {
    "code": "M06.9",
    "name": "Rheumatoid arthritis, unspecified",
    "category": "Musculoskeletal System",
    "keywords": [
      "rheumatoid arthritis",
      "ra",
      "morning stiffness",
      "small joint arthritis",
      "ra factor positive"
    ]
  },
  {
    "code": "M10.0",
    "name": "Idiopathic gout (Acute gouty arthritis)",
    "category": "Musculoskeletal System",
    "keywords": [
      "gout",
      "podagra",
      "acute gout",
      "big toe swelling",
      "hyperuricemia arthritis"
    ]
  },
  {
    "code": "M10.9",
    "name": "Gout, unspecified",
    "category": "Musculoskeletal System",
    "keywords": [
      "gouty arthritis",
      "tophi",
      "uric acid arthritis"
    ]
  },
  {
    "code": "M16.9",
    "name": "Coxarthrosis, unspecified (Osteoarthritis of hip)",
    "category": "Musculoskeletal System",
    "keywords": [
      "hip osteoarthritis",
      "hip joint pain"
    ]
  },
  {
    "code": "M17.0",
    "name": "Primary gonarthrosis, bilateral (Osteoarthritis of knees)",
    "category": "Musculoskeletal System",
    "keywords": [
      "knee osteoarthritis",
      "oa knees",
      "crepitus",
      "knee wear and tear"
    ]
  },
  {
    "code": "M17.9",
    "name": "Gonarthrosis, unspecified (Osteoarthritis of knee)",
    "category": "Musculoskeletal System",
    "keywords": [
      "osteoarthritis knee",
      "knee pain",
      "degenerative knee joint",
      "oa knee"
    ]
  },
  {
    "code": "M19.9",
    "name": "Arthrosis, unspecified (Osteoarthritis)",
    "category": "Musculoskeletal System",
    "keywords": [
      "osteoarthritis",
      "degenerative joint disease",
      "joint pain",
      "joint stiffness"
    ]
  },
  {
    "code": "M25.5",
    "name": "Pain in joint (Arthralgia)",
    "category": "Musculoskeletal System",
    "keywords": [
      "arthralgia",
      "joint pain",
      "joint ache",
      "polyarthralgia"
    ]
  },
  {
    "code": "M47.8",
    "name": "Other spondylosis (Cervical / Lumbar spondylosis)",
    "category": "Musculoskeletal System",
    "keywords": [
      "spondylosis",
      "cervical spondylosis",
      "lumbar spondylosis",
      "neck pain",
      "back stiffness"
    ]
  },
  {
    "code": "M51.1",
    "name": "Lumbar and other intervertebral disc disorders with radiculopathy (Sciatica)",
    "category": "Musculoskeletal System",
    "keywords": [
      "sciatica",
      "slip disc",
      "herniated disc",
      "pivd",
      "radiating leg pain"
    ]
  },
  {
    "code": "M51.2",
    "name": "Other specified intervertebral disc displacement",
    "category": "Musculoskeletal System",
    "keywords": [
      "disc displacement",
      "disc prolapse",
      "pivd"
    ]
  },
  {
    "code": "M54.2",
    "name": "Cervicalgia (Neck pain)",
    "category": "Musculoskeletal System",
    "keywords": [
      "neck pain",
      "cervical pain",
      "neck spasm",
      "stiff neck"
    ]
  },
  {
    "code": "M54.5",
    "name": "Low back pain (Lumbago)",
    "category": "Musculoskeletal System",
    "keywords": [
      "back pain",
      "low back pain",
      "lumbago",
      "lumbar pain",
      "back spasm",
      "backache"
    ]
  },
  {
    "code": "M62.8",
    "name": "Other specified disorders of muscle (Muscle spasm / Myalgia)",
    "category": "Musculoskeletal System",
    "keywords": [
      "myalgia",
      "muscle pain",
      "muscle spasm",
      "body ache"
    ]
  },
  {
    "code": "M65.3",
    "name": "Trigger finger",
    "category": "Musculoskeletal System",
    "keywords": [
      "trigger finger",
      "tenosynovitis",
      "locked finger"
    ]
  },
  {
    "code": "M70.6",
    "name": "Trochanteric bursitis (Hip bursitis)",
    "category": "Musculoskeletal System",
    "keywords": [
      "hip bursitis",
      "trochanteric pain"
    ]
  },
  {
    "code": "M71.3",
    "name": "Other bursal cyst (Baker's cyst / Popliteal cyst)",
    "category": "Musculoskeletal System",
    "keywords": [
      "bakers cyst",
      "popliteal cyst",
      "behind knee swelling"
    ]
  },
  {
    "code": "M72.2",
    "name": "Plantar fascial fibromatosis (Plantar fasciitis)",
    "category": "Musculoskeletal System",
    "keywords": [
      "plantar fasciitis",
      "heel pain",
      "calcaneal spur",
      "first step morning pain"
    ]
  },
  {
    "code": "M75.0",
    "name": "Adhesive capsulitis of shoulder (Frozen shoulder)",
    "category": "Musculoskeletal System",
    "keywords": [
      "frozen shoulder",
      "periarthritis shoulder",
      "stiff shoulder",
      "painful arc"
    ]
  },
  {
    "code": "M77.1",
    "name": "Lateral epicondylitis (Tennis elbow)",
    "category": "Musculoskeletal System",
    "keywords": [
      "tennis elbow",
      "lateral epicondylitis",
      "outer elbow pain"
    ]
  },
  {
    "code": "M77.2",
    "name": "Medial epicondylitis (Golfer's elbow)",
    "category": "Musculoskeletal System",
    "keywords": [
      "golfers elbow",
      "medial epicondylitis",
      "inner elbow pain"
    ]
  },
  {
    "code": "M79.1",
    "name": "Myalgia (Generalised muscular pain)",
    "category": "Musculoskeletal System",
    "keywords": [
      "myalgia",
      "body aches",
      "muscle tenderness"
    ]
  },
  {
    "code": "M79.7",
    "name": "Fibromyalgia",
    "category": "Musculoskeletal System",
    "keywords": [
      "fibromyalgia",
      "chronic widespread pain",
      "tender points",
      "fatigue"
    ]
  },
  {
    "code": "M81.0",
    "name": "Postmenopausal osteoporosis",
    "category": "Musculoskeletal System",
    "keywords": [
      "osteoporosis",
      "bone density low",
      "fragility fracture"
    ]
  },
  {
    "code": "M81.9",
    "name": "Osteoporosis, unspecified",
    "category": "Musculoskeletal System",
    "keywords": [
      "osteoporosis",
      "weak bones",
      "osteopenia"
    ]
  },
  {
    "code": "N00.9",
    "name": "Acute nephritic syndrome, unspecified (Glomerulonephritis)",
    "category": "Genitourinary System",
    "keywords": [
      "acute glomerulonephritis",
      "agn",
      "hematuria edema",
      "post strep"
    ]
  },
  {
    "code": "N04.9",
    "name": "Nephrotic syndrome, unspecified",
    "category": "Genitourinary System",
    "keywords": [
      "nephrotic syndrome",
      "massive proteinuria",
      "facial puffiness",
      "frothy urine"
    ]
  },
  {
    "code": "N17.9",
    "name": "Acute renal failure, unspecified (Acute kidney injury / AKI)",
    "category": "Genitourinary System",
    "keywords": [
      "acute kidney injury",
      "aki",
      "acute renal failure",
      "oliguria",
      "high creatinine"
    ]
  },
  {
    "code": "N18.9",
    "name": "Chronic kidney disease, unspecified (CKD)",
    "category": "Genitourinary System",
    "keywords": [
      "chronic kidney disease",
      "ckd",
      "chronic renal failure",
      "crf",
      "elevated creatinine",
      "renal insufficiency"
    ]
  },
  {
    "code": "N20.0",
    "name": "Calculus of kidney (Nephrolithiasis / Renal stone)",
    "category": "Genitourinary System",
    "keywords": [
      "kidney stone",
      "renal calculi",
      "renal calculus",
      "flank pain",
      "stone in kidney"
    ]
  },
  {
    "code": "N20.1",
    "name": "Calculus of ureter (Ureteric stone)",
    "category": "Genitourinary System",
    "keywords": [
      "ureteric stone",
      "ureteral stone",
      "renal colic",
      "severe loin to groin pain"
    ]
  },
  {
    "code": "N20.2",
    "name": "Calculus of kidney with calculus of ureter",
    "category": "Genitourinary System",
    "keywords": [
      "kidney stone",
      "ureteric calculus",
      "colic"
    ]
  },
  {
    "code": "N21.0",
    "name": "Calculus in bladder (Bladder stone)",
    "category": "Genitourinary System",
    "keywords": [
      "bladder stone",
      "vesical calculus",
      "interrupted urination"
    ]
  },
  {
    "code": "N23",
    "name": "Unspecified renal colic",
    "category": "Genitourinary System",
    "keywords": [
      "renal colic",
      "kidney pain",
      "ureteric colic",
      "severe flank pain"
    ]
  },
  {
    "code": "N30.0",
    "name": "Acute cystitis (Urinary bladder infection)",
    "category": "Genitourinary System",
    "keywords": [
      "cystitis",
      "acute cystitis",
      "burning micturition",
      "frequency urgency"
    ]
  },
  {
    "code": "N30.9",
    "name": "Cystitis, unspecified",
    "category": "Genitourinary System",
    "keywords": [
      "bladder infection",
      "cystitis"
    ]
  },
  {
    "code": "N34.1",
    "name": "Nonspecific urethritis",
    "category": "Genitourinary System",
    "keywords": [
      "urethritis",
      "urethral discharge",
      "dysuria"
    ]
  },
  {
    "code": "N39.0",
    "name": "Urinary tract infection, site not specified (UTI)",
    "category": "Genitourinary System",
    "keywords": [
      "uti",
      "urinary tract infection",
      "burning urination",
      "dysuria",
      "pus cells in urine",
      "urine infection"
    ]
  },
  {
    "code": "N40",
    "name": "Hyperplasia of prostate (Benign prostatic hyperplasia / BPH)",
    "category": "Genitourinary System",
    "keywords": [
      "bph",
      "benign prostatic hyperplasia",
      "enlarged prostate",
      "nocturia",
      "weak stream",
      "hesitancy",
      "dribbling"
    ]
  },
  {
    "code": "N41.0",
    "name": "Acute prostatitis",
    "category": "Genitourinary System",
    "keywords": [
      "acute prostatitis",
      "prostate infection",
      "perineal pain",
      "fever"
    ]
  },
  {
    "code": "N43.3",
    "name": "Hydrocele, unspecified",
    "category": "Genitourinary System",
    "keywords": [
      "hydrocele",
      "scrotal swelling",
      "fluid in scrotum"
    ]
  },
  {
    "code": "N44",
    "name": "Torsion of testis",
    "category": "Genitourinary System",
    "keywords": [
      "testicular torsion",
      "acute scrotum",
      "severe scrotal pain",
      "emergency"
    ]
  },
  {
    "code": "N45.9",
    "name": "Orchitis, epididymitis and epididymo-orchitis without abscess",
    "category": "Genitourinary System",
    "keywords": [
      "epididymo-orchitis",
      "scrotal pain",
      "testicular swelling"
    ]
  },
  {
    "code": "N47",
    "name": "Redundant prepuce, phimosis and paraphimosis",
    "category": "Genitourinary System",
    "keywords": [
      "phimosis",
      "tight foreskin",
      "paraphimosis",
      "circumcision"
    ]
  },
  {
    "code": "N70.9",
    "name": "Salpingitis and oophoritis, unspecified",
    "category": "Genitourinary System",
    "keywords": [
      "salpingitis",
      "adnexal tenderness"
    ]
  },
  {
    "code": "N73.9",
    "name": "Female pelvic inflammatory disease, unspecified (PID)",
    "category": "Genitourinary System",
    "keywords": [
      "pid",
      "pelvic inflammatory disease",
      "lower abdominal pain female",
      "cervical excitation"
    ]
  },
  {
    "code": "N76.0",
    "name": "Acute vaginitis",
    "category": "Genitourinary System",
    "keywords": [
      "vaginitis",
      "vaginal discharge",
      "pruritus vulvae",
      "white discharge"
    ]
  },
  {
    "code": "N76.1",
    "name": "Subacute and chronic vaginitis",
    "category": "Genitourinary System",
    "keywords": [
      "leukorrhea",
      "chronic discharge",
      "vaginal itching"
    ]
  },
  {
    "code": "N80.9",
    "name": "Endometriosis, unspecified",
    "category": "Genitourinary System",
    "keywords": [
      "endometriosis",
      "chronic pelvic pain",
      "dyspareunia"
    ]
  },
  {
    "code": "N91.2",
    "name": "Amenorrhoea, unspecified (Secondary amenorrhoea)",
    "category": "Genitourinary System",
    "keywords": [
      "amenorrhea",
      "missed period",
      "stopped periods"
    ]
  },
  {
    "code": "N92.0",
    "name": "Excessive and frequent menstruation with regular cycle (Menorrhagia)",
    "category": "Genitourinary System",
    "keywords": [
      "menorrhagia",
      "heavy periods",
      "heavy bleeding",
      "blood clots menses"
    ]
  },
  {
    "code": "N92.1",
    "name": "Excessive and frequent menstruation with irregular cycle (Polymenorrhagia)",
    "category": "Genitourinary System",
    "keywords": [
      "irregular bleeding",
      "frequent periods"
    ]
  },
  {
    "code": "N93.8",
    "name": "Other specified abnormal uterine and vaginal bleeding (DUB / AUB)",
    "category": "Genitourinary System",
    "keywords": [
      "aub",
      "dub",
      "dysfunctional uterine bleeding",
      "abnormal uterine bleeding"
    ]
  },
  {
    "code": "N94.6",
    "name": "Dysmenorrhoea, unspecified (Painful periods)",
    "category": "Genitourinary System",
    "keywords": [
      "dysmenorrhea",
      "painful menstruation",
      "period cramps",
      "menses pain"
    ]
  },
  {
    "code": "N95.1",
    "name": "Menopausal and perimenopausal states (Menopausal syndrome)",
    "category": "Genitourinary System",
    "keywords": [
      "menopause",
      "hot flashes",
      "night sweats",
      "climacteric"
    ]
  },
  {
    "code": "R00.0",
    "name": "Tachycardia, unspecified",
    "category": "Symptoms & Clinical Signs",
    "keywords": [
      "tachycardia",
      "fast heart rate",
      "racing pulse"
    ]
  },
  {
    "code": "R00.1",
    "name": "Bradycardia, unspecified",
    "category": "Symptoms & Clinical Signs",
    "keywords": [
      "bradycardia",
      "slow pulse",
      "slow heart rate"
    ]
  },
  {
    "code": "R00.2",
    "name": "Palpitations",
    "category": "Symptoms & Clinical Signs",
    "keywords": [
      "palpitations",
      "heart pounding",
      "fluttering heart"
    ]
  },
  {
    "code": "R04.0",
    "name": "Epistaxis (Nosebleed)",
    "category": "Symptoms & Clinical Signs",
    "keywords": [
      "epistaxis",
      "nosebleed",
      "bleeding nose",
      "nasal bleeding"
    ]
  },
  {
    "code": "R04.2",
    "name": "Haemoptysis (Coughing blood)",
    "category": "Symptoms & Clinical Signs",
    "keywords": [
      "hemoptysis",
      "coughing blood",
      "blood in sputum"
    ]
  },
  {
    "code": "R05",
    "name": "Cough",
    "category": "Symptoms & Clinical Signs",
    "keywords": [
      "cough",
      "dry cough",
      "productive cough",
      "chronic cough",
      "khasi"
    ]
  },
  {
    "code": "R06.0",
    "name": "Dyspnoea (Shortness of breath / Breathlessness)",
    "category": "Symptoms & Clinical Signs",
    "keywords": [
      "dyspnea",
      "shortness of breath",
      "breathlessness",
      "sob",
      "difficulty breathing"
    ]
  },
  {
    "code": "R06.2",
    "name": "Wheezing",
    "category": "Symptoms & Clinical Signs",
    "keywords": [
      "wheezing",
      "chest whistle",
      "noisy breathing"
    ]
  },
  {
    "code": "R07.0",
    "name": "Pain in throat",
    "category": "Symptoms & Clinical Signs",
    "keywords": [
      "throat pain",
      "sore throat",
      "odynophagia"
    ]
  },
  {
    "code": "R07.2",
    "name": "Precordial pain",
    "category": "Symptoms & Clinical Signs",
    "keywords": [
      "precordial pain",
      "anterior chest pain"
    ]
  },
  {
    "code": "R07.4",
    "name": "Chest pain, unspecified",
    "category": "Symptoms & Clinical Signs",
    "keywords": [
      "chest pain",
      "chest discomfort",
      "non-cardiac chest pain",
      "chest tightness"
    ]
  },
  {
    "code": "R10.0",
    "name": "Acute abdomen",
    "category": "Symptoms & Clinical Signs",
    "keywords": [
      "acute abdomen",
      "severe abdominal pain",
      "guarding rigidity"
    ]
  },
  {
    "code": "R10.1",
    "name": "Pain localized to upper abdomen (Epigastric pain)",
    "category": "Symptoms & Clinical Signs",
    "keywords": [
      "epigastric pain",
      "upper stomach pain",
      "upper abdominal pain"
    ]
  },
  {
    "code": "R10.3",
    "name": "Pain localized to lower abdomen",
    "category": "Symptoms & Clinical Signs",
    "keywords": [
      "lower abdominal pain",
      "suprapubic pain",
      "pelvic discomfort"
    ]
  },
  {
    "code": "R10.4",
    "name": "Other and unspecified abdominal pain (Stomach ache)",
    "category": "Symptoms & Clinical Signs",
    "keywords": [
      "abdominal pain",
      "stomach pain",
      "stomach ache",
      "belly ache",
      "colic"
    ]
  },
  {
    "code": "R11",
    "name": "Nausea and vomiting",
    "category": "Symptoms & Clinical Signs",
    "keywords": [
      "vomiting",
      "nausea",
      "emesis",
      "feeling sick",
      "retching"
    ]
  },
  {
    "code": "R12",
    "name": "Heartburn (Pyrosis)",
    "category": "Symptoms & Clinical Signs",
    "keywords": [
      "heartburn",
      "acid belch",
      "chest burn",
      "water brash"
    ]
  },
  {
    "code": "R13",
    "name": "Dysphagia (Difficulty swallowing)",
    "category": "Symptoms & Clinical Signs",
    "keywords": [
      "dysphagia",
      "difficulty swallowing",
      "food getting stuck"
    ]
  },
  {
    "code": "R14",
    "name": "Flatulence and related conditions (Abdominal distension / Gas)",
    "category": "Symptoms & Clinical Signs",
    "keywords": [
      "gas",
      "flatulence",
      "bloating",
      "abdominal fullness",
      "belching"
    ]
  },
  {
    "code": "R17",
    "name": "Unspecified jaundice (Hyperbilirubinaemia / Icterus)",
    "category": "Symptoms & Clinical Signs",
    "keywords": [
      "jaundice",
      "icterus",
      "yellow eyes",
      "yellow urine",
      "manjal kamalai"
    ]
  },
  {
    "code": "R18",
    "name": "Ascites (Fluid in abdomen)",
    "category": "Symptoms & Clinical Signs",
    "keywords": [
      "ascites",
      "fluid abdomen",
      "distended abdomen"
    ]
  },
  {
    "code": "R20.2",
    "name": "Paraesthesia of skin (Tingling / Numbness)",
    "category": "Symptoms & Clinical Signs",
    "keywords": [
      "tingling",
      "numbness",
      "paresthesia",
      "pins and needles"
    ]
  },
  {
    "code": "R21",
    "name": "Rash and other nonspecific skin eruption",
    "category": "Symptoms & Clinical Signs",
    "keywords": [
      "rash",
      "skin eruption",
      "red spots"
    ]
  },
  {
    "code": "R25.2",
    "name": "Cramp and spasm (Leg cramps / Muscle cramps)",
    "category": "Symptoms & Clinical Signs",
    "keywords": [
      "leg cramp",
      "calf cramp",
      "muscle cramp",
      "night cramps"
    ]
  },
  {
    "code": "R30.0",
    "name": "Dysuria (Painful urination / Burning micturition)",
    "category": "Symptoms & Clinical Signs",
    "keywords": [
      "dysuria",
      "painful urination",
      "burning micturition",
      "burning urine"
    ]
  },
  {
    "code": "R30.9",
    "name": "Painful micturition, unspecified",
    "category": "Symptoms & Clinical Signs",
    "keywords": [
      "strangury",
      "pain on urination"
    ]
  },
  {
    "code": "R31",
    "name": "Unspecified haematuria (Blood in urine)",
    "category": "Symptoms & Clinical Signs",
    "keywords": [
      "hematuria",
      "blood in urine",
      "red urine"
    ]
  },
  {
    "code": "R32",
    "name": "Unspecified urinary incontinence",
    "category": "Symptoms & Clinical Signs",
    "keywords": [
      "incontinence",
      "urine leakage",
      "stress incontinence",
      "urge incontinence"
    ]
  },
  {
    "code": "R35",
    "name": "Polyuria (Frequent urination / Nocturia)",
    "category": "Symptoms & Clinical Signs",
    "keywords": [
      "polyuria",
      "frequency of urine",
      "nocturia",
      "excessive urination"
    ]
  },
  {
    "code": "R42",
    "name": "Dizziness and giddiness (Vertigo / Lightheadedness)",
    "category": "Symptoms & Clinical Signs",
    "keywords": [
      "dizziness",
      "giddiness",
      "chakkar",
      "lightheadedness",
      "fainting feeling"
    ]
  },
  {
    "code": "R50.9",
    "name": "Fever, unspecified (Pyrexia / PUO)",
    "category": "Symptoms & Clinical Signs",
    "keywords": [
      "fever",
      "pyrexia",
      "puo",
      "fever of unknown origin",
      "high temperature",
      "febrile illness",
      "kaichal"
    ]
  },
  {
    "code": "R51",
    "name": "Headache (Cephalgia)",
    "category": "Symptoms & Clinical Signs",
    "keywords": [
      "headache",
      "head pain",
      "cephalgia",
      "thalai vali"
    ]
  },
  {
    "code": "R52.9",
    "name": "Pain, unspecified",
    "category": "Symptoms & Clinical Signs",
    "keywords": [
      "pain",
      "generalized pain",
      "body ache"
    ]
  },
  {
    "code": "R53",
    "name": "Malaise and fatigue (Generalized weakness / Lethargy)",
    "category": "Symptoms & Clinical Signs",
    "keywords": [
      "fatigue",
      "weakness",
      "malaise",
      "tiredness",
      "exhaustion",
      "lethargy",
      "general debility"
    ]
  },
  {
    "code": "R55",
    "name": "Syncope and collapse (Fainting / Blackout)",
    "category": "Symptoms & Clinical Signs",
    "keywords": [
      "syncope",
      "fainting",
      "collapse",
      "blackout",
      "vasovagal"
    ]
  },
  {
    "code": "R56.0",
    "name": "Febrile convulsions",
    "category": "Symptoms & Clinical Signs",
    "keywords": [
      "febrile fit",
      "febrile convulsion",
      "fever fits in children"
    ]
  },
  {
    "code": "R59.9",
    "name": "Enlarged lymph nodes, unspecified (Lymphadenopathy)",
    "category": "Symptoms & Clinical Signs",
    "keywords": [
      "lymphadenopathy",
      "swollen glands",
      "neck gland swelling"
    ]
  },
  {
    "code": "R60.0",
    "name": "Localized oedema (Pedal edema)",
    "category": "Symptoms & Clinical Signs",
    "keywords": [
      "pedal edema",
      "leg swelling",
      "swollen ankles",
      "pitting edema"
    ]
  },
  {
    "code": "R60.9",
    "name": "Oedema, unspecified (General swelling / Dropsy)",
    "category": "Symptoms & Clinical Signs",
    "keywords": [
      "edema",
      "anasarca",
      "swelling",
      "puffiness"
    ]
  },
  {
    "code": "R63.0",
    "name": "Anorexia (Loss of appetite)",
    "category": "Symptoms & Clinical Signs",
    "keywords": [
      "loss of appetite",
      "anorexia",
      "poor appetite",
      "not eating"
    ]
  },
  {
    "code": "R63.4",
    "name": "Abnormal weight loss",
    "category": "Symptoms & Clinical Signs",
    "keywords": [
      "weight loss",
      "unexplained weight loss",
      "loss of weight"
    ]
  },
  {
    "code": "R63.5",
    "name": "Abnormal weight gain",
    "category": "Symptoms & Clinical Signs",
    "keywords": [
      "weight gain",
      "rapid weight gain"
    ]
  },
  {
    "code": "S00.9",
    "name": "Superficial injury of head, unspecified (Contusion / Bruise)",
    "category": "Injuries & Trauma",
    "keywords": [
      "head injury",
      "head contusion",
      "bump on head",
      "bruise"
    ]
  },
  {
    "code": "S01.0",
    "name": "Open wound of scalp (Laceration of scalp)",
    "category": "Injuries & Trauma",
    "keywords": [
      "scalp cut",
      "scalp laceration",
      "bleeding scalp"
    ]
  },
  {
    "code": "S01.8",
    "name": "Open wound of other parts of head (Facial laceration)",
    "category": "Injuries & Trauma",
    "keywords": [
      "face cut",
      "facial laceration",
      "wound stitching"
    ]
  },
  {
    "code": "S06.0",
    "name": "Concussion (Mild traumatic brain injury)",
    "category": "Injuries & Trauma",
    "keywords": [
      "concussion",
      "head strike",
      "vomiting after head injury"
    ]
  },
  {
    "code": "S13.4",
    "name": "Sprain and strain of cervical spine (Whiplash)",
    "category": "Injuries & Trauma",
    "keywords": [
      "whiplash",
      "neck strain",
      "neck sprain"
    ]
  },
  {
    "code": "S20.2",
    "name": "Contusion of thorax (Chest contusion / Bruised rib)",
    "category": "Injuries & Trauma",
    "keywords": [
      "chest contusion",
      "bruised rib",
      "chest trauma"
    ]
  },
  {
    "code": "S22.3",
    "name": "Fracture of rib",
    "category": "Injuries & Trauma",
    "keywords": [
      "rib fracture",
      "broken rib"
    ]
  },
  {
    "code": "S30.0",
    "name": "Contusion of lower back and pelvis",
    "category": "Injuries & Trauma",
    "keywords": [
      "back contusion",
      "fall on back"
    ]
  },
  {
    "code": "S40.0",
    "name": "Contusion of shoulder and upper arm",
    "category": "Injuries & Trauma",
    "keywords": [
      "shoulder bruise",
      "arm contusion"
    ]
  },
  {
    "code": "S43.0",
    "name": "Dislocation of shoulder joint",
    "category": "Injuries & Trauma",
    "keywords": [
      "shoulder dislocation",
      "dislocated shoulder"
    ]
  },
  {
    "code": "S52.5",
    "name": "Fracture of lower end of radius (Colles' fracture)",
    "category": "Injuries & Trauma",
    "keywords": [
      "colles fracture",
      "wrist fracture",
      "broken wrist",
      "radius fracture"
    ]
  },
  {
    "code": "S53.0",
    "name": "Dislocation of radial head (Pulled elbow in toddlers)",
    "category": "Injuries & Trauma",
    "keywords": [
      "pulled elbow",
      "nursemaid elbow"
    ]
  },
  {
    "code": "S60.0",
    "name": "Contusion of finger(s) without damage to nail",
    "category": "Injuries & Trauma",
    "keywords": [
      "finger bruise",
      "crush finger",
      "door slam finger"
    ]
  },
  {
    "code": "S61.0",
    "name": "Open wound of finger(s) without damage to nail",
    "category": "Injuries & Trauma",
    "keywords": [
      "cut finger",
      "finger laceration",
      "wound stitch"
    ]
  },
  {
    "code": "S63.5",
    "name": "Sprain and strain of wrist",
    "category": "Injuries & Trauma",
    "keywords": [
      "wrist sprain",
      "wrist twist"
    ]
  },
  {
    "code": "S72.0",
    "name": "Fracture of neck of femur (Hip fracture in elderly)",
    "category": "Injuries & Trauma",
    "keywords": [
      "hip fracture",
      "femur neck fracture",
      "elderly fall"
    ]
  },
  {
    "code": "S82.2",
    "name": "Fracture of shaft of tibia",
    "category": "Injuries & Trauma",
    "keywords": [
      "tibia fracture",
      "broken shin",
      "leg fracture"
    ]
  },
  {
    "code": "S93.4",
    "name": "Sprain and strain of ankle",
    "category": "Injuries & Trauma",
    "keywords": [
      "ankle sprain",
      "twisted ankle",
      "swollen ankle",
      "ligament tear ankle"
    ]
  },
  {
    "code": "T14.0",
    "name": "Superficial injury of unspecified body region (Abrasion / Bruise)",
    "category": "Injuries & Trauma",
    "keywords": [
      "abrasion",
      "graze",
      "bruise",
      "scrape",
      "road rash"
    ]
  },
  {
    "code": "T14.1",
    "name": "Open wound of unspecified body region (Laceration / Cut)",
    "category": "Injuries & Trauma",
    "keywords": [
      "cut",
      "laceration",
      "wound",
      "stitched wound"
    ]
  },
  {
    "code": "T20.0",
    "name": "Burn of unspecified degree of head and neck",
    "category": "Injuries & Trauma",
    "keywords": [
      "burn",
      "head burn",
      "facial burn"
    ]
  },
  {
    "code": "T29.0",
    "name": "Burns of multiple body regions, unspecified degree",
    "category": "Injuries & Trauma",
    "keywords": [
      "burns",
      "thermal injury",
      "scalds",
      "hot water burn",
      "fire burn"
    ]
  },
  {
    "code": "T60.0",
    "name": "Toxic effect: Organophosphate and carbamate insecticides",
    "category": "Poisoning & Toxic Effects",
    "keywords": [
      "op poisoning",
      "organophosphate",
      "pesticide poisoning",
      "insecticide",
      "atropine"
    ]
  },
  {
    "code": "T63.0",
    "name": "Toxic effect of snake venom (Snake bite)",
    "category": "Poisoning & Toxic Effects",
    "keywords": [
      "snake bite",
      "viper bite",
      "cobra bite",
      "krait bite",
      "asv",
      "antivenom"
    ]
  },
  {
    "code": "T63.2",
    "name": "Toxic effect of venom of scorpion (Scorpion sting)",
    "category": "Poisoning & Toxic Effects",
    "keywords": [
      "scorpion sting",
      "scorpion bite",
      "prazosin",
      "severe local pain"
    ]
  },
  {
    "code": "T63.4",
    "name": "Toxic effect of venom of other arthropods (Wasp / Bee sting / Centipede)",
    "category": "Poisoning & Toxic Effects",
    "keywords": [
      "bee sting",
      "wasp sting",
      "centipede bite",
      "insect sting",
      "swelling sting"
    ]
  },
  {
    "code": "T78.2",
    "name": "Anaphylactic shock, unspecified",
    "category": "Poisoning & Toxic Effects",
    "keywords": [
      "anaphylaxis",
      "severe allergic reaction",
      "anaphylactic shock",
      "stridor",
      "adrenaline"
    ]
  },
  {
    "code": "T78.4",
    "name": "Allergy, unspecified",
    "category": "Poisoning & Toxic Effects",
    "keywords": [
      "allergy",
      "allergic reaction",
      "drug allergy",
      "food allergy"
    ]
  },
  {
    "code": "T88.7",
    "name": "Unspecified adverse effect of drug or medicament (ADR)",
    "category": "Poisoning & Toxic Effects",
    "keywords": [
      "adr",
      "drug reaction",
      "adverse drug reaction",
      "medication side effect"
    ]
  },
  {
    "code": "Z00.0",
    "name": "General medical examination (Routine health checkup / Master health checkup)",
    "category": "Health Service Encounters",
    "keywords": [
      "general checkup",
      "health checkup",
      "routine examination",
      "annual checkup",
      "mhc"
    ]
  },
  {
    "code": "Z01.0",
    "name": "Examination of eyes and vision (Vision screening)",
    "category": "Health Service Encounters",
    "keywords": [
      "eye checkup",
      "vision test",
      "refraction check"
    ]
  },
  {
    "code": "Z01.2",
    "name": "Dental examination",
    "category": "Health Service Encounters",
    "keywords": [
      "dental checkup",
      "oral screening"
    ]
  },
  {
    "code": "Z02.1",
    "name": "Pre-employment examination (Medical fitness certificate)",
    "category": "Health Service Encounters",
    "keywords": [
      "fitness certificate",
      "job medical",
      "medical certificate"
    ]
  },
  {
    "code": "Z09.9",
    "name": "Follow-up examination after unspecified treatment",
    "category": "Health Service Encounters",
    "keywords": [
      "follow up",
      "routine review",
      "treatment review",
      "post-illness check"
    ]
  },
  {
    "code": "Z13.1",
    "name": "Special screening examination for diabetes mellitus",
    "category": "Health Service Encounters",
    "keywords": [
      "diabetes screening",
      "blood sugar check",
      "ncd screening"
    ]
  },
  {
    "code": "Z13.6",
    "name": "Special screening examination for cardiovascular disorders (Hypertension screening)",
    "category": "Health Service Encounters",
    "keywords": [
      "bp check",
      "hypertension screening",
      "cardiovascular check"
    ]
  },
  {
    "code": "Z23",
    "name": "Need for immunization against single bacterial diseases (Vaccination / TT injection)",
    "category": "Health Service Encounters",
    "keywords": [
      "vaccination",
      "immunization",
      "tt injection",
      "tetanus toxoid"
    ]
  },
  {
    "code": "Z24.0",
    "name": "Need for immunization against poliomyelitis (Polio drops)",
    "category": "Health Service Encounters",
    "keywords": [
      "polio drops",
      "opv",
      "ipv",
      "polio vaccine"
    ]
  },
  {
    "code": "Z24.4",
    "name": "Need for immunization against measles",
    "category": "Health Service Encounters",
    "keywords": [
      "measles vaccine",
      "mr vaccine"
    ]
  },
  {
    "code": "Z25.1",
    "name": "Need for immunization against influenza (Flu vaccine)",
    "category": "Health Service Encounters",
    "keywords": [
      "flu vaccine",
      "influenza shot"
    ]
  },
  {
    "code": "Z26.8",
    "name": "Need for immunization against other specified single viral diseases (Rabies prophylaxis / ARV)",
    "category": "Health Service Encounters",
    "keywords": [
      "arv",
      "rabies vaccine",
      "anti-rabies vaccination",
      "dog bite shot"
    ]
  },
  {
    "code": "Z71.3",
    "name": "Dietary counselling and surveillance (Nutrition advice / Diabetic diet)",
    "category": "Health Service Encounters",
    "keywords": [
      "diet counseling",
      "nutrition advice",
      "weight loss counseling",
      "diabetic diet"
    ]
  },
  {
    "code": "Z72.0",
    "name": "Tobacco use (Smoking cessation counseling)",
    "category": "Health Service Encounters",
    "keywords": [
      "quitting smoking",
      "tobacco cessation",
      "de-addiction guidance"
    ]
  }
];

/**
 * Perform offline search across code, diagnosis name, and clinical keywords.
 * Returns results ranked with exact code matches and prefix matches prioritized.
 */
export function searchICD10(query: string, maxResults: number = 25): ICD10Entry[] {
  if (!query || !query.trim()) {
    return [];
  }
  const cleanQuery = query.trim().toLowerCase();
  
  // Exact code match
  const exactCodeMatches: ICD10Entry[] = [];
  // Starts-with code matches
  const codePrefixMatches: ICD10Entry[] = [];
  // Starts-with name matches
  const namePrefixMatches: ICD10Entry[] = [];
  // Substring or keyword matches
  const generalMatches: ICD10Entry[] = [];

  for (const entry of ICD10_DATASET) {
    const codeLower = entry.code.toLowerCase();
    const nameLower = entry.name.toLowerCase();

    if (codeLower === cleanQuery) {
      exactCodeMatches.push(entry);
    } else if (codeLower.startsWith(cleanQuery)) {
      codePrefixMatches.push(entry);
    } else if (nameLower.startsWith(cleanQuery)) {
      namePrefixMatches.push(entry);
    } else if (
      codeLower.includes(cleanQuery) ||
      nameLower.includes(cleanQuery) ||
      (entry.keywords && entry.keywords.some(kw => kw.toLowerCase().includes(cleanQuery)))
    ) {
      generalMatches.push(entry);
    }
  }

  const results = [
    ...exactCodeMatches,
    ...codePrefixMatches,
    ...namePrefixMatches,
    ...generalMatches
  ];

  return results.slice(0, maxResults);
}

/**
 * Lookup an ICD-10 entry by exact code.
 */
export function getICD10ByCode(code: string): ICD10Entry | undefined {
  if (!code) return undefined;
  const cleanCode = code.trim().toLowerCase();
  return ICD10_DATASET.find(item => item.code.toLowerCase() === cleanCode);
}
