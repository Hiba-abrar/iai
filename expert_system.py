"""
expert_system.py — the rule-based expert system behind the Health Diagnosis Assistant.

This file contains ONLY the diagnosis engine (no Streamlit / UI code).
app.py imports expert_diagnose() from here and displays the results.
"""

# ════════════════════════════════════════════════════════════════════════════
#  EXPERT SYSTEM  (rule-based inference engine)
#  ─ Knowledge base   : one explicit IF / ELIF / ELSE rule per condition (below)
#  ─ Working memory   : Facts  (the symptoms, days and severity the user entered)
#  ─ Inference engine : expert_diagnose()  fires every rule and adjusts certainty
#  ─ Explanation      : every fired rule also returns the symptoms that triggered it
# ════════════════════════════════════════════════════════════════════════════

# ── Symptom groups: dropdown names that mean the same clinical thing (only symptoms that exist in diseases.csv) ──
FEVER     = ("Fever",)
COUGH     = ("Cough", "Coughing", "Persistent Cough", "Chronic Cough", "Cough with Phlegm", "Cough at Night")
HEADACHE  = ("Headache", "Mild Headache", "Occasional Headaches", "Severe Headache")
BREATH    = ("Shortness of Breath", "Rapid Breathing", "Breathlessness")
NAUSEA    = ("Nausea", "Vomiting")
TIRED     = ("Fatigue", "Mild Fatigue", "Weakness")
BELLY     = ("Abdominal Cramps", "Severe Abdominal Pain", "Stomach Pain", "Pain Around Navel")
DIZZY     = ("Dizziness", "Lightheadedness")
THROAT    = ("Sore Throat", "Itchy Throat")
ACHES     = ("Body Ache", "Muscle Pain")
APPETITE  = ("Loss of Appetite",)
WTLOSS    = ("Unexplained Weight Loss",)

NONE = (0, [])      # "rule did not fire"

HIGH_FEVER_MIN = 7  # Fever rated 7-10 counts as a HIGH fever
MILD_FEVER_MAX = 4  # Fever rated 1-4  counts as a MILD / low-grade fever


# ── Working memory ──────────────────────────────────────────────────────────
class Facts:
    """What the user told us: each selected symptom with its duration and severity."""
    def __init__(self, symptoms, days, severity):
        self.severity = dict(zip(symptoms, severity))
        self.days     = dict(zip(symptoms, days))

    def has(self, *names):                     # True if ANY of these symptoms was reported
        return any(n in self.severity for n in names)

    def count(self, *names):                   # how many of these symptoms were reported
        return sum(1 for n in names if n in self.severity)

    def high_fever(self):                      # Fever reported with a high severity score
        return self.severity.get("Fever", 0) >= HIGH_FEVER_MIN

    def mild_fever(self):                      # Fever reported with a low severity score
        return "Fever" in self.severity and self.severity["Fever"] <= MILD_FEVER_MAX

    def lasting(self, *names, days):           # True if ANY of them has lasted >= `days` days
        return any(self.days.get(n, 0) >= days for n in names)


def fire(certainty, f, names):
    """Rule fired: return its certainty (0-100) and the reported symptoms that support it."""
    return certainty, [n for n in names if n in f.severity]


# ── Knowledge base: one rule per condition ──────────────────────────────────
# Every rule reads:  IF <symptom pattern> THEN <certainty>, checked from the most
# specific (strongest) pattern down to the weakest.  ELSE the rule does not fire.

def rule_common_cold(f):
    S = ("Runny Nose", "Sneezing", "Sore Throat", "Nasal Congestion", "Watery Eyes", "Mild Headache") + COUGH + (("Fever",) if f.mild_fever() else ())   # only a MILD fever fits a cold
    if not f.has(*S):
        return NONE
    elif f.lasting(*S, days=21):                       # a cold clears within ~2 weeks
        return fire(20, f, S)
    elif f.has("Runny Nose") and f.has("Sneezing") and (f.has("Sore Throat", *COUGH) or f.mild_fever()):
        return fire(90, f, S)
    elif f.count("Runny Nose", "Sneezing", "Nasal Congestion", "Sore Throat", "Watery Eyes") >= 3:
        return fire(75, f, S)
    elif f.count(*S) >= 3:
        return fire(55, f, S)
    elif f.count(*S) >= 2:
        return fire(35, f, S)
    else:
        return fire(15, f, S)                          # only one cold symptom reported


