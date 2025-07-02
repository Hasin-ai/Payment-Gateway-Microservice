import re
import json
from typing import Any, Dict, Optional
from app.core.config import settings

class DataMasker:
    def __init__(self):
        self.sensitive_patterns = {
            'password': re.compile(r'password|passwd|pwd', re.IGNORECASE),
            'token': re.compile(r'token|key|secret|auth', re.IGNORECASE),
            'credit_card': re.compile(r'\b\d{4}[\s-]?\d{4}[\s-]?\d{4}[\s-]?\d{4}\b'),
            'email': re.compile(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'),
            'phone': re.compile(r'\b\d{3}[-.]?\d{3}[-.]?\d{4}\b'),
            'ssn': re.compile(r'\b\d{3}-?\d{2}-?\d{4}\b')
        }
    
    def mask_sensitive_fields(self, data: Optional[Any]) -> Optional[Any]:
        """Mask sensitive data in various data types"""
        if data is None:
            return None
        
        if isinstance(data, dict):
            return self._mask_dict(data)
        elif isinstance(data, list):
            return [self.mask_sensitive_fields(item) for item in data]
        elif isinstance(data, str):
            return self._mask_string(data)
        else:
            return data
    
    def _mask_dict(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Mask sensitive fields in dictionary"""
        masked_data = {}
        
        for key, value in data.items():
            if self._is_sensitive_field(key):
                masked_data[key] = self._mask_value(value)
            else:
                masked_data[key] = self.mask_sensitive_fields(value)
        
        return masked_data
    
    def _mask_string(self, data: str) -> str:
        """Mask sensitive patterns in string"""
        masked_data = data
        
        # Mask credit card numbers
        masked_data = self.sensitive_patterns['credit_card'].sub('****-****-****-****', masked_data)
        
        # Mask email addresses (partially)
        def mask_email(match):
            email = match.group()
            local, domain = email.split('@')
            if len(local) > 2:
                masked_local = local[:2] + '*' * (len(local) - 2)
            else:
                masked_local = '*' * len(local)
            return f"{masked_local}@{domain}"
        
        masked_data = self.sensitive_patterns['email'].sub(mask_email, masked_data)
        
        # Mask phone numbers
        masked_data = self.sensitive_patterns['phone'].sub('***-***-****', masked_data)
        
        # Mask SSN
        masked_data = self.sensitive_patterns['ssn'].sub('***-**-****', masked_data)
        
        return masked_data
    
    def _is_sensitive_field(self, field_name: str) -> bool:
        """Check if field name indicates sensitive data"""
        field_lower = field_name.lower()
        
        # Check against configured sensitive fields
        for sensitive_field in settings.SENSITIVE_FIELDS:
            if sensitive_field.lower() in field_lower:
                return True
        
        # Check against patterns
        for pattern_name, pattern in self.sensitive_patterns.items():
            if pattern.search(field_name):
                return True
        
        return False
    
    def _mask_value(self, value: Any) -> str:
        """Mask a sensitive value"""
        if value is None:
            return None
        
        if isinstance(value, str):
            if len(value) <= 4:
                return "*" * len(value)
            else:
                return value[:2] + "*" * (len(value) - 4) + value[-2:]
        else:
            return "[REDACTED]"
