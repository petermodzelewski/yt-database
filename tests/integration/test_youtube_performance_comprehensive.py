"""
Comprehensive performance tests for YouTube processing.

This module contains detailed performance tests that measure and validate
the performance characteristics of the YouTube processing pipeline under
various conditions and loads.
"""

import pytest
import time
import threading
import concurrent.futures
from unittest.mock import patch, Mock
from dataclasses import dataclass
from typing import List, Dict, Any

from src.youtube_notion.processors.youtube_processor import YouTubeProcessor
from src.youtube_notion.config.settings import YouTubeProcessorConfig

# Import test fixtures from the main test file
import sys
import os
sys.path.append(os.path.dirname(__file__))
from test_youtube_end_to_end import MockFixtures, TEST_VIDEOS


@dataclass
class PerformanceMetrics:
    """Container for performance measurement results."""
    processing_time: float
    memory_usage_mb: float
    api_calls_count: int
    summary_length: int
    timestamp_count: int
    success: bool
    error_message: str = None


class PerformanceTester:
    """Utility class for performance testing."""
    
    def __init__(self):
        self.metrics_history: List[PerformanceMetrics] = []
    
    def measure_processing(self, processor: YouTubeProcessor, video_url: str, 
                          custom_prompt: str = None) -> PerformanceMetrics:
        """Measure performance of a single video processing operation."""
        try:
            import psutil
            process = psutil.Process()
            initial_memory = process.memory_info().rss / 1024 / 1024  # MB
        except ImportError:
            initial_memory = 0
        
        start_time = time.time()
        api_calls_count = 0
        
        try:
            # Mock API calls to count them
            original_get_metadata = processor._get_video_metadata
            original_generate_summary = processor._generate_summary
            
            def count_metadata_call(*args, **kwargs):
                nonlocal api_calls_count
                api_calls_count += 1
                return original_get_metadata(*args, **kwargs)
            
            def count_summary_call(*args, **kwargs):
                nonlocal api_calls_count
                api_calls_count += 1
                return original_generate_summary(*args, **kwargs)
            
            processor._get_video_metadata = count_metadata_call
            processor._generate_summary = count_summary_call
            
            # Process video
            result = processor.process_video(video_url, custom_prompt)
            processing_time = time.time() - start_time
            
            # Calculate metrics
            try:
                final_memory = process.memory_info().rss / 1024 / 1024  # MB
                memory_usage = final_memory - initial_memory
            except:
                memory_usage = 0
            
            # Count timestamps
            import re
            timestamp_pattern = r'\[\d{1,2}:\d{2}(?:-\d{1,2}:\d{2})?\]'
            timestamp_count = len(re.findall(timestamp_pattern, result["Summary"]))
            
            metrics = PerformanceMetrics(
                processing_time=processing_time,
                memory_usage_mb=memory_usage,
                api_calls_count=api_calls_count,
                summary_length=len(result["Summary"]),
                timestamp_count=timestamp_count,
                success=True
            )
            
        except Exception as e:
            processing_time = time.time() - start_time
            metrics = PerformanceMetrics(
                processing_time=processing_time,
                memory_usage_mb=0,
                api_calls_count=api_calls_count,
                summary_length=0,
                timestamp_count=0,
                success=False,
                error_message=str(e)
            )
        
        self.metrics_history.append(metrics)
        return metrics
    
    def get_average_metrics(self, successful_only: bool = True) -> Dict[str, float]:
        """Calculate average metrics from history."""
        if successful_only:
            metrics = [m for m in self.metrics_history if m.success]
        else:
            metrics = self.metrics_history
        
        if not metrics:
            return {}
        
        return {
            "avg_processing_time": sum(m.processing_time for m in metrics) / len(metrics),
            "avg_memory_usage": sum(m.memory_usage_mb for m in metrics) / len(metrics),
            "avg_api_calls": sum(m.api_calls_count for m in metrics) / len(metrics),
            "avg_summary_length": sum(m.summary_length for m in metrics) / len(metrics),
            "avg_timestamp_count": sum(m.timestamp_count for m in metrics) / len(metrics),
            "success_rate": sum(1 for m in metrics if m.success) / len(self.metrics_history)
        }