def rule_flu(f):
    S = ("Body Ache", "Headache", "Chills", "Fatigue", "Sore Throat", "Sweating", "Muscle Pain", "Mild Fatigue", "Weakness") + FEVER + COUGH
    fever, aches = f.has(*FEVER), f.has(*ACHES)
    if f.lasting(*S, days=14):                         # flu is an acute illness
        return fire(30, f, S) if f.count(*S) >= 3 else fire(15, f, S)
    elif fever and aches and f.has("Chills") and f.has(*TIRED, *COUGH, *THROAT):
        return fire(90, f, S)
    elif fever and aches and f.has("Chills", *TIRED, *COUGH, *THROAT, *HEADACHE):
        return fire(75, f, S)
    elif f.high_fever() and f.count(*S) >= 3:
        return fire(65, f, S)
    elif fever and f.count(*S) >= 4:
        return fire(50, f, S)
    elif fever and aches:
        return fire(40, f, S)
    elif f.has("Chills") and f.count(*S) >= 3:         # chills + several flu symptoms, even without a fever entry
        return fire(45, f, S)
    elif f.has(*S):                                    # fallback: at least one symptom of this condition was reported
        return fire(15, f, S)
    else:
        return NONE


def rule_covid19(f):
    S = ("Loss of Smell", "Fatigue", "Body Ache", "Sore Throat", "Headache") + FEVER + COUGH + BREATH
    fever, cough = f.has(*FEVER), f.has(*COUGH)
    if f.has("Loss of Smell") and fever and cough:
        return fire(95, f, S)
    elif f.has("Loss of Smell") and f.count(*S) >= 3:
        return fire(85, f, S)
    elif fever and cough and f.has(*BREATH):
        return fire(80, f, S)
    elif fever and cough and f.count(*S) >= 4:
        return fire(65, f, S)
    elif f.has("Loss of Smell"):                       # hallmark symptom on its own
        return fire(45, f, S)
    elif fever and cough:
        return fire(35, f, S)
    elif f.count(*S) >= 3:
        return fire(30, f, S)
    elif f.has(*S):                                    # fallback: at least one symptom of this condition was reported
        return fire(15, f, S)
    else:
        return NONE


def rule_strep_throat(f):
    S = ("Sore Throat", "Difficulty Swallowing", "Red Spots on Palate", "Swollen Lymph Nodes", "Headache", "Nausea", "Loss of Appetite") + FEVER
    if not f.has("Sore Throat"):                       # without a sore throat only the specific signs count
        return fire(40, f, S) if f.has("Red Spots on Palate", "Swollen Lymph Nodes") and f.count(*S) >= 3 else fire(15, f, S)
    elif f.has("Red Spots on Palate"):
        return fire(90, f, S)
    elif f.has(*FEVER) and f.has("Swollen Lymph Nodes", "Difficulty Swallowing") and not f.has(*COUGH, "Runny Nose"):
        return fire(85, f, S)
    elif f.has(*FEVER) and f.has("Swollen Lymph Nodes", "Difficulty Swallowing"):
        return fire(55, f, S)                          # cough / runny nose point to a virus instead
    elif f.count(*S) >= 3:
        return fire(50, f, S)
    elif f.has(*FEVER):
        return fire(35, f, S)
    elif f.has(*S):                                    # fallback: at least one symptom of this condition was reported
        return fire(15, f, S)
    else:
        return NONE


