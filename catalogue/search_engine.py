"""
Smart Multilingual Medical Search Engine & Symptom Thesaurus
Provides intelligent query parsing, stop-word removal, and semantic symptom-to-medicine mapping
supporting English, Hindi (Devanagari), Hinglish, and colloquial healthcare queries.
"""

import re
import unicodedata
from django.db.models import Q, Case, When, Value, IntegerField
from .models import Medicine, HealthCategory, HealthCondition

# Common filler and stop words in Hindi (Devanagari & Romanized), Hinglish, and English
STOP_WORDS = {
    # Hinglish & Romanized stop words
    'ki', 'ka', 'ke', 'ko', 'me', 'mein', 'se', 'par', 'aur', 'ya', 'hai', 'he', 'tha',
    'wali', 'wala', 'wale', 'bhi', 'keliye', 'ke_liye', 'liye', 'kuch', 'koi', 'chahiye',
    'batao', 'dikhao', 'dawa', 'dawai', 'dawae', 'dawaiya', 'dawayen', 'goli', 'tablet',
    'tablets', 'capsule', 'capsules', 'syrup', 'injection', 'cream', 'gel', 'ointment',
    'drop', 'drops', 'medicine', 'medicines', 'drug', 'drugs', 'med', 'meds', 'ilaj',
    'upchar', 'bimaari', 'bimari', 'samadhaan', 'sahi', 'best', 'top', 'good',
    
    # Devanagari Hindi stop words
    'की', 'का', 'के', 'को', 'में', 'से', 'पर', 'और', 'या', 'है', 'था', 'थी', 'थे',
    'वाली', 'वाला', 'वाले', 'भी', 'केलिए', 'के_लिए', 'लिए', 'कुछ', 'कोई', 'चाहिए',
    'बताओ', 'दिखाओ', 'दवा', 'दवाई', 'दवाएं', 'दवाइयां', 'गोली', 'टैबलेट', 'कैप्सूल',
    'सिरप', 'इंजेक्शन', 'क्रीम', 'जेल', 'ड्रॉप', 'इलाज', 'उपचार', 'बीमारी', 'बीमारियां',
    'समाधान', 'सही', 'सबसे', 'अच्छी', 'अच्छा',

    # English stop words
    'for', 'in', 'of', 'and', 'or', 'the', 'a', 'an', 'to', 'with', 'by', 'cure',
    'treatment', 'relief', 'help', 'take', 'need', 'give', 'use', 'used', 'effective'
}

