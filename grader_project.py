import json
import unittest
from abc import ABC, abstractmethod
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import Callable, Dict, List, Tuple
from dataclasses import dataclass

def log_grading(func):
    def wrapper(*args, **kwargs):
        print(f"Ocjenjivanje: {func.__name__}")
        result = func(*args, **kwargs)
        print(f"Gotovo!")
        return result
    return wrapper

def time_measure(func):
    import time
    def wrapper(*args, **kwargs):
        start = time.time()
        result = func(*args, **kwargs)
        elapsed = time.time() - start
        print(f"Vrijeme potrebno za ocjenjivanje: {elapsed:.3f}s")
        return result
    return wrapper

def make_grading_scale(min_pass: float = 50.0) -> Callable[[float], Tuple[int, str]]:
    """
    >>> checker = make_grading_scale(50)
    >>> grade, name = checker(95.0)
    >>> grade == 5
    True
    >>> grade_2, name_2 = checker(55.0)
    >>> grade_2 == 2
    True
    """
    attempts = 0
    last_percentage = None
    
    def assign_grade(percentage: float) -> Tuple[int, str]:
        nonlocal attempts, last_percentage
        
        attempts += 1
        last_percentage = percentage
      
        if percentage >= 90:
            return 5, "odličan"
        elif percentage >= 80:
            return 4, "vrlo dobar"
        elif percentage >= 60:
            return 3, "dobar"
        elif percentage >= min_pass:
            return 2, "dovoljan"
        else:
            return 1, "nedovoljan"
    
    def get_stats() -> Dict:
        return {'attempts': attempts, 'last_percentage': last_percentage}
    
    assign_grade.get_stats = get_stats
    return assign_grade

class Evaluator(ABC):
   
    @abstractmethod
    def evaluate(self, student_answers: Dict[int, str], reference: Dict[int, str]) -> int:
        pass

class SimpleEvaluator(Evaluator):
    
    def evaluate(self, student_answers: Dict[int, str], reference: Dict[int, str]) -> int:
        correct = 0
        for question_id, correct_answer in reference.items():
            if student_answers.get(question_id) == correct_answer:
                correct += 1
        return correct

@dataclass
class ExamResult:
    student_name: str
    correct_answers: int
    total_questions: int
    percentage: float
    grade: int
    grade_name: str
    
    def __str__(self) -> str:
        return (f"{self.student_name}: {self.correct_answers}/{self.total_questions} "
                f"({self.percentage:.1f}%) -> OCJENA {self.grade} ({self.grade_name})")

class ExamGrader:
    def __init__(self, reference_exam: Dict[int, str]):
        self.reference_exam = reference_exam
        self.evaluator = SimpleEvaluator()
        self.grade_assigner = make_grading_scale(min_pass=50.0)
    
    @log_grading
    def grade_single_student(self, student_name: str, answers: Dict[int, str]) -> ExamResult:

        correct = self.evaluator.evaluate(answers, self.reference_exam)
        total = len(self.reference_exam)
        percentage = (correct / total) * 100
        
        grade, grade_name = self.grade_assigner(percentage)
        
        return ExamResult(
            student_name=student_name,
            correct_answers=correct,
            total_questions=total,
            percentage=percentage,
            grade=grade,
            grade_name=grade_name
        )
    
    @time_measure
    @log_grading
    def grade_all_students(self, students: Dict[str, Dict[int, str]]) -> List[ExamResult]:
        results = []
        
        with ThreadPoolExecutor(max_workers=4) as executor:
            futures = {
                executor.submit(
                    self.grade_single_student, 
                    name, 
                    answers
                ): name for name, answers in students.items()
            }
            
            for future in futures:
                results.append(future.result())
        
        return sorted(results, key=lambda x: x.percentage, reverse=True)

def load_students_from_folder(folder: str) -> Dict[str, Dict[int, str]]:
    students: Dict[str, Dict[int, str]] = {}
    exams_path = Path(folder)

    if not exams_path.exists():
        print(f"Mapa '{folder}' ne postoji.")
        return students

    json_files = sorted(exams_path.glob("*.json"))
    if not json_files:
        print(f"Nema JSON datoteka u mapi '{folder}'.")
        return students

    for exam_file in json_files:
        try:
            data = json.loads(exam_file.read_text(encoding="utf-8"))
            answers = data.get("answers", data)

            normalized: Dict[int, str] = {}
            for key, value in answers.items():
                try:
                    q_num = int(key)
                except (TypeError, ValueError):
                    continue
                normalized[q_num] = value

            student_name = exam_file.stem
            students[student_name] = normalized
        except Exception as exc:
            print(f"Greška pri čitanju {exam_file.name}: {exc}")
    return students

class TestExamGrader(unittest.TestCase):
    def setUp(self):
        self.reference = {1: 'A', 2: 'B', 3: 'C', 4: 'A', 5: 'B'}
        self.grader = ExamGrader(self.reference)
    
    def test_evaluator_perfect_score(self):
        student = {1: 'A', 2: 'B', 3: 'C', 4: 'A', 5: 'B'}
        correct = self.grader.evaluator.evaluate(student, self.reference)
        self.assertEqual(correct, 5)
    
    def test_evaluator_partial_score(self):
        student = {1: 'A', 2: 'B', 3: 'C', 4: 'B', 5: 'B'}
        correct = self.grader.evaluator.evaluate(student, self.reference)
        self.assertEqual(correct, 4)
    
    def test_grading_scale_excellent(self):
        grade, name = self.grader.grade_assigner(95.0)
        self.assertEqual(grade, 5)
        self.assertEqual(name, "odličan")
    
    def test_grading_scale_good(self):
        grade, name = self.grader.grade_assigner(70.0)
        self.assertEqual(grade, 3)
        self.assertEqual(name, "dobar")
    
    def test_grading_scale_pass(self):
        grade, name = self.grader.grade_assigner(55.0)
        self.assertEqual(grade, 2)
        self.assertEqual(name, "dovoljan")
    
    def test_grading_scale_fail(self):
        grade, name = self.grader.grade_assigner(40.0)
        self.assertEqual(grade, 1)
        self.assertEqual(name, "nedovoljan")
    
    def test_closure_stats(self):
        checker = make_grading_scale()
        checker(80.0)
        checker(85.0)
        stats = checker.get_stats()
        
        self.assertEqual(stats['attempts'], 2)
        self.assertEqual(stats['last_percentage'], 85.0)
    
    def test_grade_single_student(self):
        student_answers = {1: 'A', 2: 'B', 3: 'C', 4: 'A', 5: 'B'}
        result = self.grader.grade_single_student("Marko", student_answers)
        
        self.assertEqual(result.correct_answers, 5)
        self.assertEqual(result.percentage, 100.0)
        self.assertEqual(result.grade, 5)

if __name__ == "__main__":
    from gui_grader import main
    main()
    
