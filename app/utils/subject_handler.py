from ..models.sqlite.models import Subject

def get_subject_enum(subject_string):
    """Convert subject string to Subject enum, handling various formats"""
    subject_mapping = {
        'math': Subject.MATH,
        'mathematics': Subject.MATH,
        'maths': Subject.MATH,
        'science': Subject.SCIENCE,
        'biology': Subject.SCIENCE,
        'chemistry': Subject.SCIENCE,
        'physics': Subject.SCIENCE,
        'english': Subject.ENGLISH,
        'language arts': Subject.ENGLISH,
        'literature': Subject.ENGLISH,
        'reading': Subject.ENGLISH,
        'history': Subject.HISTORY,
        'social studies': Subject.HISTORY,
        'world history': Subject.HISTORY,
        'geography': Subject.GEOGRAPHY,
        'geo': Subject.GEOGRAPHY
    }
    
    normalized_subject = subject_string.lower().strip()
    return subject_mapping.get(normalized_subject, None) 