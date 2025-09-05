#!/usr/bin/env python3
"""
Balance manager for tracking user balance and token consumption.
"""
import json
import os
from pathlib import Path
from typing import Dict, Any, Optional, Tuple
from datetime import datetime, timezone, timedelta
from auth import get_current_user_data_dir, auth
from model_manager import model_manager
from pricing_service import pricing_service

class BalanceManager:
    def __init__(self):
        self.balance_file_name = "balance.json"
        self.transactions_file_name = "transactions.json"
    
    def get_balance_file_path(self, username: str = None) -> Path:
        """Get the path to the user's balance file."""
        if username:
            user_data_dir = auth.get_user_data_directory(username)
        else:
            user_data_dir = get_current_user_data_dir()
        return user_data_dir / self.balance_file_name
    
    def get_transactions_file_path(self, username: str = None) -> Path:
        """Get the path to the user's transactions file."""
        if username:
            user_data_dir = auth.get_user_data_directory(username)
        else:
            user_data_dir = get_current_user_data_dir()
        return user_data_dir / self.transactions_file_name
    
    def get_balance(self, username: str = None) -> Dict[str, Any]:
        """Get current balance information."""
        try:
            balance_file = self.get_balance_file_path(username)
            balance_file.parent.mkdir(parents=True, exist_ok=True)
            
            if balance_file.exists():
                try:
                    with open(balance_file, 'r', encoding='utf-8') as f:
                        balance_data = json.load(f)
                except (json.JSONDecodeError, FileNotFoundError):
                    balance_data = self._create_default_balance()
            else:
                balance_data = self._create_default_balance()
            
            # Always ensure the current model is saved
            balance_data['current_model'] = model_manager.get_current_model()
            
            return balance_data
        except Exception as e:
            print(f"Error getting balance: {e}")
            return self._create_default_balance()
    
    def _create_default_balance(self) -> Dict[str, Any]:
        """Create default balance data."""
        return {
            "balance_rub": 1000.0,
            "total_input_tokens": 0,
            "total_output_tokens": 0,
            "total_cost_usd": 0.0,
            "total_cost_rub": 0.0,
            "current_model": model_manager.get_current_model(),
            "last_updated": datetime.now(timezone(timedelta(hours=3))).isoformat()
        }
    
    def save_balance(self, balance_data: Dict[str, Any], username: str = None) -> bool:
        """Save balance information to file."""
        try:
            balance_file = self.get_balance_file_path(username)
            balance_file.parent.mkdir(parents=True, exist_ok=True)
            
            # Always ensure the current model is saved
            balance_data['current_model'] = model_manager.get_current_model()
            
            with open(balance_file, 'w', encoding='utf-8') as f:
                json.dump(balance_data, f, ensure_ascii=False, indent=2)
            return True
        except Exception as e:
            print(f"Error saving balance: {e}")
            return False
    
    def calculate_token_cost(self, input_tokens: int, output_tokens: int, model: str) -> Tuple[float, float]:
        """Calculate cost in USD and RUB for given token usage."""
        try:
            # Use the pricing service to get current pricing data
            pricing_data = pricing_service.get_pricing_data()
            
            models = pricing_data.get('models', {})
            exchange_rates = pricing_data.get('exchange_rates', {})
            markup_coefficient = pricing_data.get('markup_coefficient', 1.0)
            
            if model not in models:
                print(f"Model {model} not found in pricing data")
                return 0.0, 0.0
            
            model_pricing = models[model]
            usd_to_rub = exchange_rates.get('USD_to_RUB', 95.5)
            
            # Calculate base costs
            input_cost_usd = (input_tokens / 1000) * model_pricing['input_price_per_1k_tokens']
            output_cost_usd = (output_tokens / 1000) * model_pricing['output_price_per_1k_tokens']
            base_cost_usd = input_cost_usd + output_cost_usd
            
            # Apply markup coefficient
            total_cost_usd = base_cost_usd * markup_coefficient
            total_cost_rub = total_cost_usd * usd_to_rub
            
            return total_cost_usd, total_cost_rub
            
        except Exception as e:
            print(f"Error calculating token cost: {e}")
            return 0.0, 0.0
    
    def consume_tokens(self, input_tokens: int, output_tokens: int, model: str, activity_type: str = "chatbot") -> bool:
        """Consume tokens and update balance."""
        try:
            # Calculate costs
            cost_usd, cost_rub = self.calculate_token_cost(input_tokens, output_tokens, model)
            
            # Get current balance
            balance_data = self.get_balance()
            
            # Update balance
            balance_data['balance_rub'] -= cost_rub
            balance_data['total_input_tokens'] += input_tokens
            balance_data['total_output_tokens'] += output_tokens
            balance_data['total_cost_usd'] += cost_usd
            balance_data['total_cost_rub'] += cost_rub
            balance_data['last_updated'] = datetime.now(timezone(timedelta(hours=3))).isoformat()
            
            # Save updated balance
            if not self.save_balance(balance_data):
                return False
            
            # Record transaction
            self.record_transaction(input_tokens, output_tokens, model, cost_usd, cost_rub, activity_type)
            
            return True
            
        except Exception as e:
            print(f"Error consuming tokens: {e}")
            return False
    
    def record_transaction(self, input_tokens: int, output_tokens: int, model: str, cost_usd: float, cost_rub: float, activity_type: str, username: str = None, is_credit: bool = False):
        """Record a transaction for history."""
        try:
            transactions_file = self.get_transactions_file_path(username)
            transactions_file.parent.mkdir(parents=True, exist_ok=True)
            
            # Load existing transactions
            transactions = []
            if transactions_file.exists():
                try:
                    with open(transactions_file, 'r', encoding='utf-8') as f:
                        transactions = json.load(f)
                except (json.JSONDecodeError, FileNotFoundError):
                    transactions = []
            
            # Add new transaction
            transaction = {
                "timestamp": datetime.now(timezone(timedelta(hours=3))).isoformat(),
                "activity_type": activity_type,
                "model": model,
                "input_tokens": input_tokens,
                "output_tokens": output_tokens,
                "cost_usd": cost_usd,
                "cost_rub": cost_rub,
                "balance_after": self.get_balance(username)['balance_rub'],
                "is_credit": is_credit  # New field to distinguish credits from debits
            }
            
            transactions.append(transaction)
            
            # Keep only last 100 transactions
            if len(transactions) > 100:
                transactions = transactions[-100:]
            
            # Save transactions
            with open(transactions_file, 'w', encoding='utf-8') as f:
                json.dump(transactions, f, ensure_ascii=False, indent=2)
                
        except Exception as e:
            print(f"Error recording transaction: {e}")
    
    def get_transactions(self, limit: int = 50, username: str = None) -> list:
        """Get recent transactions."""
        try:
            transactions_file = self.get_transactions_file_path(username)
            
            if not transactions_file.exists():
                return []
            
            with open(transactions_file, 'r', encoding='utf-8') as f:
                transactions = json.load(f)
            
            # Return most recent transactions
            return transactions[-limit:] if len(transactions) > limit else transactions
            
        except Exception as e:
            print(f"Error getting transactions: {e}")
            return []
    
    def refresh_balance_model(self) -> bool:
        """Refresh the current model in balance data to match model manager."""
        try:
            balance_data = self.get_balance()
            # Update the model to current
            balance_data['current_model'] = model_manager.get_current_model()
            return self.save_balance(balance_data)
        except Exception as e:
            print(f"Error refreshing balance model: {e}")
            return False
    
    # Admin methods for balance management
    def admin_increase_balance(self, username: str, amount_rub: float, reason: str = "Manual balance increase") -> Dict[str, Any]:
        """Admin method to increase user balance."""
        try:
            if not auth.user_exists(username):
                return {"success": False, "error": f"User {username} does not exist"}
            
            if amount_rub <= 0:
                return {"success": False, "error": "Amount must be positive"}
            
            # Get current balance
            balance_data = self.get_balance(username)
            
            # Increase balance
            old_balance = balance_data['balance_rub']
            balance_data['balance_rub'] += amount_rub
            balance_data['last_updated'] = datetime.now(timezone(timedelta(hours=3))).isoformat()
            
            # Save updated balance
            if not self.save_balance(balance_data, username):
                return {"success": False, "error": "Failed to save balance"}
            
            # Record admin transaction as a credit (positive transaction)
            self.record_transaction(
                input_tokens=0,
                output_tokens=0,
                model="admin",
                cost_usd=0.0,
                cost_rub=amount_rub,
                activity_type="balance_increase",
                username=username,
                is_credit=True  # Mark as credit transaction
            )
            
            return {
                "success": True,
                "message": f"Balance increased by ₽{amount_rub:.2f}",
                "old_balance": old_balance,
                "new_balance": balance_data['balance_rub'],
                "increase_amount": amount_rub
            }
            
        except Exception as e:
            print(f"Error increasing balance: {e}")
            return {"success": False, "error": str(e)}
    
    def admin_get_all_balances(self) -> Dict[str, Any]:
        """Admin method to get all user balances."""
        try:
            all_users = auth.get_all_users()
            balances = {}
            
            for username in all_users.keys():
                if username != "admin":  # Skip admin user
                    try:
                        balance_data = self.get_balance(username)
                        balances[username] = {
                            "balance_rub": balance_data.get('balance_rub', 0.0),
                            "total_cost_rub": balance_data.get('total_cost_rub', 0.0),
                            "total_input_tokens": balance_data.get('total_input_tokens', 0),
                            "total_output_tokens": balance_data.get('total_output_tokens', 0),
                            "last_updated": balance_data.get('last_updated', ''),
                            "current_model": balance_data.get('current_model', 'gpt-4o-mini')
                        }
                    except Exception as e:
                        print(f"Error getting balance for {username}: {e}")
                        balances[username] = {"error": str(e)}
            
            return {"success": True, "balances": balances}
            
        except Exception as e:
            print(f"Error getting all balances: {e}")
            return {"success": False, "error": str(e)}

# Global balance manager instance
balance_manager = BalanceManager() 