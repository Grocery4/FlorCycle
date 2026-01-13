from .models import DailyLog, Symptom, Mood, Medication

def get_day_log(user, target_date):
    return DailyLog.objects.filter(user=user, date=target_date).first()

def initialize_log_data():
    """
    Populates the database with initial symptoms, moods, and medications
    if they don't already exist.
    """
    symptoms = [
        "Abdominal cramps", "Acne", "Anxiety", "Backache", "Bloating", "Body ache",
        "Cervical firmness", "Cervical mucus", "Cervical opening", "Chills", "Confusion",
        "Constipation", "Cottage-cheese", "Cramps", "Cravings", "Creamy", "Diarrhea",
        "Dizziness", "Dry", "Egg-white", "Fainting", "Fatigue", "Fever", "Foul-smelling",
        "Gas", "Green", "Headache", "Hot flashees", "Hunger", "Illness", "Influenza",
        "Insomnia", "Irritability", "Irritation", "Itchiness", "Low back pain",
        "Migraines", "Moodiness", "Muscle pain", "Nausea", "Neck ache", "Night sweats",
        "Ovulation Pain", "Pelvic pain", "Pms", "Rashes", "Sensitive breasts",
        "Severe Pain", "Shoulder ache", "Sticky", "Stress", "Breast tenderness",
        "Tension", "Unable to concentrate", "Watery", "Weight gain", "With blood"
    ]

    moods = [
        "Angry", "Anxious", "Ashamed", "Assertive", "Bashful", "Blue", "Bored",
        "Confident", "Depresed", "Disappointed", "Distrustful", "Embarassed",
        "Emotional", "Evil", "Excited", "Exhausted", "Fliratious", "Forgetful",
        "Frisky", "Frustrated", "Furious", "Good", "Grumpy", "Happy", "Harsh",
        "Hopeful", "Horny", "Ill", "Impatient", "In love", "Indifferent", "Inspired",
        "Jealous", "Lonely", "Mischievous", "Miserable", "Neutral", "Normal",
        "Panicky", "Peaceful", "Playful", "Proud", "Pure", "Relaxed", "Sad",
        "Satisfied", "Secretive", "Sexy", "Silly", "Sleepy", "Smug", "Stressed",
        "Stunned", "Surprise", "Tense", "Tormented", "Unsafe", "Weird", "Worried"
    ]

    medications = [
        "Contraceptive pill", "V-ring", "Patch", "Injection", "IUD", "Implant"
    ]

    for name in symptoms:
        Symptom.objects.get_or_create(name=name)

    for name in moods:
        Mood.objects.get_or_create(name=name)

    for name in medications:
        Medication.objects.get_or_create(name=name)