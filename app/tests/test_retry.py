"""
Tests para el módulo de retry.

Tests unitarios que validan el comportamiento del retry decorator
con backoff exponencial.
"""

import pytest
import time
from unittest.mock import Mock, patch
from utils.retry import retry_with_backoff, RetryConfig


class TestRetryWithBackoff:
    """Tests para retry_with_backoff decorator."""
    
    def test_successful_call_no_retry(self):
        """Test que función exitosa no reintenta."""
        mock_func = Mock(return_value="success")
        
        @retry_with_backoff(max_retries=3)
        def test_func():
            return mock_func()
        
        result = test_func()
        
        assert result == "success"
        assert mock_func.call_count == 1
    
    def test_retry_on_exception(self):
        """Test que reintenta en excepción."""
        mock_func = Mock(side_effect=[
            ConnectionError("fail 1"),
            ConnectionError("fail 2"),
            "success"
        ])
        
        @retry_with_backoff(
            max_retries=3,
            initial_delay=0.1,
            exceptions=(ConnectionError,)
        )
        def test_func():
            return mock_func()
        
        result = test_func()
        
        assert result == "success"
        assert mock_func.call_count == 3
    
    def test_max_retries_exceeded(self):
        """Test que lanza excepción después de max_retries."""
        mock_func = Mock(side_effect=ConnectionError("persistent error"))
        
        @retry_with_backoff(
            max_retries=2,
            initial_delay=0.1,
            exceptions=(ConnectionError,)
        )
        def test_func():
            return mock_func()
        
        with pytest.raises(ConnectionError):
            test_func()
        
        assert mock_func.call_count == 3  # initial + 2 retries
    
    def test_backoff_timing(self):
        """Test que backoff aumenta exponencialmente."""
        call_times = []
        
        def failing_func():
            call_times.append(time.time())
            if len(call_times) < 3:
                raise ConnectionError("fail")
            return "success"
        
        @retry_with_backoff(
            max_retries=3,
            initial_delay=0.1,
            backoff_factor=2.0,
            exceptions=(ConnectionError,)
        )
        def test_func():
            return failing_func()
        
        test_func()
        
        # Verificar que delays aumentan
        assert len(call_times) == 3
        delay1 = call_times[1] - call_times[0]
        delay2 = call_times[2] - call_times[1]
        
        assert delay1 >= 0.1  # First delay
        assert delay2 >= 0.2  # Second delay (2x)
        assert delay2 > delay1  # Backoff exponencial
    
    def test_on_retry_callback(self):
        """Test que callback se llama en cada reintento."""
        callback_calls = []
        
        def on_retry_callback(error, attempt):
            callback_calls.append((error, attempt))
        
        mock_func = Mock(side_effect=[
            ValueError("fail 1"),
            ValueError("fail 2"),
            "success"
        ])
        
        @retry_with_backoff(
            max_retries=3,
            initial_delay=0.1,
            exceptions=(ValueError,),
            on_retry=on_retry_callback
        )
        def test_func():
            return mock_func()
        
        test_func()
        
        assert len(callback_calls) == 2  # 2 failures before success
        assert callback_calls[0][1] == 1  # First retry
        assert callback_calls[1][1] == 2  # Second retry


class TestRetryConfig:
    """Tests para RetryConfig."""
    
    def test_retry_config_decorator(self):
        """Test que RetryConfig aplica configuración correctamente."""
        config = RetryConfig(
            max_retries=2,
            initial_delay=0.1,
            exceptions=(ValueError,)
        )
        
        mock_func = Mock(side_effect=[ValueError(), ValueError(), "success"])
        
        @config.decorator
        def test_func():
            return mock_func()
        
        result = test_func()
        
        assert result == "success"
        assert mock_func.call_count == 3
    
    def test_predefined_configs(self):
        """Test que configuraciones predefinidas existen."""
        from utils.retry import BIGQUERY_RETRY, GEMINI_API_RETRY, NETWORK_RETRY
        
        assert isinstance(BIGQUERY_RETRY, RetryConfig)
        assert isinstance(GEMINI_API_RETRY, RetryConfig)
        assert isinstance(NETWORK_RETRY, RetryConfig)
        
        assert BIGQUERY_RETRY.max_retries == 5
        assert GEMINI_API_RETRY.max_retries == 3
        assert NETWORK_RETRY.max_retries == 3


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