# Rich Medical Thesaurus: Maps colloquial symptom phrases to medical indications & therapeutic categories
MEDICAL_THESAURUS = [
    # --- STOMACH PAIN, ABDOMINAL CRAMPS & GASTRO / पेट दर्द ---
    {
        'triggers': [
            'pet dard', 'pet me dard', 'stomach pain', 'stomach ache', 'abdominal pain',
            'pet kharab', 'belly pain', 'cramping', 'stomach cramp', 'stomach problem',
            'पेट दर्द', 'पेट में दर्द', 'मरोड़', 'पेट खराब', 'पेट की खराबी', 'पेट दर्द की दवा'
        ],
        'keywords': [
            'pain relief', 'stomach', 'abdominal', 'gastric', 'gastro', 'antacid',
            'digestion', 'peptic', 'cramp', 'spasm', 'acid reflux', 'gerd', 'pain', 'analgesic'
        ]
    },
    # --- ACIDITY, GAS & HEARTBURN / गैस, एसिडिटी, बदहजमी ---
    {
        'triggers': [
            'gas', 'acidity', 'acid reflux', 'heartburn', 'gerd', 'badhazmi', 'khatti dakar',
            'seene me jalan', 'jalan', 'pet me jalan', 'indigestion', 'bloating', 'gastric problem',
            'gas acidity', 'gas ki dawa',
            'गैस', 'एसिडिटी', 'बदहजमी', 'खट्टी डकार', 'जलन', 'सीने में जलन', 'पेट में जलन', 'गैस की दवा'
        ],
        'keywords': [
            'pain relief', 'antacid', 'gastric', 'gastro', 'acid', 'acid reflux', 'stomach',
            'gerd', 'heartburn', 'indigestion', 'pantothenic', 'panadol', 'aleve'
        ]
    },
    # --- HEADACHE & MIGRAINE / सर दर्द ---
    {
        'triggers': [
            'sir dard', 'sar dard', 'headache', 'migraine', 'matha dard', 'aadhakapaali',
            'aadha sishi', 'head pain', 'tension headache',
            'सर दर्द', 'सिर दर्द', 'माइग्रेन', 'माथा दर्द', 'सिर का दर्द', 'सर का दर्द', 'सर दर्द की दवा'
        ],
        'keywords': [
            'headache', 'migraine', 'saridon', 'aspirin', 'paracetamol', 'panadol',
            'naprosyn', 'aleve', 'motrin', 'celebrex', 'tramadol', 'pain relief', 'analgesic'
        ]
    },
    # --- FEVER / बुखार ---
    {
        'triggers': [
            'bukhar', 'fever', 'pyrexia', 'tap', 'jwar', 'taap', 'hararat', 'badan garm',
            'बुखार', 'ज्वर', 'ताप', 'हरारत', 'बुखार की दवा'
        ],
        'keywords': [
            'fever', 'pyrexia', 'paracetamol', 'panadol', 'acetaminophen', 'dolo',
            'calpol', 'crocin', 'saridon', 'pain relief', 'antipyretic'
        ]
    },
    # --- COUGH, SORE THROAT & RESPIRATORY / खांसी, गले में दर्द ---
    {
        'triggers': [
            'khansi', 'cough', 'cough syrup', 'sukhi khansi', 'balgam', 'gale me kharash',
            'gale me dard', 'sore throat', 'throat pain', 'gala kharab',
            'खांसी', 'कफ', 'गले में खराश', 'गले में दर्द', 'बलगम', 'सूखी खांसी', 'खांसी की दवा'
        ],
        'keywords': [
            'cough', 'throat', 'pharyngitis', 'bronchitis', 'respiratory', 'cold', 'flu',
            'cough syrup', 'asthma', 'allegra', 'advair', 'ventolin', 'singulair',
            'antihistamine', 'respiratory health'
        ]
    },
    # --- COLD, FLU & RUNNY NOSE / सर्दी, जुकाम, छींक ---
    {
        'triggers': [
            'sardi', 'jukham', 'cold', 'flu', 'runny nose', 'naak behna', 'chheenk',
            'sneezing', 'nazla', 'band naak',
            'सर्दी', 'जुकाम', 'छींक', 'नाक बहना', 'नजला', 'सर्दी जुकाम', 'जुकाम की दवा'
        ],
        'keywords': [
            'cold', 'flu', 'coryza', 'rhinitis', 'allergy', 'sneezing', 'runny nose',
            'allegra', 'zyrtec', 'claritin', 'antihistamine', 'allergy medicine', 'respiratory'
        ]
    },
    # --- BODY PAIN, JOINT PAIN & ARTHRITIS / बदन दर्द, जोड़ों का दर्द ---
    {
        'triggers': [
            'badan dard', 'body pain', 'jodo ka dard', 'joint pain', 'kamar dard', 'back pain',
            'ghutne ka dard', 'knee pain', 'muscle pain', 'manspeshi dard', 'arthritis', 'gathiya',
            'swelling', 'sujan', 'dard', 'painkiller', 'pain killer',
            'दर्द', 'बदन दर्द', 'जोड़ों का दर्द', 'कमर दर्द', 'गठिया', 'सूजन', 'जोड़ों में दर्द', 'दर्द की दवा'
        ],
        'keywords': [
            'pain relief', 'analgesic', 'pain', 'arthritis', 'joint pain', 'back pain',
            'celebrex', 'naprosyn', 'aleve', 'aspirin', 'motrin', 'tramadol', 'panadol',
            'co codamol', 'inflammation'
        ]
    },
    # --- DIABETES & BLOOD SUGAR / शुगर, मधुमेह ---
    {
        'triggers': [
            'sugar', 'diabetes', 'madhumeh', 'blood sugar', 'high sugar', 'glucose', 'shugar',
            'शुगर', 'मधुमेह', 'डायबिटीज', 'ब्लड शुगर', 'शुगर की दवा'
        ],
        'keywords': [
            'diabetes', 'sugar', 'glucose', 'metformin', 'insulin', 'januvia',
            'glucophage', 'actos', 'glycemia', 'pancreas'
        ]
    },
    # --- BLOOD PRESSURE & HYPERTENSION / बीपी, ब्लड प्रेशर ---
    {
        'triggers': [
            'bp', 'blood pressure', 'high bp', 'low bp', 'hypertension', 'raktchap', 'uccha raktchap',
            'रक्तचाप', 'हाई बीपी', 'ब्लड प्रेशर', 'उच्च रक्तचाप', 'बीपी की दवा'
        ],
        'keywords': [
            'blood pressure', 'hypertension', 'blood pressure medicine', 'amlodipine',
            'lisinopril', 'losartan', 'atenolol', 'metoprolol', 'catapres',
            'cardiovascular', 'heart health'
        ]
    },
    # --- HEART HEALTH & CHOLESTEROL / दिल की बीमारी, कोलेस्ट्रॉल ---
    {
        'triggers': [
            'heart', 'dil', 'heart attack', 'chest pain', 'seene me dard', 'cholesterol', 'charbi',
            'triglyceride', 'heart health',
            'दिल', 'हार्ट', 'कोलेस्ट्रॉल', 'सीने में दर्द', 'हार्ट अटैक'
        ],
        'keywords': [
            'heart health', 'cardiology', 'angina', 'cholesterol', 'lipitor',
            'crestor', 'zocor', 'pravachol', 'amlodipine', 'aspirin', 'cardiovascular', 'statin'
        ]
    },
    # --- ASTHMA & BREATHING ISSUES / दमा, सांस फूलना ---
    {
        'triggers': [
            'asthma', 'dama', 'swas', 'sans phulna', 'saans lene me dikkat', 'breathless',
            'inhaler', 'wheezing', 'दमा', 'अस्थमा', 'सांस फूलना', 'सांस की तकलीफ'
        ],
        'keywords': [
            'asthma', 'asthma medicine', 'respiratory', 'inhaler', 'advair',
            'ventolin', 'proair', 'symbicort', 'singulair', 'bronchial', 'lungs', 'respiratory health'
        ]
    },
    # --- VOMITING & NAUSEA / उल्टी, जी मिचलाना ---
    {
        'triggers': [
            'ulti', 'vomiting', 'nausea', 'jee machlana', 'matli', 'dast ulti',
            'उल्टी', 'जी मिचलाना', 'मतली', 'उल्टी की दवा'
        ],
        'keywords': [
            'vomiting', 'nausea', 'antiemetic', 'motion sickness', 'ondansetron',
            'domperidone', 'gastric'
        ]
    },
    # --- LOOSE MOTION & DIARRHEA / दस्त, पेट खराब ---
    {
        'triggers': [
            'dast', 'loose motion', 'diarrhea', 'dehydration',
            'दस्त', 'लूज मोशन', 'डायरिया', 'दस्त की दवा'
        ],
        'keywords': [
            'diarrhea', 'loose motion', 'dehydration', 'gastro', 'ors', 'loperamide',
            'electrolytes', 'stomach'
        ]
    },
    # --- CONSTIPATION / कब्ज ---
    {
        'triggers': [
            'kabz', 'constipation', 'pet saaf', 'shoch me dikkat',
            'कब्ज', 'पेट साफ', 'कब्ज की दवा'
        ],
        'keywords': [
            'constipation', 'laxative', 'stool softener', 'dulcolax', 'senna',
            'fiber', 'gastro'
        ]
    },
    # --- ALLERGY, ITCHING & SKIN / खुजली, दाद, एलर्जी ---
    {
        'triggers': [
            'khujli', 'skin allergy', 'daadh', 'rashes', 'allergy', 'pimples', 'daane',
            'itching', 'fungal', 'daan', 'tvacha',
            'खुजली', 'दाद', 'एलर्जी', 'त्वचा', 'दाने', 'खाज', 'खुजली की दवा'
        ],
        'keywords': [
            'allergy', 'allergy medicine', 'skin', 'itching', 'urticaria', 'hives',
            'eczema', 'dermatology', 'allegra', 'zyrtec', 'claritin', 'antihistamine', 'antifungal'
        ]
    },
    # --- SLEEP, DEPRESSION & ANXIETY / नींद, तनाव, डिप्रेशन ---
    {
        'triggers': [
            'neend', 'sleep', 'insomnia', 'depression', 'stress', 'tanav', 'chinta',
            'ghabrahat', 'anxiety', 'mood', 'bechaini',
            'नींद', 'तनाव', 'डिप्रेशन', 'चिंता', 'घबराहट', 'बेचैनी', 'नींद की दवा'
        ],
        'keywords': [
            'depression', 'antidepressants', 'antidepressants medicine', 'anxiety',
            'insomnia', 'sleep', 'mental health', 'lexapro', 'zoloft', 'prozac',
            'celexa', 'cymbalta', 'wellbutrin', 'abilify', 'aplenzin'
        ]
    },
    # --- THYROID / थायरॉयड ---
    {
        'triggers': [
            'thyroid', 'thayroid', 'motapa thyroid', 'thakan thyroid',
            'थायरॉयड', 'थायराइड', 'थायराइड की दवा'
        ],
        'keywords': [
            'thyroid', 'thyroid medicine', 'hypothyroidism', 'synthroid',
            'levothyroxine', 'armour thyroid', 'metabolism'
        ]
    },
    # --- CANCER & TUMOR / कैंसर, ट्यूमर ---
    {
        'triggers': [
            'cancer', 'tumor', 'tumour', 'chemo', 'chemotherapy', 'oncology',
            'कैंसर', 'ट्यूमर', 'कैंसर की दवा'
        ],
        'keywords': [
            'cancer', 'oncology', 'chemotherapy', 'abirapro', 'cyclophosphamide',
            'tamoxifen', 'malignancy'
        ]
    },
    # --- VITAMINS & IMMUNITY / कमजोरी, विटामिन ---
    {
        'triggers': [
            'vitamin', 'vitamins', 'kamjori', 'kamzori', 'weakness', 'thakan',
            'multivitamin', 'calcium', 'iron', 'immunity', 'energy',
            'विटामिन', 'कमजोरी', 'ताकत'
        ],
        'keywords': [
            'vitamins & supplements', 'vitamin', 'calcium', 'iron', 'mineral',
            'multivitamin', 'energy', 'immunity', 'supplement'
        ]
    },
    # --- ANTIBIOTICS & INFECTIONS / इन्फेक्शन, एंटीबायोटिक ---
    {
        'triggers': [
            'antibiotic', 'infection', 'infeksion', 'bacterial', 'ghav', 'pus',
            'jakham', 'foda',
            'इन्फेक्शन', 'एंटीबायोटिक', 'घाव', 'बैक्टीरियल'
        ],
        'keywords': [
            'antibiotic', 'infection', 'bacterial', 'amoxil', 'augmentin',
            'cipro', 'zithromax', 'keflex', 'antimicrobial'
        ]
    }
]

