"""
Tests for Matching Engine

Tests for ML-based agent-skill matching, price prediction, and delivery estimation.
"""

import sys
import os
# Add the src directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from datetime import datetime, timedelta
import unittest
import importlib.util

# Import models directly
sys.path.insert(0, 'src')

from datetime import datetime, timedelta
import unittest

from trustyclaw.models.matching import (
    TaskRequirements,
    RenterHistory,
    AgentRecommendation,
    SkillMatch,
    PricePrediction,
    TimeEstimate,
    DemandForecast,
    ComplexityLevel,
)

# Import matching module directly (bypass SDK __init__.py to avoid import issues)
matching_path = os.path.join(os.path.dirname(__file__), '..', '..', 'trustyclaw', 'sdk', 'matching.py')
spec = importlib.util.spec_from_file_location("matching_module", matching_path)
matching_module = importlib.util.module_from_spec(spec)
sys.modules['trustyclaw.sdk.matching'] = matching_module
spec.loader.exec_module(matching_module)

MatchingEngine = matching_module.MatchingEngine
get_matching_engine = matching_module.get_matching_engine
from trustyclaw.sdk.matching import MatchingEngine, get_matching_engine


class TestMatchingEngine(unittest.TestCase):
    """Tests for the MatchingEngine class"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.engine = get_matching_engine()
    
    def test_engine_initialization(self):
        """Test that engine initializes correctly"""
        self.assertIsNotNone(self.engine)
        self.assertIsInstance(self.engine, MatchingEngine)
    
    def test_recommend_agents_returns_list(self):
        """Test that recommend_agents returns a list"""
        task = TaskRequirements(
            title="Generate AI images",
            description="Create AI-generated images",
            required_skills=["AI", "Images"],
            category="image-generation",
            complexity=0.5,
        )
        
        recommendations = self.engine.recommend_agents(
            task_requirements=task,
            renter_history=None,
            budget=1000000,
        )
        
        self.assertIsInstance(recommendations, list)
        self.assertGreater(len(recommendations), 0)
    
    def test_recommend_agents_sorted_by_score(self):
        """Test that recommendations are sorted by overall score"""
        task = TaskRequirements(
            title="Python development",
            description="Build Python API",
            required_skills=["Python", "API"],
            category="code-generation",
            complexity=0.7,
        )
        
        recommendations = self.engine.recommend_agents(
            task_requirements=task,
            renter_history=None,
            budget=2000000,
        )
        
        # Check sorted by score descending
        for i in range(len(recommendations) - 1):
            self.assertGreaterEqual(
                recommendations[i].overall_score,
                recommendations[i + 1].overall_score,
            )
    
    def test_recommend_agents_within_budget(self):
        """Test that all recommendations are within budget"""
        task = TaskRequirements(
            title="Data analysis",
            description="Analyze data and create charts",
            required_skills=["Data", "Analysis"],
            category="data-analysis",
            complexity=0.4,
        )
        
        budget = 600000
        recommendations = self.engine.recommend_agents(
            task_requirements=task,
            renter_history=None,
            budget=budget,
        )
        
        for rec in recommendations:
            self.assertLessEqual(rec.price_prediction, budget)
    
    def test_recommendation_structure(self):
        """Test that recommendations have required fields"""
        task = TaskRequirements(
            title="Image generation",
            description="Create images",
            required_skills=["AI", "Art"],
            category="image-generation",
            complexity=0.3,
        )
        
        recommendations = self.engine.recommend_agents(
            task_requirements=task,
            renter_history=None,
            budget=1000000,
        )
        
        if recommendations:
            rec = recommendations[0]
            self.assertTrue(hasattr(rec, 'agent_address'))
            self.assertTrue(hasattr(rec, 'overall_score'))
            self.assertTrue(hasattr(rec, 'price_prediction'))
            self.assertTrue(hasattr(rec, 'estimated_delivery_hours'))
            self.assertTrue(hasattr(rec, 'confidence'))
    
    def test_recommendation_reasons(self):
        """Test that recommendations include reasons"""
        task = TaskRequirements(
            title="Code development",
            description="Develop code",
            required_skills=["Python", "Backend"],
            category="code-generation",
            complexity=0.6,
        )
        
        recommendations = self.engine.recommend_agents(
            task_requirements=task,
            renter_history=None,
            budget=2000000,
        )
        
        if recommendations:
            rec = recommendations[0]
            self.assertIsInstance(rec.reasons, list)
    
    def test_recommendation_risk_factors(self):
        """Test that recommendations include risk factors"""
        task = TaskRequirements(
            title="Image generation",
            description="Create images",
            required_skills=["AI", "Images"],
            category="image-generation",
            complexity=0.5,
        )
        
        recommendations = self.engine.recommend_agents(
            task_requirements=task,
            renter_history=None,
            budget=1000000,
        )
        
        if recommendations:
            rec = recommendations[0]
            self.assertIsInstance(rec.risk_factors, list)


class TestPricePrediction(unittest.TestCase):
    """Tests for price prediction functionality"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.engine = get_matching_engine()
    
    def test_predict_price_returns_prediction(self):
        """Test that predict_price returns a PricePrediction"""
        prediction = self.engine.predict_price(
            skill_id="image-generation",
            complexity=0.5,
            urgency=0.3,
            demand_forecast=0.5,
        )
        
        self.assertIsInstance(prediction, PricePrediction)
        self.assertGreater(prediction.predicted_price, 0)
    
    def test_price_within_range(self):
        """Test that actual price is within predicted range"""
        prediction = self.engine.predict_price(
            skill_id="code-generation",
            complexity=0.7,
            urgency=0.5,
            demand_forecast=0.6,
        )
        
        self.assertGreaterEqual(
            prediction.price_range_low,
            prediction.predicted_price * 0.8,
        )
        self.assertLessEqual(
            prediction.price_range_high,
            prediction.predicted_price * 1.2,
        )
    
    def test_price_confidence_in_range(self):
        """Test that confidence is within valid range"""
        prediction = self.engine.predict_price(
            skill_id="data-analysis",
            complexity=0.5,
            urgency=0.5,
            demand_forecast=0.5,
        )
        
        self.assertGreaterEqual(prediction.confidence, 0.0)
        self.assertLessEqual(prediction.confidence, 1.0)
    
    def test_complexity_affects_price(self):
        """Test that higher complexity increases price"""
        pred_simple = self.engine.predict_price(
            skill_id="image-generation",
            complexity=0.2,
            urgency=0.3,
            demand_forecast=0.5,
        )
        
        pred_complex = self.engine.predict_price(
            skill_id="image-generation",
            complexity=0.9,
            urgency=0.3,
            demand_forecast=0.5,
        )
        
        self.assertGreater(
            pred_complex.predicted_price,
            pred_simple.predicted_price,
        )
    
    def test_urgency_affects_price(self):
        """Test that higher urgency increases price"""
        pred_low = self.engine.predict_price(
            skill_id="image-generation",
            complexity=0.5,
            urgency=0.1,
            demand_forecast=0.5,
        )
        
        pred_high = self.engine.predict_price(
            skill_id="image-generation",
            complexity=0.5,
            urgency=0.9,
            demand_forecast=0.5,
        )
        
        self.assertGreater(
            pred_high.predicted_price,
            pred_low.predicted_price,
        )
    
    def test_demand_affects_price(self):
        """Test that demand affects price"""
        pred_low = self.engine.predict_price(
            skill_id="image-generation",
            complexity=0.5,
            urgency=0.3,
            demand_forecast=0.1,
        )
        
        pred_high = self.engine.predict_price(
            skill_id="image-generation",
            complexity=0.5,
            urgency=0.3,
            demand_forecast=0.9,
        )
        
        self.assertGreater(
            pred_high.predicted_price,
            pred_low.predicted_price,
        )
    
    def test_price_factors_present(self):
        """Test that prediction includes factor breakdown"""
        prediction = self.engine.predict_price(
            skill_id="writing",
            complexity=0.6,
            urgency=0.4,
            demand_forecast=0.5,
        )
        
        self.assertIsInstance(prediction.factors, dict)
        self.assertIn('complexity', prediction.factors)
        self.assertIn('urgency', prediction.factors)
        self.assertIn('demand', prediction.factors)
    
    def test_recommendation_present(self):
        """Test that prediction includes recommendation"""
        prediction = self.engine.predict_price(
            skill_id="translation",
            complexity=0.5,
            urgency=0.3,
            demand_forecast=0.5,
        )
        
        self.assertIsInstance(prediction.recommendation, str)
        self.assertGreater(len(prediction.recommendation), 0)