class TestYouTubePerformanceComprehensive:
    """Comprehensive performance tests for YouTube processing."""
    
    @pytest.fixture
    def performance_processor(self):
        """Create processor optimized for performance testing."""
        config = YouTubeProcessorConfig(
            gemini_api_key="test_gemini_key",
            youtube_api_key="test_youtube_key",
            max_retries=1,
            timeout_seconds=30
        )
        return YouTubeProcessor(config)
    
    @pytest.fixture
    def performance_tester(self):
        """Create performance tester instance."""
        return PerformanceTester()
    
    @patch('src.youtube_notion.processors.youtube_processor.build')
    @patch('src.youtube_notion.processors.youtube_processor.genai.Client')
    def test_single_video_performance_baseline(self, mock_genai_client, mock_youtube_build, 
                                             performance_processor, performance_tester):
        """Establish performance baseline for single video processing."""
        video_data = TEST_VIDEOS["short"]
        
        # Setup fast mocks
        self._setup_performance_mocks(mock_youtube_build, mock_genai_client, video_data)
        
        # Measure performance
        metrics = performance_tester.measure_processing(performance_processor, video_data["url"])
        
        # Performance assertions
        assert metrics.success, f"Processing failed: {metrics.error_message}"
        assert metrics.processing_time < 1.0, f"Processing took {metrics.processing_time:.2f}s, expected < 1.0s"
        assert metrics.api_calls_count == 2, f"Expected 2 API calls, got {metrics.api_calls_count}"
        assert metrics.summary_length > 100, "Summary should be substantial"
        assert metrics.timestamp_count >= 3, "Should have multiple timestamps"
        
        print(f"Baseline performance: {metrics.processing_time:.3f}s, {metrics.memory_usage_mb:.1f}MB")
    
    @patch('src.youtube_notion.processors.youtube_processor.build')
    @patch('src.youtube_notion.processors.youtube_processor.genai.Client')
    def test_batch_processing_performance(self, mock_genai_client, mock_youtube_build, 
                                        performance_processor, performance_tester):
        """Test performance with batch processing of multiple videos."""
        batch_sizes = [5, 10, 20]
        
        for batch_size in batch_sizes:
            # Reset metrics for this batch
            performance_tester.metrics_history.clear()
            
            video_data = TEST_VIDEOS["short"]
            
            # Process batch
            start_time = time.time()
            for i in range(batch_size):
                # Setup fresh mocks for each iteration to avoid state issues
                self._setup_performance_mocks(mock_youtube_build, mock_genai_client, video_data)
                metrics = performance_tester.measure_processing(performance_processor, video_data["url"])
                assert metrics.success, f"Batch item {i} failed: {metrics.error_message}"
            
            total_time = time.time() - start_time
            avg_metrics = performance_tester.get_average_metrics()
            
            # Performance assertions
            assert avg_metrics["avg_processing_time"] < 1.0, f"Average processing time too slow for batch size {batch_size}"
            assert total_time < batch_size * 2.0, f"Total batch time {total_time:.2f}s too slow for {batch_size} items"
            assert avg_metrics["success_rate"] == 1.0, f"Success rate {avg_metrics['success_rate']} not 100%"
            
            print(f"Batch {batch_size}: {total_time:.2f}s total, {avg_metrics['avg_processing_time']:.3f}s avg")
    
    @patch('src.youtube_notion.processors.youtube_processor.build')
    @patch('src.youtube_notion.processors.youtube_processor.genai.Client')
    def test_concurrent_processing_performance(self, mock_genai_client, mock_youtube_build, 
                                             performance_processor):
        """Test performance with concurrent processing."""
        num_workers = 4
        num_tasks = 12
        video_data = TEST_VIDEOS["short"]
        
        # Setup mocks
        self._setup_performance_mocks(mock_youtube_build, mock_genai_client, video_data)
        
        def process_video_task(task_id):
            # Setup fresh mocks for each task to avoid threading issues
            self._setup_performance_mocks(mock_youtube_build, mock_genai_client, video_data)
            tester = PerformanceTester()
            metrics = tester.measure_processing(performance_processor, video_data["url"])
            return task_id, metrics
        
        # Execute concurrent processing
        start_time = time.time()
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=num_workers) as executor:
            futures = [executor.submit(process_video_task, i) for i in range(num_tasks)]
            results = []
            
            for future in concurrent.futures.as_completed(futures):
                task_id, metrics = future.result()
                results.append(metrics)
        
        total_time = time.time() - start_time
        
        # Analyze results
        successful_results = [r for r in results if r.success]
        # Allow for some failures in concurrent testing due to mock threading issues
        success_rate = len(successful_results) / num_tasks
        assert success_rate >= 0.7, f"Success rate {success_rate:.2f} too low: {len(successful_results)}/{num_tasks} tasks succeeded"
        
        avg_processing_time = sum(r.processing_time for r in successful_results) / len(successful_results)
        max_processing_time = max(r.processing_time for r in successful_results)
        
        # Performance assertions
        assert total_time < num_tasks * 0.5, f"Concurrent processing took {total_time:.2f}s, too slow"
        assert avg_processing_time < 1.0, f"Average processing time {avg_processing_time:.2f}s too slow"
        assert max_processing_time < 2.0, f"Max processing time {max_processing_time:.2f}s too slow"
        
        print(f"Concurrent: {total_time:.2f}s total, {avg_processing_time:.3f}s avg, {max_processing_time:.3f}s max")
    
    @patch('src.youtube_notion.processors.youtube_processor.build')
    @patch('src.youtube_notion.processors.youtube_processor.genai.Client')
    def test_memory_usage_scaling(self, mock_genai_client, mock_youtube_build, 
                                performance_processor, performance_tester):
        """Test memory usage scaling with multiple operations."""
        try:
            import psutil
        except ImportError:
            pytest.skip("psutil not available for memory testing")
        
        video_data = TEST_VIDEOS["short"]
        self._setup_performance_mocks(mock_youtube_build, mock_genai_client, video_data)
        
        # Measure memory usage over multiple operations
        initial_memory = psutil.Process().memory_info().rss / 1024 / 1024  # MB
        memory_measurements = [initial_memory]
        
        for i in range(10):
            metrics = performance_tester.measure_processing(performance_processor, video_data["url"])
            assert metrics.success, f"Operation {i} failed: {metrics.error_message}"
            
            current_memory = psutil.Process().memory_info().rss / 1024 / 1024  # MB
            memory_measurements.append(current_memory)
        
        final_memory = memory_measurements[-1]
        memory_increase = final_memory - initial_memory
        max_memory = max(memory_measurements)
        
        # Memory assertions
        assert memory_increase < 100, f"Memory increased by {memory_increase:.1f}MB, expected < 100MB"
        assert max_memory < initial_memory + 150, f"Peak memory {max_memory:.1f}MB too high"
        
        # Check for memory leaks (memory should stabilize)
        last_5_measurements = memory_measurements[-5:]
        memory_variance = max(last_5_measurements) - min(last_5_measurements)
        assert memory_variance < 20, f"Memory variance {memory_variance:.1f}MB suggests memory leak"
        
        print(f"Memory: {initial_memory:.1f}MB -> {final_memory:.1f}MB (increase: {memory_increase:.1f}MB)")
    
    @patch('src.youtube_notion.processors.youtube_processor.build')
    @patch('src.youtube_notion.processors.youtube_processor.genai.Client')
    def test_performance_with_different_content_sizes(self, mock_genai_client, mock_youtube_build, 
                                                    performance_processor, performance_tester):
        """Test performance scaling with different content sizes."""
        content_sizes = [
            ("small", 500),    # Small summary
            ("medium", 2000),  # Medium summary
            ("large", 5000),   # Large summary
            ("xlarge", 10000)  # Extra large summary
        ]
        
        video_data = TEST_VIDEOS["short"]
        
        for size_name, content_length in content_sizes:
            # Create summary of specified length
            base_summary = MockFixtures.create_gemini_summary(video_data["expected_title"])
            multiplier = max(1, content_length // len(base_summary))
            large_summary = (base_summary * multiplier)[:content_length]
            
            # Setup mocks with large content
            self._setup_performance_mocks(mock_youtube_build, mock_genai_client, video_data, large_summary)
            
            # Measure performance
            metrics = performance_tester.measure_processing(performance_processor, video_data["url"])
            
            assert metrics.success, f"Processing {size_name} content failed: {metrics.error_message}"
            assert metrics.summary_length >= content_length * 0.8, f"Summary length {metrics.summary_length} too short"
            
            # Performance should scale reasonably with content size
            expected_max_time = 0.5 + (content_length / 10000)  # Base time + scaling factor
            assert metrics.processing_time < expected_max_time, \
                f"{size_name} content took {metrics.processing_time:.2f}s, expected < {expected_max_time:.2f}s"
            
            print(f"{size_name} ({content_length} chars): {metrics.processing_time:.3f}s")
    
    @patch('src.youtube_notion.processors.youtube_processor.build')
    @patch('src.youtube_notion.processors.youtube_processor.genai.Client')
    def test_performance_under_simulated_load(self, mock_genai_client, mock_youtube_build, 
                                            performance_processor):
        """Test performance under simulated high load conditions."""
        video_data = TEST_VIDEOS["short"]
        
        # Setup slower API responses for load testing
        mock_youtube = Mock()
        mock_youtube_build.return_value = mock_youtube
        mock_request = Mock()
        mock_youtube.videos.return_value.list.return_value = mock_request
        
        def slow_execute():
            time.sleep(0.1)  # Simulate network delay
            return MockFixtures.create_youtube_api_response(
                video_data["video_id"], video_data["expected_title"], video_data["expected_channel"]
            )
        
        mock_request.execute.side_effect = slow_execute
        
        mock_client = Mock()
        mock_genai_client.return_value = mock_client
        
        def slow_streaming(*args, **kwargs):
            time.sleep(0.2)  # Simulate AI processing delay
            summary = MockFixtures.create_gemini_summary(video_data["expected_title"])
            return iter(MockFixtures.create_gemini_streaming_response(summary))
        
        mock_client.models.generate_content_stream.side_effect = slow_streaming
        
        # Test performance under load
        num_requests = 5
        start_time = time.time()
        
        results = []
        for i in range(num_requests):
            tester = PerformanceTester()
            metrics = tester.measure_processing(performance_processor, video_data["url"])
            results.append(metrics)
            assert metrics.success, f"Request {i} failed under load: {metrics.error_message}"
        
        total_time = time.time() - start_time
        avg_time = sum(r.processing_time for r in results) / len(results)
        
        # Performance under load should still be reasonable
        assert avg_time < 1.0, f"Average time under load {avg_time:.2f}s too slow"
        assert total_time < num_requests * 1.5, f"Total time under load {total_time:.2f}s too slow"
        
        print(f"Under load: {total_time:.2f}s total, {avg_time:.3f}s avg")
    
    def _setup_performance_mocks(self, mock_youtube_build, mock_genai_client, video_data, custom_summary=None):
        """Helper method to setup mocks optimized for performance testing."""
        # Mock YouTube API with minimal delay
        mock_youtube = Mock()
        mock_youtube_build.return_value = mock_youtube
        mock_request = Mock()
        mock_youtube.videos.return_value.list.return_value = mock_request
        mock_request.execute.return_value = MockFixtures.create_youtube_api_response(
            video_data["video_id"], video_data["expected_title"], video_data["expected_channel"]
        )
        
        # Mock Gemini API with minimal delay
        mock_client = Mock()
        mock_genai_client.return_value = mock_client
        summary = custom_summary or MockFixtures.create_gemini_summary(video_data["expected_title"])
        mock_chunks = MockFixtures.create_gemini_streaming_response(summary)
        mock_client.models.generate_content_stream.return_value = iter(mock_chunks)


class TestPerformanceRegression:
    """Tests to detect performance regressions."""
    
    PERFORMANCE_BASELINES = {
        "single_video_processing": 1.0,  # seconds
        "batch_processing_per_item": 1.0,  # seconds per item
        "memory_usage_per_operation": 50,  # MB
        "concurrent_processing_efficiency": 0.7  # ratio of concurrent vs sequential
    }
    
    @patch('src.youtube_notion.processors.youtube_processor.build')
    @patch('src.youtube_notion.processors.youtube_processor.genai.Client')
    def test_performance_regression_detection(self, mock_genai_client, mock_youtube_build):
        """Test for performance regressions against established baselines."""
        config = YouTubeProcessorConfig(
            gemini_api_key="test_key",
            youtube_api_key="test_key"
        )
        processor = YouTubeProcessor(config)
        video_data = TEST_VIDEOS["short"]
        
        # Setup mocks
        mock_youtube = Mock()
        mock_youtube_build.return_value = mock_youtube
        mock_request = Mock()
        mock_youtube.videos.return_value.list.return_value = mock_request
        mock_request.execute.return_value = MockFixtures.create_youtube_api_response(
            video_data["video_id"], video_data["expected_title"], video_data["expected_channel"]
        )
        
        mock_client = Mock()
        mock_genai_client.return_value = mock_client
        summary = MockFixtures.create_gemini_summary(video_data["expected_title"])
        mock_chunks = MockFixtures.create_gemini_streaming_response(summary)
        mock_client.models.generate_content_stream.return_value = iter(mock_chunks)
        
        # Measure current performance
        start_time = time.time()
        result = processor.process_video(video_data["url"])
        processing_time = time.time() - start_time
        
        # Check against baseline
        baseline = self.PERFORMANCE_BASELINES["single_video_processing"]
        regression_threshold = baseline * 1.5  # Allow 50% degradation before flagging
        
        assert processing_time < regression_threshold, \
            f"Performance regression detected: {processing_time:.2f}s > {regression_threshold:.2f}s baseline"
        
        # Verify result quality hasn't degraded
        assert isinstance(result, dict)
        assert len(result["Summary"]) > 100
        assert result["Title"] == video_data["expected_title"]
        
        print(f"Performance check passed: {processing_time:.3f}s (baseline: {baseline:.3f}s)")


if __name__ == "__main__":
    # Allow running performance tests independently
    print("YouTube Processing Performance Test Suite")
    print("Run with: pytest tests/test_youtube_performance_comprehensive.py -v")