def rule_pneumonia(f):
    S = ("Chest Pain", "Cough with Phlegm", "Shaking Chills", "Fatigue", "Rapid Breathing", "Sweating") + FEVER + COUGH + BREATH
    cough, fever, breath = f.has(*COUGH), f.has(*FEVER), f.has(*BREATH)
    if cough and fever and breath and f.has("Shaking Chills", "Chest Pain"):
        return fire(90, f, S)
    elif cough and fever and f.has("Shaking Chills", "Chest Pain", "Cough with Phlegm"):
        return fire(80, f, S)
    elif f.has("Cough with Phlegm") and breath:
        return fire(70, f, S)
    elif f.has("Chest Pain") and cough and breath:
        return fire(65, f, S)
    elif cough and fever and breath:
        return fire(55, f, S)
    elif f.count(*S) >= 4:
        return fire(50, f, S)
    elif f.count(*S) >= 3:
        return fire(35, f, S)
    elif f.has(*S):                                    # fallback: at least one symptom of this condition was reported
        return fire(15, f, S)
    else:
        return NONE


def rule_asthma(f):
    S = ("Wheezing", "Chest Tightness", "Difficulty Sleeping", "Cough at Night") + COUGH + BREATH
    if f.has("Wheezing") and f.has("Chest Tightness", *BREATH) and f.has(*COUGH):
        return fire(90, f, S)
    elif f.has("Wheezing") and f.count(*S) >= 3:
        return fire(80, f, S)
    elif f.has("Chest Tightness") and f.has("Cough at Night") and f.has(*BREATH):
        return fire(70, f, S)
    elif f.has("Cough at Night") and f.has("Difficulty Sleeping", "Chest Tightness", *BREATH):
        return fire(55, f, S)
    elif f.has("Wheezing"):                            # hallmark symptom on its own
        return fire(45, f, S)
    elif f.count(*S) >= 3:
        return fire(35, f, S)
    elif f.has(*S):                                    # fallback: at least one symptom of this condition was reported
        return fire(15, f, S)
    else:
        return NONE


def rule_bronchitis(f):
    S = ("Persistent Cough", "Mucus Production", "Fatigue", "Fever", "Chest Discomfort", "Sore Throat", "Shortness of Breath", "Mild Headache", "Cough")
    if f.lasting("Persistent Cough", "Chronic Cough", days=90):     # >3 months = chronic, not acute
        return fire(25, f, S)
    elif f.has("Persistent Cough") and f.has("Mucus Production") and f.has("Chest Discomfort", "Fatigue", *FEVER, "Sore Throat"):
        return fire(90, f, S)
    elif f.has("Persistent Cough") and f.count(*S) >= 3:
        return fire(75, f, S)
    elif f.has("Mucus Production") and f.has(*COUGH):
        return fire(65, f, S)
    elif f.has("Persistent Cough") and f.count(*S) >= 2:
        return fire(55, f, S)
    elif f.count(*S) >= 3:
        return fire(40, f, S)
    elif f.has(*S):                                    # fallback: at least one symptom of this condition was reported
        return fire(15, f, S)
    else:
        return NONE


def rule_allergic_rhinitis(f):
    S = ("Itchy Eyes", "Sneezing", "Watery Eyes", "Runny Nose", "Nasal Congestion", "Itchy Throat", "Postnasal Drip", "Mild Fatigue")
    fever = f.has(*FEVER)
    if not f.has(*S):
        return NONE
    elif f.count(*S) < 2:
        return fire(15, f, S)
    elif fever:                                        # allergies do not cause fever
        return fire(25, f, S)
    elif f.has("Sneezing") and f.has("Itchy Eyes", "Watery Eyes") and f.has("Runny Nose", "Nasal Congestion"):
        return fire(90, f, S)
    elif f.has("Itchy Eyes") and f.count(*S) >= 3:
        return fire(80, f, S)
    elif f.count(*S) >= 3:
        return fire(65, f, S)
    else:
        return fire(40, f, S)


