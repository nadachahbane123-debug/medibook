"""
Module IA d'orientation médicale - MediBook
Utilise TF-IDF + similarité cosinus (scikit-learn)
"""
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np

SPECIALTY_KNOWLEDGE = {
    'Cardiologie': {
        'keywords': [
            'douleur poitrine', 'douleur thoracique', 'palpitations', 'palpitation',
            'essoufflement', 'tachycardie', 'arythmie', 'infarctus', 'hypertension',
            'tension artérielle', 'cœur', 'cardiaque', 'angine poitrine', 'pression artérielle',
            'pouls', 'fibrillation', 'souffle cardiaque', 'insuffisance cardiaque',
            'malaise cardiaque', 'syncope cardiaque', 'dyspnée', 'œdème jambes',
            'douleur bras gauche', 'sueurs froides', 'oppression thoracique',
            # Répétition intentionnelle pour augmenter le poids
            'douleur poitrine douleur poitrine', 'palpitations cœur',
            'douleur thoracique cœur', 'essoufflement cardiaque'
        ],
        'urgency_keywords': ['douleur thoracique', 'infarctus', 'malaise', 'syncope', 'palpitations fortes'],
        'icon': '❤️'
    },
    'Dermatologie': {
        'keywords': [
            'peau', 'boutons peau', 'rougeurs peau', 'acné', 'éruption cutanée',
            'démangeaisons peau', 'prurit', 'eczéma', 'psoriasis', 'allergie cutanée',
            'urticaire', 'taches peau', 'cicatrice', 'grain beauté', 'verrues',
            'champignon peau', 'mycose', 'alopécie', 'perte cheveux', 'ongle',
            'peau sèche', 'brûlure peau', 'plaie', 'abcès peau', 'kyste peau',
            'dermatite', 'zona', 'impétigo', 'mélanome'
        ],
        'urgency_keywords': ['éruption soudaine', 'œdème visage', 'difficulté respirer'],
        'icon': '🧴'
    },
    'Pédiatrie': {
        'keywords': [
            'enfant', 'bébé', 'nourrisson', 'pédiatrie', 'fièvre enfant',
            'croissance enfant', 'vaccin enfant', 'développement enfant',
            'nouveau-né', 'toux enfant', 'otite enfant', 'convulsions enfant',
            'diarrhée enfant', 'vomissements enfant', 'infection enfant',
            'pleurs bébé', 'biberon', 'poids bébé', 'coliques bébé',
            'eruption bébé', 'fièvre nourrisson', 'pédiatre'
        ],
        'urgency_keywords': ['convulsions', 'fièvre élevée enfant', 'détresse respiratoire bébé'],
        'icon': '👶'
    },
    'Gynécologie': {
        'keywords': [
            'gynécologie', 'règles', 'menstruation', 'cycle menstruel', 'grossesse',
            'contraception', 'kyste ovaire', 'col utérus', 'frottis', 'ménopause',
            'douleur pelvienne', 'pertes vaginales', 'infection vaginale', 'utérus',
            'trompes', 'ovaires', 'sein', 'mammographie', 'endométriose', 'fibrome',
            'accouchement', 'fertilité', 'contraceptif', 'pilule', 'aménorrhée'
        ],
        'urgency_keywords': ['saignement anormal', 'douleur pelvienne aiguë', 'grossesse complications'],
        'icon': '🌸'
    },
    'Ophtalmologie': {
        'keywords': [
            'yeux', 'vision', 'vue basse', 'myopie', 'lunettes', 'cataracte',
            'glaucome', 'conjonctivite', 'rougeur yeux', 'larmoiement',
            'douleur yeux', 'trouble vision', 'vision floue', 'diplopie',
            'corps étranger œil', 'brûlure yeux', 'sécheresse oculaire',
            'rétine', 'cornée', 'décollement rétine', 'dégénérescence maculaire'
        ],
        'urgency_keywords': ['perte vision', 'corps étranger', 'douleur aiguë yeux'],
        'icon': '👁️'
    },
    'ORL': {
        'keywords': [
            'oreille douleur', 'nez bouché', 'gorge irritée', 'otite', 'sinusite',
            'angine', 'amygdales', 'rhume', 'toux chronique', 'surdité',
            'acouphènes', 'bourdonnements oreille', 'saignement nez', 'epistaxis',
            'voix enrouée', 'aphonie', 'ronflement', 'apnée sommeil',
            'polypose nasale', 'sinus douloureux', 'pharyngite', 'laryngite',
            'bouchon cérumen', 'vertige oreille'
        ],
        'urgency_keywords': ['hémorragie nasale', 'surdité soudaine', 'vertige sévère'],
        'icon': '👂'
    },
    'Dentisterie': {
        'keywords': [
            'dent douleur', 'dentaire', 'mal aux dents', 'carie', 'abcès dentaire',
            'gencive saignement', 'couronne dentaire', 'implant dentaire',
            'extraction dent', 'orthodontie', 'appareil dentaire',
            'sensibilité dentaire', 'plaque dentaire', 'tartre', 'bruxisme',
            'dent cassée', 'dent sagesse', 'périodontite', 'gingivite'
        ],
        'urgency_keywords': ['abcès dentaire', 'douleur intense dent', 'fracture dent'],
        'icon': '🦷'
    },
    'Neurologie': {
        'keywords': [
            'migraine', 'maux tête chroniques', 'céphalée', 'AVC',
            'accident vasculaire cérébral', 'épilepsie', 'convulsions adulte',
            'paralysie', 'engourdissement membres', 'tremblements', 'Parkinson',
            'sclérose', 'perte mémoire', 'Alzheimer', 'névralgie', 'nerf douleur',
            'sciatique', 'neuropathie', 'trouble neurologique', 'confusion',
            'perte équilibre chronique', 'diplopie neurologique'
        ],
        'urgency_keywords': ['AVC', 'paralysie soudaine', 'confusion mentale', 'convulsions adulte'],
        'icon': '🧠'
    },
    'Médecine Générale': {
        'keywords': [
            'fièvre adulte', 'fatigue générale', 'grippe', 'infection générale',
            'bilan santé', 'check-up', 'certificat médical', 'ordonnance',
            'diabète suivi', 'cholestérol', 'obésité', 'vaccin adulte',
            'consultation générale', 'asthénie', 'perte poids inexpliquée',
            'prise poids', 'stress', 'insomnie', 'anxiété générale',
            'mal général', 'malaise général'
        ],
        'urgency_keywords': ['fièvre élevée adulte', 'infection grave'],
        'icon': '🏥'
    },
    'Orthopédie': {
        'keywords': [
            'fracture os', 'entorse', 'foulure', 'douleur articulation',
            'genou douleur', 'hanche douleur', 'épaule douleur', 'poignet douleur',
            'cheville douleur', 'colonne vertébrale', 'douleur dos', 'lombalgie',
            'hernie discale', 'arthrose', 'arthrite', 'rhumatisme', 'tendinite',
            'ligament déchiré', 'douleur musculaire', 'blessure sport', 'luxation',
            'douleur osseuse', 'inflammation articulaire'
        ],
        'urgency_keywords': ['fracture', 'douleur intense os', 'incapacité marcher'],
        'icon': '🦴'
    },
    'Gastroentérologie': {
        'keywords': [
            'douleur abdominale', 'douleur estomac', 'intestin', 'diarrhée chronique',
            'constipation', 'nausée vomissement', 'brûlures estomac', 'reflux gastrique',
            'hémorroïdes', 'colon', 'foie douleur', 'pancréas', 'vésicule biliaire',
            'appendicite', 'ulcère gastrique', 'gastrite', 'colite', 'Crohn',
            'sang dans selles', 'transit perturbé', 'ballonnements', 'flatulences'
        ],
        'urgency_keywords': ['sang selles', 'vomissement sang', 'douleur abdominale aiguë'],
        'icon': '🫀'
    },
    'Urologie': {
        'keywords': [
            'douleur urinaire', 'rein douleur', 'calcul rénal', 'infection urinaire',
            'cystite', 'prostate douleur', 'difficulté uriner', 'fréquence miction',
            'incontinence', 'sang urines', 'hématurie', 'colique néphrétique',
            'testicule douleur', 'vessie douleur', 'érection problème',
            'brûlure miction', 'envie uriner fréquente'
        ],
        'urgency_keywords': ['colique néphrétique', 'sang urines', 'rétention urinaire'],
        'icon': '💊'
    },
}