class TestDeliveryEstimation(unittest.TestCase):
    """Tests for delivery time estimation"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.engine = get_matching_engine()
    
    def test_estimate_delivery_returns_estimate(self):
        """Test that estimate_delivery_time returns a TimeEstimate"""
        estimate = self.engine.estimate_delivery_time(
            agent_address="GFeyFZLmvsw7aKHNoUUM84tCvgKf34ojbpKeKcuXDE5q",
            task_complexity=0.5,
            current_queue=2,
        )
        
        self.assertIsInstance(estimate, TimeEstimate)
        self.assertGreater(estimate.estimated_hours, 0)
    
    def test_delivery_earliest_before_latest(self):
        """Test that earliest time is before latest time"""
        estimate = self.engine.estimate_delivery_time(
            agent_address="HajVDaadfi6vxrt7y6SRZWBHVYCTscCc8Cwurbqbmg5B",
            task_complexity=0.6,
            current_queue=3,
        )
        
        self.assertLessEqual(estimate.earliest_hours, estimate.estimated_hours)
        self.assertLessEqual(estimate.estimated_hours, estimate.latest_hours)
    
    def test_queue_affects_delivery(self):
        """Test that higher queue increases delivery time"""
        est_low = self.engine.estimate_delivery_time(
            agent_address="3WaHbF7k9ced4d2wA8caUHq2v57ujD4J2c57L8wZXfhN",
            task_complexity=0.5,
            current_queue=0,
        )
        
        est_high = self.engine.estimate_delivery_time(
            agent_address="3WaHbF7k9ced4d2wA8caUHq2v57ujD4J2c57L8wZXfhN",
            task_complexity=0.5,
            current_queue=10,
        )
        
        self.assertGreater(
            est_high.estimated_hours,
            est_low.estimated_hours,
        )
    
    def test_complexity_affects_delivery(self):
        """Test that higher complexity increases delivery time"""
        est_simple = self.engine.estimate_delivery_time(
            agent_address="GFeyFZLmvsw7aKHNoUUM84tCvgKf34ojbpKeKcuXDE5q",
            task_complexity=0.1,
            current_queue=2,
        )
        
        est_complex = self.engine.estimate_delivery_time(
            agent_address="GFeyFZLmvsw7aKHNoUUM84tCvgKf34ojbpKeKcuXDE5q",
            task_complexity=0.9,
            current_queue=2,
        )
        
        self.assertGreater(
            est_complex.estimated_hours,
            est_simple.estimated_hours,
        )
    
    def test_delivery_confidence_in_range(self):
        """Test that confidence is within valid range"""
        estimate = self.engine.estimate_delivery_time(
            agent_address="HajVDaadfi6vxrt7y6SRZWBHVYCTscCc8Cwurbqbmg5B",
            task_complexity=0.5,
            current_queue=3,
        )
        
        self.assertGreaterEqual(estimate.confidence, 0.0)
        self.assertLessEqual(estimate.confidence, 1.0)
    
    def test_delivery_factors_present(self):
        """Test that estimate includes factor breakdown"""
        estimate = self.engine.estimate_delivery_time(
            agent_address="3WaHbF7k9ced4d2wA8caUHq2v57ujD4J2c57L8wZXfhN",
            task_complexity=0.5,
            current_queue=2,
        )
        
        self.assertIsInstance(estimate.factors, dict)
        self.assertIn('base_time', estimate.factors)
        self.assertIn('complexity_factor', estimate.factors)
        self.assertIn('queue_factor', estimate.factors)


class TestDemandForecasting(unittest.TestCase):
    """Tests for demand forecasting"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.engine = get_matching_engine()
    
    def test_forecast_demand_returns_forecast(self):
        """Test that forecast_demand returns a DemandForecast"""
        forecast = self.engine.forecast_demand("image-generation")
        
        self.assertIsInstance(forecast, DemandForecast)
    
    def test_demand_values_in_range(self):
        """Test that demand values are within valid range"""
        forecast = self.engine.forecast_demand("code-generation")
        
        self.assertGreaterEqual(forecast.current_demand, 0.0)
        self.assertLessEqual(forecast.current_demand, 1.0)
        self.assertGreaterEqual(forecast.predicted_demand, 0.0)
        self.assertLessEqual(forecast.predicted_demand, 1.0)
    
    def test_trend_is_valid(self):
        """Test that trend is a valid value"""
        forecast = self.engine.forecast_demand("data-analysis")
        
        self.assertIn(forecast.trend, ['rising', 'stable', 'declining'])
    
    def test_peak_hours_format(self):
        """Test that peak hours is a list of integers"""
        forecast = self.engine.forecast_demand("writing")
        
        self.assertIsInstance(forecast.peak_hours, list)
        for hour in forecast.peak_hours:
            self.assertIsInstance(hour, int)
            self.assertGreaterEqual(hour, 0)
            self.assertLessEqual(hour, 23)