def rule_migraine(f):
    S = ("Severe Throbbing Pain", "Nausea", "Sensitivity to Light", "Aura", "Vomiting", "Sensitivity to Sound", "Neck Stiffness", "Dizziness", "Severe Headache", "Headache")
    if f.has("Severe Throbbing Pain") and f.has("Aura", "Sensitivity to Light", "Sensitivity to Sound"):
        return fire(95, f, S)
    elif f.has("Aura") and f.count(*S) >= 2:
        return fire(85, f, S)
    elif f.has("Severe Throbbing Pain") and f.has(*NAUSEA):
        return fire(85, f, S)
    elif f.has("Sensitivity to Light") and f.has("Sensitivity to Sound") and f.has(*HEADACHE, *NAUSEA):
        return fire(75, f, S)
    elif f.has(*HEADACHE) and f.has(*NAUSEA) and f.has("Sensitivity to Light", "Sensitivity to Sound"):
        return fire(70, f, S)
    elif f.has("Severe Throbbing Pain"):
        return fire(55, f, S)
    elif f.has(*HEADACHE) and f.has(*NAUSEA):
        return fire(40, f, S)
    elif f.has(*S):                                    # fallback: at least one symptom of this condition was reported
        return fire(15, f, S)
    else:
        return NONE


def rule_type2_diabetes(f):
    S = ("Increased Thirst", "Frequent Urination", "Unexplained Weight Loss", "Blurred Vision", "Fatigue", "Slow Healing Wounds", "Tingling in Hands", "Frequent Infections")
    if f.has("Increased Thirst") and f.has("Frequent Urination") and f.has("Blurred Vision", "Unexplained Weight Loss", "Slow Healing Wounds"):
        return fire(95, f, S)
    elif f.has("Increased Thirst") and f.has("Frequent Urination"):
        return fire(80, f, S)
    elif f.has("Slow Healing Wounds") and f.has("Frequent Infections", "Blurred Vision", "Tingling in Hands"):
        return fire(70, f, S)
    elif f.count(*S) >= 3:
        return fire(60, f, S)
    elif f.has("Increased Thirst", "Slow Healing Wounds") and f.count(*S) >= 2:
        return fire(40, f, S)
    elif f.has(*S):                                    # fallback: at least one symptom of this condition was reported
        return fire(15, f, S)
    else:
        return NONE


def rule_hypertension(f):
    S = ("Occasional Headaches", "Dizziness", "Shortness of Breath", "Nosebleeds", "Chest Pain", "Blurred Vision", "Fatigue", "Palpitations")
    if f.has("Occasional Headaches", *HEADACHE) and f.has(*DIZZY) and f.has("Blurred Vision", "Nosebleeds", "Palpitations"):
        return fire(85, f, S)
    elif f.has("Nosebleeds") and f.count(*S) >= 2:
        return fire(75, f, S)
    elif f.count(*S) >= 4:
        return fire(65, f, S)
    elif f.count(*S) >= 3:
        return fire(50, f, S)
    elif f.has("Occasional Headaches") and f.count(*S) >= 2:
        return fire(35, f, S)
    elif f.has(*S):                                    # fallback: at least one symptom of this condition was reported
        return fire(15, f, S)
    else:
        return NONE


def rule_gastroenteritis(f):
    S = ("Diarrhea", "Vomiting", "Abdominal Cramps", "Nausea", "Fever", "Loss of Appetite", "Stomach Pain", "Dehydration")
    if f.lasting("Diarrhea", days=14):                 # diarrhea >2 weeks is not a stomach flu
        return fire(30, f, S) if f.count(*S) >= 2 else fire(15, f, S)
    elif f.has("Diarrhea") and f.has("Vomiting") and f.has(*BELLY, "Nausea", "Dehydration", *FEVER):
        return fire(95, f, S)
    elif f.has("Diarrhea") and f.has("Vomiting"):
        return fire(85, f, S)
    elif f.has("Diarrhea") and f.has("Abdominal Cramps", "Nausea") and f.count(*S) >= 3:
        return fire(80, f, S)
    elif f.has("Diarrhea") and f.count(*S) >= 2:
        return fire(65, f, S)
    elif f.has("Vomiting") and f.has("Nausea") and f.has(*BELLY):
        return fire(50, f, S)
    elif f.count(*S) >= 3:
        return fire(40, f, S)
    elif f.has(*S):                                    # fallback: at least one symptom of this condition was reported
        return fire(15, f, S)
    else:
        return NONE


