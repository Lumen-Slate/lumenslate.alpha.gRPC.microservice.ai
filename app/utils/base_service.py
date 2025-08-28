"""
Base service class for all gRPC service implementations.
Provides common functionality and utilities.
"""

import logging
import asyncio
import re
from concurrent.futures import ThreadPoolExecutor
from typing import Any, Dict, Union


class BaseService:
    """Base class for all gRPC service implementations"""
    
    def __init__(self, logger=None):
        self.logger = logger or logging.getLogger(__name__)
        self.executor = ThreadPoolExecutor(max_workers=10)

    async def _run_in_executor(self, func, *args):
        """Helper to run sync functions in executor"""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(self.executor, func, *args)

    def _mask_sensitive_data(self, data: Union[str, Dict[str, Any]], mask_char: str = "*") -> Union[str, Dict[str, Any]]:
        """Mask sensitive data to prevent secrets from being logged"""
        sensitive_patterns = [
            r'GOOGLE_API_KEY', r'API_KEY', r'TOKEN', r'SECRET', r'PASSWORD',
            r'CREDENTIALS', r'AUTH', r'BEARER', r'SERVICE_ACCOUNT', r'CLIENT_SECRET'
        ]
        
        def should_mask_key(key: str) -> bool:
            return any(re.search(pattern, key, re.IGNORECASE) for pattern in sensitive_patterns)
        
        def mask_value(value: str, show_length: int = 4) -> str:
            if not value or len(value) <= show_length:
                return mask_char * 8
            return value[:show_length] + mask_char * (len(value) - show_length)
        
        if isinstance(data, dict):
            masked_dict = {}
            for key, value in data.items():
                if should_mask_key(str(key)):
                    if isinstance(value, str):
                        masked_dict[key] = mask_value(value)
                    else:
                        masked_dict[key] = f"<{type(value).__name__}:masked>"
                elif isinstance(value, dict):
                    masked_dict[key] = self._mask_sensitive_data(value, mask_char)
                elif isinstance(value, str) and re.match(r'^[a-zA-Z0-9_\-\.]{20,}$', value):
                    masked_dict[key] = mask_value(value)
                else:
                    masked_dict[key] = value
            return masked_dict
        elif isinstance(data, str):
            # Mask API key patterns in strings
            if re.match(r'^AIza[a-zA-Z0-9_\-]{35}', data):
                return mask_value(data)
            return data
        return data

    def _handle_exception(self, context, error, operation_name):
        """Common exception handling for gRPC methods"""
        self.logger.exception(f"[{operation_name}] Failed with error: {str(error)}")
        try:
            import grpc
            context.set_code(grpc.StatusCode.INTERNAL)
            context.set_details(str(error))
        except ImportError:
            # Fallback if grpc is not available
            pass

    def _log_success(self, operation_name, additional_info=None):
        """Common success logging - only for errors or warnings in production"""
        # Reduced logging for production - only log significant events
        pass

    def _safe_log_request(self, operation_name, request_data):
        """Safely log request without exposing sensitive data - reduced for production"""
        # Only log in development or when debugging specific issues
        pass

    def _safe_log_response(self, operation_name, response_data):
        """Safely log response without exposing sensitive data - reduced for production"""
        # Only log in development or when debugging specific issues  
        pass
