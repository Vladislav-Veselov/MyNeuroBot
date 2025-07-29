#!/usr/bin/env python3
"""
Data masking utility for personal information protection.
"""

import re
from typing import Tuple, Dict, Any, List

class DataMasker:
    """Utility class for masking personal information in text."""
    
    def __init__(self):
        # Email regex pattern
        self.email_pattern = re.compile(
            r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        )
        
        # Phone number patterns (various formats)
        self.phone_patterns = [
            # Russian phone numbers
            re.compile(r'\b\+?7[-.\s]?\(?(\d{3})\)?[-.\s]?(\d{3})[-.\s]?(\d{2})[-.\s]?(\d{2})\b'),
            re.compile(r'\b8[-.\s]?\(?(\d{3})\)?[-.\s]?(\d{3})[-.\s]?(\d{2})[-.\s]?(\d{2})\b'),
            # International format
            re.compile(r'\b\+?[1-9]\d{1,14}\b'),
            # Simple 10-15 digit numbers
            re.compile(r'\b\d{10,15}\b'),
        ]
        
        # Credit card patterns
        self.credit_card_pattern = re.compile(
            r'\b\d{4}[-\s]?\d{4}[-\s]?\d{4}[-\s]?\d{4}\b'
        )
        
        # Passport patterns (Russian)
        self.passport_pattern = re.compile(
            r'\b\d{4}\s?\d{6}\b'
        )
        
        # SSN pattern (US)
        self.ssn_pattern = re.compile(
            r'\b\d{3}-\d{2}-\d{4}\b'
        )
    
    def mask_email(self, text: str) -> Tuple[str, Dict[str, Any]]:
        """
        Mask email addresses in text.
        
        Args:
            text: Input text containing potential email addresses
            
        Returns:
            Tuple of (masked_text, mask_info)
        """
        masked_text = text
        mask_info = {
            'emails': [],
            'total_masked': 0
        }
        
        def replace_email(match):
            email = match.group(0)
            mask_info['emails'].append(email)
            mask_info['total_masked'] += 1
            
            # Create a masked version: user***@domain.com
            if '@' in email:
                username, domain = email.split('@', 1)
                if len(username) > 2:
                    masked_username = username[:2] + '***'
                else:
                    masked_username = '***'
                return f"{masked_username}@{domain}"
            else:
                return "***@***.com"
        
        masked_text = self.email_pattern.sub(replace_email, masked_text)
        return masked_text, mask_info
    
    def mask_phone(self, text: str) -> Tuple[str, Dict[str, Any]]:
        """
        Mask phone numbers in text.
        
        Args:
            text: Input text containing potential phone numbers
            
        Returns:
            Tuple of (masked_text, mask_info)
        """
        masked_text = text
        mask_info = {
            'phones': [],
            'total_masked': 0
        }
        
        def replace_phone(match):
            phone = match.group(0)
            mask_info['phones'].append(phone)
            mask_info['total_masked'] += 1
            
            # Create a masked version: +7 (***) ***-**-**
            if phone.startswith('+7') or phone.startswith('8'):
                return "+7 (***) ***-**-**"
            elif phone.startswith('+'):
                return "+*** *** *** ***"
            else:
                return "*** *** *** ***"
        
        for pattern in self.phone_patterns:
            masked_text = pattern.sub(replace_phone, masked_text)
        
        return masked_text, mask_info
    
    def mask_credit_card(self, text: str) -> Tuple[str, Dict[str, Any]]:
        """
        Mask credit card numbers in text.
        
        Args:
            text: Input text containing potential credit card numbers
            
        Returns:
            Tuple of (masked_text, mask_info)
        """
        masked_text = text
        mask_info = {
            'credit_cards': [],
            'total_masked': 0
        }
        
        def replace_credit_card(match):
            card = match.group(0)
            mask_info['credit_cards'].append(card)
            mask_info['total_masked'] += 1
            return "**** **** **** ****"
        
        masked_text = self.credit_card_pattern.sub(replace_credit_card, masked_text)
        return masked_text, mask_info
    
    def mask_passport(self, text: str) -> Tuple[str, Dict[str, Any]]:
        """
        Mask passport numbers in text.
        
        Args:
            text: Input text containing potential passport numbers
            
        Returns:
            Tuple of (masked_text, mask_info)
        """
        masked_text = text
        mask_info = {
            'passports': [],
            'total_masked': 0
        }
        
        def replace_passport(match):
            passport = match.group(0)
            mask_info['passports'].append(passport)
            mask_info['total_masked'] += 1
            return "**** ******"
        
        masked_text = self.passport_pattern.sub(replace_passport, masked_text)
        return masked_text, mask_info
    
    def mask_ssn(self, text: str) -> Tuple[str, Dict[str, Any]]:
        """
        Mask SSN numbers in text.
        
        Args:
            text: Input text containing potential SSN numbers
            
        Returns:
            Tuple of (masked_text, mask_info)
        """
        masked_text = text
        mask_info = {
            'ssns': [],
            'total_masked': 0
        }
        
        def replace_ssn(match):
            ssn = match.group(0)
            mask_info['ssns'].append(ssn)
            mask_info['total_masked'] += 1
            return "***-**-****"
        
        masked_text = self.ssn_pattern.sub(replace_ssn, masked_text)
        return masked_text, mask_info
    
    def mask_conversation_history(self, conversation_history: List[Dict[str, str]]) -> List[Dict[str, str]]:
        """
        Mask personal information in conversation history.
        
        Args:
            conversation_history: List of message dictionaries with 'role' and 'content' keys
            
        Returns:
            List of masked message dictionaries
        """
        masked_history = []
        
        for msg in conversation_history:
            if msg['role'] == 'user':
                # Mask user messages
                masked_content, _ = self.mask_all_personal_data(msg['content'])
                masked_history.append({
                    'role': msg['role'],
                    'content': masked_content
                })
            else:
                # Assistant messages don't need masking
                masked_history.append(msg)
        
        return masked_history
    
    def mask_all_personal_data(self, text: str) -> Tuple[str, Dict[str, Any]]:
        """
        Mask all types of personal data in text.
        
        Args:
            text: Input text containing potential personal information
            
        Returns:
            Tuple of (masked_text, mask_info)
        """
        if not text:
            return text, {}
        
        masked_text = text
        total_mask_info = {
            'emails': [],
            'phones': [],
            'credit_cards': [],
            'passports': [],
            'ssns': [],
            'total_masked': 0
        }
        
        # Apply all masking functions
        masked_text, email_info = self.mask_email(masked_text)
        masked_text, phone_info = self.mask_phone(masked_text)
        masked_text, card_info = self.mask_credit_card(masked_text)
        masked_text, passport_info = self.mask_passport(masked_text)
        masked_text, ssn_info = self.mask_ssn(masked_text)
        
        # Combine all mask info
        total_mask_info['emails'] = email_info.get('emails', [])
        total_mask_info['phones'] = phone_info.get('phones', [])
        total_mask_info['credit_cards'] = card_info.get('credit_cards', [])
        total_mask_info['passports'] = passport_info.get('passports', [])
        total_mask_info['ssns'] = ssn_info.get('ssns', [])
        total_mask_info['total_masked'] = (
            email_info.get('total_masked', 0) +
            phone_info.get('total_masked', 0) +
            card_info.get('total_masked', 0) +
            passport_info.get('total_masked', 0) +
            ssn_info.get('total_masked', 0)
        )
        
        return masked_text, total_mask_info

# Global instance
data_masker = DataMasker() 