def rule_uti(f):
    S = ("Painful Urination", "Frequent Urination", "Cloudy Urine", "Pelvic Pain", "Strong Urge to Urinate", "Burning Sensation", "Blood in Urine", "Lower Back Pain")
    if f.has("Painful Urination") and f.has("Burning Sensation", "Cloudy Urine", "Strong Urge to Urinate", "Blood in Urine", "Pelvic Pain"):
        return fire(95, f, S)
    elif f.has("Frequent Urination") and f.has("Strong Urge to Urinate") and f.count(*S) >= 3:
        return fire(80, f, S)
    elif f.has("Cloudy Urine") and f.count(*S) >= 2:
        return fire(70, f, S)
    elif f.has("Painful Urination") and f.has("Frequent Urination"):
        return fire(65, f, S)
    elif f.has("Painful Urination"):
        return fire(50, f, S)
    elif f.count(*S) >= 3:
        return fire(45, f, S)
    elif f.has(*S):                                    # fallback: at least one symptom of this condition was reported
        return fire(15, f, S)
    else:
        return NONE


def rule_gerd(f):
    S = ("Heartburn", "Regurgitation", "Chest Pain", "Difficulty Swallowing", "Chronic Cough", "Sour Taste in Mouth", "Bloating", "Nausea")
    if f.has("Heartburn") and f.has("Regurgitation", "Sour Taste in Mouth"):
        return fire(95, f, S)
    elif f.has("Heartburn") and f.count(*S) >= 2:
        return fire(80, f, S)
    elif f.has("Regurgitation") and f.has("Sour Taste in Mouth"):
        return fire(80, f, S)
    elif f.has("Sour Taste in Mouth", "Regurgitation") and f.count(*S) >= 2:
        return fire(55, f, S)
    elif f.has("Heartburn"):
        return fire(50, f, S)
    elif f.count(*S) >= 3:
        return fire(40, f, S)
    elif f.has(*S):                                    # fallback: at least one symptom of this condition was reported
        return fire(15, f, S)
    else:
        return NONE


def rule_anemia(f):
    S = ("Fatigue", "Weakness", "Pale Skin", "Shortness of Breath", "Dizziness", "Cold Hands and Feet", "Brittle Nails", "Headache")
    if f.has("Pale Skin") and f.has("Fatigue", "Weakness") and f.has("Cold Hands and Feet", "Brittle Nails", *DIZZY, *BREATH):
        return fire(95, f, S)
    elif f.has("Pale Skin") and f.count(*S) >= 2:
        return fire(85, f, S)
    elif f.has("Brittle Nails", "Cold Hands and Feet") and f.count(*S) >= 2:
        return fire(70, f, S)
    elif f.has(*TIRED) and f.has(*DIZZY) and f.has(*BREATH):
        return fire(50, f, S)
    elif f.count(*S) >= 3:
        return fire(40, f, S)
    elif f.has(*S):                                    # fallback: at least one symptom of this condition was reported
        return fire(15, f, S)
    else:
        return NONE


def rule_depression(f):
    S = ("Persistent Sadness", "Loss of Interest", "Insomnia", "Hopelessness", "Worthlessness", "Difficulty Concentrating", "Social Withdrawal", "Suicidal Thoughts")
    core = f.count("Persistent Sadness", "Loss of Interest", "Hopelessness", "Worthlessness")
    if core >= 2 and f.lasting(*S, days=14):           # core mood symptoms for 2+ weeks
        return fire(95, f, S)
    elif f.has("Persistent Sadness") and f.has("Loss of Interest"):
        return fire(90, f, S)
    elif f.has("Suicidal Thoughts") and f.count(*S) >= 2:
        return fire(85, f, S)
    elif core >= 2:
        return fire(80, f, S)
    elif f.count(*S) >= 3:
        return fire(65, f, S)
    elif f.has("Persistent Sadness", "Loss of Interest", "Hopelessness") and f.count(*S) >= 2:
        return fire(45, f, S)
    elif f.has(*S):                                    # fallback: at least one symptom of this condition was reported
        return fire(15, f, S)
    else:
        return NONE


