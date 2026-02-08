import json
import tempfile
import unittest
from pathlib import Path
from typing import Dict

import grader_project as grader


def _make_answers(reference: Dict[int, str], count: int) -> Dict[str, str]:
    return {str(i): reference[i] for i in range(1, count + 1)}


class TestGraderProject(unittest.TestCase):
    def test_grading_scale_thresholds(self):
        scale = grader.make_grading_scale(min_pass=50.0)
        self.assertEqual(scale(95.0)[0], 5)
        self.assertEqual(scale(85.0)[0], 4)
        self.assertEqual(scale(70.0)[0], 3)
        self.assertEqual(scale(55.0)[0], 2)
        self.assertEqual(scale(40.0)[0], 1)

    def test_grade_single_student_basic(self):
        reference = {1: 'A', 2: 'B', 3: 'C', 4: 'A', 5: 'D'}
        grader_instance = grader.ExamGrader(reference)
        student_answers = {1: 'A', 2: 'B', 3: 'C', 4: 'A', 5: 'D'}

        result = grader_instance.grade_single_student("Ana", student_answers)

        self.assertEqual(result.correct_answers, 5)
        self.assertEqual(result.total_questions, 5)
        self.assertEqual(result.percentage, 100.0)
        self.assertEqual(result.grade, 5)

    def test_load_students_from_folder(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            exam_path = Path(tmpdir) / "student.json"
            reference = {1: 'A', 2: 'B', 3: 'C'}
            answers = _make_answers(reference, 3)
            exam_path.write_text(json.dumps({"answers": answers}), encoding="utf-8")

            students = grader.load_students_from_folder(tmpdir)

            self.assertIn("student", students)
            self.assertEqual(students["student"][1], 'A')
            self.assertEqual(students["student"][2], 'B')
            self.assertEqual(students["student"][3], 'C')