class TestSkillMatching(unittest.TestCase):
    """Tests for skill matching algorithms"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.engine = get_matching_engine()
    
    def test_skill_match_structure(self):
        """Test that skill match has required fields"""
        task = TaskRequirements(
            title="AI Image Generation",
            description="Create AI images",
            required_skills=["AI", "Images"],
            category="image-generation",
            complexity=0.5,
        )
        
        recommendations = self.engine.recommend_agents(
            task_requirements=task,
            renter_history=None,
            budget=1000000,
        )
        
        if recommendations:
            rec = recommendations[0]
            self.assertIsInstance(rec.skill_matches, list)
            if rec.skill_matches:
                match = rec.skill_matches[0]
                self.assertIsInstance(match, SkillMatch)
                self.assertTrue(hasattr(match, 'match_score'))
                self.assertTrue(hasattr(match, 'skill_coverage'))
                self.assertTrue(hasattr(match, 'rating'))
    
    def test_match_score_in_range(self):
        """Test that match scores are within valid range"""
        task = TaskRequirements(
            title="Python Development",
            description="Build Python applications",
            required_skills=["Python"],
            category="code-generation",
            complexity=0.6,
        )
        
        recommendations = self.engine.recommend_agents(
            task_requirements=task,
            renter_history=None,
            budget=2000000,
        )
        
        for rec in recommendations:
            for match in rec.skill_matches:
                self.assertGreaterEqual(match.match_score, 0.0)
                self.assertLessEqual(match.match_score, 1.0)


class TestCompatibilityScoring(unittest.TestCase):
    """Tests for compatibility scoring"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.engine = get_matching_engine()
    
    def test_compatibility_with_history(self):
        """Test compatibility scoring with renter history"""
        history = RenterHistory(
            renter_address="test_renter",
            total_tasks=10,
            completed_tasks=8,
            average_rating_given=4.5,
            preferred_categories=["code-generation"],
            average_task_complexity=0.6,
            repeat_hire_rate=0.3,
        )
        
        task = TaskRequirements(
            title="Python API Development",
            description="Build Python API",
            required_skills=["Python", "API"],
            category="code-generation",
            complexity=0.6,
        )
        
        recommendations = self.engine.recommend_agents(
            task_requirements=task,
            renter_history=history,
            budget=2000000,
        )
        
        # Should have at least one recommendation
        self.assertGreater(len(recommendations), 0)
        
        # Check compatibility score is present and in range
        for rec in recommendations:
            self.assertGreaterEqual(rec.compatibility_score, 0.0)
            self.assertLessEqual(rec.compatibility_score, 1.0)
    
    def test_default_compatibility(self):
        """Test default compatibility when no history"""
        task = TaskRequirements(
            title="Image Generation",
            description="Create images",
            required_skills=["AI"],
            category="image-generation",
            complexity=0.4,
        )
        
        recommendations = self.engine.recommend_agents(
            task_requirements=task,
            renter_history=None,
            budget=1000000,
        )
        
        # Should still work without history
        self.assertGreater(len(recommendations), 0)