def rule_anxiety(f):
    S = ("Excessive Worry", "Restlessness", "Rapid Heartbeat", "Sweating", "Trembling", "Difficulty Concentrating", "Irritability", "Sleep Problems")
    if f.has("Excessive Worry") and f.has("Restlessness", "Trembling", "Rapid Heartbeat", "Irritability", "Sleep Problems"):
        return fire(95, f, S)
    elif f.count(*S) >= 4:
        return fire(70, f, S)
    elif f.has("Excessive Worry"):
        return fire(50, f, S)
    elif f.has("Restlessness", "Irritability") and f.count(*S) >= 3:
        return fire(45, f, S)
    elif f.count(*S) >= 3:
        return fire(35, f, S)
    elif f.has(*S):                                    # fallback: at least one symptom of this condition was reported
        return fire(15, f, S)
    else:
        return NONE


def rule_ibs(f):
    S = ("Abdominal Cramps", "Bloating", "Diarrhea", "Constipation", "Mucus in Stool", "Gas", "Stomach Pain", "Urgency to Defecate")
    if f.has("Mucus in Stool") and f.has("Abdominal Cramps", "Bloating", "Gas"):
        return fire(90, f, S)
    elif f.has("Abdominal Cramps") and f.has("Bloating") and f.has("Diarrhea", "Constipation"):
        return fire(85, f, S)
    elif f.has("Diarrhea") and f.has("Constipation"):  # alternating bowel habit
        return fire(75, f, S)
    elif f.count(*S) >= 3:
        return fire(65, f, S)
    elif f.count(*S) >= 2:
        return fire(35, f, S)
    elif f.has(*S):                                    # fallback: at least one symptom of this condition was reported
        return fire(15, f, S)
    else:
        return NONE


def rule_appendicitis(f):
    S = ("Severe Abdominal Pain", "Pain Around Navel", "Nausea", "Vomiting", "Fever", "Loss of Appetite", "Abdominal Rigidity", "Rebound Tenderness")
    if f.has("Rebound Tenderness", "Abdominal Rigidity") and f.has(*BELLY):
        return fire(95, f, S)
    elif f.has("Pain Around Navel") and f.has(*NAUSEA) and f.has(*FEVER, *APPETITE):
        return fire(90, f, S)
    elif f.has("Severe Abdominal Pain") and f.has(*NAUSEA) and f.has(*FEVER):
        return fire(80, f, S)
    elif f.has("Pain Around Navel") and f.count(*S) >= 2:
        return fire(75, f, S)
    elif f.has("Severe Abdominal Pain") and f.count(*S) >= 2:
        return fire(60, f, S)
    elif f.count(*S) >= 3:
        return fire(45, f, S)
    elif f.has(*S):                                    # fallback: at least one symptom of this condition was reported
        return fire(15, f, S)
    else:
        return NONE


def rule_tuberculosis(f):
    S = ("Persistent Cough", "Coughing Blood", "Night Sweats", "Unexplained Weight Loss", "Fatigue", "Fever", "Chest Pain", "Loss of Appetite", "Cough", "Chronic Cough")
    if f.lasting(*COUGH, days=21) and f.has("Night Sweats", "Unexplained Weight Loss", "Coughing Blood", *FEVER):
        return fire(90, f, S)                          # cough > 3 weeks + constitutional signs
    elif f.has("Coughing Blood") and f.has("Night Sweats", *WTLOSS):
        return fire(90, f, S)
    elif f.has("Night Sweats") and f.has(*WTLOSS) and f.has(*COUGH):
        return fire(90, f, S)
    elif f.has("Night Sweats") and f.has(*WTLOSS):
        return fire(70, f, S)
    elif f.lasting(*COUGH, days=14) and f.count(*S) >= 3:
        return fire(65, f, S)
    elif f.has("Coughing Blood"):
        return fire(60, f, S)
    elif f.count(*S) >= 4:
        return fire(50, f, S)
    elif f.count(*S) >= 3:
        return fire(35, f, S)
    elif f.has(*S):                                    # fallback: at least one symptom of this condition was reported
        return fire(15, f, S)
    else:
        return NONE