def normalize_text(text):
    """Normalize unicode characters, trim spaces and lower-case text."""
    if not text:
        return ""
    text = unicodedata.normalize('NFKD', text)
    # Remove excessive punctuation while keeping Hindi and English characters intact
    text = re.sub(r'[\'\"\.,\/\?!\(\)\[\]\{\}\+\-\*&%$#@~`^|<>]+', ' ', text)
    text = re.sub(r'\s+', ' ', text).strip().lower()
    return text

def extract_search_tokens(raw_query):
    """
    Cleans the query, filters stop-words, and extracts core search tokens
    with prioritized compound phrase thesaurus expansions.
    """
    norm = normalize_text(raw_query)
    if not norm:
        return [], []

    expanded_terms = set()
    matched_compound = False

    # 1. First Pass: Multi-word Compound Phrase Matching (e.g. 'pet dard', 'सर दर्द', 'blood pressure')
    for entry in MEDICAL_THESAURUS:
        for trigger in entry['triggers']:
            t_norm = normalize_text(trigger)
            if t_norm and (t_norm in norm or norm in t_norm):
                matched_compound = True
                for kw in entry['keywords']:
                    expanded_terms.add(kw)

    # 2. Tokenize into individual words
    raw_tokens = norm.split()
    core_tokens = [w for w in raw_tokens if w not in STOP_WORDS and len(w) > 1]

    # If all tokens were stop words, fall back to raw tokens
    if not core_tokens and raw_tokens:
        core_tokens = raw_tokens

    # 3. Second Pass: Single-word Matching if no compound was matched
    if not matched_compound:
        for word in core_tokens:
            for entry in MEDICAL_THESAURUS:
                for trigger in entry['triggers']:
                    t_norm = normalize_text(trigger)
                    if word == t_norm or (len(word) >= 4 and (word in t_norm or t_norm in word)):
                        for kw in entry['keywords']:
                            expanded_terms.add(kw)

    return core_tokens, list(expanded_terms)

