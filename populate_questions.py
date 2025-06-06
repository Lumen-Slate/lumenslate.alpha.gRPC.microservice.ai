#!/usr/bin/env python3
"""
Script to populate the questions table with 120 random questions.
Distribution: 30 English, 30 Math, 30 History, 30 Science
Each question has 4 multiple choice options.
"""

import json
import random
import sys
import os

# Add the current directory to Python path to import models
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from models.sqlite import get_db, engine, Base
from models.sqlite.models import Questions

def populate_questions():
    """Populate the questions table with random questions from each subject."""
    
    # Sample questions for each subject (30 each)
    english_questions = [
        ("What is the plural form of 'child'?", ["childs", "children", "childes", "child"], "children"),
        ("Which of the following is a synonym for 'happy'?", ["sad", "joyful", "angry", "tired"], "joyful"),
        ("What type of word is 'quickly'?", ["noun", "verb", "adjective", "adverb"], "adverb"),
        ("Who wrote 'Romeo and Juliet'?", ["Charles Dickens", "William Shakespeare", "Jane Austen", "Mark Twain"], "William Shakespeare"),
        ("What is the past tense of 'run'?", ["runned", "ran", "runed", "running"], "ran"),
        ("Which of these is a compound word?", ["basketball", "running", "happy", "quickly"], "basketball"),
        ("What is an antonym for 'hot'?", ["warm", "cold", "burning", "heated"], "cold"),
        ("What is the main idea of a paragraph called?", ["topic sentence", "conclusion", "supporting detail", "transition"], "topic sentence"),
        ("Which word is spelled correctly?", ["recieve", "receive", "receve", "recieive"], "receive"),
        ("What type of sentence is 'Stop running!'?", ["declarative", "interrogative", "imperative", "exclamatory"], "imperative"),
        ("What is a metaphor?", ["a comparison using like or as", "a direct comparison", "a sound device", "a type of rhyme"], "a direct comparison"),
        ("What does the prefix 'un-' mean?", ["again", "not", "before", "after"], "not"),
        ("Which word is a proper noun?", ["city", "dog", "London", "happy"], "London"),
        ("What is alliteration?", ["rhyming words", "repeated consonant sounds", "opposite meanings", "similar meanings"], "repeated consonant sounds"),
        ("In 'The cat sat on the mat', what is the subject?", ["cat", "sat", "mat", "the"], "cat"),
        ("What is a simile?", ["a direct comparison", "a comparison using like or as", "an exaggeration", "a contradiction"], "a comparison using like or as"),
        ("What is the superlative form of 'good'?", ["gooder", "better", "best", "most good"], "best"),
        ("Which word is an abstract noun?", ["table", "happiness", "book", "car"], "happiness"),
        ("What punctuation mark ends a question?", ["period", "exclamation mark", "question mark", "comma"], "question mark"),
        ("What is personification?", ["comparing two things", "giving human qualities to non-human things", "exaggerating", "using like or as"], "giving human qualities to non-human things"),
        ("Which is the correct plural of 'mouse'?", ["mouses", "mice", "mooses", "mouse"], "mice"),
        ("What type of word connects sentences or clauses?", ["noun", "verb", "conjunction", "preposition"], "conjunction"),
        ("Which word rhymes with 'cat'?", ["dog", "hat", "car", "cup"], "hat"),
        ("What is the comparative form of 'tall'?", ["tallest", "taller", "more tall", "most tall"], "taller"),
        ("In poetry, what is a stanza?", ["a line", "a word", "a group of lines", "a rhyme"], "a group of lines"),
        ("What is the opposite of 'ancient'?", ["old", "modern", "historic", "traditional"], "modern"),
        ("Which sentence is written in passive voice?", ["The dog chased the ball.", "The ball was chased by the dog.", "I am running.", "She sings beautifully."], "The ball was chased by the dog."),
        ("What is the correct possessive form for multiple dogs?", ["dogs' toys", "dog's toys", "dogs toy's", "dogs toys'"], "dogs' toys"),
        ("Which sentence uses correct grammar?", ["Me and John went to the store.", "John and I went to the store.", "John and me went to the store.", "I and John went to the store."], "John and I went to the store."),
        ("What is a synonym for 'big'?", ["small", "large", "tiny", "little"], "large")
    ]
    
    math_questions = [
        ("What is 7 × 8?", ["54", "56", "58", "64"], "56"),
        ("What is 144 ÷ 12?", ["11", "12", "13", "14"], "12"),
        ("What is the area of a rectangle with length 6 and width 4?", ["20", "24", "28", "10"], "24"),
        ("What is 25% of 80?", ["15", "20", "25", "30"], "20"),
        ("What is the square root of 64?", ["6", "7", "8", "9"], "8"),
        ("What is 3² + 4²?", ["25", "49", "24", "12"], "25"),
        ("What is the perimeter of a square with side length 5?", ["15", "20", "25", "10"], "20"),
        ("What is 0.5 as a fraction?", ["1/3", "1/2", "2/3", "3/4"], "1/2"),
        ("What is 15 + 28?", ["43", "42", "44", "41"], "43"),
        ("What is the value of x in: 2x + 5 = 13?", ["3", "4", "5", "6"], "4"),
        ("What is 100 - 37?", ["63", "67", "73", "77"], "63"),
        ("What is 3/4 + 1/4?", ["1", "4/8", "4/4", "1 or 4/4"], "1 or 4/4"),
        ("What is the next number in the sequence: 2, 4, 8, 16, ___?", ["24", "28", "32", "20"], "32"),
        ("What is 6! (6 factorial)?", ["36", "120", "720", "5040"], "720"),
        ("What is the slope of a horizontal line?", ["0", "1", "undefined", "-1"], "0"),
        ("What is 2⁴?", ["8", "12", "16", "24"], "16"),
        ("What is the area of a circle with radius 3? (Use π)", ["6π", "9π", "12π", "18π"], "9π"),
        ("What is the greatest common factor of 12 and 18?", ["3", "6", "9", "12"], "6"),
        ("What is 5x - 3x?", ["2x", "8x", "2", "15x"], "2x"),
        ("What is the volume of a cube with side length 3?", ["9", "18", "27", "36"], "27"),
        ("What is the median of: 3, 7, 9, 12, 15?", ["7", "9", "12", "15"], "9"),
        ("What is 4/5 as a decimal?", ["0.75", "0.8", "0.85", "0.9"], "0.8"),
        ("What is the sum of angles in a triangle?", ["90°", "180°", "270°", "360°"], "180°"),
        ("What is 12 × 15?", ["180", "175", "185", "170"], "180"),
        ("What is the probability of flipping heads on a fair coin?", ["0.25", "0.5", "0.75", "1"], "0.5"),
        ("If y = 3x + 2 and x = 4, what is y?", ["10", "12", "14", "16"], "14"),
        ("What is 20% of 150?", ["25", "30", "35", "40"], "30"),
        ("What is 8²?", ["16", "64", "128", "256"], "64"),
        ("What is the circumference of a circle with radius 5? (Use 2πr)", ["5π", "10π", "25π", "50π"], "10π"),
        ("What is 72 ÷ 8?", ["8", "9", "10", "11"], "9")
    ]
    
    history_questions = [
        ("In which year did World War II end?", ["1944", "1945", "1946", "1947"], "1945"),
        ("Who was the first President of the United States?", ["Thomas Jefferson", "John Adams", "George Washington", "Benjamin Franklin"], "George Washington"),
        ("Which ancient civilization built the pyramids of Giza?", ["Greeks", "Romans", "Egyptians", "Mesopotamians"], "Egyptians"),
        ("In which year did the Berlin Wall fall?", ["1987", "1988", "1989", "1990"], "1989"),
        ("Who was the famous queen of ancient Egypt?", ["Nefertiti", "Cleopatra", "Hatshepsut", "Ankhesenamun"], "Cleopatra"),
        ("Which empire was ruled by Julius Caesar?", ["Greek Empire", "Roman Empire", "Persian Empire", "Byzantine Empire"], "Roman Empire"),
        ("In which year did the American Civil War begin?", ["1860", "1861", "1862", "1863"], "1861"),
        ("Who discovered America in 1492?", ["Vasco da Gama", "Ferdinand Magellan", "Christopher Columbus", "Amerigo Vespucci"], "Christopher Columbus"),
        ("Which war was fought between 1914-1918?", ["World War II", "World War I", "Korean War", "Vietnam War"], "World War I"),
        ("Who was the British Prime Minister during most of World War II?", ["Neville Chamberlain", "Winston Churchill", "Clement Attlee", "Anthony Eden"], "Winston Churchill"),
        ("Which revolution began in France in 1789?", ["Industrial Revolution", "French Revolution", "American Revolution", "Russian Revolution"], "French Revolution"),
        ("Who was the leader of Nazi Germany?", ["Heinrich Himmler", "Joseph Goebbels", "Adolf Hitler", "Hermann Göring"], "Adolf Hitler"),
        ("In which year did the Titanic sink?", ["1910", "1911", "1912", "1913"], "1912"),
        ("Who was the first man to walk on the moon?", ["Buzz Aldrin", "Neil Armstrong", "John Glenn", "Alan Shepard"], "Neil Armstrong"),
        ("In which year did India gain independence?", ["1946", "1947", "1948", "1949"], "1947"),
        ("Who wrote the 95 Theses?", ["John Calvin", "Martin Luther", "Thomas Aquinas", "Erasmus"], "Martin Luther"),
        ("Which battle marked the end of Napoleon's rule?", ["Battle of Austerlitz", "Battle of Waterloo", "Battle of Leipzig", "Battle of Trafalgar"], "Battle of Waterloo"),
        ("In which year did the Russian Revolution occur?", ["1916", "1917", "1918", "1919"], "1917"),
        ("Which treaty ended World War I?", ["Treaty of Versailles", "Treaty of Paris", "Treaty of Trianon", "Treaty of Sevres"], "Treaty of Versailles"),
        ("Who was the founder of the Mongol Empire?", ["Kublai Khan", "Genghis Khan", "Ogedei Khan", "Tolui Khan"], "Genghis Khan"),
        ("In which city was President Kennedy assassinated?", ["Houston", "Austin", "Dallas", "San Antonio"], "Dallas"),
        ("Which civilization created the first writing system?", ["Egyptians", "Sumerians", "Chinese", "Greeks"], "Sumerians"),
        ("Who was the last Tsar of Russia?", ["Nicholas I", "Alexander III", "Nicholas II", "Alexander II"], "Nicholas II"),
        ("In which year did the Cold War officially end?", ["1989", "1990", "1991", "1992"], "1991"),
        ("Which explorer first reached the South Pole?", ["Robert Scott", "Ernest Shackleton", "Roald Amundsen", "Edmund Hillary"], "Roald Amundsen"),
        ("Who was the leader of the Soviet Union during the Cuban Missile Crisis?", ["Joseph Stalin", "Leonid Brezhnev", "Nikita Khrushchev", "Mikhail Gorbachev"], "Nikita Khrushchev"),
        ("In which year did the Boston Tea Party occur?", ["1772", "1773", "1774", "1775"], "1773"),
        ("Which ancient wonder was located in Alexandria?", ["Colossus of Rhodes", "Lighthouse of Alexandria", "Hanging Gardens", "Temple of Artemis"], "Lighthouse of Alexandria"),
        ("Who was the first female pharaoh of Egypt?", ["Cleopatra", "Nefertiti", "Hatshepsut", "Ankhesenamun"], "Hatshepsut"),
        ("Which dynasty built the Great Wall of China?", ["Han Dynasty", "Tang Dynasty", "Ming Dynasty", "Qing Dynasty"], "Ming Dynasty")
    ]
    
    science_questions = [
        ("What is the chemical symbol for water?", ["H2O", "CO2", "NaCl", "O2"], "H2O"),
        ("How many bones are in the adult human body?", ["196", "206", "216", "226"], "206"),
        ("What gas do plants absorb during photosynthesis?", ["Oxygen", "Nitrogen", "Carbon dioxide", "Hydrogen"], "Carbon dioxide"),
        ("What is the smallest unit of matter?", ["Molecule", "Atom", "Cell", "Electron"], "Atom"),
        ("Which planet is closest to the Sun?", ["Venus", "Earth", "Mercury", "Mars"], "Mercury"),
        ("What is the largest organ in the human body?", ["Liver", "Lung", "Brain", "Skin"], "Skin"),
        ("What is the chemical formula for table salt?", ["NaCl", "KCl", "CaCl2", "MgCl2"], "NaCl"),
        ("How many chambers does a human heart have?", ["2", "3", "4", "5"], "4"),
        ("What is the process by which plants make food?", ["Respiration", "Photosynthesis", "Transpiration", "Germination"], "Photosynthesis"),
        ("What is the hardest natural substance on Earth?", ["Gold", "Iron", "Diamond", "Quartz"], "Diamond"),
        ("Which blood type is the universal donor?", ["A", "B", "AB", "O"], "O"),
        ("What is the center of an atom called?", ["Electron", "Proton", "Neutron", "Nucleus"], "Nucleus"),
        ("How many chromosomes do humans have?", ["44", "46", "48", "50"], "46"),
        ("What is the most abundant gas in Earth's atmosphere?", ["Oxygen", "Carbon dioxide", "Nitrogen", "Argon"], "Nitrogen"),
        ("Which organelle is the powerhouse of the cell?", ["Nucleus", "Ribosome", "Mitochondria", "Chloroplast"], "Mitochondria"),
        ("What is the pH of pure water?", ["6", "7", "8", "9"], "7"),
        ("What force keeps planets in orbit around the Sun?", ["Electromagnetic", "Strong nuclear", "Weak nuclear", "Gravitational"], "Gravitational"),
        ("What is the main component of the Sun?", ["Helium", "Hydrogen", "Oxygen", "Carbon"], "Hydrogen"),
        ("How many teeth does an adult human typically have?", ["28", "30", "32", "34"], "32"),
        ("What is the study of earthquakes called?", ["Geology", "Seismology", "Meteorology", "Oceanography"], "Seismology"),
        ("Which element has the chemical symbol 'Fe'?", ["Fluorine", "Iron", "Lead", "Francium"], "Iron"),
        ("What is the largest planet in our solar system?", ["Saturn", "Jupiter", "Neptune", "Uranus"], "Jupiter"),
        ("What is water changing from liquid to gas called?", ["Condensation", "Evaporation", "Sublimation", "Precipitation"], "Evaporation"),
        ("Which vitamin is produced by sunlight exposure?", ["Vitamin A", "Vitamin B", "Vitamin C", "Vitamin D"], "Vitamin D"),
        ("What galaxy contains our solar system?", ["Andromeda", "Milky Way", "Whirlpool", "Triangulum"], "Milky Way"),
        ("How many pairs of ribs do humans have?", ["10", "11", "12", "13"], "12"),
        ("What is the chemical symbol for gold?", ["Go", "Gd", "Au", "Ag"], "Au"),
        ("Which part of the brain controls balance?", ["Cerebrum", "Cerebellum", "Brain stem", "Hippocampus"], "Cerebellum"),
        ("What is the speed of light in vacuum?", ["300,000 km/s", "3,000,000 km/s", "30,000 km/s", "300,000,000 m/s"], "300,000,000 m/s"),
        ("What type of energy is stored in food?", ["Kinetic", "Potential", "Chemical", "Thermal"], "Chemical")
    ]
    
    # Combine all questions with their subjects
    all_questions = [
        ("English", english_questions),
        ("Math", math_questions), 
        ("History", history_questions),
        ("Science", science_questions)
    ]
    
    # Create all tables
    Base.metadata.create_all(bind=engine)
    
    db_gen = get_db()
    db = next(db_gen)
    
    try:
        questions_added = 0
        
        for subject_name, questions_list in all_questions:
            print(f"\n📚 Adding {subject_name} questions...")
            for question_text, options, answer in questions_list:
                question = Questions(
                    subject=subject_name,
                    question=question_text,
                    options=json.dumps(options),
                    answer=answer
                )
                
                db.add(question)
                questions_added += 1
                print(f"  ✓ Added: {question_text[:60]}...")
        
        db.commit()
        print(f"\n🎉 Successfully added {questions_added} questions to the database!")
        
        # Verify the data
        total_questions = db.query(Questions).count()
        print(f"\n📊 Database Summary:")
        print(f"Total questions in database: {total_questions}")
        
        for subject in ["English", "Math", "History", "Science"]:
            count = db.query(Questions).filter(Questions.subject == subject).count()
            print(f"  {subject}: {count} questions")
            
    except Exception as e:
        print(f"❌ Error occurred: {e}")
        db.rollback()
        raise
    finally:
        db.close()

if __name__ == "__main__":
    print("🚀 Starting to populate questions database...")
    populate_questions()
    print("✅ Script completed successfully!") 