def rule_malaria(f):
    S = ("Shaking Chills", "Sweating", "Headache", "Nausea", "Vomiting", "Muscle Pain", "Fatigue") + FEVER
    if f.high_fever() and f.has("Shaking Chills") and f.has("Sweating"):
        return fire(95, f, S)
    elif f.has(*FEVER) and f.has("Shaking Chills") and f.has(*HEADACHE, *NAUSEA, "Muscle Pain"):
        return fire(85, f, S)
    elif f.has("Shaking Chills") and f.has(*FEVER):
        return fire(65, f, S)
    elif f.high_fever() and f.count(*S) >= 4:
        return fire(60, f, S)
    elif f.count(*S) >= 4:
        return fire(45, f, S)
    elif f.count(*S) >= 3:
        return fire(35, f, S)
    elif f.has(*S):                                    # fallback: at least one symptom of this condition was reported
        return fire(15, f, S)
    else:
        return NONE


def rule_dengue(f):
    S = ("Severe Headache", "Pain Behind Eyes", "Joint Pain", "Muscle Pain", "Rash", "Nausea", "Vomiting") + FEVER
    fever = f.has(*FEVER)
    if f.has("Pain Behind Eyes") and fever and f.has("Joint Pain", "Muscle Pain", "Rash"):
        return fire(95, f, S)
    elif f.high_fever() and f.has("Severe Headache") and f.has("Joint Pain", "Muscle Pain", "Rash"):
        return fire(85, f, S)
    elif f.has("Pain Behind Eyes") and f.count(*S) >= 2:
        return fire(80, f, S)
    elif fever and f.has("Rash") and f.has("Joint Pain", "Muscle Pain"):
        return fire(70, f, S)
    elif f.count(*S) >= 4:
        return fire(55, f, S)
    elif f.count(*S) >= 3:
        return fire(40, f, S)
    elif f.has(*S):                                    # fallback: at least one symptom of this condition was reported
        return fire(15, f, S)
    else:
        return NONE


def rule_sinusitis(f):
    S = ("Facial Pain", "Nasal Congestion", "Runny Nose", "Reduced Sense of Smell", "Fatigue") + HEADACHE + COUGH + FEVER
    if f.has("Facial Pain") and f.has("Nasal Congestion") and f.has("Reduced Sense of Smell", "Runny Nose", *HEADACHE):
        return fire(95, f, S)
    elif f.has("Facial Pain") and f.lasting("Nasal Congestion", "Runny Nose", "Facial Pain", days=10) and f.count(*S) >= 2:
        return fire(90, f, S)                          # symptoms for 10+ days
    elif f.has("Facial Pain") and f.count(*S) >= 2:
        return fire(85, f, S)
    elif f.has("Reduced Sense of Smell") and f.has("Nasal Congestion"):
        return fire(80, f, S)
    elif f.has("Nasal Congestion") and f.has(*HEADACHE) and f.has(*FEVER):
        return fire(65, f, S)
    elif f.count(*S) >= 4:
        return fire(55, f, S)
    elif f.count(*S) >= 3:
        return fire(40, f, S)
    elif f.has(*S):                                    # fallback: at least one symptom of this condition was reported
        return fire(15, f, S)
    else:
        return NONE


def rule_stroke(f):
    S = ("Sudden Numbness", "Confusion", "Trouble Speaking", "Vision Problems", "Severe Headache", "Dizziness", "Loss of Balance", "Facial Drooping")
    key = f.count("Sudden Numbness", "Facial Drooping", "Trouble Speaking")     # FAST warning signs
    if key >= 2:
        return fire(95, f, S)
    elif key == 1 and f.count(*S) >= 3:
        return fire(85, f, S)
    elif key == 1 and f.count(*S) >= 2:
        return fire(80, f, S)
    elif key == 1:                                     # any single warning sign is treated as an emergency
        return fire(55, f, S)
    elif f.count(*S) >= 3:
        return fire(50, f, S)
    elif f.has("Loss of Balance") and f.has("Vision Problems", "Confusion"):
        return fire(35, f, S)
    elif f.has(*S):                                    # fallback: at least one symptom of this condition was reported
        return fire(15, f, S)
    else:
        return NONE