def execute_smart_search(raw_query):
    """
    Executes a high-relevance multi-tiered search across Medicine catalog.
    Returns: (medicines_queryset, matched_categories_queryset, matched_conditions_queryset, meta_info)
    """
    if not raw_query or not raw_query.strip():
        return (Medicine.objects.none(), HealthCategory.objects.none(), HealthCondition.objects.none(), {})

    core_tokens, expanded_keywords = extract_search_tokens(raw_query)
    clean_query = normalize_text(raw_query)

    # Base Queryset with prefetching
    base_qs = Medicine.objects.filter(is_active=True).select_related(
        'manufacturer', 'category'
    ).prefetch_related('category_image_assets', 'images', 'categories', 'conditions')

    # Tier 1: Direct Exact / Substring match in medicine name, generic name, brand name
    tier1_q = (
        Q(name__icontains=clean_query) |
        Q(generic_name__icontains=clean_query) |
        Q(brand_name__icontains=clean_query)
    )

    # Tier 2: Token match in names, generic name, brand name, composition, also_known_as
    tier2_q = Q()
    for token in core_tokens:
        tier2_q |= (
            Q(name__icontains=token) |
            Q(generic_name__icontains=token) |
            Q(brand_name__icontains=token) |
            Q(also_known_as__icontains=token) |
            Q(composition__icontains=token)
        )

    # Tier 3: Thesaurus & Symptom/Indication/Category match
    tier3_q = Q()
    all_search_terms = list(set(core_tokens + expanded_keywords))
    for term in all_search_terms:
        tier3_q |= (
            Q(name__icontains=term) |
            Q(generic_name__icontains=term) |
            Q(uses__icontains=term) |
            Q(conditions__name__icontains=term) |
            Q(categories__name__icontains=term) |
            Q(category__name__icontains=term)
        )

    # Tier 4: Broad overview/description match
    tier4_q = Q()
    for token in core_tokens:
        tier4_q |= (
            Q(overview__icontains=token) |
            Q(description__icontains=token) |
            Q(how_it_works__icontains=token)
        )

    combined_filter = tier1_q | tier2_q | tier3_q | tier4_q
    matched_medicines = base_qs.filter(combined_filter).distinct()

    # Annotate relevance score for optimal sorting (100 -> 80 -> 50 -> 20)
    scored_medicines = matched_medicines.annotate(
        relevance_score=Case(
            When(tier1_q, then=Value(100)),
            When(tier2_q, then=Value(80)),
            When(tier3_q, then=Value(50)),
            When(tier4_q, then=Value(20)),
            default=Value(10),
            output_field=IntegerField()
        )
    ).order_by('-relevance_score', 'name')

    # Also find matching categories
    cat_q = Q(name__icontains=clean_query)
    for term in all_search_terms:
        cat_q |= Q(name__icontains=term) | Q(description__icontains=term)
    matched_categories = HealthCategory.objects.filter(cat_q).distinct()[:6]

    # Also find matching conditions
    cond_q = Q(name__icontains=clean_query)
    for term in all_search_terms:
        cond_q |= Q(name__icontains=term) | Q(description__icontains=term)
    matched_conditions = HealthCondition.objects.filter(cond_q).select_related('category').distinct()[:6]

    meta_info = {
        'clean_query': clean_query,
        'core_tokens': core_tokens,
        'expanded_keywords': expanded_keywords,
        'has_symptom_expansion': len(expanded_keywords) > 0,
    }

    return (scored_medicines, matched_categories, matched_conditions, meta_info)
