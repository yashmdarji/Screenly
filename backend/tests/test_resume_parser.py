import unittest
from backend.app.services.resume_parser import ResumeParserService

SAMPLE_ML_RESUME = """
Alex Chen
Email: alex.chen@example.com | Phone: 555-019-2834
OBJECTIVE: AI/ML Engineer
SKILLS: Python, PyTorch, Scikit-Learn, Docker, SQL, Backpropagation, Gradient Descent, RAG
PROJECTS:
- Built RAG-Based Document Intelligence Engine using PyTorch and FastAPI
- Neural Image Segmentation on Cityscapes dataset
EXPERIENCE: ML Intern at Tech Corp
"""


class TestResumeParser(unittest.TestCase):
    def test_contact_and_name_extraction(self):
        result = ResumeParserService.parse_resume(SAMPLE_ML_RESUME, target_role="AI/ML Engineer")
        self.assertEqual(result.candidate_name, "Alex Chen")
        self.assertEqual(result.email, "alex.chen@example.com")
        self.assertIsNotNone(result.phone)

    def test_skills_and_domain_categorization(self):
        result = ResumeParserService.parse_resume(SAMPLE_ML_RESUME, target_role="AI/ML Engineer")
        self.assertIn("python", result.raw_skills_list)
        self.assertIn("pytorch", result.raw_skills_list)
        self.assertIn("docker", result.raw_skills_list)
        self.assertTrue(len(result.domains_detected) > 0)
        self.assertGreater(result.matched_role_alignment, 0.2)


if __name__ == "__main__":
    unittest.main()