def rule_heart_attack(f):
    S = ("Chest Pain", "Shortness of Breath", "Sweating", "Nausea", "Lightheadedness", "Arm Pain", "Jaw Pain", "Fatigue")
    if f.has("Chest Pain", "Chest Tightness") and f.has("Arm Pain", "Jaw Pain") and f.has("Sweating", *BREATH, "Nausea"):
        return fire(95, f, S)
    elif f.has("Chest Pain", "Chest Tightness") and f.has("Arm Pain", "Jaw Pain"):
        return fire(90, f, S)
    elif f.has("Chest Pain") and f.has("Shortness of Breath") and f.has("Sweating"):
        return fire(85, f, S)
    elif f.has("Chest Pain") and f.count(*S) >= 2:
        return fire(65, f, S)
    elif f.has("Arm Pain", "Jaw Pain") and f.count(*S) >= 2:
        return fire(55, f, S)
    elif f.count(*S) >= 3:
        return fire(40, f, S)
    elif f.has(*S):                                    # fallback: at least one symptom of this condition was reported
        return fire(15, f, S)
    else:
        return NONE


# ── Rule base: condition name (exactly as written in diseases.csv) → its rule ──
RULES = {
    "Common Cold":                                    rule_common_cold,
    "Flu (Influenza)":                                rule_flu,
    "COVID-19":                                       rule_covid19,
    "Streptococcal Pharyngitis":                      rule_strep_throat,
    "Pneumonia (Bacterial)":                          rule_pneumonia,
    "Asthma":                                         rule_asthma,
    "Bronchitis (Acute)":                             rule_bronchitis,
    "Allergic Rhinitis (Hay Fever)":                  rule_allergic_rhinitis,
    "Migraine":                                       rule_migraine,
    "Type 2 Diabetes":                                rule_type2_diabetes,
    "Hypertension (High Blood Pressure)":             rule_hypertension,
    "Gastroenteritis (Stomach Flu)":                  rule_gastroenteritis,
    "Urinary Tract Infection (UTI)":                  rule_uti,
    "Gastroesophageal Reflux Disease (GERD)":         rule_gerd,
    "Anemia (Iron Deficiency)":                       rule_anemia,
    "Depression (Major Depressive Disorder)":         rule_depression,
    "Anxiety Disorder":                               rule_anxiety,
    "Irritable Bowel Syndrome (IBS)":                 rule_ibs,
    "Appendicitis":                                   rule_appendicitis,
    "Tuberculosis (TB)":                              rule_tuberculosis,
    "Malaria":                                        rule_malaria,
    "Dengue Fever":                                   rule_dengue,
    "Sinusitis":                                      rule_sinusitis,
    "Stroke":                                         rule_stroke,
    "Heart Attack (Myocardial Infarction)":           rule_heart_attack,
}


# ── Inference engine ────────────────────────────────────────────────────────
def adjust_for_severity(certainty, f, evidence):
    """Severe supporting symptoms raise the certainty; very mild ones lower it."""
    if certainty == 0 or not evidence:
        return 0
    avg = sum(f.severity[s] for s in evidence) / len(evidence)
    if avg >= 7:
        certainty += 5
    elif avg <= 3:
        certainty -= 10
    return max(1, min(certainty, 99))


def expert_diagnose(selected_symptoms, day_counts, severity_scores):
    """Fire every rule against the user's facts.
    Returns [(condition, certainty %, supporting symptoms)] for the rules that fired."""
    facts = Facts(selected_symptoms, day_counts, severity_scores)
    fired = []
    for condition, rule in RULES.items():
        certainty, evidence = rule(facts)
        certainty = adjust_for_severity(certainty, facts, evidence)
        if certainty > 0:
            fired.append((condition, certainty, evidence))
    return fired