class TestMetrics(unittest.TestCase):
    """Tests for matching metrics"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.engine = get_matching_engine()
    
    def test_get_metrics(self):
        """Test that get_metrics returns valid metrics"""
        metrics = self.engine.get_metrics()
        
        self.assertIsInstance(metrics.total_matches, int)
        self.assertGreaterEqual(metrics.average_score, 0.0)
        self.assertLessEqual(metrics.average_score, 1.0)
        self.assertGreaterEqual(metrics.coverage_rate, 0.0)
        self.assertLessEqual(metrics.coverage_rate, 1.0)
    
    def test_record_outcome(self):
        """Test recording task outcome"""
        initial_count = len(self.engine._task_outcomes)
        
        self.engine.record_outcome(
            task_id="test_task_1",
            agent_address="GFeyFZLmvsw7aKHNoUUM84tCvgKf34ojbpKeKcuXDE5q",
            predicted_price=500000,
            actual_price=480000,
            predicted_hours=2,
            actual_hours=3,
            user_rating=4.5,
        )
        
        self.assertGreater(len(self.engine._task_outcomes), initial_count)


class TestTaskRequirements(unittest.TestCase):
    """Tests for TaskRequirements model"""
    
    def test_task_requirements_to_dict(self):
        """Test that TaskRequirements converts to dict"""
        task = TaskRequirements(
            title="Test Task",
            description="Test description",
            required_skills=["Python"],
            category="code-generation",
            complexity=0.5,
        )
        
        task_dict = task.to_dict()
        
        self.assertEqual(task_dict['title'], "Test Task")
        self.assertEqual(task_dict['category'], "code-generation")
        self.assertIn('required_skills', task_dict)
    
    def test_task_complexity_level(self):
        """Test complexity level enum"""
        task = TaskRequirements(
            title="Simple Task",
            complexity=0.2,
            complexity_level=ComplexityLevel.SIMPLE,
        )
        
        self.assertEqual(task.complexity_level, ComplexityLevel.SIMPLE)


def run_tests():
    """Run all tests"""
    suite = unittest.TestLoader().loadTestsFromTestCase(TestMatchingEngine)
    suite.addTests(unittest.TestLoader().loadTestsFromTestCase(TestPricePrediction))
    suite.addTests(unittest.TestLoader().loadTestsFromTestCase(TestDeliveryEstimation))
    suite.addTests(unittest.TestLoader().loadTestsFromTestCase(TestDemandForecasting))
    suite.addTests(unittest.TestLoader().loadTestsFromTestCase(TestSkillMatching))
    suite.addTests(unittest.TestLoader().loadTestsFromTestCase(TestCompatibilityScoring))
    suite.addTests(unittest.TestLoader().loadTestsFromTestCase(TestMetrics))
    suite.addTests(unittest.TestLoader().loadTestsFromTestCase(TestTaskRequirements))
    
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    return result.wasSuccessful()


if __name__ == "__main__":
    success = run_tests()
    exit(0 if success else 1)
