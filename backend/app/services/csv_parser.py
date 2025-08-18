import pandas as pd
from typing import List, Dict, Any, Tuple
from datetime import datetime
import re
import logging
from dataclasses import dataclass

logger = logging.getLogger(__name__)

@dataclass
class ParsingResult:
    """Result of CSV parsing with detailed statistics"""
    transactions: List[Dict[str, Any]]
    errors: List[Dict[str, Any]]
    warnings: List[Dict[str, Any]]
    statistics: Dict[str, Any]

class CSVParser:
    def __init__(self):
        # Extended date formats for better flexibility
        self.common_date_formats = [
            '%Y-%m-%d', '%m/%d/%Y', '%d/%m/%Y', '%Y/%m/%d',
            '%m-%d-%Y', '%d-%m-%Y', '%b %d, %Y', '%B %d, %Y',
            '%Y-%m-%d %H:%M:%S', '%m/%d/%Y %H:%M:%S', '%d/%m/%Y %H:%M:%S',
            '%Y-%m-%d %H:%M', '%m/%d/%Y %H:%M', '%d/%m/%Y %H:%M',
            '%Y%m%d', '%m%d%Y', '%d%m%Y',  # Compact formats
            '%b %d %Y', '%B %d %Y',  # Space-separated
            '%d-%b-%Y', '%d-%B-%Y',  # Day-first with month names
            '%Y-%b-%d', '%Y-%B-%d',  # Year-first with month names
        ]
        
        # Currency symbols and patterns for amount parsing
        self.currency_symbols = ['$', '€', '£', '¥', '₹', '₽', '₩', '₪', '₦', '₨', '₴', '₸', '₺', '₼', '₾', '₿']
        self.amount_patterns = [
            r'^[\s]*[+-]?[\d,]*\.?\d+[\s]*$',  # Basic number
            r'^[\s]*[+-]?[\d,]*\.?\d+[\s]*[A-Z]{3}[\s]*$',  # With currency code
            r'^[\s]*[A-Z]{3}[\s]*[+-]?[\d,]*\.?\d+[\s]*$',  # Currency code first
        ]
    
    def parse_dataframe(self, df: pd.DataFrame) -> ParsingResult:
        """Parse DataFrame and extract transaction data with comprehensive error tracking"""
        transactions = []
        errors = []
        warnings = []
        
        # Security validation first
        security_issues = self._validate_csv_security(df)
        if security_issues:
            errors.extend(security_issues)
            return ParsingResult(transactions, errors, warnings, self._get_statistics(transactions, errors, warnings))
        
        # Detect column mapping
        column_mapping = self._detect_columns(df.columns)
        
        # Log column mapping for debugging
        logger.info(f"Detected column mapping: {column_mapping}")
        
        # Validate required columns
        missing_required = []
        for required_field in ['date', 'description']:
            if required_field not in column_mapping:
                missing_required.append(required_field)
        
        # Check for amount format (either single amount or debit/credit)
        has_amount = 'amount' in column_mapping
        has_debit_credit = 'debit' in column_mapping and 'credit' in column_mapping
        
        if not has_amount and not has_debit_credit:
            missing_required.append('amount (or debit/credit columns)')
        
        if missing_required:
            error_msg = f"Missing required columns: {', '.join(missing_required)}"
            logger.error(error_msg)
            errors.append({
                'type': 'missing_required_columns',
                'message': error_msg,
                'details': {'missing_columns': missing_required}
            })
            return ParsingResult(transactions, errors, warnings, self._get_statistics(transactions, errors, warnings))
        
        # Process each row
        for index, row in df.iterrows():
            row_number = index + 1
            try:
                transaction = self._parse_row(row, column_mapping, row_number)
                if transaction:
                    transactions.append(transaction)
                    
                    # Check for potential issues and add warnings
                    row_warnings = self._check_for_warnings(transaction, row_number)
                    warnings.extend(row_warnings)
                    
            except Exception as e:
                error_detail = {
                    'row_number': row_number,
                    'error_type': type(e).__name__,
                    'message': str(e),
                    'raw_data': row.to_dict(),
                    'column_mapping': column_mapping
                }
                errors.append(error_detail)
                logger.error(f"Error parsing row {row_number}: {e}")
                logger.debug(f"Row {row_number} raw data: {row.to_dict()}")
        
        # Generate statistics
        statistics = self._get_statistics(transactions, errors, warnings)
        
        # Log summary
        logger.info(f"CSV parsing completed: {len(transactions)} successful, {len(errors)} errors, {len(warnings)} warnings")
        
        return ParsingResult(transactions, errors, warnings, statistics)
    
    def _validate_csv_security(self, df: pd.DataFrame) -> List[Dict[str, Any]]:
        """Validate CSV for security issues before processing"""
        security_errors = []
        
        # Check for excessive number of columns (potential memory exhaustion)
        if len(df.columns) > 100:
            security_errors.append({
                'type': 'security_violation',
                'message': f"Excessive number of columns: {len(df.columns)} (max: 100)",
                'details': {'column_count': len(df.columns), 'max_allowed': 100}
            })
        
        # Check for excessive number of rows (potential memory exhaustion)
        if len(df) > 1000000:  # 1 million rows
            security_errors.append({
                'type': 'security_violation',
                'message': f"Excessive number of rows: {len(df)} (max: 1,000,000)",
                'details': {'row_count': len(df), 'max_allowed': 1000000}
            })
        
        # Check for suspicious column names
        suspicious_column_patterns = [
            r'<script.*?>',
            r'javascript:',
            r'<?php',
            r'<%.*%>',
            r'eval\s*\(',
            r'exec\s*\(',
            r'system\s*\(',
            r'shell_exec\s*\(',
        ]
        
        for col in df.columns:
            col_str = str(col).lower()
            for pattern in suspicious_column_patterns:
                if re.search(pattern, col_str, re.IGNORECASE):
                    security_errors.append({
                        'type': 'security_violation',
                        'message': f"Suspicious column name detected: {col}",
                        'details': {'column_name': col, 'pattern': pattern}
                    })
        
        # Check for suspicious data patterns in first few rows (sample check)
        sample_size = min(10, len(df))
        if sample_size > 0:
            sample_df = df.head(sample_size)
            
            for index, row in sample_df.iterrows():
                for col, value in row.items():
                    if pd.isna(value):
                        continue
                    
                    value_str = str(value).lower()
                    
                    # Check for script injections
                    script_patterns = [
                        r'<script.*?>.*?</script>',
                        r'javascript:',
                        r'vbscript:',
                        r'<?php.*?\?>',
                        r'<%.*?%>',
                        r'eval\s*\(',
                        r'document\.cookie',
                        r'window\.location',
                        r'alert\s*\(',
                    ]
                    
                    for pattern in script_patterns:
                        if re.search(pattern, value_str, re.IGNORECASE | re.DOTALL):
                            security_errors.append({
                                'type': 'security_violation',
                                'message': f"Suspicious content detected in row {index + 1}, column '{col}': {pattern}",
                                'details': {
                                    'row_number': index + 1,
                                    'column': col,
                                    'pattern': pattern,
                                    'value_sample': value_str[:100]  # First 100 chars
                                }
                            })
                    
                    # Check for SQL injection patterns
                    sql_patterns = [
                        r'union\s+select',
                        r'insert\s+into',
                        r'delete\s+from',
                        r'update\s+.*\s+set',
                        r'drop\s+table',
                        r'create\s+table',
                        r'alter\s+table',
                        r'exec\s*\(',
                        r'sp_executesql',
                        r'xp_cmdshell',
                    ]
                    
                    for pattern in sql_patterns:
                        if re.search(pattern, value_str, re.IGNORECASE):
                            security_errors.append({
                                'type': 'security_violation',
                                'message': f"Potential SQL injection detected in row {index + 1}, column '{col}': {pattern}",
                                'details': {
                                    'row_number': index + 1,
                                    'column': col,
                                    'pattern': pattern,
                                    'value_sample': value_str[:100]
                                }
                            })
                    
                    # Check for excessive binary data in text fields
                    if isinstance(value, str) and len(value) > 0:
                        try:
                            # Check for high ratio of non-printable characters
                            non_printable = sum(1 for c in value if ord(c) < 32 and c not in '\t\n\r')
                            if len(value) > 0 and (non_printable / len(value)) > 0.1:
                                security_errors.append({
                                    'type': 'security_violation',
                                    'message': f"High ratio of non-printable characters in row {index + 1}, column '{col}'",
                                    'details': {
                                        'row_number': index + 1,
                                        'column': col,
                                        'non_printable_ratio': non_printable / len(value)
                                    }
                                })
                        except:
                            pass  # Skip if unable to analyze
        
        # Check for column name collisions with system fields
        system_reserved_names = [
            'id', 'user_id', 'password', 'token', 'session', 'admin',
            'root', 'system', 'config', 'database', 'schema'
        ]
        
        for col in df.columns:
            col_lower = str(col).lower()
            if col_lower in system_reserved_names:
                security_errors.append({
                    'type': 'security_warning',
                    'message': f"Column name '{col}' conflicts with system reserved name",
                    'details': {'column_name': col}
                })
        
        return security_errors
    
    def _check_for_warnings(self, transaction: Dict[str, Any], row_number: int) -> List[Dict[str, Any]]:
        """Check for potential issues and return warnings"""
        warnings = []
        
        # Check for very large amounts
        if abs(transaction['amount']) > 1000000:
            warnings.append({
                'row_number': row_number,
                'warning_type': 'large_amount',
                'message': f"Large amount detected: {transaction['amount']}",
                'details': {'amount': transaction['amount']}
            })
        
        # Check for very old dates
        if transaction['date'] < datetime(2000, 1, 1):
            warnings.append({
                'row_number': row_number,
                'warning_type': 'old_date',
                'message': f"Very old date detected: {transaction['date']}",
                'details': {'date': transaction['date'].isoformat()}
            })
        
        # Check for future dates
        if transaction['date'] > datetime.now():
            warnings.append({
                'row_number': row_number,
                'warning_type': 'future_date',
                'message': f"Future date detected: {transaction['date']}",
                'details': {'date': transaction['date'].isoformat()}
            })
        
        # Check for very short descriptions
        if len(transaction['description']) < 3:
            warnings.append({
                'row_number': row_number,
                'warning_type': 'short_description',
                'message': f"Very short description: '{transaction['description']}'",
                'details': {'description': transaction['description']}
            })
        
        # Check for zero amounts
        if transaction['amount'] == 0:
            warnings.append({
                'row_number': row_number,
                'warning_type': 'zero_amount',
                'message': "Zero amount transaction detected",
                'details': {'amount': transaction['amount']}
            })
        
        return warnings
    
    def _get_statistics(self, transactions: List[Dict], errors: List[Dict], warnings: List[Dict]) -> Dict[str, Any]:
        """Generate comprehensive parsing statistics"""
        total_rows = len(transactions) + len(errors)
        
        if total_rows == 0:
            return {
                'total_rows': 0,
                'successful_parsing': 0,
                'failed_parsing': 0,
                'success_rate': 0.0,
                'warning_count': 0,
                'error_types': {},
                'warning_types': {},
                'amount_range': {'min': 0, 'max': 0, 'avg': 0},
                'date_range': {'earliest': None, 'latest': None},
                'income_count': 0,
                'expense_count': 0
            }
        
        # Calculate success rate
        success_rate = (len(transactions) / total_rows) * 100 if total_rows > 0 else 0
        
        # Error type breakdown
        error_types = {}
        for error in errors:
            error_type = error.get('error_type', 'unknown')
            error_types[error_type] = error_types.get(error_type, 0) + 1
        
        # Warning type breakdown
        warning_types = {}
        for warning in warnings:
            warning_type = warning.get('warning_type', 'unknown')
            warning_types[warning_type] = warning_types.get(warning_type, 0) + 1
        
        # Amount statistics
        amounts = [t['amount'] for t in transactions if 'amount' in t]
        amount_range = {
            'min': min(amounts) if amounts else 0,
            'max': max(amounts) if amounts else 0,
            'avg': sum(amounts) / len(amounts) if amounts else 0
        }
        
        # Date range
        dates = [t['date'] for t in transactions if 'date' in t]
        date_range = {
            'earliest': min(dates) if dates else None,
            'latest': max(dates) if dates else None
        }
        
        # Income vs expense count
        income_count = sum(1 for t in transactions if t.get('is_income', False))
        expense_count = len(transactions) - income_count
        
        return {
            'total_rows': total_rows,
            'successful_parsing': len(transactions),
            'failed_parsing': len(errors),
            'success_rate': round(success_rate, 2),
            'warning_count': len(warnings),
            'error_types': error_types,
            'warning_types': warning_types,
            'amount_range': amount_range,
            'date_range': date_range,
            'income_count': income_count,
            'expense_count': expense_count
        }
    
    def _detect_columns(self, columns: pd.Index) -> Dict[str, str]:
        """Detect which columns contain what data"""
        column_mapping = {}
        columns_lower = [col.lower() for col in columns]
        
        # Date column detection
        date_keywords = ['date', 'transaction_date', 'posted_date', 'value_date', 'trans_date']
        for keyword in date_keywords:
            for i, col in enumerate(columns_lower):
                if keyword in col:
                    column_mapping['date'] = columns[i]
                    break
            if 'date' in column_mapping:
                break
        
        # Check for debit/credit format
        has_debit = any('debit' in col for col in columns_lower)
        has_credit = any('credit' in col for col in columns_lower)
        
        if has_debit and has_credit:
            # Use debit/credit format
            for i, col in enumerate(columns_lower):
                if 'debit' in col:
                    column_mapping['debit'] = columns[i]
                elif 'credit' in col:
                    column_mapping['credit'] = columns[i]
        else:
            # Single amount column detection
            amount_keywords = ['amount', 'transaction_amount', 'sum', 'value', 'total']
            for keyword in amount_keywords:
                for i, col in enumerate(columns_lower):
                    if keyword in col:
                        column_mapping['amount'] = columns[i]
                        break
                if 'amount' in column_mapping:
                    break
        
        # Description column detection
        desc_keywords = ['description', 'memo', 'notes', 'transaction_description', 'detail', 'narration', 'particulars']
        for keyword in desc_keywords:
            for i, col in enumerate(columns_lower):
                if keyword in col:
                    column_mapping['description'] = columns[i]
                    break
            if 'description' in column_mapping:
                break
        
        # Vendor column detection (optional)
        vendor_keywords = ['vendor', 'merchant', 'payee', 'company', 'account', 'party', 'beneficiary']
        for keyword in vendor_keywords:
            for i, col in enumerate(columns_lower):
                if keyword in col:
                    column_mapping['vendor'] = columns[i]
                    break
            if 'vendor' in column_mapping:
                break
        
        # Reference column detection (optional)
        ref_keywords = ['reference', 'ref', 'transaction_id', 'id', 'check_no', 'cheque_no']
        for keyword in ref_keywords:
            for i, col in enumerate(columns_lower):
                if keyword in col:
                    column_mapping['reference'] = columns[i]
                    break
            if 'reference' in column_mapping:
                break
        
        return column_mapping
    
    def _parse_row(self, row: pd.Series, column_mapping: Dict[str, str], row_number: int) -> Dict[str, Any]:
        """Parse a single row into transaction data"""
        transaction = {
            'row_number': row_number,
            'raw_data': row.to_dict()
        }
        
        # Parse date
        if 'date' in column_mapping:
            date_value = row[column_mapping['date']]
            transaction['date'] = self._parse_date(date_value, row_number)
        else:
            raise ValueError("Date column not found")
        
        # Parse amount (handle both single amount and debit/credit format)
        if 'debit' in column_mapping and 'credit' in column_mapping:
            # Debit/credit format
            debit_value = row[column_mapping['debit']]
            credit_value = row[column_mapping['credit']]
            
            debit_amount = self._parse_amount(debit_value, row_number) if pd.notna(debit_value) else 0.0
            credit_amount = self._parse_amount(credit_value, row_number) if pd.notna(credit_value) else 0.0
            
            # Debits are negative (expenses), credits are positive (income)
            if debit_amount > 0:
                transaction['amount'] = -debit_amount  # Negative for expenses
                transaction['is_income'] = False
            elif credit_amount > 0:
                transaction['amount'] = credit_amount  # Positive for income
                transaction['is_income'] = True
            else:
                raise ValueError("Both debit and credit are zero or empty")
        elif 'amount' in column_mapping:
            # Single amount column
            amount_value = row[column_mapping['amount']]
            transaction['amount'] = self._parse_amount(amount_value, row_number)
        else:
            raise ValueError("Neither amount column nor debit/credit columns found")
        
        # Parse description
        if 'description' in column_mapping:
            description_value = row[column_mapping['description']]
            if pd.isna(description_value):
                raise ValueError("Description value is empty")
            transaction['description'] = str(description_value).strip()
            if not transaction['description']:
                raise ValueError("Description is empty after stripping")
        else:
            raise ValueError("Description column not found")
        
        # Parse vendor (optional)
        if 'vendor' in column_mapping:
            vendor_value = row[column_mapping['vendor']]
            if pd.notna(vendor_value):
                transaction['vendor'] = str(vendor_value).strip()
        elif 'reference' in column_mapping:
            # Use reference as vendor if no vendor column exists
            ref_value = row[column_mapping['reference']]
            if pd.notna(ref_value):
                transaction['vendor'] = str(ref_value).strip()
        
        # Parse reference (optional)
        if 'reference' in column_mapping:
            ref_value = row[column_mapping['reference']]
            if pd.notna(ref_value):
                transaction['reference'] = str(ref_value).strip()
        
        # Determine if income or expense (only for single amount format)
        if 'debit' not in column_mapping or 'credit' not in column_mapping:
            transaction['is_income'] = transaction['amount'] > 0
        
        return transaction
    
    def _parse_date(self, date_value: Any, row_number: int) -> datetime:
        """Parse date value into datetime object with enhanced error handling"""
        if pd.isna(date_value):
            raise ValueError("Date value is empty")
        
        # If already datetime
        if isinstance(date_value, datetime):
            return date_value
        
        # Try to parse as string
        date_str = str(date_value).strip()
        
        # Handle empty strings
        if not date_str:
            raise ValueError("Date value is empty string")
        
        # Try common formats first
        for fmt in self.common_date_formats:
            try:
                return datetime.strptime(date_str, fmt)
            except ValueError:
                continue
        
        # Try pandas parsing with various options
        try:
            # Try with different parsing options
            parsed_date = pd.to_datetime(date_str, errors='raise', infer_datetime_format=True)
            return parsed_date.to_pydatetime()
        except Exception as e:
            # Try with more flexible parsing
            try:
                parsed_date = pd.to_datetime(date_str, errors='raise', format='mixed')
                return parsed_date.to_pydatetime()
            except:
                # Last resort: try with dayfirst option
                try:
                    parsed_date = pd.to_datetime(date_str, errors='raise', dayfirst=True)
                    return parsed_date.to_pydatetime()
                except:
                    raise ValueError(f"Could not parse date: '{date_str}'. Supported formats: YYYY-MM-DD, MM/DD/YYYY, DD/MM/YYYY, etc.")
    
    def _parse_amount(self, amount_value: Any, row_number: int) -> float:
        """Parse amount value into float with enhanced error handling"""
        if pd.isna(amount_value):
            raise ValueError("Amount value is empty")
        
        # If already numeric
        if isinstance(amount_value, (int, float)):
            return float(amount_value)
        
        # Parse string
        amount_str = str(amount_value).strip()
        
        # Handle empty strings
        if not amount_str:
            raise ValueError("Amount value is empty string")
        
        # Remove currency symbols
        for symbol in self.currency_symbols:
            amount_str = amount_str.replace(symbol, '')
        
        # Remove common currency codes (3-letter codes like USD, EUR, etc.)
        amount_str = re.sub(r'\b[A-Z]{3}\b', '', amount_str)
        
        # Remove spaces and other non-numeric characters except digits, decimal point, minus, plus, and comma
        amount_str = re.sub(r'[^\d.,+-]', '', amount_str)
        
        # Handle different decimal separators
        if ',' in amount_str and '.' in amount_str:
            # European format: 1.234,56 -> 1234.56
            if amount_str.find(',') > amount_str.find('.'):
                amount_str = amount_str.replace('.', '').replace(',', '.')
            else:
                # US format: 1,234.56 -> 1234.56
                amount_str = amount_str.replace(',', '')
        elif ',' in amount_str:
            # Check if comma is decimal separator (European format)
            parts = amount_str.split(',')
            if len(parts) == 2 and len(parts[1]) <= 2:
                # Likely decimal separator
                amount_str = amount_str.replace(',', '.')
            else:
                # Likely thousands separator
                amount_str = amount_str.replace(',', '')
        
        # Validate the cleaned string
        if not re.match(r'^[+-]?\d*\.?\d+$', amount_str):
            raise ValueError(f"Could not parse amount: '{amount_value}' -> cleaned: '{amount_str}'")
        
        try:
            return float(amount_str)
        except ValueError:
            raise ValueError(f"Could not convert to float: '{amount_str}' (original: '{amount_value}')")