def suggest_specialty(symptoms_text):
    """
    Analyse les symptômes et suggère une spécialité médicale
    en utilisant TF-IDF + cosine similarity
    """
    if not symptoms_text or len(symptoms_text.strip()) < 3:
        return {
            'specialty': 'Médecine Générale',
            'confidence': 0.0,
            'alternatives': [],
            'message': 'Veuillez décrire vos symptômes plus en détail.'
        }

    symptoms_lower = symptoms_text.lower()

    # Règles directes pour les cas clairs — priorité absolue
    direct_rules = [
        (['douleur poitrine', 'douleur thoracique', 'oppression poitrine',
          'palpitation', 'cœur', 'cardiaque', 'tachycardie', 'arythmie',
          'essoufflement effort', 'douleur bras gauche'], 'Cardiologie'),
        (['dent', 'gencive', 'carie', 'dentaire', 'bouche douleur'], 'Dentisterie'),
        (['enfant', 'bébé', 'nourrisson', 'pédiatre'], 'Pédiatrie'),
        (['règles', 'menstruation', 'grossesse', 'gynéco', 'ovaire', 'utérus'], 'Gynécologie'),
        (['yeux', 'vision', 'vue', 'œil', 'ophtalmologie'], 'Ophtalmologie'),
        (['oreille', 'gorge', 'nez', 'sinusite', 'angine', 'otite'], 'ORL'),
        (['genou', 'hanche', 'dos', 'fracture', 'entorse', 'articulation', 'lombalgie'], 'Orthopédie'),
        (['estomac', 'ventre', 'intestin', 'diarrhée', 'reflux', 'gastrite'], 'Gastroentérologie'),
        (['urine', 'rein', 'prostate', 'cystite', 'miction'], 'Urologie'),
        (['peau', 'bouton', 'acné', 'eczéma', 'démangeaison', 'éruption'], 'Dermatologie'),
        (['migraine', 'épilepsie', 'AVC', 'paralysie', 'tremblement', 'névralgie'], 'Neurologie'),
    ]

    for keywords, specialty in direct_rules:
        for kw in keywords:
            if kw in symptoms_lower:
                # Confirmer avec TF-IDF
                break
        else:
            continue

        # Calculer quand même le score pour avoir la confiance
        specialty_names = list(SPECIALTY_KNOWLEDGE.keys())
        specialty_texts = [' '.join(SPECIALTY_KNOWLEDGE[s]['keywords']) for s in specialty_names]
        all_texts = specialty_texts + [symptoms_lower]

        try:
            vectorizer = TfidfVectorizer(analyzer='word', ngram_range=(1, 2), min_df=1)
            tfidf_matrix = vectorizer.fit_transform(all_texts)
            symptoms_vector = tfidf_matrix[-1]
            specialty_vectors = tfidf_matrix[:-1]
            similarities = cosine_similarity(symptoms_vector, specialty_vectors)[0]
            ranked = sorted(zip(specialty_names, similarities), key=lambda x: x[1], reverse=True)

            idx = specialty_names.index(specialty)
            confidence = round(float(similarities[idx]) * 100, 1)

            alternatives = [
                {'name': name, 'score': round(float(score) * 100, 1)}
                for name, score in ranked[:4]
                if name != specialty and score > 0.01
            ][:3]

            icon = SPECIALTY_KNOWLEDGE.get(specialty, {}).get('icon', '🏥')
            return {
                'specialty': specialty,
                'specialty_icon': icon,
                'confidence': max(confidence, 45.0),
                'alternatives': alternatives,
                'message': f'Sur la base de vos symptômes, je vous suggère de consulter un spécialiste en {specialty} ({icon}). Cette orientation est indicative - seul un médecin peut établir un diagnostic.'
            }
        except Exception:
            icon = SPECIALTY_KNOWLEDGE.get(specialty, {}).get('icon', '🏥')
            return {
                'specialty': specialty,
                'specialty_icon': icon,
                'confidence': 50.0,
                'alternatives': [],
                'message': f'Je vous suggère de consulter un spécialiste en {specialty} ({icon}).'
            }

    # Pas de règle directe → TF-IDF pur
    specialty_names = list(SPECIALTY_KNOWLEDGE.keys())
    specialty_texts = [' '.join(SPECIALTY_KNOWLEDGE[s]['keywords']) for s in specialty_names]
    all_texts = specialty_texts + [symptoms_lower]

    try:
        vectorizer = TfidfVectorizer(analyzer='word', ngram_range=(1, 2), min_df=1, max_features=5000)
        tfidf_matrix = vectorizer.fit_transform(all_texts)
        symptoms_vector = tfidf_matrix[-1]
        specialty_vectors = tfidf_matrix[:-1]
        similarities = cosine_similarity(symptoms_vector, specialty_vectors)[0]

        ranked = sorted(zip(specialty_names, similarities), key=lambda x: x[1], reverse=True)
        top_specialty, top_score = ranked[0]
        alternatives = [
            {'name': name, 'score': round(float(score) * 100, 1)}
            for name, score in ranked[1:4]
            if score > 0.01
        ]

        if top_score < 0.05:
            return {
                'specialty': 'Médecine Générale',
                'confidence': round(float(top_score) * 100, 1),
                'alternatives': alternatives,
                'message': 'Je n\'ai pas pu identifier une spécialité précise. Je vous recommande de consulter un médecin généraliste qui vous orientera.'
            }

        confidence = round(float(top_score) * 100, 1)
        icon = SPECIALTY_KNOWLEDGE.get(top_specialty, {}).get('icon', '🏥')

        return {
            'specialty': top_specialty,
            'specialty_icon': icon,
            'confidence': confidence,
            'alternatives': alternatives,
            'message': f'Sur la base de vos symptômes, je vous suggère de consulter un spécialiste en {top_specialty} ({icon}). Cette orientation est indicative - seul un médecin peut établir un diagnostic.'
        }

    except Exception:
        return {
            'specialty': 'Médecine Générale',
            'confidence': 0.0,
            'alternatives': [],
            'message': 'Erreur d\'analyse. Consultez un médecin généraliste.'
        }


def classify_urgency(text):
    """Classifie l'urgence d'un motif de consultation"""
    text_lower = text.lower()

    high_urgency_keywords = [
        'urgent', 'urgence', 'douleur intense', 'douleur aiguë', 'sang', 'saignement',
        'perte connaissance', 'difficultés respirer', 'infarctus', 'avc', 'paralysie',
        'convulsions', 'allergie grave', 'choc', 'trauma', 'accident', 'brûlure grave',
        'intoxication', 'overdose', 'fracture', 'inconscient'
    ]

    medium_urgency_keywords = [
        'fièvre élevée', 'douleur modérée', 'infection', 'vomissements répétés',
        'forte toux', 'détérioration', 'aggravation', 'depuis plusieurs jours',
        'empirer', 'gonflement', 'inflammation'
    ]

    for keyword in high_urgency_keywords:
        if keyword in text_lower:
            return 'high'

    for keyword in medium_urgency_keywords:
        if keyword in text_lower:
            return 'medium'

    return 'low'